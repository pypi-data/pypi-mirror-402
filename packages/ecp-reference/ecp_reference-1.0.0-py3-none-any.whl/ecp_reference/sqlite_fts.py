from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable

from .errors import BuildError
from .utils import (
    looks_like_text,
    rfc3339_now,
    read_json,
    read_text_file,
    sha256_bytes,
    sha256_text,
    within_scope,
    write_json,
)

SQLITE_FTS_INDEX_FORMAT = "sqlite-fts-index-v1"
DEFAULT_DB_FILENAME = "fts.sqlite"
DEFAULT_FTS_TABLE = "chunks"


def sqlite_fts5_available() -> bool:
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE VIRTUAL TABLE t USING fts5(x);")
        conn.close()
        return True
    except Exception:
        return False


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _init_db(conn: sqlite3.Connection, *, table: str) -> None:
    # Store a normalized token stream in a single indexed column (tokens) to
    # keep indexing deterministic across platforms and to avoid relying on
    # sqlite tokenizer quirks for code identifiers.
    conn.execute(
        f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS {table} USING fts5(
            chunk_id UNINDEXED,
            source_id UNINDEXED,
            path UNINDEXED,
            start_line UNINDEXED,
            end_line UNINDEXED,
            file_sha256 UNINDEXED,
            chunk_sha256 UNINDEXED,
            tokens
        );
        """
    )


def _chunk_lines(
    lines: list[str],
    *,
    max_chars: int,
    overlap_chars: int,
) -> list[tuple[int, int, str]]:
    if max_chars <= 0:
        raise BuildError(f"chunking max_chars must be > 0 (got {max_chars})")
    if overlap_chars < 0:
        raise BuildError(f"chunking overlap_chars must be >= 0 (got {overlap_chars})")

    chunks: list[tuple[int, int, str]] = []
    i = 0
    while i < len(lines):
        chars = 0
        j = i
        while j < len(lines) and chars + len(lines[j]) <= max_chars:
            chars += len(lines[j])
            j += 1

        if j == i:
            j = i + 1

        start_line = i + 1
        end_line = j
        text = "".join(lines[i:j])
        chunks.append((start_line, end_line, text))

        if j >= len(lines):
            break

        if overlap_chars == 0:
            i = j
            continue

        overlap = 0
        k = j - 1
        while k > i and overlap + len(lines[k]) <= overlap_chars:
            overlap += len(lines[k])
            k -= 1
        next_i = k + 1
        if next_i >= j:
            next_i = j
        i = next_i

    return chunks


def _iter_scoped_files(
    root: Path,
    *,
    include: list[str],
    exclude: list[str],
    deadline: float | None = None,
) -> list[Path]:
    files: list[Path] = []
    for dirpath, _, filenames in os.walk(root):
        if deadline is not None and time.monotonic() > deadline:
            raise BuildError("Index build exceeded max_update_duration_seconds.")
        for fn in filenames:
            if deadline is not None and time.monotonic() > deadline:
                raise BuildError("Index build exceeded max_update_duration_seconds.")
            p = Path(dirpath) / fn
            try:
                rel = p.relative_to(root).as_posix()
            except Exception:
                continue
            if within_scope(rel, include, exclude):
                files.append(p)
    return files


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _fts_token_stream(*, tokens: list[str]) -> str:
    # Keep ordering stable but dedupe within a chunk to reduce index bloat.
    seen: set[str] = set()
    out: list[str] = []
    for t in tokens:
        s = str(t).strip()
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return " ".join(out)


def build_sqlite_fts_index_multi(
    *,
    index_id: str,
    sources: list[Any],
    out_dir: Path,
    max_file_bytes: int,
    max_files: int,
    chunk_max_chars: int,
    chunk_overlap_chars: int,
    deadline: float | None = None,
    created_at: str | None = None,
    db_filename: str = DEFAULT_DB_FILENAME,
    table: str = DEFAULT_FTS_TABLE,
) -> None:
    if not sqlite_fts5_available():
        raise BuildError(
            "SQLite FTS5 is not available in this Python environment; "
            "use the keyword-index-v2 backend instead."
        )

    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    created_at = created_at or rfc3339_now()
    built_at = rfc3339_now()

    db_path = out_dir / db_filename
    if db_path.exists():
        db_path.unlink(missing_ok=True)

    conn = _connect(db_path)
    try:
        _init_db(conn, table=table)
        conn.execute("BEGIN;")

        file_count = 0
        chunk_count = 0
        file_manifests: dict[str, dict[str, dict[str, Any]]] = {}

        chunks_path = out_dir / "chunks.jsonl"
        chunks_path.parent.mkdir(parents=True, exist_ok=True)
        chunks_file = chunks_path.open("w", encoding="utf-8")
        sources_meta: list[dict[str, Any]] = []
        for src in sources:
            sources_meta.append(
                {
                    "source_id": getattr(src, "source_id", ""),
                    "source_type": getattr(src, "source_type", ""),
                    "uri": getattr(src, "source_uri", ""),
                    "classification": getattr(src, "classification", None),
                    "license": getattr(src, "license", None),
                    "revision": getattr(src, "revision", {}) or {},
                }
            )

        sources_by_id = {
            str(s.get("source_id") or ""): s for s in sources_meta if s.get("source_id")
        }

        try:
            from .utils import tokenize

            for src in sources:
                source_id = str(getattr(src, "source_id", "") or "")
                source_root = Path(getattr(src, "source_root")).resolve()
                include = list(getattr(src, "include", []) or ["**/*"])
                exclude = list(getattr(src, "exclude", []) or [])
                source_uri = str(getattr(src, "source_uri", "") or "")
                revision = getattr(src, "revision", {}) or {}
                classification = getattr(src, "classification", None)
                license = getattr(src, "license", None)

                scoped_files = _iter_scoped_files(
                    source_root,
                    include=include,
                    exclude=exclude,
                    deadline=deadline,
                )
                file_count += len(scoped_files)
                if file_count > max_files:
                    raise BuildError(
                        f"Refusing to index {file_count} files (> max_files={max_files}). Narrow scope or raise max_files."
                    )

                per_source_manifest: dict[str, dict[str, Any]] = {}

                for p in scoped_files:
                    if deadline is not None and time.monotonic() > deadline:
                        raise BuildError("Index build exceeded max_update_duration_seconds.")

                    rel = p.relative_to(source_root).as_posix()
                    try:
                        st = p.stat()
                    except Exception:
                        continue

                    if st.st_size > max_file_bytes:
                        per_source_manifest[rel] = {
                            "sha256": None,
                            "size": st.st_size,
                            "skipped": "too_large",
                        }
                        continue
                    if not looks_like_text(p):
                        per_source_manifest[rel] = {
                            "sha256": None,
                            "size": st.st_size,
                            "skipped": "binary_or_non_utf8",
                        }
                        continue

                    text = read_text_file(p)
                    file_sha = sha256_text(text)
                    per_source_manifest[rel] = {"sha256": file_sha, "size": st.st_size, "skipped": None}

                    lines = text.splitlines(keepends=True)
                    chunks = _chunk_lines(
                        lines, max_chars=chunk_max_chars, overlap_chars=chunk_overlap_chars
                    )
                    for start_line, end_line, chunk_text in chunks:
                        # Avoid indexing empty chunks (still cite-able via file/path if needed).
                        chunk_tokens = tokenize(chunk_text) + tokenize(rel)
                        if not chunk_tokens:
                            continue
                        chunk_sha = sha256_bytes(chunk_text.encode("utf-8"))
                        chunk_id = f"{source_id}::{rel}#L{start_line}-L{end_line}"
                        conn.execute(
                            f"INSERT INTO {table}(chunk_id, source_id, path, start_line, end_line, file_sha256, chunk_sha256, tokens) VALUES (?,?,?,?,?,?,?,?)",
                            (
                                chunk_id,
                                source_id,
                                rel,
                                int(start_line),
                                int(end_line),
                                file_sha,
                                chunk_sha,
                                _fts_token_stream(tokens=chunk_tokens),
                            ),
                        )
                        chunk_count += 1

                        rec: dict[str, Any] = {
                            "chunk_id": chunk_id,
                            "source_id": source_id,
                            "uri": source_uri,
                            "artifact_path": rel,
                            "revision": revision,
                            "loc": {"start_line": int(start_line), "end_line": int(end_line)},
                            "chunk_hash": chunk_sha,
                        }
                        if classification:
                            rec["classification"] = classification
                        if license:
                            rec["license"] = license
                        chunks_file.write(json.dumps(rec, ensure_ascii=False) + "\n")

                file_manifests[source_id] = per_source_manifest
        finally:
            chunks_file.close()

        conn.commit()

    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()

    index_data = {
        "format": SQLITE_FTS_INDEX_FORMAT,
        "index_id": index_id,
        "created_at": created_at,
        "built_at": built_at,
        "sources": sources_meta,
        "config": {
            "max_file_bytes": int(max_file_bytes),
            "max_files": int(max_files),
            "tokenizer": "regex[A-Za-z0-9_]+;lower;stopwords;len>=2;split_camel;split_snake;split_digits",
            "chunking": {
                "method": "line-window",
                "max_chars": int(chunk_max_chars),
                "overlap_chars": int(chunk_overlap_chars),
                "language_hints": [],
            },
        },
        "sqlite": {"path": db_filename, "table": table, "fts5": True},
        "stats": {"chunks": int(chunk_count), "files": int(file_count)},
    }

    descriptor = {
        "index_id": index_id,
        "type": "keyword",
        "created_at": created_at,
        "built_at": built_at,
        "chunking": index_data["config"]["chunking"],
        "retrieval_defaults": {"top_k": 8, "filters_supported": ["path_prefix", "source_id"]},
        "provenance": {
            "index_data_path": "index_data.json",
            "file_manifest_path": "file_manifest.json",
            "chunks_path": "chunks.jsonl",
            "build_info_path": "build_info.json",
            "sqlite_path": db_filename,
        },
    }

    file_manifest_out = {
        "format": "ecp-file-manifest-v2",
        "built_at": built_at,
        "sources": file_manifests,
    }

    build_info = {
        "index_id": index_id,
        "type": "keyword",
        "created_at": created_at,
        "built_at": built_at,
        "sources": sources_meta,
        "config": index_data.get("config"),
        "stats": index_data.get("stats"),
    }

    write_json(out_dir / "index.json", descriptor)
    write_json(out_dir / "index_data.json", index_data)
    write_json(out_dir / "file_manifest.json", file_manifest_out)
    write_json(out_dir / "build_info.json", build_info)


def load_sqlite_fts_index(index_dir: Path) -> dict:
    path = index_dir / "index_data.json"
    if not path.exists():
        raise BuildError(f"Missing index_data.json at: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("format") != SQLITE_FTS_INDEX_FORMAT:
        raise BuildError(f"Index format is not {SQLITE_FTS_INDEX_FORMAT!r}.")
    return data


def incremental_update_sqlite_fts_index_multi(
    *,
    index_dir: Path,
    index_data: dict,
    sources: list[Any],
    changes: dict[str, dict[str, Any]],
    file_manifests: dict[str, dict[str, dict[str, Any]]],
    max_file_bytes: int,
    deadline: float | None = None,
) -> None:
    if not sqlite_fts5_available():
        raise BuildError(
            "SQLite FTS5 is not available in this Python environment; "
            "use the keyword-index-v2 backend instead."
        )

    if index_data.get("format") != SQLITE_FTS_INDEX_FORMAT:
        raise BuildError(
            f"Cannot incremental update index format '{index_data.get('format')}'; rebuild required."
        )

    sqlite_cfg = index_data.get("sqlite") if isinstance(index_data.get("sqlite"), dict) else {}
    db_filename = str(sqlite_cfg.get("path") or DEFAULT_DB_FILENAME)
    table = str(sqlite_cfg.get("table") or DEFAULT_FTS_TABLE)
    db_path = (index_dir / db_filename).resolve()
    if not db_path.exists():
        raise BuildError(f"Missing sqlite index database at: {db_path}")

    cfg = index_data.get("config") if isinstance(index_data.get("config"), dict) else {}
    chunking_cfg = cfg.get("chunking") if isinstance(cfg.get("chunking"), dict) else {}
    try:
        chunk_max_chars = int(chunking_cfg.get("max_chars") or 4000)
    except Exception:
        chunk_max_chars = 4000
    try:
        chunk_overlap_chars = int(chunking_cfg.get("overlap_chars") or 200)
    except Exception:
        chunk_overlap_chars = 200
    chunk_max_chars = max(1, min(chunk_max_chars, int(max_file_bytes)))
    chunk_overlap_chars = max(0, min(chunk_overlap_chars, chunk_max_chars - 1))

    sources_meta: list[dict[str, Any]] = []
    for src in sources:
        sources_meta.append(
            {
                "source_id": getattr(src, "source_id", ""),
                "source_type": getattr(src, "source_type", ""),
                "uri": getattr(src, "source_uri", ""),
                "classification": getattr(src, "classification", None),
                "license": getattr(src, "license", None),
                "revision": getattr(src, "revision", {}) or {},
            }
        )
    index_data["sources"] = sources_meta
    index_data["built_at"] = rfc3339_now()

    conn = _connect(db_path)
    try:
        _init_db(conn, table=table)
        conn.execute("BEGIN;")

        for src in sources:
            sid = str(getattr(src, "source_id", "") or "")
            src_changes = changes.get(sid) or {}
            changed_files = list(src_changes.get("changed_files") or [])
            removed_files = list(src_changes.get("removed_files") or [])
            if not changed_files and not removed_files:
                continue

            source_root = Path(getattr(src, "source_root")).resolve()
            include = list(getattr(src, "include", []) or ["**/*"])
            exclude = list(getattr(src, "exclude", []) or [])

            for rel in removed_files:
                conn.execute(
                    f"DELETE FROM {table} WHERE source_id = ? AND path = ?",
                    (sid, str(rel)),
                )

            for rel in changed_files:
                if deadline is not None and time.monotonic() > deadline:
                    raise BuildError("Incremental update exceeded max_update_duration_seconds.")

                abs_path = source_root / str(rel)
                conn.execute(
                    f"DELETE FROM {table} WHERE source_id = ? AND path = ?",
                    (sid, str(rel)),
                )
                if not abs_path.exists():
                    continue
                if not within_scope(str(rel), include, exclude):
                    continue

                try:
                    st = abs_path.stat()
                except Exception:
                    continue
                if st.st_size > max_file_bytes:
                    continue
                if not looks_like_text(abs_path):
                    continue

                text = read_text_file(abs_path)
                file_sha = sha256_text(text)
                lines = text.splitlines(keepends=True)

                chunks = _chunk_lines(lines, max_chars=chunk_max_chars, overlap_chars=chunk_overlap_chars)
                for start_line, end_line, chunk_text in chunks:
                    from .utils import tokenize

                    chunk_tokens = tokenize(chunk_text) + tokenize(str(rel))
                    if not chunk_tokens:
                        continue
                    chunk_sha = sha256_bytes(chunk_text.encode("utf-8"))
                    chunk_id = f"{sid}::{rel}#L{start_line}-L{end_line}"
                    conn.execute(
                        f"INSERT INTO {table}(chunk_id, source_id, path, start_line, end_line, file_sha256, chunk_sha256, tokens) VALUES (?,?,?,?,?,?,?,?)",
                        (
                            chunk_id,
                            sid,
                            str(rel),
                            int(start_line),
                            int(end_line),
                            file_sha,
                            chunk_sha,
                            _fts_token_stream(tokens=chunk_tokens),
                        ),
                    )

        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()

    # Rewrite derived artifacts from sqlite DB for consistency.
    built_at = index_data.get("built_at") or rfc3339_now()
    created_at = index_data.get("created_at") or rfc3339_now()

    sources_by_id: dict[str, dict[str, Any]] = {
        str(s.get("source_id") or ""): s for s in sources_meta if s.get("source_id")
    }

    def _iter_chunk_records() -> Iterable[dict[str, Any]]:
        conn2 = _connect(db_path)
        try:
            cur = conn2.execute(
                f"SELECT chunk_id, source_id, path, start_line, end_line, chunk_sha256 FROM {table}"
            )
            for chunk_id, source_id, rel_path, start_line, end_line, chunk_sha in cur:
                src_meta = sources_by_id.get(str(source_id)) or {}
                rec: dict[str, Any] = {
                    "chunk_id": str(chunk_id),
                    "source_id": str(source_id),
                    "uri": src_meta.get("uri") or "",
                    "artifact_path": str(rel_path),
                    "revision": src_meta.get("revision") or {},
                    "loc": {"start_line": int(start_line), "end_line": int(end_line)},
                    "chunk_hash": str(chunk_sha),
                }
                classification = src_meta.get("classification")
                license = src_meta.get("license")
                if classification:
                    rec["classification"] = classification
                if license:
                    rec["license"] = license
                yield rec
        finally:
            conn2.close()

    chunk_count = 0
    chunks_path = index_dir / "chunks.jsonl"
    chunks_path.parent.mkdir(parents=True, exist_ok=True)
    with chunks_path.open("w", encoding="utf-8") as f:
        for rec in _iter_chunk_records():
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            chunk_count += 1

    index_data["stats"] = {"chunks": int(chunk_count)}

    descriptor_path = index_dir / "index.json"
    desc = read_json(descriptor_path) if descriptor_path.exists() else {}
    if not isinstance(desc, dict):
        desc = {}
    desc.setdefault("index_id", index_data.get("index_id"))
    desc.setdefault("type", "keyword")
    desc.setdefault("created_at", created_at)
    desc["built_at"] = built_at
    desc.setdefault("chunking", cfg.get("chunking") if isinstance(cfg, dict) else {})
    desc.setdefault("retrieval_defaults", {"top_k": 8, "filters_supported": ["path_prefix", "source_id"]})
    desc.setdefault("provenance", {})
    if isinstance(desc["provenance"], dict):
        desc["provenance"].setdefault("index_data_path", "index_data.json")
        desc["provenance"].setdefault("file_manifest_path", "file_manifest.json")
        desc["provenance"].setdefault("chunks_path", "chunks.jsonl")
        desc["provenance"].setdefault("build_info_path", "build_info.json")
        desc["provenance"].setdefault("sqlite_path", db_filename)

    file_manifest_out = {
        "format": "ecp-file-manifest-v2",
        "built_at": built_at,
        "sources": file_manifests,
    }

    build_info = {
        "index_id": index_data.get("index_id"),
        "type": "keyword",
        "created_at": created_at,
        "built_at": built_at,
        "sources": sources_meta,
        "config": index_data.get("config"),
        "stats": index_data.get("stats"),
    }

    write_json(index_dir / "index_data.json", index_data)
    write_json(descriptor_path, desc)
    write_json(index_dir / "file_manifest.json", file_manifest_out)
    write_json(index_dir / "build_info.json", build_info)
