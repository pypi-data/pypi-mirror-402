from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from .config import get_metadata_path


SCHEMA_VERSION = 2


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(base_path: Path | None = None) -> None:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            create table if not exists meta (
                key text primary key,
                value text not null
            )
            """
        )
        cur.execute(
            """
            create table if not exists datasets (
                id integer primary key autoincrement,
                name text not null unique
            )
            """
        )
        cur.execute(
            """
            create table if not exists versions (
                id integer primary key autoincrement,
                dataset_id integer not null,
                version text not null,
                created_at text not null,
                object_path text not null,
                content_hash text not null,
                rows_count integer,
                columns_count integer,
                schema_json text,
                stats_json text,
                foreign key (dataset_id) references datasets(id),
                unique(dataset_id, version)
            )
            """
        )
        cur.execute(
            """
            create table if not exists experiments (
                id integer primary key autoincrement,
                external_id text not null unique,
                dataset_version_id integer not null,
                created_at text not null,
                metadata_json text,
                foreign key (dataset_version_id) references versions(id)
            )
            """
        )
        cur.execute(
            """
            create table if not exists lineage (
                id integer primary key autoincrement,
                dataset_version_id integer not null,
                step_name text not null,
                step_order integer not null,
                created_at text not null,
                metadata_json text,
                foreign key (dataset_version_id) references versions(id)
            )
            """
        )
        cur.execute(
            """
            create table if not exists version_tags (
                id integer primary key autoincrement,
                version_id integer not null,
                tag text not null,
                unique(version_id, tag),
                foreign key (version_id) references versions(id)
            )
            """
        )
        cur.execute(
            """
            create table if not exists channels (
                id integer primary key autoincrement,
                version_id integer not null,
                channel text not null,
                unique(version_id, channel),
                foreign key (version_id) references versions(id)
            )
            """
        )
        cur.execute(
            "insert or replace into meta(key, value) values (?, ?)",
            ("schema_version", str(SCHEMA_VERSION)),
        )
        conn.commit()
    finally:
        conn.close()


def _get_or_create_dataset(conn: sqlite3.Connection, name: str) -> int:
    cur = conn.cursor()
    cur.execute("select id from datasets where name = ?", (name,))
    row = cur.fetchone()
    if row is not None:
        return int(row["id"])
    cur.execute("insert into datasets(name) values (?)", (name,))
    conn.commit()
    return int(cur.lastrowid)


@dataclass
class VersionRecord:
    id: int
    dataset_name: str
    version: str
    created_at: datetime
    object_path: str
    content_hash: str
    rows_count: int | None
    columns_count: int | None
    schema_json: str | None
    stats_json: str | None


def insert_version(
    dataset_name: str,
    version: str,
    object_path: str,
    content_hash: str,
    rows_count: int | None,
    columns_count: int | None,
    schema: dict[str, Any] | None,
    stats: dict[str, Any] | None,
    base_path: Path | None = None,
) -> VersionRecord:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        dataset_id = _get_or_create_dataset(conn, dataset_name)
        cur = conn.cursor()
        created_at = datetime.now(UTC).isoformat()
        cur.execute(
            """
            insert into versions(
                dataset_id, version, created_at, object_path, content_hash,
                rows_count, columns_count, schema_json, stats_json
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dataset_id,
                version,
                created_at,
                object_path,
                content_hash,
                rows_count,
                columns_count,
                json.dumps(schema) if schema is not None else None,
                json.dumps(stats) if stats is not None else None,
            ),
        )
        conn.commit()
        version_id = int(cur.lastrowid)
        return VersionRecord(
            id=version_id,
            dataset_name=dataset_name,
            version=version,
            created_at=datetime.fromisoformat(created_at),
            object_path=object_path,
            content_hash=content_hash,
            rows_count=rows_count,
            columns_count=columns_count,
            schema_json=json.dumps(schema) if schema is not None else None,
            stats_json=json.dumps(stats) if stats is not None else None,
        )
    finally:
        conn.close()


def list_datasets(base_path: Path | None = None) -> list[str]:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("select name from datasets order by name asc")
        rows = cur.fetchall()
        return [row["name"] for row in rows]
    finally:
        conn.close()


def get_dataset_summary(dataset_name: str, base_path: Path | None = None) -> dict[str, Any] | None:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("select id from datasets where name = ?", (dataset_name,))
        if cur.fetchone() is None:
            return None
    finally:
        conn.close()

    versions = list_versions(dataset_name, base_path)
    if not versions:
        return {
            "name": dataset_name,
            "versions_count": 0,
            "latest_version": None,
            "last_updated": None,
        }
    
    latest = versions[-1]
    return {
        "name": dataset_name,
        "versions_count": len(versions),
        "latest_version": latest.version,
        "last_updated": latest.created_at.isoformat(),
        "rows_count": latest.rows_count,
        "columns_count": latest.columns_count,
    }


