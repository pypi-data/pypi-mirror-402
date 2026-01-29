from __future__ import annotations

import hashlib
import shutil
from collections import OrderedDict
from pathlib import Path

import pandas as pd

from .config import get_root, load_config


def _hash_bytes(data: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


_CACHE_MAX_ENTRIES = 8
_df_cache: "OrderedDict[tuple[str, tuple[str, ...] | None, str | None], pd.DataFrame]" = (
    OrderedDict()
)


def _cache_get(
    key: tuple[str, tuple[str, ...] | None, str | None],
) -> pd.DataFrame | None:
    cached = _df_cache.get(key)
    if cached is None:
        return None
    _df_cache.move_to_end(key)
    return cached


def _cache_put(
    key: tuple[str, tuple[str, ...] | None, str | None],
    value: pd.DataFrame,
) -> None:
    _df_cache[key] = value
    _df_cache.move_to_end(key)
    if len(_df_cache) > _CACHE_MAX_ENTRIES:
        _df_cache.popitem(last=False)


def _objects_dir(base_path: Path | None, remote: str | None) -> tuple[Path, Path]:
    root = get_root(base_path)
    config = load_config(base_path)
    remotes = config.get("remotes") or {}
    active_remote = config.get("active_remote")
    effective_remote = remote or active_remote
    if effective_remote is None:
        return root, root / "objects"
    remote_conf = remotes.get(effective_remote)
    if not remote_conf:
        raise ValueError(f"Unknown remote {effective_remote}")
    kind = remote_conf.get("kind", "local")
    if kind != "local":
        raise ValueError(f"Remote kind {kind} is not supported yet")
    path_value = remote_conf.get("path")
    if not path_value:
        raise ValueError(f"Remote {effective_remote} has no path configured")
    objects_dir = Path(path_value).expanduser().resolve()
    objects_dir.mkdir(parents=True, exist_ok=True)
    return root, objects_dir


def store_dataset_file(
    source: Path,
    base_path: Path | None = None,
    remote: str | None = None,
) -> tuple[str, str]:
    root, objects_dir = _objects_dir(base_path, remote)
    data = source.read_bytes()
    content_hash = _hash_bytes(data)
    ext = source.suffix
    subdir = objects_dir / content_hash[:2]
    subdir.mkdir(parents=True, exist_ok=True)
    dest = subdir / f"{content_hash}{ext}"
    if not dest.exists():
        temp = dest.with_suffix(dest.suffix + ".tmp")
        temp.write_bytes(data)
        temp.replace(dest)
    rel_path = dest.relative_to(root)
    return str(rel_path), content_hash


def load_dataset_file(object_path: str, base_path: Path | None = None) -> Path:
    root = get_root(base_path)
    return root / object_path


def load_dataset_dataframe(
    object_path: str,
    base_path: Path | None = None,
    columns: list[str] | None = None,
    where: str | None = None,
) -> pd.DataFrame:
    file_path = load_dataset_file(object_path, base_path)
    key = (str(file_path), tuple(columns) if columns is not None else None, where)
    cached = _cache_get(key)
    if cached is not None:
        return cached
    suffix = file_path.suffix.lower()
    effective_columns = None if where is not None else columns
    if suffix in {".csv", ".txt"}:
        df = pd.read_csv(file_path, usecols=effective_columns)
    elif suffix in {".parquet"}:
        if effective_columns is not None:
            df = pd.read_parquet(file_path, columns=effective_columns)
        else:
            df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
    if where is not None:
        df = df.query(where)
        if columns is not None:
            df = df[columns]
    _cache_put(key, df)
    return df


def store_dataframe(
    df: pd.DataFrame,
    filename: str,
    base_path: Path | None = None,
    remote: str | None = None,
) -> tuple[str, str]:
    root, objects_dir = _objects_dir(base_path, remote)
    ext = Path(filename).suffix or ".parquet"
    temp = objects_dir / f"temp{ext}"
    if ext == ".csv":
        df.to_csv(temp, index=False)
    else:
        df.to_parquet(temp, index=False)
    data = temp.read_bytes()
    content_hash = _hash_bytes(data)
    subdir = objects_dir / content_hash[:2]
    subdir.mkdir(parents=True, exist_ok=True)
    dest = subdir / f"{content_hash}{ext}"
    if not dest.exists():
        shutil.move(str(temp), dest)
    else:
        temp.unlink(missing_ok=True)
    rel_path = dest.relative_to(root)
    return str(rel_path), content_hash
