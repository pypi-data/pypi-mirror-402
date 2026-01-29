from __future__ import annotations

import dataclasses
import json
import math
import os
import time
from pathlib import Path
from typing import Any, Iterable

from .errors import BuildError
from .utils import (
    looks_like_text,
    normalize_posix,
    rfc3339_now,
    sha256_bytes,
    read_text_file,
    sha256_text,
    tokenize,
    within_scope,
    write_json,
    write_jsonl,
    read_json,
)
from .vectors import (
    SparseVector,
    hash_embed,
    read_vectors_dense_payload_as_sparse,
    read_vectors_jsonl,
    write_vectors_bin,
    write_vectors_jsonl,
    write_vectors_npy,
)

DEFAULT_MAX_FILE_BYTES = 512_000  # 512KB; keep PoC fast
DEFAULT_MAX_FILES = 20_000
DEFAULT_CHUNK_MAX_CHARS = 4_000
DEFAULT_CHUNK_OVERLAP_CHARS = 200

VECTOR_INDEX_FORMAT = "vector-index-v1"
DEFAULT_VECTOR_DIMENSIONS = 256
DEFAULT_VECTOR_METRIC = "cosine"
DEFAULT_VECTOR_MODEL = "hash-embedding-v1"
DEFAULT_VECTOR_PROVIDER = "local"
DEFAULT_VECTORS_FILENAME = "vectors.jsonl"
DEFAULT_VECTOR_FORMAT = "sparse-jsonl-v1"
DEFAULT_DENSE_DTYPE = "float32"
DEFAULT_DENSE_ENDIANNESS = "little"
DEFAULT_DENSE_ENCODING = "row-major"
DEFAULT_DENSE_CHUNK_ID_ORDER = "chunk_id_lex"


def _normalize_vector_cfg(vector_cfg: dict[str, Any]) -> dict[str, Any]:
    """Normalize vector payload settings for vector-index-v1."""
    vectors_rel = str(vector_cfg.get("vectors_path") or DEFAULT_VECTORS_FILENAME)
    if not vectors_rel:
        vectors_rel = DEFAULT_VECTORS_FILENAME
        vector_cfg["vectors_path"] = vectors_rel

    suffix = Path(vectors_rel).suffix.lower()
    vf = str(vector_cfg.get("vector_format") or "").strip()
    if not vf:
        if suffix == ".bin":
            vf = "dense-bin-v1"
        elif suffix == ".npy":
            vf = "dense-npy-v1"
        else:
            vf = DEFAULT_VECTOR_FORMAT
    vector_cfg["vector_format"] = vf

    if vf in ("dense-bin-v1", "dense-npy-v1"):
        vector_cfg.setdefault("dtype", DEFAULT_DENSE_DTYPE)
        vector_cfg.setdefault("endianness", DEFAULT_DENSE_ENDIANNESS)
        vector_cfg.setdefault("encoding", DEFAULT_DENSE_ENCODING)
        vector_cfg.setdefault("chunk_id_order", DEFAULT_DENSE_CHUNK_ID_ORDER)

        dtype = str(vector_cfg.get("dtype") or "").strip().lower()
        if dtype not in ("float32", "float64"):
            raise BuildError(f"Unsupported vector.dtype for {VECTOR_INDEX_FORMAT}: {dtype!r}")

        endianness = str(vector_cfg.get("endianness") or "").strip().lower()
        if endianness not in ("little", "big"):
            raise BuildError(f"Unsupported vector.endianness for {VECTOR_INDEX_FORMAT}: {endianness!r}")

        encoding = str(vector_cfg.get("encoding") or "").strip().lower()
        if encoding != "row-major":
            raise BuildError(f"Unsupported vector.encoding for {VECTOR_INDEX_FORMAT}: {encoding!r}")

        order = str(vector_cfg.get("chunk_id_order") or "").strip()
        if order not in ("chunk_id_lex", "chunks_jsonl"):
            raise BuildError(f"Unsupported vector.chunk_id_order for {VECTOR_INDEX_FORMAT}: {order!r}")

        if vf == "dense-bin-v1" and suffix not in ("", ".bin"):
            raise BuildError(f"dense-bin-v1 requires vectors_path to end in .bin (got {vectors_rel!r})")
        if vf == "dense-npy-v1" and suffix not in ("", ".npy"):
            raise BuildError(f"dense-npy-v1 requires vectors_path to end in .npy (got {vectors_rel!r})")
    else:
        # JSONL payloads
        if vf not in ("sparse-jsonl-v1", "dense-jsonl-v1"):
            raise BuildError(f"Unsupported vector.vector_format for {VECTOR_INDEX_FORMAT}: {vf!r}")
        if suffix not in ("", ".jsonl"):
            raise BuildError(f"{vf} requires vectors_path to end in .jsonl (got {vectors_rel!r})")

    return vector_cfg


@dataclasses.dataclass(frozen=True)
class SourceSpec:
    source_id: str
    source_type: str
    source_uri: str
    source_root: Path
    include: list[str]
    exclude: list[str]
    revision: dict
    classification: str | None = None
    license: str | None = None


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
    for dirpath, dirnames, filenames in os.walk(root):
        if deadline is not None and time.monotonic() > deadline:
            raise BuildError("Index build exceeded max_update_duration_seconds.")
        for fn in filenames:
            if deadline is not None and time.monotonic() > deadline:
                raise BuildError("Index build exceeded max_update_duration_seconds.")
            p = Path(dirpath) / fn
            try:
                rel = normalize_posix(p.relative_to(root))
            except Exception:
                continue
            if within_scope(rel, include, exclude):
                files.append(p)
    return files

def _read_text_file(path: Path) -> str:
    # Caller should have checked looks_like_text
    return read_text_file(path)

