from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Iterator

from .metadata import get_experiment_dataset_version, list_channels, list_tags, record_experiment
from .versioning import resolve_version


_current_dataset: ContextVar[str | None] = ContextVar("datashift_current_dataset", default=None)
_current_experiment: ContextVar[str | None] = ContextVar("datashift_current_experiment", default=None)


@contextmanager
def use(dataset_spec: str, experiment_id: str | None = None, base_path: Path | None = None) -> Iterator[str]:
    record = resolve_version(dataset_spec, base_path)
    token_dataset = _current_dataset.set(f"{record.dataset_name}@{record.version}")
    token_experiment = None
    if experiment_id is not None:
        token_experiment = _current_experiment.set(experiment_id)
        record_experiment(
            external_id=experiment_id,
            dataset_version_id=record.id,
            metadata={"dataset": f"{record.dataset_name}@{record.version}"},
            base_path=base_path,
        )
        _log_mlflow_dataset_metadata(record.dataset_name, record.version, base_path)
    try:
        yield f"{record.dataset_name}@{record.version}"
    finally:
        _current_dataset.reset(token_dataset)
        if token_experiment is not None:
            _current_experiment.reset(token_experiment)


def reproduce_experiment(
    experiment_id: str,
    base_path: Path | None = None,
) -> str:
    record = get_experiment_dataset_version(experiment_id, base_path)
    if record is None:
        raise ValueError(f"No experiment found with id {experiment_id}")
    return f"{record.dataset_name}@{record.version}"


def _log_mlflow_dataset_metadata(
    dataset_name: str,
    version: str,
    base_path: Path | None,
) -> None:
    try:
        import mlflow
    except Exception:
        return
    run = mlflow.active_run()
    if run is None:
        return
    tags = list_tags(dataset_name, base_path)
    channels = list_channels(dataset_name, base_path)
    tag_map = {tag: ver for tag, ver in tags}
    channel_map = {channel: ver for channel, ver in channels}
    mlflow.set_tags(
        {
            "datashift.dataset_name": dataset_name,
            "datashift.dataset_version": version,
            "datashift.dataset_tags": ",".join(sorted(tag_map.keys())),
            "datashift.dataset_channels": ",".join(sorted(channel_map.keys())),
        }
    )
