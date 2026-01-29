from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd

from .metadata import VersionRecord
from .storage import load_dataset_dataframe
from .versioning import resolve_version


@dataclass
class ColumnDrift:
    column: str
    null_delta: float | None
    unique_delta: float | None
    mean_delta: float | None
    std_delta: float | None


@dataclass
class DiffResult:
    left: VersionRecord
    right: VersionRecord
    rows_added: int
    rows_removed: int
    column_drifts: list[ColumnDrift]


def _row_diff(left_df: pd.DataFrame, right_df: pd.DataFrame) -> tuple[int, int]:
    left_keys = left_df.index
    right_keys = right_df.index
    added = right_keys.difference(left_keys)
    removed = left_keys.difference(right_keys)
    return int(len(added)), int(len(removed))


def _compute_drift(left_df: pd.DataFrame, right_df: pd.DataFrame) -> list[ColumnDrift]:
    columns = sorted(set(left_df.columns) | set(right_df.columns))
    result: list[ColumnDrift] = []
    for col in columns:
        if col not in left_df.columns or col not in right_df.columns:
            result.append(
                ColumnDrift(
                    column=col,
                    null_delta=None,
                    unique_delta=None,
                    mean_delta=None,
                    std_delta=None,
                )
            )
            continue
        left = left_df[col]
        right = right_df[col]
        left_null_ratio = float(left.isna().mean())
        right_null_ratio = float(right.isna().mean())
        left_unique_ratio = float(left.nunique(dropna=True) / max(len(left), 1))
        right_unique_ratio = float(right.nunique(dropna=True) / max(len(right), 1))

        mean_delta = None
        std_delta = None
        if pd.api.types.is_numeric_dtype(left) and pd.api.types.is_numeric_dtype(right):
            left_mean = float(left.mean())
            right_mean = float(right.mean())
            left_std = float(left.std())
            right_std = float(right.std())
            mean_delta = right_mean - left_mean
            std_delta = right_std - left_std

        result.append(
            ColumnDrift(
                column=col,
                null_delta=right_null_ratio - left_null_ratio,
                unique_delta=right_unique_ratio - left_unique_ratio,
                mean_delta=mean_delta,
                std_delta=std_delta,
            )
        )
    return result


def diff_datasets(
    left_spec: str,
    right_spec: str,
    base_path,
) -> DiffResult:
    left_record = resolve_version(left_spec, base_path)
    right_record = resolve_version(right_spec, base_path)
    left_df = load_dataset_dataframe(left_record.object_path, base_path)
    right_df = load_dataset_dataframe(right_record.object_path, base_path)
    rows_added, rows_removed = _row_diff(left_df, right_df)
    drifts = _compute_drift(left_df, right_df)
    return DiffResult(
        left=left_record,
        right=right_record,
        rows_added=rows_added,
        rows_removed=rows_removed,
        column_drifts=drifts,
    )


def format_diff_summary(diff: DiffResult) -> str:
    lines: list[str] = []
    lines.append(
        f"Diff {diff.left.dataset_name}@{diff.left.version} -> "
        f"{diff.right.dataset_name}@{diff.right.version}"
    )
    lines.append(f"+ {diff.rows_added} rows added")
    lines.append(f"- {diff.rows_removed} rows removed")
    for drift in diff.column_drifts:
        if drift.null_delta is None or drift.unique_delta is None:
            lines.append(f"~ column {drift.column} changed presence")
            continue
        null_change_pct = drift.null_delta * 100
        unique_change_pct = drift.unique_delta * 100
        if abs(null_change_pct) > 0.1:
            direction = "increased" if null_change_pct > 0 else "decreased"
            lines.append(
                f"- column {drift.column} nulls {direction} by {abs(null_change_pct):.2f}%"
            )
        if abs(unique_change_pct) > 0.1:
            direction = "increased" if unique_change_pct > 0 else "decreased"
            lines.append(
                f"- column {drift.column} uniqueness {direction} by "
                f"{abs(unique_change_pct):.2f}%"
            )
        
        if drift.mean_delta is not None and abs(drift.mean_delta) > 1e-6:
            direction = "increased" if drift.mean_delta > 0 else "decreased"
            lines.append(
                f"- column {drift.column} mean {direction} by {abs(drift.mean_delta):.4f}"
            )
            
        if drift.std_delta is not None and abs(drift.std_delta) > 1e-6:
            direction = "increased" if drift.std_delta > 0 else "decreased"
            lines.append(
                f"- column {drift.column} std {direction} by {abs(drift.std_delta):.4f}"
            )
    return "\n".join(lines)


def diff_to_dict(diff: DiffResult) -> Dict[str, Any]:
    return {
        "left": {
            "dataset": diff.left.dataset_name,
            "version": diff.left.version,
            "created_at": diff.left.created_at.isoformat(),
            "rows": diff.left.rows_count,
        },
        "right": {
            "dataset": diff.right.dataset_name,
            "version": diff.right.version,
            "created_at": diff.right.created_at.isoformat(),
            "rows": diff.right.rows_count,
        },
        "rows_added": diff.rows_added,
        "rows_removed": diff.rows_removed,
        "columns": [
            {
                "column": drift.column,
                "null_delta": drift.null_delta,
                "unique_delta": drift.unique_delta,
                "mean_delta": drift.mean_delta,
                "std_delta": drift.std_delta,
            }
            for drift in diff.column_drifts
        ],
    }