def build_keyword_index(
    *,
    index_id: str,
    source_id: str,
    source_type: str,
    source_uri: str,
    source_root: Path,
    include: list[str],
    exclude: list[str],
    out_dir: Path,
    source_revision: dict,
    classification: str | None = None,
    license: str | None = None,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_files: int = DEFAULT_MAX_FILES,
    deadline: float | None = None,
) -> dict:
    """Build a keyword index and write it to out_dir.

    Produces:
      - out_dir/index.json (descriptor)
      - out_dir/index_data.json (content)
      - out_dir/file_manifest.json (file hashes for non-git incremental refresh)
    """
    source_root = source_root.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    files = _iter_scoped_files(source_root, include=include, exclude=exclude, deadline=deadline)
    if len(files) > max_files:
        raise BuildError(f"Refusing to index {len(files)} files (> max_files={max_files}). Narrow scope or raise max_files.")

    documents: dict[str, dict] = {}
    doc_terms: dict[str, dict[str, int]] = {}
    terms: dict[str, dict[str, Any]] = {}  # token -> {df, postings: [[doc_id, tf], ...]}

    file_manifest: dict[str, dict[str, Any]] = {}

    for p in files:
        if deadline is not None and time.monotonic() > deadline:
            raise BuildError("Index build exceeded max_update_duration_seconds.")
        rel = p.relative_to(source_root).as_posix()
        try:
            st = p.stat()
        except Exception:
            continue
        if st.st_size > max_file_bytes:
            # Track in manifest but skip indexing.
            file_manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "too_large"}
            continue
        if not looks_like_text(p):
            file_manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "binary_or_non_utf8"}
            continue

        sha = sha256_text(_read_text_file(p))
        file_manifest[rel] = {"sha256": sha, "size": st.st_size, "skipped": None}

        text = _read_text_file(p)
        line_count = max(1, text.count("\n") + 1)
        tokens = tokenize(text)
        if not tokens:
            documents[rel] = {
                "path": rel,
                "sha256": sha,
                "size": st.st_size,
                "mtime": int(st.st_mtime),
                "lines": line_count,
            }
            doc_terms[rel] = {}
            continue

        # term frequency
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1

        documents[rel] = {
            "path": rel,
            "sha256": sha,
            "size": st.st_size,
            "mtime": int(st.st_mtime),
            "lines": line_count,
        }
        doc_terms[rel] = tf

        for t, c in tf.items():
            entry = terms.get(t)
            if entry is None:
                entry = {"df": 0, "postings": []}
                terms[t] = entry
            entry["df"] += 1
            entry["postings"].append([rel, c])

    index_data = {
        "format": "keyword-index-v1",
        "index_id": index_id,
        "created_at": rfc3339_now(),
        "built_at": rfc3339_now(),
        "source": {
            "source_id": source_id,
            "source_type": source_type,
            "uri": source_uri,
            "classification": classification,
            "license": license,
        },
        "source_revision": source_revision,
        "config": {
            "max_file_bytes": max_file_bytes,
            "max_files": max_files,
            "tokenizer": "regex[A-Za-z0-9_]+;lower;stopwords;len>=2;split_camel;split_snake;split_digits",
        },
        "documents": documents,
        "doc_terms": doc_terms,
        "terms": terms,
    }

    descriptor = {
        "index_id": index_id,
        "type": "keyword",
        "created_at": index_data["created_at"],
        "built_at": index_data["built_at"],
        "chunking": {
            "method": "file",
            "max_chars": max_file_bytes,
            "overlap_chars": 0,
            "language_hints": [],
        },
        "retrieval_defaults": {
            "top_k": 8,
            "filters_supported": ["path_prefix", "source_id"],
        },
        "provenance": {
            "index_data_path": "index_data.json",
            "file_manifest_path": "file_manifest.json",
            "chunks_path": "chunks.jsonl",
            "build_info_path": "build_info.json",
        },
    }

    chunk_records: list[dict[str, Any]] = []
    for doc_id, meta in documents.items():
        end_line = int(meta.get("lines") or 1)
        rec: dict[str, Any] = {
            "chunk_id": doc_id,
            "source_id": source_id,
            "uri": source_uri,
            "artifact_path": doc_id,
            "revision": source_revision,
            "loc": {"start_line": 1, "end_line": end_line},
            "chunk_hash": meta.get("sha256"),
        }
        if classification:
            rec["classification"] = classification
        if license:
            rec["license"] = license
        chunk_records.append(rec)

    build_info = {
        "index_id": index_id,
        "type": "keyword",
        "created_at": index_data["created_at"],
        "built_at": index_data["built_at"],
        "source": index_data.get("source"),
        "source_revision": source_revision,
        "config": index_data.get("config"),
        "stats": {
            "documents": len(documents),
            "terms": len(terms),
        },
    }

    write_json(out_dir / "index.json", descriptor)
    write_json(out_dir / "index_data.json", index_data)
    write_json(out_dir / "file_manifest.json", file_manifest)
    write_jsonl(out_dir / "chunks.jsonl", chunk_records)
    write_json(out_dir / "build_info.json", build_info)
    return index_data

def load_keyword_index(index_dir: Path) -> dict:
    index_path = index_dir / "index_data.json"
    if not index_path.exists():
        raise BuildError(f"Missing index_data.json at: {index_path}")
    return read_json(index_path)

def save_keyword_index(index_dir: Path, index_data: dict) -> None:
    """Save keyword index and update descriptor with built_at timestamp."""     
    index_dir.mkdir(parents=True, exist_ok=True)
    # Avoid leaking build-machine absolute paths into published artifacts.
    index_data.pop("source_root", None)
    write_json(index_dir / "index_data.json", index_data)

    # Update index descriptor with new built_at timestamp
    descriptor_path = index_dir / "index.json"
    try:
        descriptor = read_json(descriptor_path) if descriptor_path.exists() else {}
        if not isinstance(descriptor, dict):
            descriptor = {}

        descriptor.setdefault("index_id", index_data.get("index_id"))
        descriptor.setdefault("type", "keyword")
        descriptor.setdefault("created_at", index_data.get("created_at", rfc3339_now()))
        descriptor["built_at"] = index_data.get("built_at", rfc3339_now())
        descriptor.setdefault(
            "chunking",
            {
                "method": "file",
                "max_chars": int((index_data.get("config") or {}).get("max_file_bytes", DEFAULT_MAX_FILE_BYTES)),
                "overlap_chars": 0,
                "language_hints": [],
            },
        )
        descriptor.setdefault(
            "retrieval_defaults",
            {
                "top_k": 8,
                "filters_supported": ["path_prefix", "source_id"],
            },
        )
        descriptor.setdefault("provenance", {})
        if isinstance(descriptor["provenance"], dict):
            descriptor["provenance"].setdefault("index_data_path", "index_data.json")
            descriptor["provenance"].setdefault("file_manifest_path", "file_manifest.json")
            descriptor["provenance"].setdefault("chunks_path", "chunks.jsonl")
            descriptor["provenance"].setdefault("build_info_path", "build_info.json")

        write_json(descriptor_path, descriptor)
    except Exception:
        pass  # Non-critical; descriptor update is best-effort

    # Refresh provenance artifacts best-effort.
    try:
        source = index_data.get("source") or {}
        source_id = source.get("source_id") or "unknown"
        source_uri = source.get("uri") or ""
        source_revision = index_data.get("source_revision") or {}
        classification = source.get("classification")
        license = source.get("license")

        chunk_records: list[dict[str, Any]] = []
        for doc_id, meta in (index_data.get("documents") or {}).items():
            if not isinstance(meta, dict):
                continue
            end_line = int(meta.get("lines") or 1)
            rec: dict[str, Any] = {
                "chunk_id": doc_id,
                "source_id": source_id,
                "uri": source_uri,
                "artifact_path": doc_id,
                "revision": source_revision,
                "loc": {"start_line": 1, "end_line": end_line},
                "chunk_hash": meta.get("sha256"),
            }
            if classification:
                rec["classification"] = classification
            if license:
                rec["license"] = license
            chunk_records.append(rec)

        build_info = {
            "index_id": index_data.get("index_id"),
            "type": "keyword",
            "created_at": index_data.get("created_at"),
            "built_at": index_data.get("built_at"),
            "source": index_data.get("source"),
            "source_revision": source_revision,
            "config": index_data.get("config"),
            "stats": {
                "documents": len(index_data.get("documents") or {}),
                "terms": len(index_data.get("terms") or {}),
            },
        }

        write_jsonl(index_dir / "chunks.jsonl", chunk_records)
        write_json(index_dir / "build_info.json", build_info)
    except Exception:
        pass

