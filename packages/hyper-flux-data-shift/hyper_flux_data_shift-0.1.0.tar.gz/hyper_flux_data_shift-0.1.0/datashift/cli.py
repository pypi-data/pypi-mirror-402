from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import (
    diff_datasets,
    format_diff_summary,
    list_channels,
    list_tags,
    snapshot_dataset,
)
from .diffing import diff_to_dict
from .versioning import checkout_dataset, resolve_version
from .config import load_config, save_config, get_root
from .metadata import set_channel, set_version_tag


def _cmd_snapshot(args: argparse.Namespace) -> None:
    result = snapshot_dataset(dataset_name=args.name, source_path=args.path, remote=args.remote)
    print(f"Snapshot created: {result.dataset}@{result.version}")


def _cmd_list(args: argparse.Namespace) -> None:
    datasets = list_datasets()
    if not datasets:
        print("No datasets found.")
        return
    for name in datasets:
        print(name)


def _cmd_show(args: argparse.Namespace) -> None:
    summary = get_dataset_summary(args.name)
    if summary is None:
        print(f"Dataset '{args.name}' not found.")
        return

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Dataset: {summary['name']}")
        print(f"Total Versions: {summary['versions_count']}")
        print(f"Latest Version: {summary['latest_version'] or 'N/A'}")
        print(f"Last Updated: {summary['last_updated'] or 'N/A'}")
        if summary['latest_version']:
            print(f"Rows: {summary['rows_count']}")
            print(f"Columns: {summary['columns_count']}")



def _cmd_diff(args: argparse.Namespace) -> None:
    diff = diff_datasets(args.left, args.right, None)
    if getattr(args, "json", False):
        print(json.dumps(diff_to_dict(diff), indent=2))
    else:
        print(format_diff_summary(diff))


def _cmd_checkout(args: argparse.Namespace) -> None:
    output = checkout_dataset(args.spec, args.output)
    print(f"Materialized to {output}")


def _cmd_reproduce(args: argparse.Namespace) -> None:
    from .experiment import reproduce_experiment

    spec = reproduce_experiment(args.experiment_id)
    print(spec)


def _cmd_init(args: argparse.Namespace) -> None:
    base = Path(args.root).expanduser().resolve() if args.root else Path.cwd()
    root = get_root(base)
    config = load_config(base)
    remotes = config.get("remotes") or {}
    if "local" not in remotes:
        remotes["local"] = {
            "kind": "local",
            "path": str(root / "objects"),
        }
    config["remotes"] = remotes
    if "active_remote" not in config:
        config["active_remote"] = "local"
    save_config(config, base)
    print(str(root))


def _cmd_tag_set(args: argparse.Namespace) -> None:
    record = resolve_version(args.spec)
    set_version_tag(record.dataset_name, record.id, args.tag)
    print(f"Tag {args.tag} -> {record.dataset_name}@{record.version}")


def _cmd_tag_list(args: argparse.Namespace) -> None:
    entries = list_tags(args.dataset)
    for tag, version in entries:
        print(f"{tag}\t{version}")


def _cmd_channel_set(args: argparse.Namespace) -> None:
    record = resolve_version(args.spec)
    set_channel(record.dataset_name, record.id, args.channel)
    print(f"Channel {args.channel} -> {record.dataset_name}@{record.version}")


def _cmd_channel_list(args: argparse.Namespace) -> None:
    entries = list_channels(args.dataset)
    for channel, version in entries:
        print(f"{channel}\t{version}")


