from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd

from .config import get_root
from .metadata import (
    VersionRecord,
    get_latest_version,
    get_version_by_label,
    init_db,
    insert_version,
    list_versions as _list_versions,
    list_datasets as _list_datasets,
    get_dataset_summary as _get_dataset_summary,
    next_version_label,
    set_channel,
    set_version_tag,
)
from .storage import load_dataset_dataframe, load_dataset_file, store_dataframe, store_dataset_file


@dataclass
class SnapshotResult:
    dataset: str
    version: str
    object_path: str
    content_hash: str


def _infer_dataset_name_from_path(path: Path) -> str:
    return path.stem


def _compute_schema_and_stats(df: pd.DataFrame) -> tuple[dict, dict]:
    schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
    stats: dict[str, dict] = {}
    for col in df.columns:
        series = df[col]
        stats[col] = {
            "non_null": int(series.notna().sum()),
            "nulls": int(series.isna().sum()),
            "unique": int(series.nunique(dropna=True)),
        }
    return schema, stats


def snapshot_dataset(
    dataset_name: str | None = None,
    source_path: str | Path | None = None,
    df: pd.DataFrame | None = None,
    base_path: Path | None = None,
    remote: str | None = None,
    set_defaults: bool = True,
) -> SnapshotResult:
    if source_path is None and df is None:
        raise ValueError("Either source_path or df must be provided")
    if source_path is not None and df is not None:
        raise ValueError("Provide only one of source_path or df")
    init_db(base_path)
    if source_path is not None:
        source = Path(source_path)
        name = dataset_name or _infer_dataset_name_from_path(source)
        object_path, content_hash = store_dataset_file(source, base_path, remote=remote)
        data_df = load_dataset_dataframe(object_path, base_path)
    else:
        if dataset_name is None:
            raise ValueError("dataset_name is required when snapshotting from DataFrame")
        name = dataset_name
        object_path, content_hash = store_dataframe(df, f"{name}.parquet", base_path, remote=remote)
        data_df = df if df is not None else pd.DataFrame()
    schema, stats = _compute_schema_and_stats(data_df)
    rows_count = int(data_df.shape[0])
    columns_count = int(data_df.shape[1])
    version_label = next_version_label(name, base_path)
    record = insert_version(
        dataset_name=name,
        version=version_label,
        object_path=object_path,
        content_hash=content_hash,
        rows_count=rows_count,
        columns_count=columns_count,
        schema=schema,
        stats=stats,
        base_path=base_path,
    )
    if set_defaults:
        set_version_tag(name, record.id, "latest", base_path)
        set_channel(name, record.id, "default", base_path)
    return SnapshotResult(
        dataset=record.dataset_name,
        version=record.version,
        object_path=record.object_path,
        content_hash=record.content_hash,
    )


def parse_dataset_spec(spec: str) -> tuple[str, str | None, str | None, str | None]:
    if "#" in spec:
        name, tag = spec.split("#", 1)
        return name, None, tag, None
    if ":" in spec and "@" not in spec:
        name, channel = spec.split(":", 1)
        return name, None, None, channel
    if "@" in spec:
        name, version = spec.split("@", 1)
        return name, version, None, None
    return spec, None, None, None


def resolve_version(
    dataset_spec: str,
    base_path: Path | None = None,
) -> VersionRecord:
    from . import metadata as _md

    name, version_label, tag, channel = parse_dataset_spec(dataset_spec)
    init_db(base_path)
    if tag is not None:
        record = _md.get_version_by_tag(name, tag, base_path)
        if record is None:
            raise ValueError(f"Dataset {name} has no tag {tag}")
        return record
    if channel is not None:
        record = _md.get_version_by_channel(name, channel, base_path)
        if record is None:
            raise ValueError(f"Dataset {name} has no channel {channel}")
        return record
    if version_label is None:
        latest = get_latest_version(name, None, base_path)
        if latest is None:
            raise ValueError(f"No versions found for dataset {name}")
        return latest
    if version_label.startswith("20") and len(version_label) == 10:
        before = datetime.fromisoformat(version_label)
        record = get_latest_version(name, before, base_path)
        if record is None:
            raise ValueError(f"No version of {name} before {version_label}")
        return record
    record = get_version_by_label(name, version_label, base_path)
    if record is None:
        raise ValueError(f"Dataset {name} has no version {version_label}")
    return record