def _remove_doc_from_terms(index_data: dict, doc_id: str) -> None:
    doc_terms = index_data.get("doc_terms", {}).get(doc_id, {})
    terms = index_data.get("terms", {})
    for token, tf in doc_terms.items():
        entry = terms.get(token)
        if not entry:
            continue
        postings = entry.get("postings", [])
        postings = [p for p in postings if p[0] != doc_id]
        if postings:
            entry["postings"] = postings
            entry["df"] = len(postings)
        else:
            terms.pop(token, None)

    index_data.get("doc_terms", {}).pop(doc_id, None)
    index_data.get("documents", {}).pop(doc_id, None)

def _add_doc(index_data: dict, *, doc_id: str, metadata: dict, tf: dict[str, int]) -> None:
    index_data.setdefault("documents", {})[doc_id] = metadata
    index_data.setdefault("doc_terms", {})[doc_id] = tf
    terms = index_data.setdefault("terms", {})
    for token, c in tf.items():
        entry = terms.get(token)
        if entry is None:
            entry = {"df": 0, "postings": []}
            terms[token] = entry
        # Ensure no duplicates; remove if exists then add.
        entry["postings"] = [p for p in entry["postings"] if p[0] != doc_id]
        entry["postings"].append([doc_id, c])
        entry["df"] = len(entry["postings"])

def incremental_update_keyword_index(
    *,
    index_data: dict,
    source_root: Path,
    include: list[str],
    exclude: list[str],
    changed_files: list[str],
    removed_files: list[str],
    source_revision: dict | None = None,
    max_file_bytes: int | None = None,
    deadline: float | None = None,
) -> dict:
    """Incrementally update the keyword index.

    changed_files/removed_files are relative POSIX paths from source_root.
    """
    source_root = source_root.resolve()
    max_file_bytes = max_file_bytes or index_data.get("config", {}).get("max_file_bytes", DEFAULT_MAX_FILE_BYTES)

    # Remove deleted docs
    for rel in removed_files:
        _remove_doc_from_terms(index_data, rel)

    # Update changed docs
    for rel in changed_files:
        if deadline is not None and time.monotonic() > deadline:
            raise BuildError("Incremental update exceeded max_update_duration_seconds.")
        abs_path = source_root / rel
        if not abs_path.exists():
            _remove_doc_from_terms(index_data, rel)
            continue

        # scope check (in case policy changed)
        if not within_scope(rel, include, exclude):
            _remove_doc_from_terms(index_data, rel)
            continue

        try:
            st = abs_path.stat()
        except Exception:
            continue

        # Remove prior state
        if rel in index_data.get("documents", {}):
            _remove_doc_from_terms(index_data, rel)

        if st.st_size > max_file_bytes:
            continue
        if not looks_like_text(abs_path):
            continue

        sha = sha256_text(read_text_file(abs_path))
        text = read_text_file(abs_path)
        line_count = max(1, text.count("\n") + 1)
        tokens = tokenize(text)
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1

        meta = {
            "path": rel,
            "sha256": sha,
            "size": st.st_size,
            "mtime": int(st.st_mtime),
            "lines": line_count,
        }
        _add_doc(index_data, doc_id=rel, metadata=meta, tf=tf)

    index_data["built_at"] = rfc3339_now()
    if source_revision is not None:
        index_data["source_revision"] = source_revision
    return index_data


def _write_keyword_index_artifacts_v2(
    index_dir: Path,
    *,
    index_data: dict,
    file_manifests: dict[str, dict[str, dict[str, Any]]],
) -> None:
    index_dir = index_dir.resolve()
    index_dir.mkdir(parents=True, exist_ok=True)

    built_at = index_data.get("built_at") or rfc3339_now()
    created_at = index_data.get("created_at") or rfc3339_now()

    cfg = index_data.get("config") or {}
    chunking_cfg = (cfg.get("chunking") or {}) if isinstance(cfg, dict) else {}

    descriptor = {
        "index_id": index_data.get("index_id"),
        "type": "keyword",
        "created_at": created_at,
        "built_at": built_at,
        "chunking": {
            "method": chunking_cfg.get("method", "line-window"),
            "max_chars": int(chunking_cfg.get("max_chars") or DEFAULT_CHUNK_MAX_CHARS),
            "overlap_chars": int(chunking_cfg.get("overlap_chars") or 0),
            "language_hints": list(chunking_cfg.get("language_hints") or []),
        },
        "retrieval_defaults": {
            "top_k": 8,
            "filters_supported": ["path_prefix", "source_id"],
        },
        "provenance": {
            "index_data_path": "index_data.json",
            "file_manifest_path": "file_manifest.json",
            "chunks_path": "chunks.jsonl",
            "build_info_path": "build_info.json",
        },
    }

    sources_by_id: dict[str, dict[str, Any]] = {}
    for s in index_data.get("sources") or []:
        if not isinstance(s, dict):
            continue
        sid = s.get("source_id")
        if sid:
            sources_by_id[str(sid)] = s

    chunk_records: list[dict[str, Any]] = []
    docs = index_data.get("documents") or {}
    if isinstance(docs, dict):
        for doc_id, meta in docs.items():
            if not isinstance(meta, dict):
                continue
            source_id = str(meta.get("source_id") or "repo")
            src_meta = sources_by_id.get(source_id) or {}
            rel_path = meta.get("path") or ""
            start_line = int(meta.get("start_line") or 1)
            end_line = int(meta.get("end_line") or 1)
            rec: dict[str, Any] = {
                "chunk_id": doc_id,
                "source_id": source_id,
                "uri": src_meta.get("uri") or "",
                "artifact_path": rel_path,
                "revision": src_meta.get("revision") or {},
                "loc": {"start_line": start_line, "end_line": end_line},
                "chunk_hash": meta.get("chunk_sha256") or meta.get("sha256") or meta.get("file_sha256"),
            }
            classification = src_meta.get("classification")
            license = src_meta.get("license")
            if classification:
                rec["classification"] = classification
            if license:
                rec["license"] = license
            chunk_records.append(rec)

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
        "sources": list(sources_by_id.values()),
        "config": cfg,
        "stats": {
            "documents": len(docs) if isinstance(docs, dict) else 0,
            "terms": len(index_data.get("terms") or {}),
        },
    }

    write_json(index_dir / "index.json", descriptor)
    write_json(index_dir / "index_data.json", index_data)
    write_json(index_dir / "file_manifest.json", file_manifest_out)
    write_jsonl(index_dir / "chunks.jsonl", chunk_records)
    write_json(index_dir / "build_info.json", build_info)


