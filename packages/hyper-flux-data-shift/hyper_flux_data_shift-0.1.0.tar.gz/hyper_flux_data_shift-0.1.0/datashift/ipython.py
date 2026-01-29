from __future__ import annotations

import argparse
import shlex
from typing import Any

import pandas as pd

from . import diff_datasets, format_diff_summary, load, snapshot_dataset
from .versioning import resolve_version


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="%datashift", add_help=False)
    sub = parser.add_subparsers(dest="command", required=True)

    p_snapshot = sub.add_parser("snapshot", add_help=False)
    p_snapshot.add_argument("target", type=str)
    p_snapshot.add_argument("--name", type=str)

    p_diff = sub.add_parser("diff", add_help=False)
    p_diff.add_argument("left", type=str)
    p_diff.add_argument("right", type=str)

    p_show = sub.add_parser("show", add_help=False)
    p_show.add_argument("spec", type=str)
    p_show.add_argument("--max-rows", type=int, default=10)

    return parser


_PARSER = _build_parser()


def _snapshot_cmd(ns: argparse.Namespace, user_ns: dict[str, Any]) -> None:
    target = ns.target
    value = user_ns.get(target)
    if isinstance(value, pd.DataFrame):
        result = snapshot_dataset(dataset_name=ns.name or target, df=value)
    else:
        result = snapshot_dataset(dataset_name=ns.name, source_path=target)
    print(f"Snapshot created: {result.dataset}@{result.version}")


def _diff_cmd(ns: argparse.Namespace) -> None:
    diff = diff_datasets(ns.left, ns.right, None)
    print(format_diff_summary(diff))


def _show_cmd(ns: argparse.Namespace) -> None:
    spec = ns.spec
    df = load(spec)
    rows, cols = df.shape
    print(f"Dataset {spec}")
    print(f"rows={rows} cols={cols}")
    print()
    print(df.head(ns.max_rows))
    print()
    numeric = df.select_dtypes(include=["number"])
    if not numeric.empty:
        print("numeric_summary=")
        print(numeric.describe().T)


def datashift(line: str) -> None:
    from IPython import get_ipython

    ip = get_ipython()
    if ip is None:
        raise RuntimeError("%datashift can only be used inside IPython")
    argv = shlex.split(line)
    if not argv:
        return
    try:
        ns = _PARSER.parse_args(argv)
    except SystemExit:
        return
    if ns.command == "snapshot":
        _snapshot_cmd(ns, ip.user_ns)
    elif ns.command == "diff":
        _diff_cmd(ns)
    elif ns.command == "show":
        _show_cmd(ns)


def load_ipython_extension(ipython) -> None:
    ipython.register_magic_function(datashift, "line", "datashift")

