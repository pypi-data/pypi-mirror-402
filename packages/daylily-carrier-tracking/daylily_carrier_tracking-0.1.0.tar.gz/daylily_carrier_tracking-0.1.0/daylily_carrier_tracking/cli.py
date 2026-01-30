import argparse
import datetime
import json
import os
import subprocess
import sys
from getpass import getpass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from daylily_carrier_tracking.config import config_path, load_yaml_mapping, write_yaml_mapping
from daylily_carrier_tracking.fedex_tracker import FedexTracker
from daylily_carrier_tracking.unified_tracker import UnifiedTracker, detect_carrier


# Keep completion scripts available from the installed console-script entrypoint
# (i.e. without needing a repo checkout).
_BASH_COMPLETION_FALLBACK = """# Bash tab completion for `tday`.
#
# Usage (one-shot):
#   source <(tday completion bash)
#
# Usage (repo checkout):
#   source /path/to/daylily-carrier-tracking/completions/tday.bash
#
# Notes:
# - This registers completion for the command name `tday` only.
# - It does NOT register completion for `./tday` or `tracking_day`.

_tday_complete() {
  local cur prev
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev=""
  if [ "$COMP_CWORD" -ge 1 ]; then
    prev="${COMP_WORDS[COMP_CWORD-1]}"
  fi

  local subcmds="test configure track doctor completion fedex ups usps"
  local global_opts="--pretty --no-color -h --help"

  # Value completion for flags that take an argument.
  case "$prev" in
    --carrier)
      COMPREPLY=( $(compgen -W "auto fedex ups usps" -- "$cur") )
      return 0
      ;;
    --api-preference)
      COMPREPLY=( $(compgen -W "auto track ship" -- "$cur") )
      return 0
      ;;
    --env)
      COMPREPLY=( $(compgen -W "prod test sandbox dev" -- "$cur") )
      return 0
      ;;
    --path|--config-path)
      COMPREPLY=( $(compgen -f -- "$cur") )
      return 0
      ;;
  esac

  # Find the first subcommand (global flags may appear before/after).
  local cmd=""
  local i
  for ((i=1; i<${#COMP_WORDS[@]}; i++)); do
    case "${COMP_WORDS[i]}" in
      test|configure|track|doctor|completion|fedex|ups|usps)
        cmd="${COMP_WORDS[i]}"
        break
        ;;
    esac
  done

  if [ -z "$cmd" ]; then
    if [[ "$cur" == -* ]]; then
      COMPREPLY=( $(compgen -W "$global_opts" -- "$cur") )
    else
      COMPREPLY=( $(compgen -W "$subcmds" -- "$cur") )
    fi
    return 0
  fi

  # `tday configure <carrier>` positional completion.
  if [ "$cmd" = "configure" ]; then
    local cmd_idx=-1
    for ((i=1; i<${#COMP_WORDS[@]}; i++)); do
      if [ "${COMP_WORDS[i]}" = "configure" ]; then
        cmd_idx=$i
        break
      fi
    done
    if [ "$cmd_idx" -ge 0 ] && [ "$COMP_CWORD" -eq $((cmd_idx + 1)) ]; then
      COMPREPLY=( $(compgen -W "fedex ups usps" -- "$cur") )
      return 0
    fi
  fi

  # `tday completion <shell>` positional completion.
  if [ "$cmd" = "completion" ]; then
    local cmd_idx=-1
    for ((i=1; i<${#COMP_WORDS[@]}; i++)); do
      if [ "${COMP_WORDS[i]}" = "completion" ]; then
        cmd_idx=$i
        break
      fi
    done
    if [ "$cmd_idx" -ge 0 ] && [ "$COMP_CWORD" -eq $((cmd_idx + 1)) ]; then
      COMPREPLY=( $(compgen -W "bash zsh" -- "$cur") )
      return 0
    fi
  fi

  local opts=""
  case "$cmd" in
    test)
      opts="$global_opts --test-fedex --test-ups --test-usps"
      ;;
    configure)
      opts="$global_opts --env --path --skip-validate"
      ;;
    track)
      opts="$global_opts --carrier --no-raw --api-preference"
      ;;
    doctor)
      opts="$global_opts --all --carrier --env --config-path --no-network --tracking-number --json"
      ;;
    completion)
      opts="$global_opts"
      ;;
    fedex)
      opts="$global_opts --api-preference --no-raw"
      ;;
    ups|usps)
      opts="$global_opts --no-raw"
      ;;
  esac

  if [[ "$cur" == -* ]]; then
    COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
  else
    COMPREPLY=()
  fi
  return 0
}

complete -F _tday_complete tday
"""


