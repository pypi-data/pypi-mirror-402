from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_CONFIG_DIRNAME = "daylily-carrier-tracking"


def default_config_dir() -> Path:
    return Path.home() / ".config" / DEFAULT_CONFIG_DIRNAME


def config_path(project: str, env: str, base_dir: Optional[Path] = None) -> Path:
    proj = (project or "").strip().lower()
    env = (env or "").strip().lower()
    if not proj:
        raise ValueError("project is required")
    if not env:
        raise ValueError("env is required")
    d = base_dir or default_config_dir()
    return d / f"{proj}_{env}.yaml"


def load_yaml_mapping(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "PyYAML is required to read config files. Install with: pip install pyyaml"
        ) from e

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"Config file must be a YAML mapping (dict): {path}")
    return dict(raw)


def write_yaml_mapping(path: Path, mapping: Dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "PyYAML is required to write config files. Install with: pip install pyyaml"
        ) from e

    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep output stable and human-friendly.
    content = yaml.safe_dump(mapping, sort_keys=True, default_flow_style=False)
    if not content.startswith("---"):
        content = "---\n" + content
    path.write_text(content, encoding="utf-8")