def checkout_dataset(
    dataset_spec: str,
    output_path: str | Path,
    base_path: Path | None = None,
) -> Path:
    record = resolve_version(dataset_spec, base_path)
    root = get_root(base_path)
    src = load_dataset_file(record.object_path, base_path)
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    return dest


def list_versions(dataset_name: str, base_path: Path | None = None) -> list[VersionRecord]:
    init_db(base_path)
    return _list_versions(dataset_name, base_path)


def list_datasets(base_path: Path | None = None) -> list[str]:
    init_db(base_path)
    return _list_datasets(base_path)


def get_dataset_summary(dataset_name: str, base_path: Path | None = None) -> dict | None:
    init_db(base_path)
    return _get_dataset_summary(dataset_name, base_path)


def load(
    dataset_spec: str,
    columns: list[str] | None = None,
    where: str | None = None,
    base_path: Path | None = None,
) -> pd.DataFrame:
    record = resolve_version(dataset_spec, base_path)
    return load_dataset_dataframe(record.object_path, base_path, columns=columns, where=where)


def split_dataset(
    dataset_spec: str,
    ratios: tuple[float, float, float] = (0.7, 0.15, 0.15),
    stratify: str | None = None,
    seed: int | None = None,
    base_path: Path | None = None,
) -> dict[str, SnapshotResult]:
    total = sum(ratios)
    if total <= 0:
        raise ValueError("Ratios must be positive")
    ratios = tuple(r / total for r in ratios)  # type: ignore[assignment]
    record = resolve_version(dataset_spec, base_path)
    df = load_dataset_dataframe(record.object_path, base_path)
    if stratify is not None and stratify not in df.columns:
        raise ValueError(f"Stratify column {stratify} not found")
    if stratify is None:
        df_shuffled = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
        n = len(df_shuffled)
        n_train = int(n * ratios[0])
        n_val = int(n * ratios[1])
        n_test = n - n_train - n_val
        train_df = df_shuffled.iloc[:n_train]
        val_df = df_shuffled.iloc[n_train : n_train + n_val]
        test_df = df_shuffled.iloc[n_train + n_val : n_train + n_val + n_test]
    else:
        train_parts = []
        val_parts = []
        test_parts = []
        for _, group in df.groupby(stratify):
            g = group.sample(frac=1.0, random_state=seed)
            n = len(g)
            n_train = int(n * ratios[0])
            n_val = int(n * ratios[1])
            n_test = n - n_train - n_val
            train_parts.append(g.iloc[:n_train])
            val_parts.append(g.iloc[n_train : n_train + n_val])
            test_parts.append(g.iloc[n_train + n_val : n_train + n_val + n_test])
        train_df = pd.concat(train_parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)
        val_df = pd.concat(val_parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)
        test_df = pd.concat(test_parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    name = record.dataset_name
    train_snapshot = snapshot_dataset(
        dataset_name=name,
        df=train_df,
        base_path=base_path,
        set_defaults=False,
    )
    val_snapshot = snapshot_dataset(
        dataset_name=name,
        df=val_df,
        base_path=base_path,
        set_defaults=False,
    )
    test_snapshot = snapshot_dataset(
        dataset_name=name,
        df=test_df,
        base_path=base_path,
        set_defaults=False,
    )
    set_channel(name, resolve_version(f"{name}@{train_snapshot.version}", base_path).id, "train", base_path)
    set_channel(name, resolve_version(f"{name}@{val_snapshot.version}", base_path).id, "val", base_path)
    set_channel(name, resolve_version(f"{name}@{test_snapshot.version}", base_path).id, "test", base_path)
    return {"train": train_snapshot, "val": val_snapshot, "test": test_snapshot}


def sample(
    dataset_spec: str,
    n: int | None = None,
    frac: float | None = None,
    seed: int | None = None,
    base_path: Path | None = None,
) -> pd.DataFrame:
    if n is None and frac is None:
        raise ValueError("Either n or frac must be provided")
    record = resolve_version(dataset_spec, base_path)
    df = load_dataset_dataframe(record.object_path, base_path)
    return df.sample(n=n, frac=frac, random_state=seed)