def _cmd_check(args: argparse.Namespace) -> None:
    diff = diff_datasets(args.baseline, args.target, None)
    info = diff_to_dict(diff)
    left_rows = info["left"].get("rows") or 0
    row_change_ratio = (diff.rows_added + diff.rows_removed) / max(left_rows, 1)
    failed = False
    if args.max_row_change is not None and row_change_ratio > args.max_row_change:
        failed = True
    for col in info["columns"]:
        nd = col["null_delta"]
        ud = col["unique_delta"]
        if nd is not None and args.max_null_delta is not None and abs(nd) > args.max_null_delta:
            failed = True
        if ud is not None and args.max_unique_delta is not None and abs(ud) > args.max_unique_delta:
            failed = True
    if args.json:
        print(json.dumps({"summary": info, "row_change_ratio": row_change_ratio, "failed": failed}, indent=2))
    else:
        print(format_diff_summary(diff))
        print()
        print(f"row_change_ratio={row_change_ratio:.4f}")
        print(f"failed={failed}")
    if args.strict and failed:
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="datashift",
        description="Datashift: dataset versioning, diffs, and drift guards for ML data",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize Datashift in this directory")
    p_init.add_argument("--root", type=str, help="Root directory for Datashift repository")
    p_init.set_defaults(func=_cmd_init)

    p_list = sub.add_parser("list", help="List all datasets")
    p_list.set_defaults(func=_cmd_list)

    p_show = sub.add_parser("show", help="Show dataset summary")
    p_show.add_argument("name", type=str, help="Dataset name")
    p_show.add_argument("--json", action="store_true", help="Output as JSON")
    p_show.set_defaults(func=_cmd_show)

    p_snapshot = sub.add_parser("snapshot", help="Create a dataset snapshot")
    p_snapshot.add_argument("path", type=str, help="Path to dataset file")
    p_snapshot.add_argument("--name", type=str, help="Logical dataset name")
    p_snapshot.add_argument("--remote", type=str, help="Remote name to store objects")
    p_snapshot.set_defaults(func=_cmd_snapshot)

    p_diff = sub.add_parser("diff", help="Diff two dataset versions")
    p_diff.add_argument("left", type=str, help="Left dataset spec")
    p_diff.add_argument("right", type=str, help="Right dataset spec")
    p_diff.add_argument("--json", action="store_true", help="Output diff as JSON")
    p_diff.set_defaults(func=_cmd_diff)

    p_checkout = sub.add_parser("checkout", help="Materialize a dataset version")
    p_checkout.add_argument("spec", type=str, help="Dataset spec like name@v1")
    p_checkout.add_argument("output", type=str, help="Output file path")
    p_checkout.set_defaults(func=_cmd_checkout)

    p_reproduce = sub.add_parser("reproduce", help="Print dataset used in an experiment")
    p_reproduce.add_argument("experiment_id", type=str)
    p_reproduce.set_defaults(func=_cmd_reproduce)

    p_tag = sub.add_parser("tag", help="Manage dataset tags")
    tag_sub = p_tag.add_subparsers(dest="tag_cmd", required=True)
    p_tag_set = tag_sub.add_parser("set", help="Set tag for a dataset version")
    p_tag_set.add_argument("spec", type=str, help="Dataset spec like name@v1")
    p_tag_set.add_argument("tag", type=str, help="Tag name")
    p_tag_set.set_defaults(func=_cmd_tag_set)
    p_tag_list = tag_sub.add_parser("list", help="List tags for a dataset")
    p_tag_list.add_argument("dataset", type=str, help="Dataset name")
    p_tag_list.set_defaults(func=_cmd_tag_list)

    p_channel = sub.add_parser("channel", help="Manage dataset channels")
    channel_sub = p_channel.add_subparsers(dest="channel_cmd", required=True)
    p_channel_set = channel_sub.add_parser("set", help="Set channel to a dataset version")
    p_channel_set.add_argument("spec", type=str, help="Dataset spec like name@v1")
    p_channel_set.add_argument("channel", type=str, help="Channel name")
    p_channel_set.set_defaults(func=_cmd_channel_set)
    p_channel_list = channel_sub.add_parser("list", help="List channels for a dataset")
    p_channel_list.add_argument("dataset", type=str, help="Dataset name")
    p_channel_list.set_defaults(func=_cmd_channel_list)

    p_check = sub.add_parser("check", help="Guardrail drift check between two versions")
    p_check.add_argument("target", type=str, help="Target dataset spec")
    p_check.add_argument("--baseline", type=str, required=True, help="Baseline dataset spec")
    p_check.add_argument("--max-row-change", type=float, default=None, help="Max allowed row change ratio")
    p_check.add_argument("--max-null-delta", type=float, default=None, help="Max allowed null ratio delta")
    p_check.add_argument("--max-unique-delta", type=float, default=None, help="Max allowed uniqueness ratio delta")
    p_check.add_argument("--json", action="store_true", help="Output result as JSON")
    p_check.add_argument("--strict", action="store_true", help="Exit with code 1 on failure")
    p_check.set_defaults(func=_cmd_check)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func")
    func(args)