def _load_file_manifests(index_dir: Path) -> dict[str, dict[str, dict[str, Any]]]:
    path = index_dir / "file_manifest.json"
    if not path.exists():
        return {}
    raw = read_json(path)
    if isinstance(raw, dict) and isinstance(raw.get("sources"), dict):
        out: dict[str, dict[str, dict[str, Any]]] = {}
        for sid, m in raw.get("sources", {}).items():
            if isinstance(m, dict):
                out[str(sid)] = m
        return out
    if isinstance(raw, dict):
        return {"repo": raw}
    return {}


def build_keyword_index_multi(
    *,
    index_id: str,
    sources: list[SourceSpec],
    out_dir: Path,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_files: int = DEFAULT_MAX_FILES,
    chunk_max_chars: int = DEFAULT_CHUNK_MAX_CHARS,
    chunk_overlap_chars: int = DEFAULT_CHUNK_OVERLAP_CHARS,
    deadline: float | None = None,
    created_at: str | None = None,
) -> tuple[dict, dict[str, dict[str, dict[str, Any]]]]:
    if not sources:
        raise BuildError("At least one source is required to build an index.")

    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    created_at = created_at or rfc3339_now()
    built_at = rfc3339_now()

    documents: dict[str, dict[str, Any]] = {}
    doc_terms: dict[str, dict[str, int]] = {}
    terms: dict[str, dict[str, Any]] = {}
    file_chunks: dict[str, dict[str, list[str]]] = {}
    file_manifests: dict[str, dict[str, dict[str, Any]]] = {}

    file_count = 0
    for src in sources:
        source_root = src.source_root.resolve()
        scoped_files = _iter_scoped_files(
            source_root,
            include=src.include,
            exclude=src.exclude,
            deadline=deadline,
        )
        file_count += len(scoped_files)
        if file_count > max_files:
            raise BuildError(
                f"Refusing to index {file_count} files (> max_files={max_files}). Narrow scope or raise max_files."
            )

        per_source_manifest: dict[str, dict[str, Any]] = {}
        per_source_file_chunks: dict[str, list[str]] = {}

        for p in scoped_files:
            if deadline is not None and time.monotonic() > deadline:
                raise BuildError("Index build exceeded max_update_duration_seconds.")

            rel = p.relative_to(source_root).as_posix()
            try:
                st = p.stat()
            except Exception:
                continue

            if st.st_size > max_file_bytes:
                per_source_manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "too_large"}
                per_source_file_chunks[rel] = []
                continue
            if not looks_like_text(p):
                per_source_manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "binary_or_non_utf8"}
                per_source_file_chunks[rel] = []
                continue

            file_sha = sha256_text(_read_text_file(p))
            per_source_manifest[rel] = {"sha256": file_sha, "size": st.st_size, "skipped": None}

            text = _read_text_file(p)
            lines = text.splitlines(keepends=True)
            file_line_count = max(1, len(lines))

            chunks = _chunk_lines(lines, max_chars=chunk_max_chars, overlap_chars=chunk_overlap_chars)
            chunk_ids: list[str] = []

            for start_line, end_line, chunk_text in chunks:
                chunk_tokens = tokenize(chunk_text)
                if not chunk_tokens:
                    continue

                chunk_sha = sha256_bytes(chunk_text.encode("utf-8"))
                doc_id = f"{src.source_id}::{rel}#L{start_line}-L{end_line}"
                chunk_ids.append(doc_id)

                tf: dict[str, int] = {}
                for t in chunk_tokens:
                    tf[t] = tf.get(t, 0) + 1

                documents[doc_id] = {
                    "source_id": src.source_id,
                    "path": rel,
                    "start_line": start_line,
                    "end_line": end_line,
                    "file_sha256": file_sha,
                    "chunk_sha256": chunk_sha,
                    "size": st.st_size,
                    "mtime": int(st.st_mtime),
                    "lines": file_line_count,
                }
                doc_terms[doc_id] = tf

                for t, c in tf.items():
                    entry = terms.get(t)
                    if entry is None:
                        entry = {"df": 0, "postings": []}
                        terms[t] = entry
                    entry["df"] += 1
                    entry["postings"].append([doc_id, c])

            per_source_file_chunks[rel] = chunk_ids

        file_manifests[src.source_id] = per_source_manifest
        file_chunks[src.source_id] = per_source_file_chunks

    index_data = {
        "format": "keyword-index-v2",
        "index_id": index_id,
        "created_at": created_at,
        "built_at": built_at,
        "sources": [
            {
                "source_id": s.source_id,
                "source_type": s.source_type,
                "uri": s.source_uri,
                "classification": s.classification,
                "license": s.license,
                "revision": s.revision,
            }
            for s in sources
        ],
        "config": {
            "max_file_bytes": max_file_bytes,
            "max_files": max_files,
            "tokenizer": "regex[A-Za-z0-9_]+;lower;stopwords;len>=2;split_camel;split_snake;split_digits",
            "chunking": {
                "method": "line-window",
                "max_chars": chunk_max_chars,
                "overlap_chars": chunk_overlap_chars,
                "language_hints": [],
            },
        },
        "documents": documents,
        "doc_terms": doc_terms,
        "terms": terms,
        "file_chunks": file_chunks,
    }

    _write_keyword_index_artifacts_v2(out_dir, index_data=index_data, file_manifests=file_manifests)
    return index_data, file_manifests