_ZSH_COMPLETION_FALLBACK = """#compdef tday

# Zsh tab completion for `tday`.
#
# One-shot:
#   source <(tday completion zsh)
#
# Install (example):
#   mkdir -p ~/.zsh/completions
#   tday completion zsh > ~/.zsh/completions/_tday
#   # then ensure ~/.zsh/completions is in $fpath and compinit is enabled

_tday() {
  local -a subcmds global_opts
  subcmds=(test configure track doctor completion fedex ups usps)
  global_opts=(--pretty --no-color -h --help)

  # Find the first subcommand (global flags may appear before/after).
  local cmd=""
  local w
  for w in $words; do
    if (( ${subcmds[(I)$w]} )); then
      cmd="$w"
      break
    fi
  done

  local prev=${words[CURRENT-1]}
  case $prev in
    --carrier)
      _values 'carrier' auto fedex ups usps
      return
      ;;
    --api-preference)
      _values 'api preference' auto track ship
      return
      ;;
    --env)
      _values 'env' prod test sandbox dev
      return
      ;;
    --path|--config-path)
      _files
      return
      ;;
  esac

  if [[ -z "$cmd" ]]; then
    if [[ ${words[CURRENT]} == -* ]]; then
      _values 'options' $global_opts
    else
      _values 'command' $subcmds
    fi
    return
  fi

  local cmd_i=${words[(i)$cmd]}
  if [[ $cmd == configure && $CURRENT -eq $((cmd_i + 1)) ]]; then
    _values 'carrier' fedex ups usps
    return
  fi

  if [[ $cmd == completion && $CURRENT -eq $((cmd_i + 1)) ]]; then
    _values 'shell' bash zsh
    return
  fi

  local -a opts
  case $cmd in
    test)
      opts=($global_opts --test-fedex --test-ups --test-usps)
      ;;
    configure)
      opts=($global_opts --env --path --skip-validate)
      ;;
    track)
      opts=($global_opts --carrier --no-raw --api-preference)
      ;;
    doctor)
      opts=($global_opts --all --carrier --env --config-path --no-network --tracking-number --json)
      ;;
    completion)
      opts=($global_opts)
      ;;
    fedex)
      opts=($global_opts --api-preference --no-raw)
      ;;
    ups|usps)
      opts=($global_opts --no-raw)
      ;;
  esac

  if [[ ${words[CURRENT]} == -* ]]; then
    _values 'options' $opts
  fi
}

compdef _tday tday
"""


def _print_json(obj: Dict[str, Any], pretty: bool) -> None:
    if pretty:
        print(json.dumps(obj, indent=2, sort_keys=True))
    else:
        print(json.dumps(obj))


def _stderr_is_tty() -> bool:
    try:
        return bool(sys.stderr.isatty())
    except Exception:
        return False


def _color_enabled(no_color: bool) -> bool:
    if no_color:
        return False
    if os.environ.get("NO_COLOR"):
        return False
    return _stderr_is_tty()


