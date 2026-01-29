from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


DEFAULT_ROOT_DIRNAME = ".datashift"
CONFIG_FILENAME = "config.json"


def _env_root() -> Path | None:
    value = os.environ.get("DATASHIFT_ROOT")
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.exists():
        raise ValueError(f"DATASHIFT_ROOT {path} does not exist")
    if not path.is_dir():
        raise ValueError(f"DATASHIFT_ROOT {path} is not a directory")
    return path.resolve()


def _find_base(start: Path | None = None) -> Path:
    env_root = _env_root()
    if env_root is not None:
        return env_root
    base = start or Path.cwd()
    current = base.resolve()
    while True:
        candidate = current / DEFAULT_ROOT_DIRNAME
        if candidate.exists() and candidate.is_dir():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return base


def get_root(base_path: Path | None = None) -> Path:
    base = base_path or _find_base()
    root = base / DEFAULT_ROOT_DIRNAME
    root.mkdir(parents=True, exist_ok=True)
    (root / "objects").mkdir(parents=True, exist_ok=True)
    return root


def get_metadata_path(base_path: Path | None = None) -> Path:
    return get_root(base_path) / "metadata.db"


def get_config_path(base_path: Path | None = None) -> Path:
    root = get_root(base_path)
    return root / CONFIG_FILENAME


def load_config(base_path: Path | None = None) -> Dict[str, Any]:
    path = get_config_path(base_path)
    if not path.exists():
        return {}
    data = path.read_text(encoding="utf-8")
    return json.loads(data)


def save_config(config: Dict[str, Any], base_path: Path | None = None) -> None:
    path = get_config_path(base_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def merge_config(updates: Dict[str, Any], base_path: Path | None = None) -> Dict[str, Any]:
    existing = load_config(base_path)

    def _merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in src.items():
            if isinstance(value, dict) and isinstance(dst.get(key), dict):
                dst[key] = _merge(dst[key], value)
            else:
                dst[key] = value
        return dst

    merged = _merge(dict(existing), updates)
    save_config(merged, base_path)
    return merged