def incremental_update_keyword_index_multi(
    *,
    index_dir: Path,
    index_data: dict,
    sources: list[SourceSpec],
    changes: dict[str, dict[str, list[str]]],
    file_manifests: dict[str, dict[str, dict[str, Any]]] | None = None,   
    max_file_bytes: int | None = None,
    deadline: float | None = None,
) -> tuple[dict, dict[str, dict[str, dict[str, Any]]]]:
    if not sources:
        raise BuildError("At least one source is required to update an index.")

    if index_data.get("format") != "keyword-index-v2":
        raise BuildError(
            f"Cannot incremental update index format '{index_data.get('format')}'; rebuild required."
        )

    cfg = index_data.get("config") or {}
    max_file_bytes = max_file_bytes or int(cfg.get("max_file_bytes") or DEFAULT_MAX_FILE_BYTES)

    chunking_cfg = (cfg.get("chunking") or {}) if isinstance(cfg, dict) else {}
    chunk_max_chars = int(chunking_cfg.get("max_chars") or DEFAULT_CHUNK_MAX_CHARS)
    chunk_overlap_chars = int(chunking_cfg.get("overlap_chars") or DEFAULT_CHUNK_OVERLAP_CHARS)

    sources_meta_by_id = {}
    for s in sources:
        sources_meta_by_id[str(s.source_id)] = {
            "source_id": s.source_id,
            "source_type": s.source_type,
            "uri": s.source_uri,
            "classification": s.classification,
            "license": s.license,
            "revision": s.revision,
        }
    index_data["sources"] = list(sources_meta_by_id.values())

    file_chunks = index_data.setdefault("file_chunks", {})
    if not isinstance(file_chunks, dict):
        file_chunks = {}
        index_data["file_chunks"] = file_chunks

    if file_manifests is None:
        file_manifests = _load_file_manifests(index_dir)

    for src in sources:
        src_changes = changes.get(src.source_id) or {}
        changed_files = list(src_changes.get("changed_files") or [])
        removed_files = list(src_changes.get("removed_files") or [])
        if not changed_files and not removed_files:
            continue

        source_root = src.source_root.resolve()
        per_source_file_chunks = file_chunks.setdefault(src.source_id, {})
        if not isinstance(per_source_file_chunks, dict):
            per_source_file_chunks = {}
            file_chunks[src.source_id] = per_source_file_chunks

        per_source_manifest = file_manifests.setdefault(src.source_id, {})

        def _remove_file_chunks(rel_path: str) -> None:
            ids = per_source_file_chunks.get(rel_path) or []
            for cid in list(ids):
                _remove_doc_from_terms(index_data, cid)
            per_source_file_chunks.pop(rel_path, None)

        for rel in removed_files:
            _remove_file_chunks(rel)
            per_source_manifest.pop(rel, None)

        for rel in changed_files:
            if deadline is not None and time.monotonic() > deadline:
                raise BuildError("Incremental update exceeded max_update_duration_seconds.")

            abs_path = source_root / rel
            if not abs_path.exists():
                _remove_file_chunks(rel)
                per_source_manifest.pop(rel, None)
                continue
            if not within_scope(rel, src.include, src.exclude):
                _remove_file_chunks(rel)
                per_source_manifest.pop(rel, None)
                continue

            _remove_file_chunks(rel)

            try:
                st = abs_path.stat()
            except Exception:
                continue

            if st.st_size > max_file_bytes:
                per_source_manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "too_large"}
                per_source_file_chunks[rel] = []
                continue
            if not looks_like_text(abs_path):
                per_source_manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "binary_or_non_utf8"}
                per_source_file_chunks[rel] = []
                continue

            file_sha = sha256_text(read_text_file(abs_path))
            per_source_manifest[rel] = {"sha256": file_sha, "size": st.st_size, "skipped": None}

            text = read_text_file(abs_path)
            lines = text.splitlines(keepends=True)
            file_line_count = max(1, len(lines))

            chunks = _chunk_lines(lines, max_chars=chunk_max_chars, overlap_chars=chunk_overlap_chars)
            chunk_ids: list[str] = []

            for start_line, end_line, chunk_text in chunks:
                chunk_tokens = tokenize(chunk_text)
                if not chunk_tokens:
                    continue

                chunk_sha = sha256_bytes(chunk_text.encode("utf-8"))
                doc_id = f"{src.source_id}::{rel}#L{start_line}-L{end_line}"
                chunk_ids.append(doc_id)

                tf: dict[str, int] = {}
                for t in chunk_tokens:
                    tf[t] = tf.get(t, 0) + 1

                meta = {
                    "source_id": src.source_id,
                    "path": rel,
                    "start_line": start_line,
                    "end_line": end_line,
                    "file_sha256": file_sha,
                    "chunk_sha256": chunk_sha,
                    "size": st.st_size,
                    "mtime": int(st.st_mtime),
                    "lines": file_line_count,
                }
                _add_doc(index_data, doc_id=doc_id, metadata=meta, tf=tf)

            per_source_file_chunks[rel] = chunk_ids

    index_data["built_at"] = rfc3339_now()
    _write_keyword_index_artifacts_v2(index_dir, index_data=index_data, file_manifests=file_manifests)
    return index_data, file_manifests


def load_vector_index(index_dir: Path) -> dict:
    index_path = index_dir / "index_data.json"
    if not index_path.exists():
        raise BuildError(f"Missing index_data.json at: {index_path}")
    return read_json(index_path)


def _hash_embed_from_config(text: str, *, embedding_cfg: dict[str, Any]) -> SparseVector:
    model = str(embedding_cfg.get("model") or DEFAULT_VECTOR_MODEL).strip()
    provider = str(embedding_cfg.get("provider") or DEFAULT_VECTOR_PROVIDER).strip()
    if model != DEFAULT_VECTOR_MODEL:
        raise BuildError(
            f"Unsupported embedding model {model!r} for {VECTOR_INDEX_FORMAT}; "
            f"PoC supports only {DEFAULT_VECTOR_MODEL!r}."
        )
    if provider not in ("local", "poc", "hash", "hashing", DEFAULT_VECTOR_PROVIDER):
        raise BuildError(
            f"Unsupported embedding provider {provider!r} for {VECTOR_INDEX_FORMAT}; "
            "PoC supports only local hashing embeddings."
        )

    dims_raw = (
        embedding_cfg.get("dimensions")
        or embedding_cfg.get("dims")
        or DEFAULT_VECTOR_DIMENSIONS
    )
    try:
        dims = int(dims_raw)
    except Exception as e:
        raise BuildError(f"Invalid embedding.dimensions: {dims_raw!r}") from e
    if dims <= 0:
        raise BuildError(f"embedding.dimensions must be > 0 (got {dims})")

    params = (
        embedding_cfg.get("params")
        if isinstance(embedding_cfg.get("params"), dict)
        else {}
    )
    salt = str(params.get("salt") or "hash-embed-v1")
    include_char_ngrams = bool(params.get("include_char_ngrams", True))
    try:
        char_ngram = int(params.get("char_ngram", 3))
    except Exception:
        char_ngram = 3
    try:
        char_ngram_weight = float(params.get("char_ngram_weight", 0.5))
    except Exception:
        char_ngram_weight = 0.5

    return hash_embed(
        text,
        dims=dims,
        salt=salt,
        include_char_ngrams=include_char_ngrams,
        char_ngram=char_ngram,
        char_ngram_weight=char_ngram_weight,
    )