def list_versions(dataset_name: str, base_path: Path | None = None) -> list[VersionRecord]:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            select v.id, d.name as dataset_name, v.version, v.created_at,
                   v.object_path, v.content_hash, v.rows_count, v.columns_count,
                   v.schema_json, v.stats_json
            from versions v
            join datasets d on v.dataset_id = d.id
            where d.name = ?
            order by v.created_at asc
            """,
            (dataset_name,),
        )
        rows = cur.fetchall()
        result: list[VersionRecord] = []
        for row in rows:
            result.append(
                VersionRecord(
                    id=int(row["id"]),
                    dataset_name=row["dataset_name"],
                    version=row["version"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    object_path=row["object_path"],
                    content_hash=row["content_hash"],
                    rows_count=row["rows_count"],
                    columns_count=row["columns_count"],
                    schema_json=row["schema_json"],
                    stats_json=row["stats_json"],
                )
            )
        return result
    finally:
        conn.close()


def get_version_by_label(
    dataset_name: str,
    version_label: str,
    base_path: Path | None = None,
) -> VersionRecord | None:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            select v.id, d.name as dataset_name, v.version, v.created_at,
                   v.object_path, v.content_hash, v.rows_count, v.columns_count,
                   v.schema_json, v.stats_json
            from versions v
            join datasets d on v.dataset_id = d.id
            where d.name = ? and v.version = ?
            """,
            (dataset_name, version_label),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return VersionRecord(
            id=int(row["id"]),
            dataset_name=row["dataset_name"],
            version=row["version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            object_path=row["object_path"],
            content_hash=row["content_hash"],
            rows_count=row["rows_count"],
            columns_count=row["columns_count"],
            schema_json=row["schema_json"],
            stats_json=row["stats_json"],
        )
    finally:
        conn.close()


def get_latest_version(
    dataset_name: str,
    before: datetime | None = None,
    base_path: Path | None = None,
) -> VersionRecord | None:
    versions = list_versions(dataset_name, base_path)
    if not versions:
        return None
    if before is None:
        return versions[-1]
    candidates = [v for v in versions if v.created_at <= before]
    if not candidates:
        return None
    return candidates[-1]


def record_experiment(
    external_id: str,
    dataset_version_id: int,
    metadata: dict[str, Any] | None,
    base_path: Path | None = None,
) -> None:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        created_at = datetime.now(UTC).isoformat()
        cur.execute(
            """
            insert or replace into experiments(
                external_id, dataset_version_id, created_at, metadata_json
            ) values (?, ?, ?, ?)
            """,
            (
                external_id,
                dataset_version_id,
                created_at,
                json.dumps(metadata) if metadata is not None else None,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_experiment_dataset_version(
    external_id: str,
    base_path: Path | None = None,
) -> VersionRecord | None:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            select v.id, d.name as dataset_name, v.version, v.created_at,
                   v.object_path, v.content_hash, v.rows_count, v.columns_count,
                   v.schema_json, v.stats_json
            from experiments e
            join versions v on e.dataset_version_id = v.id
            join datasets d on v.dataset_id = d.id
            where e.external_id = ?
            """,
            (external_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return VersionRecord(
            id=int(row["id"]),
            dataset_name=row["dataset_name"],
            version=row["version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            object_path=row["object_path"],
            content_hash=row["content_hash"],
            rows_count=row["rows_count"],
            columns_count=row["columns_count"],
            schema_json=row["schema_json"],
            stats_json=row["stats_json"],
        )
    finally:
        conn.close()


def record_lineage_step(
    dataset_version_id: int,
    step_name: str,
    step_order: int,
    metadata: dict[str, Any] | None,
    base_path: Path | None = None,
) -> None:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        created_at = datetime.now(UTC).isoformat()
        cur.execute(
            """
            insert into lineage(
                dataset_version_id, step_name, step_order, created_at, metadata_json
            ) values (?, ?, ?, ?, ?)
            """,
            (
                dataset_version_id,
                step_name,
                step_order,
                created_at,
                json.dumps(metadata) if metadata is not None else None,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def list_lineage(
    dataset_version_id: int,
    base_path: Path | None = None,
) -> list[dict[str, Any]]:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            select step_name, step_order, created_at, metadata_json
            from lineage
            where dataset_version_id = ?
            order by step_order asc
            """,
            (dataset_version_id,),
        )
        rows = cur.fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            metadata_json = row["metadata_json"]
            metadata = json.loads(metadata_json) if metadata_json is not None else None
            result.append(
                {
                    "step_name": row["step_name"],
                    "step_order": row["step_order"],
                    "created_at": row["created_at"],
                    "metadata": metadata,
                }
            )
        return result
    finally:
        conn.close()


def next_version_label(dataset_name: str, base_path: Path | None = None) -> str:
    existing = list_versions(dataset_name, base_path)
    if not existing:
        return "v1"
    last = existing[-1].version
    if last.startswith("v") and last[1:].isdigit():
        value = int(last[1:]) + 1
        return f"v{value}"
    return f"v{len(existing) + 1}"


def set_version_tag(
    dataset_name: str,
    version_id: int,
    tag: str,
    base_path: Path | None = None,
) -> None:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            delete from version_tags
            where tag = ? and version_id in (
                select v.id from versions v
                join datasets d on v.dataset_id = d.id
                where d.name = ?
            )
            """,
            (tag, dataset_name),
        )
        cur.execute(
            "insert into version_tags(version_id, tag) values (?, ?)",
            (version_id, tag),
        )
        conn.commit()
    finally:
        conn.close()


def get_version_by_tag(
    dataset_name: str,
    tag: str,
    base_path: Path | None = None,
) -> VersionRecord | None:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            select v.id, d.name as dataset_name, v.version, v.created_at,
                   v.object_path, v.content_hash, v.rows_count, v.columns_count,
                   v.schema_json, v.stats_json
            from version_tags t
            join versions v on t.version_id = v.id
            join datasets d on v.dataset_id = d.id
            where d.name = ? and t.tag = ?
            order by v.created_at desc
            limit 1
            """,
            (dataset_name, tag),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return VersionRecord(
            id=int(row["id"]),
            dataset_name=row["dataset_name"],
            version=row["version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            object_path=row["object_path"],
            content_hash=row["content_hash"],
            rows_count=row["rows_count"],
            columns_count=row["columns_count"],
            schema_json=row["schema_json"],
            stats_json=row["stats_json"],
        )
    finally:
        conn.close()


def list_tags(
    dataset_name: str,
    base_path: Path | None = None,
) -> list[tuple[str, str]]:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            select t.tag, v.version
            from version_tags t
            join versions v on t.version_id = v.id
            join datasets d on v.dataset_id = d.id
            where d.name = ?
            order by v.created_at desc
            """,
            (dataset_name,),
        )
        rows = cur.fetchall()
        return [(row["tag"], row["version"]) for row in rows]
    finally:
        conn.close()


def set_channel(
    dataset_name: str,
    version_id: int,
    channel: str,
    base_path: Path | None = None,
) -> None:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            delete from channels
            where channel = ? and version_id in (
                select v.id from versions v
                join datasets d on v.dataset_id = d.id
                where d.name = ?
            )
            """,
            (channel, dataset_name),
        )
        cur.execute(
            "insert into channels(version_id, channel) values (?, ?)",
            (version_id, channel),
        )
        conn.commit()
    finally:
        conn.close()


def get_version_by_channel(
    dataset_name: str,
    channel: str,
    base_path: Path | None = None,
) -> VersionRecord | None:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            select v.id, d.name as dataset_name, v.version, v.created_at,
                   v.object_path, v.content_hash, v.rows_count, v.columns_count,
                   v.schema_json, v.stats_json
            from channels c
            join versions v on c.version_id = v.id
            join datasets d on v.dataset_id = d.id
            where d.name = ? and c.channel = ?
            order by v.created_at desc
            limit 1
            """,
            (dataset_name, channel),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return VersionRecord(
            id=int(row["id"]),
            dataset_name=row["dataset_name"],
            version=row["version"],
            created_at=datetime.fromisoformat(row["created_at"]),
            object_path=row["object_path"],
            content_hash=row["content_hash"],
            rows_count=row["rows_count"],
            columns_count=row["columns_count"],
            schema_json=row["schema_json"],
            stats_json=row["stats_json"],
        )
    finally:
        conn.close()


def list_channels(
    dataset_name: str,
    base_path: Path | None = None,
) -> list[tuple[str, str]]:
    db_path = get_metadata_path(base_path)
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            select c.channel, v.version
            from channels c
            join versions v on c.version_id = v.id
            join datasets d on v.dataset_id = d.id
            where d.name = ?
            order by v.created_at desc
            """,
            (dataset_name,),
        )
        rows = cur.fetchall()
        return [(row["channel"], row["version"]) for row in rows]
    finally:
        conn.close()
