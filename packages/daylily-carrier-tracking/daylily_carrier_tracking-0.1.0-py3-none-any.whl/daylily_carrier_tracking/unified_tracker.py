import re
from typing import Any, Dict, Optional

from daylily_carrier_tracking.fedex_tracker import FedexTracker, default_ops_meta


def detect_carrier(tracking_number: str) -> str:
    """Best-effort carrier guess.

    This is intentionally conservative; ambiguous numeric-only numbers exist.
    """
    tn = (tracking_number or "").strip().upper()
    if tn.startswith("1Z"):
        return "ups"
    if re.fullmatch(r"[0-9]{12}|[0-9]{15}|[0-9]{20,22}", tn):
        # Could be FedEx or USPS depending on the range/format; default to fedex.
        return "fedex"
    if re.fullmatch(r"[A-Z]{2}[0-9]{9}[A-Z]{2}", tn):
        return "usps"
    return "fedex"


class UnifiedTracker:
    """Carrier-agnostic tracker facade.

    For now:
      - fedex is implemented via FedexTracker
      - ups/usps raise NotImplementedError (needs API creds + endpoint wiring)
    """

    def __init__(
        self,
        fedex_config_proj_name: str = "fedex",
        fedex_config_proj_env: str = "prod",
        fedex_config: Optional[Dict[str, Any]] = None,
    ):
        # Lazily construct per-carrier trackers so that requesting an
        # unimplemented carrier (UPS/USPS) does not require unrelated creds.
        self._fedex_config_proj_name = fedex_config_proj_name
        self._fedex_config_proj_env = fedex_config_proj_env
        self._fedex_config = fedex_config
        self._fedex: Optional[FedexTracker] = None

    def _get_fedex(self) -> FedexTracker:
        if self._fedex is None:
            self._fedex = FedexTracker(
                config_proj_name=self._fedex_config_proj_name,
                config_proj_env=self._fedex_config_proj_env,
                config=self._fedex_config,
            )
        return self._fedex

    def track(self, tracking_number: str, carrier: str = "auto", include_raw: bool = True) -> Dict[str, Any]:
        carrier = (carrier or "auto").lower()
        if carrier == "auto":
            carrier = detect_carrier(tracking_number)

        if carrier == "fedex":
            return self._get_fedex().track(tracking_number, include_raw=include_raw)
        if carrier in {"ups", "usps"}:
            raise NotImplementedError(
                f"Carrier '{carrier}' is not implemented yet. "
                "Next step: add carrier auth + tracking endpoint wiring and a normalizer."
            )
        raise ValueError("carrier must be one of: auto, fedex, ups, usps")

    def track_ops_meta(self, tracking_number: str, carrier: str = "auto") -> Dict[str, Any]:
        carrier_in = (carrier or "auto").lower()
        effective = detect_carrier(tracking_number) if carrier_in == "auto" else carrier_in

        try:
            ops = self.track(tracking_number, carrier=effective, include_raw=False)["ops_meta"]
            # Safety rail: ensure normalized response includes the carrier id.
            if isinstance(ops, dict) and not ops.get("Carrier"):
                ops["Carrier"] = effective
            return ops
        except NotImplementedError:
            ops = default_ops_meta()
            ops["Carrier"] = effective
            return ops