def _write_vector_index_artifacts_v1(
    index_dir: Path,
    *,
    index_data: dict,
    vectors_by_id: dict[str, SparseVector],
    file_manifests: dict[str, dict[str, dict[str, Any]]],
) -> None:
    index_dir = index_dir.resolve()
    index_dir.mkdir(parents=True, exist_ok=True)

    # Avoid leaking build-machine absolute paths into published artifacts.
    index_data.pop("source_root", None)

    built_at = index_data.get("built_at") or rfc3339_now()
    created_at = index_data.get("created_at") or built_at

    cfg = index_data.get("config") or {}
    if not isinstance(cfg, dict):
        cfg = {}
        index_data["config"] = cfg

    chunking_cfg = (
        cfg.get("chunking") if isinstance(cfg.get("chunking"), dict) else {}
    )
    embedding_cfg = (
        cfg.get("embedding") if isinstance(cfg.get("embedding"), dict) else {}
    )
    vector_cfg = cfg.get("vector") if isinstance(cfg.get("vector"), dict) else {}

    vectors_rel = str(vector_cfg.get("vectors_path") or DEFAULT_VECTORS_FILENAME)
    if not vectors_rel:
        vectors_rel = DEFAULT_VECTORS_FILENAME
    vector_cfg.setdefault("vectors_path", vectors_rel)
    vector_cfg.setdefault("metric", DEFAULT_VECTOR_METRIC)
    vector_cfg = _normalize_vector_cfg(vector_cfg)
    cfg["vector"] = vector_cfg

    try:
        dims = int((embedding_cfg or {}).get("dimensions") or DEFAULT_VECTOR_DIMENSIONS)
    except Exception:
        dims = DEFAULT_VECTOR_DIMENSIONS

    descriptor = {
        "index_id": index_data.get("index_id"),
        "type": "vector",
        "created_at": created_at,
        "built_at": built_at,
        "chunking": {
            "method": chunking_cfg.get("method", "line-window"),
            "max_chars": int(chunking_cfg.get("max_chars") or DEFAULT_CHUNK_MAX_CHARS),
            "overlap_chars": int(chunking_cfg.get("overlap_chars") or 0),
            "language_hints": list(chunking_cfg.get("language_hints") or []),
        },
        "embedding": dict(embedding_cfg),
        "retrieval_defaults": {
            "top_k": 8,
            "filters_supported": ["path_prefix", "source_id"],
        },
        "provenance": {
            "index_data_path": "index_data.json",
            "vectors_path": vectors_rel,
            "file_manifest_path": "file_manifest.json",
            "chunks_path": "chunks.jsonl",
            "build_info_path": "build_info.json",
        },
    }

    sources_by_id: dict[str, dict[str, Any]] = {}
    for s in index_data.get("sources") or []:
        if not isinstance(s, dict):
            continue
        sid = s.get("source_id")
        if sid:
            sources_by_id[str(sid)] = s

    chunk_records: list[dict[str, Any]] = []
    docs = index_data.get("documents") or {}
    ordered_doc_ids: list[str] = []
    if isinstance(docs, dict):
        ordered_doc_ids = [str(k) for k in docs.keys()]
        order = str(vector_cfg.get("chunk_id_order") or "chunk_id_lex")
        if order != "chunks_jsonl":
            ordered_doc_ids.sort()

        for doc_id in ordered_doc_ids:
            meta = docs.get(doc_id) or {}
            if not isinstance(meta, dict):
                continue
            source_id = str(meta.get("source_id") or "repo")
            src_meta = sources_by_id.get(source_id) or {}
            rel_path = meta.get("path") or ""
            start_line = int(meta.get("start_line") or 1)
            end_line = int(meta.get("end_line") or 1)
            rec: dict[str, Any] = {
                "chunk_id": doc_id,
                "source_id": source_id,
                "uri": src_meta.get("uri") or "",
                "artifact_path": rel_path,
                "revision": src_meta.get("revision") or {},
                "loc": {"start_line": start_line, "end_line": end_line},
                "chunk_hash": meta.get("chunk_sha256") or meta.get("file_sha256"),
            }
            classification = src_meta.get("classification")
            license = src_meta.get("license")
            if classification:
                rec["classification"] = classification
            if license:
                rec["license"] = license
            chunk_records.append(rec)

    file_manifest_out = {
        "format": "ecp-file-manifest-v2",
        "built_at": built_at,
        "sources": file_manifests,
    }

    build_info = {
        "index_id": index_data.get("index_id"),
        "type": "vector",
        "created_at": created_at,
        "built_at": built_at,
        "sources": list(sources_by_id.values()),
        "config": cfg,
        "stats": {
            "documents": len(docs) if isinstance(docs, dict) else 0,
            "dimensions": dims,
            "vectors": len(vectors_by_id),
        },
    }

    write_json(index_dir / "index.json", descriptor)
    write_json(index_dir / "index_data.json", index_data)
    write_json(index_dir / "file_manifest.json", file_manifest_out)
    write_jsonl(index_dir / "chunks.jsonl", chunk_records)

    vectors_path = index_dir / vectors_rel
    vfmt = str(vector_cfg.get("vector_format") or DEFAULT_VECTOR_FORMAT).strip()
    if vfmt == "dense-bin-v1":
        write_vectors_bin(
            vectors_path,
            chunk_ids=ordered_doc_ids,
            vectors_by_id=vectors_by_id,
            dims=dims,
            dtype=str(vector_cfg.get("dtype") or DEFAULT_DENSE_DTYPE),
            endianness=str(vector_cfg.get("endianness") or DEFAULT_DENSE_ENDIANNESS),
        )
    elif vfmt == "dense-npy-v1":
        write_vectors_npy(
            vectors_path,
            chunk_ids=ordered_doc_ids,
            vectors_by_id=vectors_by_id,
            dims=dims,
            dtype=str(vector_cfg.get("dtype") or DEFAULT_DENSE_DTYPE),
            endianness=str(vector_cfg.get("endianness") or DEFAULT_DENSE_ENDIANNESS),
        )
    elif vfmt == "dense-jsonl-v1":
        # Dense JSONL is portable but can be large; provided mainly for completeness.
        vectors_path.parent.mkdir(parents=True, exist_ok=True)
        with vectors_path.open("w", encoding="utf-8") as f:
            for cid in sorted(vectors_by_id.keys()):
                dense = [0.0] * int(dims)
                for i, v in vectors_by_id.get(cid, []) or []:
                    if 0 <= int(i) < int(dims):
                        dense[int(i)] = float(v)
                f.write(json.dumps({"chunk_id": cid, "vector": dense}, ensure_ascii=False) + "\n")
    else:
        write_vectors_jsonl(vectors_path, vectors_by_id)
    write_json(index_dir / "build_info.json", build_info)


