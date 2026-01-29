from __future__ import annotations

from pathlib import Path
from typing import Protocol

import pandas as pd

from .metadata import record_lineage_step
from .storage import load_dataset_dataframe
from .versioning import SnapshotResult, resolve_version, snapshot_dataset


class Migration(Protocol):
    def up(self, df: pd.DataFrame) -> pd.DataFrame:  # type: ignore[override]
        ...

    def down(self, df: pd.DataFrame) -> pd.DataFrame:  # type: ignore[override]
        ...


def apply_migration(
    dataset_spec: str,
    migration: Migration,
    name: str | None = None,
    base_path: Path | None = None,
) -> SnapshotResult:
    record = resolve_version(dataset_spec, base_path)
    df_source = load_dataset_dataframe(record.object_path, base_path)
    df = migration.up(df_source)
    result = snapshot_dataset(record.dataset_name, df=df, base_path=base_path)
    record_lineage_step(
        dataset_version_id=record.id,
        step_name=name or migration.__class__.__name__,
        step_order=0,
        metadata={"from_version": record.version, "to_version": result.version},
        base_path=base_path,
    )
    return result