def _c(text: str, code: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"\033[{code}m{text}\033[0m"


def _ok(text: str, enabled: bool) -> str:
    return _c(text, "32", enabled)  # green


def _warn(text: str, enabled: bool) -> str:
    return _c(text, "33", enabled)  # yellow


def _err(text: str, enabled: bool) -> str:
    return _c(text, "31", enabled)  # red


def _note(text: str, enabled: bool) -> str:
    return _c(text, "36", enabled)  # cyan


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _default_config_path(carrier: str, env: str) -> Path:
    # Centralized config dir: ~/.config/daylily-carrier-tracking/<carrier>_<env>.yaml
    return config_path(carrier, env)


def _prompt(label: str, default: Optional[str] = None, secret: bool = False, required: bool = False) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        prompt = f"{label}{suffix}: "
        raw = getpass(prompt) if secret else input(prompt)
        raw = (raw or "").strip()
        if raw:
            return raw
        if default is not None and default != "":
            return default
        if not required:
            return ""
        print("Value is required.")


def _utc_timestamp_compact() -> str:
    """UTC timestamp suitable for filenames."""

    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _prompt_yes_no(prompt: str, default: bool = False) -> bool:
    suffix = " [Y/n]" if default else " [y/N]"
    raw = input(f"{prompt}{suffix}: ")
    raw = (raw or "").strip().lower()
    if not raw:
        return bool(default)
    return raw in {"y", "yes"}


def _run_subprocess(cmd: Sequence[str], cwd: Optional[Path] = None) -> int:
    p = subprocess.run(list(cmd), cwd=str(cwd) if cwd else None)
    return int(getattr(p, "returncode", 1) or 0)


def build_parser() -> argparse.ArgumentParser:
    # Do not hardcode `prog` so installed entrypoints (tday) and repo wrappers
    # (tracking_day/tday) show the correct command name in --help output.
    p = argparse.ArgumentParser(
        description=(
            "Unified multi-carrier tracking CLI. "
            "Commands: test, configure, track. "
            "FedEx is implemented; UPS/USPS are scaffolded."
        ),
    )

    # Keep these on the top-level parser so `tday --help` advertises them and
    # users can still write `tday --pretty track ...`.
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colored status output")

    # Also attach common flags to subcommands so users can write the more
    # natural `tday track ... --pretty` / `tday track ... --no-color`.
    common = argparse.ArgumentParser(add_help=False)
    # Use SUPPRESS so subparsers don't overwrite values already parsed from the
    # top-level parser (e.g. `tday --pretty track ...`).
    common.add_argument(
        "--no-color",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Disable ANSI colored status output",
    )
    json_out = argparse.ArgumentParser(add_help=False)
    json_out.add_argument(
        "--pretty",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Pretty-print JSON output",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    test = sub.add_parser("test", parents=[common], help="Run unit tests")
    test.add_argument(
        "--test-fedex",
        action="store_true",
        help="Run only FedEx-related tests (pattern: tests/test_fedex_*.py)",
    )
    test.add_argument(
        "--test-ups",
        action="store_true",
        help="Run only UPS-related tests (pattern: tests/test_ups_*.py)",
    )
    test.add_argument(
        "--test-usps",
        action="store_true",
        help="Run only USPS-related tests (pattern: tests/test_usps_*.py)",
    )

    cfg = sub.add_parser("configure", parents=[common], help="Interactive credential setup wizard")
    cfg.add_argument("carrier", choices=["fedex", "ups", "usps"], help="Carrier to configure")
    cfg.add_argument("--env", default="prod", help="Config environment name (default: prod)")
    cfg.add_argument(
        "--path",
        default=None,
        help=(
            "Override output YAML path (default: "
            "~/.config/daylily-carrier-tracking/<carrier>_<env>.yaml)"
        ),
    )
    cfg.add_argument("--skip-validate", action="store_true", help="Do not attempt a live credential validation call")

    track = sub.add_parser("track", parents=[common, json_out], help="Live tracking call (prints JSON result)")
    track.add_argument("tracking_number", help="Tracking number")
    track.add_argument(
        "--carrier",
        default="auto",
        choices=["auto", "fedex", "ups", "usps"],
        help="Carrier selection (default: auto via detect_carrier())",
    )
    track.add_argument("--no-raw", action="store_true", help="Omit raw carrier payload from JSON output")
    track.add_argument(
        "--api-preference",
        default="auto",
        choices=["auto", "track", "ship"],
        help="FedEx only: route to track/ship endpoint (default: auto)",
    )

    # Legacy compatibility (do not duplicate logic; main() maps these to track).
    fedex = sub.add_parser(
        "fedex",
        parents=[common, json_out],
        help="(deprecated) Alias of: track --carrier fedex",
    )
    fedex.add_argument("tracking_number")
    fedex.add_argument("--api-preference", default="auto", choices=["auto", "track", "ship"], help="Route to track/ship endpoint")
    fedex.add_argument("--no-raw", action="store_true", help="Omit raw response")

    ups = sub.add_parser("ups", parents=[common, json_out], help="(deprecated) Alias of: track --carrier ups")
    ups.add_argument("tracking_number")
    ups.add_argument("--no-raw", action="store_true", help="Omit raw response")

    usps = sub.add_parser("usps", parents=[common, json_out], help="(deprecated) Alias of: track --carrier usps")
    usps.add_argument("tracking_number")
    usps.add_argument("--no-raw", action="store_true", help="Omit raw response")

    doctor = sub.add_parser(
        "doctor",
        parents=[common],
        help="Diagnose configuration + (optionally) test live FedEx OAuth/track",
    )
    doctor.add_argument(
        "--all",
        action="store_true",
        help="Run diagnostics for all carriers (fedex/ups/usps) and emit one aggregated JSON report (implies --json).",
    )
    doctor.add_argument(
        "--carrier",
        default="fedex",
        choices=["auto", "fedex", "ups", "usps"],
        help="Carrier to diagnose (default: fedex)",
    )
    doctor.add_argument("--env", default="prod", help="Config environment name (default: prod)")
    doctor.add_argument(
        "--config-path",
        default=None,
        help="Override config YAML path (otherwise uses ~/.config/daylily-carrier-tracking/<carrier>_<env>.yaml)",
    )
    doctor.add_argument(
        "--no-network",
        action="store_true",
        help="Do not make network calls (OAuth/track).",
    )
    doctor.add_argument(
        "--tracking-number",
        default=None,
        help="Optional: also perform a live track call (FedEx only).",
    )
    doctor.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON to stdout (CI/support-ticket friendly).",
    )


    comp = sub.add_parser(
        "completion",
        parents=[common],
        help="Print shell completion script (bash/zsh)",
    )
    comp.add_argument("shell", choices=["bash", "zsh"], help="Shell to generate completion for")

    return p


def _cmd_completion(args: argparse.Namespace) -> int:
    shell = str(getattr(args, "shell", "") or "").lower()
    if shell not in {"bash", "zsh"}:
        # Argparse should prevent this in normal usage; keep a safe fallback.
        sys.stdout.write(json.dumps({"error": f"unsupported shell: {shell}"}))
        sys.stdout.write("\n")
        return 2

    # Prefer repo checkout scripts when present (keeps a single source of truth
    # during development), but always have an embedded fallback for installed use.
    repo_root = Path(__file__).resolve().parents[1]
    if shell == "bash":
        p = repo_root / "completions" / "tday.bash"
        fallback = _BASH_COMPLETION_FALLBACK
    else:
        p = repo_root / "completions" / "_tday"
        fallback = _ZSH_COMPLETION_FALLBACK

    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        txt = fallback

    sys.stdout.write(txt)
    return 0


def _merge_doctor_exit_codes(exit_codes: Sequence[int]) -> int:
    """Merge per-carrier doctor exit codes into one overall code.

    Priority order matches current doctor conventions:
    - 4: track failure
    - 3: OAuth failure
    - 2: config missing/invalid or other validation error
    - 1: generic runtime error (not currently used by doctor, but reserved)
    - 0: success
    """

    ecs = list(exit_codes)
    for code in (4, 3, 2, 1, 0):
        if code in ecs:
            return code
    return 1


def _doctor_one(
    *,
    carrier_requested: str,
    env: str,
    tracking_number: Optional[str],
    config_path_override: Optional[str],
    no_network: bool,
    json_mode: bool,
    color: bool,
    emit_human: bool,
) -> Tuple[Dict[str, Any], int]:
    tn = tracking_number
    detected = detect_carrier(str(tn)) if tn else None
    carrier_effective = detected if carrier_requested == "auto" else carrier_requested

    final_rc = 0
    report: Dict[str, Any] = {
        "doctor_version": 1,
        "carrier": {
            "requested": carrier_requested,
            "detected": detected,
            "effective": carrier_effective,
        },
        "env": env,
        "python": {"executable": sys.executable, "version": sys.version},
        "package": {},
        "config": {
            "source": None,
            "path": None,
            "exists": False,
            "keys": [],
            "required": [],
            "presence": {},
        },
        "network": {
            "requested": not bool(no_network),
            "implemented": carrier_effective == "fedex",
            "note": None,
            "oauth": None,
            "track": None,
        },
        "tracking": {"number": str(tn) if tn else None, "normalized": None},
    }

    def _human(msg: str) -> None:
        if emit_human and not json_mode:
            _eprint(msg)

    _human(_note(f"Doctor: carrier={carrier_effective} env={env}", color))
    _human(_note(f"Python: {sys.executable} ({sys.version.split()[0]})", color))
    try:
        import daylily_carrier_tracking as pkg  # noqa: F401

        report["package"] = {"file": getattr(pkg, "__file__", None)}
        if getattr(pkg, "__file__", None):
            _human(_note(f"Package: {pkg.__file__}", color))
    except Exception as e:
        report["package"] = {"error": f"{type(e).__name__}: {e}"}

    if carrier_requested == "auto" and not tn:
        report["error"] = "carrier=auto requires --tracking-number"
        _human(_err("ERROR: carrier=auto requires --tracking-number", color))
        return report, 2

    if config_path_override:
        resolved_path = Path(str(config_path_override)).expanduser()
        source = "override"
    else:
        resolved_path = config_path(carrier_effective, env)
        source = "centralized"

    report["config"]["source"] = source
    report["config"]["path"] = str(resolved_path)
    report["config"]["exists"] = resolved_path.exists()
    _human(_note(f"Config ({source}): {resolved_path}", color))

    cfg: Dict[str, Any] = {}
    if resolved_path.exists():
        try:
            cfg = load_yaml_mapping(resolved_path)
            report["config"]["keys"] = sorted(list(cfg.keys()))
            _human(_note(f"Config keys: {report['config']['keys']}", color))
        except Exception as e:
            report["config"]["load_error"] = f"{type(e).__name__}: {e}"
            _human(_err(f"ERROR: Failed to load YAML: {type(e).__name__}: {e}", color))
            return report, 2
    else:
        # For FedEx we still treat missing config as an error; for UPS/USPS we
        # keep going to emit a useful stub report.
        if carrier_effective == "fedex":
            report["config"]["missing_note"] = "Expected: ~/.config/daylily-carrier-tracking/<carrier>_<env>.yaml"
            _human(_err("ERROR: Config file does not exist.", color))
            _human(_note("Expected: ~/.config/daylily-carrier-tracking/<carrier>_<env>.yaml", color))
            _human(_note("(For backward compatibility, FedEx tracker can also fall back to yaml_config_day.)", color))
            return report, 2

    def _present_len(k: str) -> str:
        v = cfg.get(k)
        if v is None:
            return "missing"
        s = str(v)
        return f"present(len={len(s)})"

    # Carrier-specific config validation
    if carrier_effective == "fedex":
        oauth_url = cfg.get("oauth_url") or cfg.get("api_url")
        report["config"]["required"] = ["oauth_url|api_url", "client_id", "client_secret"]
        report["config"]["presence"] = {
            "oauth_url|api_url": "present" if oauth_url else "missing",
            "client_id": _present_len("client_id"),
            "client_secret": _present_len("client_secret"),
        }
        report["config"]["oauth_url"] = oauth_url

        _human(_note(f"oauth_url/api_url: {oauth_url or '<missing>'}", color))
        _human(_note(f"client_id: {report['config']['presence']['client_id']}", color))
        _human(_note(f"client_secret: {report['config']['presence']['client_secret']}", color))

        if not oauth_url or not cfg.get("client_id") or not cfg.get("client_secret"):
            report["config"]["valid"] = False
            report["error"] = "Missing required FedEx config keys"
            _human(_err("ERROR: Missing required FedEx config keys.", color))
            return report, 2
        report["config"]["valid"] = True

    elif carrier_effective in {"ups", "usps"}:
        report["config"]["required"] = ["client_id", "client_secret"]
        report["config"]["presence"] = {
            "client_id": _present_len("client_id"),
            "client_secret": _present_len("client_secret"),
        }
        report["config"]["valid"] = bool(cfg.get("client_id") and cfg.get("client_secret"))
        # CI strictness: missing/invalid config for UPS/USPS should fail.
        final_rc = 0 if report["config"]["valid"] else 2
        report["network"]["implemented"] = False
        report["network"]["note"] = "network checks not implemented for this carrier"
        _human(_warn("Doctor: network checks not implemented for this carrier.", color))
    else:
        report["error"] = "Unhandled carrier"
        _human(_err("ERROR: Unhandled carrier", color))
        return report, 2

    # Optional: always include a normalized response blob when tracking number is provided.
    if tn:
        try:
            ut = UnifiedTracker(fedex_config_proj_env=env, fedex_config=cfg if carrier_effective == "fedex" else None)
            ops = ut.track_ops_meta(str(tn), carrier=carrier_effective)
            report["tracking"]["normalized"] = ops
        except Exception as e:
            report["tracking"]["normalized_error"] = f"{type(e).__name__}: {e}"

    # Network checks (FedEx only)
    if carrier_effective == "fedex":
        if no_network:
            report["network"]["note"] = "skipped per --no-network"
            _human(_warn("Skipping network checks (per --no-network).", color))
            return report, 0

        report["network"]["implemented"] = True
        _human(_note("Network check: requesting OAuth token...", color))
        try:
            ft = FedexTracker(config=cfg)
            token = ft.auth_token()
            report["network"]["oauth"] = {"ok": True, "token_len": len(token)}
            _human(_ok(f"OAuth OK (token acquired; length={len(token)}).", color))
        except Exception as e:
            status = None
            body = None
            try:
                resp = getattr(e, "response", None)
                status = getattr(resp, "status_code", None)
                body = getattr(resp, "text", None)
            except Exception:
                pass
            report["network"]["oauth"] = {
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
                "http_status": status,
                "response_body": (body[:400] if body else None),
            }
            if status is not None:
                _human(_err(f"OAuth FAILED: HTTP {status}", color))
                if body:
                    _human(_err(f"Response body (first 400 chars): {body[:400]}", color))
            else:
                _human(_err(f"OAuth FAILED: {type(e).__name__}: {e}", color))
            return report, 3

        if tn:
            _human(_note(f"Network check: tracking {tn}...", color))
            try:
                out = ft.track(str(tn), api_preference="auto", include_raw=False)
                report["network"]["track"] = {"ok": True, "response": out}
                _human(_ok("Track OK.", color))
            except Exception as e:
                report["network"]["track"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
                _human(_err(f"Track FAILED: {type(e).__name__}: {e}", color))
                return report, 4

    return report, final_rc


def _cmd_doctor(args: argparse.Namespace) -> int:
    color = _color_enabled(bool(getattr(args, "no_color", False)))
    json_mode = bool(getattr(args, "json", False))

    all_mode = bool(getattr(args, "all", False))

    carrier_requested = str(getattr(args, "carrier", "fedex") or "fedex").lower()
    env = str(getattr(args, "env", "prod") or "prod").lower()
    tn = getattr(args, "tracking_number", None)
    no_network = bool(getattr(args, "no_network", False))
    cfg_path = getattr(args, "config_path", None)

    if all_mode:
        # Aggregated mode is JSON-only (so it can be piped to jq / attached to tickets).
        if cfg_path:
            out = {
                "doctor_version": 1,
                "mode": "all",
                "env": env,
                "tracking_number": str(tn) if tn else None,
                "error": "--all cannot be used with --config-path (ambiguous; no per-carrier override yet)",
            }
            print(json.dumps(out, indent=2, sort_keys=True))
            return 2

        carriers = ["fedex", "ups", "usps"]
        per: Dict[str, Any] = {}
        rcs: Dict[str, int] = {}
        for c in carriers:
            rep, rc = _doctor_one(
                carrier_requested=c,
                env=env,
                tracking_number=str(tn) if tn else None,
                config_path_override=None,
                no_network=no_network,
                json_mode=True,
                color=color,
                emit_human=False,
            )
            per[c] = rep
            rcs[c] = rc

        overall = _merge_doctor_exit_codes(rcs.values())
        out = {
            "doctor_version": 1,
            "mode": "all",
            "env": env,
            "tracking_number": str(tn) if tn else None,
            "carriers": per,
            "summary": {
                "rc": overall,
                "by_carrier": rcs,
                "config_valid": {k: bool(per[k].get("config", {}).get("valid")) for k in carriers},
            },
        }
        print(json.dumps(out, indent=2, sort_keys=True))
        return overall

    report, rc = _doctor_one(
        carrier_requested=carrier_requested,
        env=env,
        tracking_number=str(tn) if tn else None,
        config_path_override=str(cfg_path) if cfg_path else None,
        no_network=no_network,
        json_mode=json_mode,
        color=color,
        emit_human=True,
    )

    if json_mode:
        print(json.dumps(report, indent=2, sort_keys=True))
    return rc


def _cmd_test(args: argparse.Namespace) -> int:
    color = _color_enabled(bool(getattr(args, "no_color", False)))
    tests_dir = Path.cwd() / "tests"
    if not tests_dir.exists():
        _eprint(_err("ERROR: tests/ directory not found. Run from the repo root.", color))
        return 2

    selections: List[str] = []
    if args.test_fedex:
        selections.append("fedex")
    if args.test_ups:
        selections.append("ups")
    if args.test_usps:
        selections.append("usps")

    if not selections:
        _eprint(_note("Running full test suite...", color))
        return _run_subprocess([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=Path.cwd())

    rc = 0
    for carrier in selections:
        pattern = f"test_{carrier}_*.py"
        matches = list(tests_dir.glob(pattern))
        if not matches:
            _eprint(_warn(f"No tests matched {pattern} (carrier '{carrier}' likely not implemented yet).", color))
            rc = max(rc, 2)
            continue
        _eprint(_note(f"Running {carrier} tests ({pattern})...", color))
        rc = max(
            rc,
            _run_subprocess(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern],
                cwd=Path.cwd(),
            ),
        )
    return rc


def _cmd_configure_fedex(args: argparse.Namespace) -> int:
    color = _color_enabled(bool(getattr(args, "no_color", False)))
    env = str(args.env)
    path = Path(args.path) if args.path else _default_config_path("fedex", env)

    if path.exists():
        if not path.is_file():
            _eprint(_err(f"Config path exists but is not a file: {path}", color))
            return 2
        _eprint(_warn(f"Config already exists: {path}", color))
        if not _prompt_yes_no("Overwrite it?", default=False):
            _eprint(_note("Keeping existing config (no changes made).", color))
            return 0

        ts = _utc_timestamp_compact()
        bak = Path(str(path) + f".bak.{ts}")
        i = 1
        while bak.exists():
            bak = Path(str(path) + f".bak.{ts}.{i}")
            i += 1
        path.replace(bak)
        _eprint(_note(f"Backed up existing config to: {bak}", color))

    _eprint(_note("FedEx credential setup (writes YAML config)", color))
    client_id = _prompt("client_id", required=True)
    client_secret = _prompt("client_secret", secret=True, required=True)
    oauth_url = _prompt("oauth_url", default="https://apis.fedex.com/oauth/token", required=True)
    track_url = _prompt("track_url (optional)", default="https://apis.fedex.com/track/v1/trackingnumbers", required=False)
    ship_track_url = _prompt("ship_track_url (optional)", default="", required=False)

    cfg: Dict[str, Any] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "oauth_url": oauth_url,
        "track_url": track_url or None,
        "ship_track_url": ship_track_url or None,
    }

    write_yaml_mapping(path, cfg)
    _eprint(_ok(f"Wrote: {path}", color))

    if args.skip_validate:
        _eprint(_warn("Skipping live validation (per --skip-validate).", color))
        return 0

    _eprint(_note("Validating credentials via OAuth token request...", color))
    try:
        ft = FedexTracker(config=cfg)
        token = ft.auth_token()
        _eprint(_ok(f"Validation OK (token acquired; length={len(token)}).", color))
        return 0
    except Exception as e:
        _eprint(_err(f"Validation FAILED: {type(e).__name__}: {e}", color))
        return 3


def _cmd_configure(args: argparse.Namespace) -> int:
    carrier = str(args.carrier).lower()
    color = _color_enabled(bool(getattr(args, "no_color", False)))
    if carrier == "fedex":
        return _cmd_configure_fedex(args)
    if carrier in {"ups", "usps"}:
        path = Path(args.path) if args.path else _default_config_path(carrier, str(args.env))
        _eprint(_warn(f"{carrier.upper()} configuration is scaffolded but validation is not implemented yet.", color))
        _eprint(_note(f"Creating placeholder config at: {path}", color))
        placeholder = {
            "client_id": "",
            "client_secret": "",
            "oauth_url": "",
        }
        write_yaml_mapping(path, placeholder)
        return 2
    raise ValueError("Unhandled carrier")


def _cmd_track(args: argparse.Namespace) -> int:
    color = _color_enabled(bool(getattr(args, "no_color", False)))
    tn = str(args.tracking_number)
    carrier = str(args.carrier).lower()
    include_raw = not bool(args.no_raw)
    api_preference = str(getattr(args, "api_preference", "auto")).lower()

    resolved_carrier = carrier
    if carrier == "auto":
        resolved_carrier = detect_carrier(tn)
        _eprint(_note(f"Auto-detected carrier: {resolved_carrier}", color))

    try:
        if resolved_carrier == "fedex":
            ft = FedexTracker()
            out = ft.track(tn, api_preference=api_preference, include_raw=include_raw)
        else:
            if api_preference != "auto":
                _eprint(_warn("--api-preference is FedEx-only; ignoring for non-FedEx carriers.", color))
            ut = UnifiedTracker()
            out = ut.track(tn, carrier=resolved_carrier, include_raw=include_raw)

        _eprint(_ok("Track call completed.", color))
        _print_json(out, pretty=bool(args.pretty))
        return 0
    except NotImplementedError as e:
        _eprint(_err(f"ERROR: {e}", color))
        return 2
    except Exception as e:
        _eprint(_err(f"ERROR: {type(e).__name__}: {e}", color))
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.cmd == "test":
        return _cmd_test(args)
    if args.cmd == "configure":
        return _cmd_configure(args)
    if args.cmd == "track":
        return _cmd_track(args)
    if args.cmd == "doctor":
        return _cmd_doctor(args)
    if args.cmd == "completion":
        return _cmd_completion(args)

    # Deprecated aliases (kept for backward compatibility).
    if args.cmd in {"fedex", "ups", "usps"}:
        args2 = argparse.Namespace(**vars(args))
        args2.cmd = "track"
        args2.carrier = args.cmd
        if not hasattr(args2, "api_preference"):
            args2.api_preference = "auto"
        return _cmd_track(args2)

    color = _color_enabled(bool(getattr(args, "no_color", False)))
    _eprint(_err("ERROR: Unhandled command", color))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