def build_vector_index_multi(
    *,
    index_id: str,
    sources: list[SourceSpec],
    out_dir: Path,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_files: int = DEFAULT_MAX_FILES,
    chunk_max_chars: int = DEFAULT_CHUNK_MAX_CHARS,
    chunk_overlap_chars: int = DEFAULT_CHUNK_OVERLAP_CHARS,
    embedding: dict[str, Any] | None = None,
    vector: dict[str, Any] | None = None,
    deadline: float | None = None,
    created_at: str | None = None,
) -> tuple[dict, dict[str, dict[str, dict[str, Any]]]]:
    if not sources:
        raise BuildError("At least one source is required to build an index.")

    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    created_at = created_at or rfc3339_now()
    built_at = rfc3339_now()

    embedding_cfg: dict[str, Any] = dict(embedding or {})
    embedding_cfg.setdefault("model", DEFAULT_VECTOR_MODEL)
    embedding_cfg.setdefault("provider", DEFAULT_VECTOR_PROVIDER)
    embedding_cfg.setdefault("dimensions", DEFAULT_VECTOR_DIMENSIONS)
    if not isinstance(embedding_cfg.get("params"), dict):
        embedding_cfg["params"] = {}

    vector_cfg: dict[str, Any] = dict(vector or {})
    vector_cfg.setdefault("metric", DEFAULT_VECTOR_METRIC)
    vector_cfg.setdefault("vectors_path", DEFAULT_VECTORS_FILENAME)
    vector_cfg = _normalize_vector_cfg(vector_cfg)

    metric = str(vector_cfg.get("metric") or DEFAULT_VECTOR_METRIC).strip().lower()
    if metric not in ("cosine", "dot"):
        raise BuildError(f"Unsupported vector.metric for {VECTOR_INDEX_FORMAT}: {metric!r}")

    docs: dict[str, dict[str, Any]] = {}
    vectors_by_id: dict[str, SparseVector] = {}
    file_chunks: dict[str, dict[str, list[str]]] = {}
    file_manifests: dict[str, dict[str, dict[str, Any]]] = {}

    file_count = 0
    for src in sources:
        source_root = src.source_root.resolve()
        scoped_files = _iter_scoped_files(
            source_root,
            include=src.include,
            exclude=src.exclude,
            deadline=deadline,
        )
        file_count += len(scoped_files)
        if file_count > max_files:
            raise BuildError(
                f"Refusing to index {file_count} files (> max_files={max_files}). Narrow scope or raise max_files."
            )

        per_source_manifest: dict[str, dict[str, Any]] = {}
        per_source_file_chunks: dict[str, list[str]] = {}

        for p in scoped_files:
            if deadline is not None and time.monotonic() > deadline:
                raise BuildError("Index build exceeded max_update_duration_seconds.")

            rel = p.relative_to(source_root).as_posix()
            try:
                st = p.stat()
            except Exception:
                continue

            if st.st_size > max_file_bytes:
                per_source_manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "too_large"}
                per_source_file_chunks[rel] = []
                continue
            if not looks_like_text(p):
                per_source_manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "binary_or_non_utf8"}
                per_source_file_chunks[rel] = []
                continue

            file_sha = sha256_text(_read_text_file(p))
            per_source_manifest[rel] = {"sha256": file_sha, "size": st.st_size, "skipped": None}

            text = _read_text_file(p)
            lines = text.splitlines(keepends=True)
            file_line_count = max(1, len(lines))

            chunks = _chunk_lines(lines, max_chars=chunk_max_chars, overlap_chars=chunk_overlap_chars)
            chunk_ids: list[str] = []

            for start_line, end_line, chunk_text in chunks:
                chunk_tokens = tokenize(chunk_text)
                if not chunk_tokens:
                    continue

                chunk_sha = sha256_bytes(chunk_text.encode("utf-8"))
                doc_id = f"{src.source_id}::{rel}#L{start_line}-L{end_line}"
                chunk_ids.append(doc_id)

                docs[doc_id] = {
                    "source_id": src.source_id,
                    "path": rel,
                    "start_line": start_line,
                    "end_line": end_line,
                    "file_sha256": file_sha,
                    "chunk_sha256": chunk_sha,
                    "size": st.st_size,
                    "mtime": int(st.st_mtime),
                    "lines": file_line_count,
                }
                vectors_by_id[doc_id] = _hash_embed_from_config(chunk_text, embedding_cfg=embedding_cfg)

            per_source_file_chunks[rel] = chunk_ids

        file_manifests[src.source_id] = per_source_manifest
        file_chunks[src.source_id] = per_source_file_chunks

    index_data = {
        "format": VECTOR_INDEX_FORMAT,
        "index_id": index_id,
        "created_at": created_at,
        "built_at": built_at,
        "sources": [
            {
                "source_id": s.source_id,
                "source_type": s.source_type,
                "uri": s.source_uri,
                "classification": s.classification,
                "license": s.license,
                "revision": s.revision,
            }
            for s in sources
        ],
        "config": {
            "max_file_bytes": max_file_bytes,
            "max_files": max_files,
            "tokenizer": "regex[A-Za-z0-9_]+;lower;stopwords;len>=2;split_camel;;split_snake;split_digits",
            "chunking": {
                "method": "line-window",
                "max_chars": chunk_max_chars,
                "overlap_chars": chunk_overlap_chars,
                "language_hints": [],
            },
            "embedding": embedding_cfg,
            "vector": vector_cfg,
        },
        "documents": docs,
        "file_chunks": file_chunks,
    }

    _write_vector_index_artifacts_v1(
        out_dir,
        index_data=index_data,
        vectors_by_id=vectors_by_id,
        file_manifests=file_manifests,
    )
    return index_data, file_manifests


