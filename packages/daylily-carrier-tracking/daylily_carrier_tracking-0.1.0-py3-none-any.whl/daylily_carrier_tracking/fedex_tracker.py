import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import requests


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    if not value:
        return None
    # Python 3.10 datetime.fromisoformat() does not accept trailing 'Z'
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _weekday_name(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dt.weekday()]


def _get_nested(d: Dict[str, Any], path: Tuple[str, ...], default: Any = "") -> Any:
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _default_ops_meta() -> Dict[str, Any]:
    return {
        "Carrier": "",
        "Pickup_dt": "",
        "Delivery_dt": "",
        "Tender_dt": "",
        "Ship_dt": "",
        # Match README invalid/expired example.
        "Transit_Time_sec": -1,
        "Delivery_Status": "na",
        "Origin_state": "na",
        "Destination_state": "na",
        "Destination_city": "",
        "Origin_city": "",
        "Delivery_weekday": "",
        "Ship_weekday": "",
        "Origin_state_alt": "",
        "Destination_state_alt": "",
    }


def default_ops_meta() -> Dict[str, Any]:
    """Public helper exposing the legacy ops-meta schema defaults."""
    return _default_ops_meta()


def normalize_fedex_track_ops_meta(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the legacy 'ops-meta' fields from a FedEx Track API v1 response.

    This is intentionally conservative and returns "na"/empty values when the
    payload is missing or indicates NOTFOUND.
    """

    ops = _default_ops_meta()
    ops["Carrier"] = "fedex"

    track_results = _get_nested(raw, ("output", "completeTrackResults"), default=[])
    if not track_results:
        return ops

    trk_res_list = track_results[0].get("trackResults") or []
    if not trk_res_list:
        return ops

    trk_res = trk_res_list[0]  # match README behavior: single summarized record
    if isinstance(trk_res, dict) and trk_res.get("error"):
        return ops

    # For a valid payload (no per-tracking error), keep Transit_Time_sec empty
    # unless we can compute it from dates.
    ops["Transit_Time_sec"] = ""

    ops["Origin_state"] = _get_nested(
        trk_res,
        ("originLocation", "locationContactAndAddress", "address", "stateOrProvinceCode"),
        default=ops["Origin_state"],
    )
    ops["Origin_city"] = _get_nested(
        trk_res,
        ("originLocation", "locationContactAndAddress", "address", "city"),
        default=ops["Origin_city"],
    )
    ops["Origin_state_alt"] = ops["Origin_state"]

    ops["Destination_state"] = _get_nested(
        trk_res,
        ("lastUpdatedDestinationAddress", "stateOrProvinceCode"),
        default=ops["Destination_state"],
    )
    ops["Destination_city"] = _get_nested(
        trk_res,
        ("lastUpdatedDestinationAddress", "city"),
        default=ops["Destination_city"],
    )
    ops["Destination_state_alt"] = _get_nested(
        trk_res,
        ("serviceDetail", "shortDescription"),
        default=ops["Destination_state_alt"],
    )

    status = _get_nested(trk_res, ("latestStatusDetail", "statusByLocale"), default="")
    if status:
        ops["Delivery_Status"] = status

    date_and_times = trk_res.get("dateAndTimes") or []
    for st in date_and_times:
        if not isinstance(st, dict):
            continue
        t = st.get("type")
        v = st.get("dateTime")
        if not t or not v:
            continue
        if "ACTUAL_PICKUP" in t:
            ops["Pickup_dt"] = v
        elif "ACTUAL_DELIVERY" in t:
            ops["Delivery_dt"] = v
        elif t == "SHIP" or "SHIP" in t:
            ops["Ship_dt"] = v
        elif "ACTUAL_TENDER" in t:
            ops["Tender_dt"] = v

    delivery_dt = _parse_iso_datetime(ops["Delivery_dt"])
    ship_dt = _parse_iso_datetime(ops["Ship_dt"])
    tender_dt = _parse_iso_datetime(ops["Tender_dt"])

    ops["Delivery_weekday"] = _weekday_name(delivery_dt)
    ops["Ship_weekday"] = _weekday_name(ship_dt)

    transit = ""
    if delivery_dt and tender_dt:
        transit = (delivery_dt - tender_dt).total_seconds()
    elif delivery_dt and ship_dt:
        transit = (delivery_dt - ship_dt).total_seconds()
    ops["Transit_Time_sec"] = transit

    return ops


def _looks_not_found(raw: Dict[str, Any]) -> bool:
    track_results = _get_nested(raw, ("output", "completeTrackResults"), default=[])
    if not track_results:
        return False
    trk_res_list = track_results[0].get("trackResults") or []
    if not trk_res_list:
        return False
    trk_res = trk_res_list[0]
    err = trk_res.get("error") if isinstance(trk_res, dict) else None
    code = (err or {}).get("code", "")
    return "NOTFOUND" in str(code).upper()


@dataclass
class FedexApiCallMeta:
    api: str
    url: str
    http_status: Optional[int]
    elapsed_ms: Optional[int]


class FedexOAuthTokenProvider:
    def __init__(self, oauth_url: str, client_id: str, client_secret: str):
        self._oauth_url = oauth_url
        self._client_id = client_id
        self._client_secret = client_secret

        self._token: Optional[str] = None
        self._expires_at: Optional[datetime] = None

    def get_token(self) -> str:
        now = datetime.now(timezone.utc)
        if self._token and self._expires_at and now < self._expires_at:
            return self._token

        payload = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = requests.post(self._oauth_url, data=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError(f"FedEx OAuth response missing access_token: {json.dumps(data)[:500]}")
        expires_in = int(data.get("expires_in", 3300))

        # Refresh a bit early.
        self._token = token
        self._expires_at = now + timedelta(seconds=max(60, expires_in - 60))
        return token


class FedexTracker:
    """Unified FedEx tracker.

    - Supports Track API v1 out of the box.
    - Supports an optional 'Ship API v1 tracking-like endpoint' if configured.

    You can route via api_preference:
      - 'track'  : Track API only
      - 'ship'   : Ship endpoint only (requires ship_track_url)
      - 'auto'   : Track first; if NOTFOUND and ship is configured, try ship
    """

    def __init__(
        self,
        config_proj_name: str = "fedex",
        config_proj_env: str = "prod",
        config: Optional[Dict[str, Any]] = None,
        track_url: str = "https://apis.fedex.com/track/v1/trackingnumbers",
        ship_track_url: Optional[str] = None,
    ):
        if config is None:
            cfg: Dict[str, Any]
            # Preferred location (centralized):
            #   ~/.config/daylily-carrier-tracking/<proj>_<env>.yaml
            try:
                from daylily_carrier_tracking.config import config_path, load_yaml_mapping

                new_path = config_path(config_proj_name, config_proj_env)
                if new_path.exists():
                    cfg = load_yaml_mapping(new_path)
                else:
                    raise FileNotFoundError(str(new_path))
            except Exception:
                # Backward-compatible fallback:
                #   ~/.config/<proj>/<proj>_<env>.yaml  (yaml_config_day)
                try:
                    import yaml_config_day.config_manager as YCM  # type: ignore
                except ModuleNotFoundError as e:
                    raise ModuleNotFoundError(
                        "No config found in the new default location (~/.config/daylily-carrier-tracking/) "
                        "and yaml_config_day is not installed for legacy config loading. "
                        "Either install yaml_config_day, or create a config file at: "
                        f"~/.config/daylily-carrier-tracking/{config_proj_name}_{config_proj_env}.yaml, "
                        "or pass config={...} when constructing FedexTracker."
                    ) from e

                yconfig = YCM.ProjectConfigManager(config_proj_name, config_proj_env)
                cfg = yconfig.get_config()
        else:
            cfg = dict(config)

        oauth_url = cfg.get("oauth_url") or cfg.get("api_url")
        if not oauth_url:
            raise ValueError("Missing oauth_url/api_url in config")

        self._track_url = cfg.get("track_url") or track_url
        self._ship_track_url = cfg.get("ship_track_url") or ship_track_url

        self._token_provider = FedexOAuthTokenProvider(
            oauth_url=oauth_url,
            client_id=cfg["client_id"],
            client_secret=cfg["client_secret"],
        )

    def _post_json(self, url: str, payload: Dict[str, Any], api_name: str) -> Tuple[Dict[str, Any], FedexApiCallMeta]:
        token = self._token_provider.get_token()
        headers = {
            "Content-Type": "application/json",
            "X-locale": "en_US",
            "Authorization": "Bearer " + token,
        }
        started = time.time()
        resp = requests.post(url, data=json.dumps(payload), headers=headers)
        elapsed_ms = int((time.time() - started) * 1000)
        http_status = getattr(resp, "status_code", None)
        data = resp.json()
        return data, FedexApiCallMeta(api=api_name, url=url, http_status=http_status, elapsed_ms=elapsed_ms)

    def auth_token(self) -> str:
        return self._token_provider.get_token()

    def track_raw(self, tracking_number: str, api_preference: str = "auto") -> Tuple[Dict[str, Any], FedexApiCallMeta]:
        payload = {
            "includeDetailedScans": True,
            "trackingInfo": [{"trackingNumberInfo": {"trackingNumber": str(tracking_number)}}],
        }

        api_preference = (api_preference or "auto").lower()
        if api_preference not in {"auto", "track", "ship"}:
            raise ValueError("api_preference must be one of: auto, track, ship")

        if api_preference in {"track", "auto"}:
            raw, meta = self._post_json(self._track_url, payload, api_name="track_v1")
            if api_preference == "track":
                return raw, meta
            if not _looks_not_found(raw) or not self._ship_track_url:
                return raw, meta

        if not self._ship_track_url:
            raise RuntimeError("Ship API fallback requested but ship_track_url is not configured")
        raw, meta = self._post_json(self._ship_track_url, payload, api_name="ship_v1")
        return raw, meta

    def track_ops_meta(self, tracking_number: str, api_preference: str = "auto") -> Dict[str, Any]:
        raw, _ = self.track_raw(tracking_number, api_preference=api_preference)
        return normalize_fedex_track_ops_meta(raw)

    def track(self, tracking_number: str, api_preference: str = "auto", include_raw: bool = True) -> Dict[str, Any]:
        raw, meta = self.track_raw(tracking_number, api_preference=api_preference)
        out = {
            "carrier": "fedex",
            "tracking_number": str(tracking_number),
            "source": {
                "api": meta.api,
                "url": meta.url,
                "http_status": meta.http_status,
                "elapsed_ms": meta.elapsed_ms,
            },
            "ops_meta": normalize_fedex_track_ops_meta(raw),
        }
        if include_raw:
            out["raw"] = raw
        return out