def incremental_update_vector_index_multi(
    *,
    index_dir: Path,
    index_data: dict,
    sources: list[SourceSpec],
    changes: dict[str, dict[str, list[str]]],
    file_manifests: dict[str, dict[str, dict[str, Any]]] | None = None,
    max_file_bytes: int | None = None,
    deadline: float | None = None,
) -> tuple[dict, dict[str, dict[str, dict[str, Any]]]]:
    if not sources:
        raise BuildError("At least one source is required to update an index.")
    if index_data.get("format") != VECTOR_INDEX_FORMAT:
        raise BuildError(
            f"Cannot incremental update index format '{index_data.get('format')}'; rebuild required."
        )

    cfg = index_data.get("config") or {}
    if not isinstance(cfg, dict):
        cfg = {}
        index_data["config"] = cfg

    max_file_bytes = max_file_bytes or int(cfg.get("max_file_bytes") or DEFAULT_MAX_FILE_BYTES)

    chunking_cfg = cfg.get("chunking") if isinstance(cfg.get("chunking"), dict) else {}
    chunk_max_chars = int(chunking_cfg.get("max_chars") or DEFAULT_CHUNK_MAX_CHARS)
    chunk_overlap_chars = int(chunking_cfg.get("overlap_chars") or DEFAULT_CHUNK_OVERLAP_CHARS)

    embedding_cfg = cfg.get("embedding") if isinstance(cfg.get("embedding"), dict) else {}
    dims = int(embedding_cfg.get("dimensions") or DEFAULT_VECTOR_DIMENSIONS)

    vector_cfg = cfg.get("vector") if isinstance(cfg.get("vector"), dict) else {}
    vector_cfg = _normalize_vector_cfg(vector_cfg)
    cfg["vector"] = vector_cfg

    vectors_rel = str(vector_cfg.get("vectors_path") or DEFAULT_VECTORS_FILENAME)
    vectors_path = (index_dir / vectors_rel).resolve()

    vfmt = str(vector_cfg.get("vector_format") or DEFAULT_VECTOR_FORMAT).strip()
    if vfmt in ("dense-bin-v1", "dense-npy-v1"):
        order = str(vector_cfg.get("chunk_id_order") or DEFAULT_DENSE_CHUNK_ID_ORDER)
        docs0 = index_data.get("documents") if isinstance(index_data.get("documents"), dict) else {}
        if order == "chunks_jsonl":
            chunk_ids = []
            chunks_path = (index_dir / "chunks.jsonl").resolve()
            if chunks_path.exists():
                try:
                    with chunks_path.open("r", encoding="utf-8") as f:
                        for line in f:
                            s = line.strip()
                            if not s:
                                continue
                            rec = json.loads(s)
                            if isinstance(rec, dict) and rec.get("chunk_id"):
                                chunk_ids.append(str(rec.get("chunk_id")))
                except Exception:
                    chunk_ids = sorted([str(k) for k in docs0.keys()]) if isinstance(docs0, dict) else []
            else:
                chunk_ids = sorted([str(k) for k in docs0.keys()]) if isinstance(docs0, dict) else []
        else:
            chunk_ids = sorted([str(k) for k in docs0.keys()]) if isinstance(docs0, dict) else []

        vectors_by_id = read_vectors_dense_payload_as_sparse(
            vectors_path,
            chunk_ids=chunk_ids,
            dims=dims,
            dtype=str(vector_cfg.get("dtype") or DEFAULT_DENSE_DTYPE),
            endianness=str(vector_cfg.get("endianness") or DEFAULT_DENSE_ENDIANNESS),
            normalize=False,
        )
    else:
        vectors_by_id = read_vectors_jsonl(vectors_path, dims=dims, normalize=False)

    sources_meta_by_id = {}
    for s in sources:
        sources_meta_by_id[str(s.source_id)] = {
            "source_id": s.source_id,
            "source_type": s.source_type,
            "uri": s.source_uri,
            "classification": s.classification,
            "license": s.license,
            "revision": s.revision,
        }
    index_data["sources"] = list(sources_meta_by_id.values())

    file_chunks = index_data.setdefault("file_chunks", {})
    if not isinstance(file_chunks, dict):
        file_chunks = {}
        index_data["file_chunks"] = file_chunks

    docs = index_data.setdefault("documents", {})
    if not isinstance(docs, dict):
        docs = {}
        index_data["documents"] = docs

    if file_manifests is None:
        file_manifests = _load_file_manifests(index_dir)

    for src in sources:
        src_changes = changes.get(src.source_id) or {}
        changed_files = list(src_changes.get("changed_files") or [])
        removed_files = list(src_changes.get("removed_files") or [])
        if not changed_files and not removed_files:
            continue

        source_root = src.source_root.resolve()
        per_source_file_chunks = file_chunks.setdefault(src.source_id, {})
        if not isinstance(per_source_file_chunks, dict):
            per_source_file_chunks = {}
            file_chunks[src.source_id] = per_source_file_chunks

        per_source_manifest = file_manifests.setdefault(src.source_id, {})

        def _remove_file_chunks(rel_path: str) -> None:
            ids = per_source_file_chunks.get(rel_path) or []
            for cid in list(ids):
                docs.pop(cid, None)
                vectors_by_id.pop(cid, None)
            per_source_file_chunks.pop(rel_path, None)

        for rel in removed_files:
            _remove_file_chunks(rel)
            per_source_manifest.pop(rel, None)

        for rel in changed_files:
            if deadline is not None and time.monotonic() > deadline:
                raise BuildError("Incremental update exceeded max_update_duration_seconds.")

            abs_path = source_root / rel
            if not abs_path.exists():
                _remove_file_chunks(rel)
                per_source_manifest.pop(rel, None)
                continue
            if not within_scope(rel, src.include, src.exclude):
                _remove_file_chunks(rel)
                per_source_manifest.pop(rel, None)
                continue

            _remove_file_chunks(rel)

            try:
                st = abs_path.stat()
            except Exception:
                continue

            if st.st_size > max_file_bytes:
                per_source_manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "too_large"}
                per_source_file_chunks[rel] = []
                continue
            if not looks_like_text(abs_path):
                per_source_manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "binary_or_non_utf8"}
                per_source_file_chunks[rel] = []
                continue

            file_sha = sha256_text(read_text_file(abs_path))
            per_source_manifest[rel] = {"sha256": file_sha, "size": st.st_size, "skipped": None}

            text = read_text_file(abs_path)
            lines = text.splitlines(keepends=True)
            file_line_count = max(1, len(lines))

            chunks = _chunk_lines(lines, max_chars=chunk_max_chars, overlap_chars=chunk_overlap_chars)
            chunk_ids: list[str] = []

            for start_line, end_line, chunk_text in chunks:
                chunk_tokens = tokenize(chunk_text)
                if not chunk_tokens:
                    continue

                chunk_sha = sha256_bytes(chunk_text.encode("utf-8"))
                doc_id = f"{src.source_id}::{rel}#L{start_line}-L{end_line}"
                chunk_ids.append(doc_id)

                docs[doc_id] = {
                    "source_id": src.source_id,
                    "path": rel,
                    "start_line": start_line,
                    "end_line": end_line,
                    "file_sha256": file_sha,
                    "chunk_sha256": chunk_sha,
                    "size": st.st_size,
                    "mtime": int(st.st_mtime),
                    "lines": file_line_count,
                }
                vectors_by_id[doc_id] = _hash_embed_from_config(chunk_text, embedding_cfg=embedding_cfg)

            per_source_file_chunks[rel] = chunk_ids

    index_data["built_at"] = rfc3339_now()
    _write_vector_index_artifacts_v1(
        index_dir,
        index_data=index_data,
        vectors_by_id=vectors_by_id,
        file_manifests=file_manifests,
    )
    return index_data, file_manifests
