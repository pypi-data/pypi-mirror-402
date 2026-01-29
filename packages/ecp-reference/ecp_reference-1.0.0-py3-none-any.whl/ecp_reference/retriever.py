from __future__ import annotations

import dataclasses
import json
import math
import re
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from .errors import QueryError
from .utils import (
    Citation,
    chunk_lines_around_match,
    citation_to_dict,
    normalize_newlines,
    rfc3339_now,
    read_text_file,
    resolve_under_root,
    sha256_bytes,
    tokenize,
    within_scope,
)
from .vectors import (
    coerce_query_vector,
    hash_embed,
    open_dense_vector_reader_from_file,
    read_vectors_jsonl,
    sparse_dot,
)


def _git_show_text(
    repo: Path,
    *,
    commit: str,
    rel_path: str,
    timeout_seconds: int = 20,
) -> str | None:
    try:
        p = subprocess.run(
            ["git", "-C", str(repo), "show", f"{commit}:{rel_path}"],
            capture_output=True,
            timeout=timeout_seconds,
        )
    except Exception:
        return None

    if p.returncode != 0:
        return None
    try:
        text = p.stdout.decode("utf-8")
    except Exception:
        text = p.stdout.decode("utf-8", errors="replace")
    return normalize_newlines(text)


def _descriptor_chunks_path(index_dir: Path) -> Path | None:
    """Resolve chunks.jsonl path from index descriptor if declared."""
    desc_path = index_dir / "index.json"
    if not desc_path.exists():
        return None
    try:
        desc = json.loads(desc_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(desc, dict):
        return None
    prov = desc.get("provenance") if isinstance(desc.get("provenance"), dict) else {}
    rel = prov.get("chunks_path")
    if not rel:
        return None
    try:
        return resolve_under_root(index_dir, str(rel))
    except Exception:
        return None

@dataclasses.dataclass
class RetrievedChunk:
    path: str
    line_start: int
    line_end: int
    snippet: str
    score: float
    citation: Citation

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "snippet": self.snippet,
            "score": self.score,
            "citation": citation_to_dict(self.citation),
        }

def _rank_documents(index_data: dict, query_tokens: list[str], *, top_k: int = 8) -> list[tuple[str, float]]:
    terms = index_data.get("terms", {})
    documents = index_data.get("documents", {})
    doc_terms = index_data.get("doc_terms", {})

    if not documents:
        return []

    N = len(documents)
    scores: dict[str, float] = {}

    for t in query_tokens:
        entry = terms.get(t)
        if not entry:
            continue
        df = max(1, int(entry.get("df", 1)))
        idf = math.log((N + 1) / (df + 1)) + 1.0
        for doc_id, tf in entry.get("postings", []):
            # Normalize by doc length to reduce bias toward large files.
            dl = max(1, sum(doc_terms.get(doc_id, {}).values()))
            scores[doc_id] = scores.get(doc_id, 0.0) + (float(tf) * idf) / math.sqrt(dl)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]

def retrieve(
    *,
    index_data: dict,
    source_roots: dict[str, Path] | None = None,
    source_meta: dict[str, dict[str, Any]] | None = None,
    classification: str | None,
    question: str,
    top_k: int = 5,
    snippet_window: int = 3,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    allowed_source_ids: list[str] | None = None,
    path_prefixes: list[str] | None = None,
    scopes: dict[str, tuple[list[str], list[str]]] | None = None,
) -> list[RetrievedChunk]:
    """Retrieve relevant chunks for a question.

    Args:
        index_data: Loaded keyword index data.
        source_roots: Mapping from source_id to absolute source root path.
        source_meta: Mapping from source_id to {source_type, uri, revision, license}.
        classification: Security classification (optional).
        question: The user's question.
        top_k: Number of results to return.
        snippet_window: Lines of context around matches.
        allowed_source_ids: Optional allowlist of sources to retrieve from.
        path_prefixes: Optional list of path prefixes to include (posix-style).
        scopes: Optional mapping from source_id to (include, exclude) patterns.

    Returns:
        List of RetrievedChunk objects with citations.
    """
    allowed = set(allowed_source_ids or [])
    prefixes = [Path(p).as_posix().lstrip("/") for p in (path_prefixes or [])]

    roots = {str(k): v.resolve() for k, v in (source_roots or {}).items()}
    if not roots:
        raise QueryError("No source_roots configured for retrieval.")

    meta_by_source: dict[str, dict[str, Any]] = {}
    if source_meta:
        meta_by_source = {str(k): (v if isinstance(v, dict) else {}) for k, v in source_meta.items()}
    else:
        src = index_data.get("source") or {}
        sid = str(src.get("source_id") or "repo")
        meta_by_source[sid] = {
            "source_type": src.get("source_type") or "filesystem",
            "uri": src.get("uri") or "",
            "revision": index_data.get("source_revision") or {},
            "license": src.get("license"),
        }

    query_tokens = tokenize(question)
    if not query_tokens:
        raise QueryError("Query produced no usable tokens; try using more specific keywords.")

    # Rank documents - retrieve slightly more than top_k to handle missing files
    ranked = _rank_documents(index_data, query_tokens, top_k=top_k + 3)
    if not ranked:
        return []

    chunks: list[RetrievedChunk] = []
    for doc_id, score in ranked:
        if len(chunks) >= top_k:
            break

        doc_meta = (index_data.get("documents") or {}).get(doc_id) or {}
        if not isinstance(doc_meta, dict):
            doc_meta = {}

        doc_source_id = str(
            doc_meta.get("source_id")
            or (index_data.get("source") or {}).get("source_id")
            or "repo"
        )
        if allowed and doc_source_id not in allowed:
            continue

        rel_path = str(doc_meta.get("path") or doc_id)
        if prefixes and not any(rel_path.startswith(p) for p in prefixes):
            continue

        inc = include or ["**/*"]
        exc = exclude or []
        if scopes and doc_source_id in scopes:
            inc, exc = scopes[doc_source_id]

        if inc is not None or exc is not None:
            if not within_scope(rel_path, inc or ["**/*"], exc or []):
                continue

        root = roots.get(doc_source_id)
        if root is None:
            continue

        m = meta_by_source.get(doc_source_id) or {}
        source_type = str(m.get("source_type") or "filesystem")
        revision = m.get("revision") or {}

        try:
            abs_path = resolve_under_root(root, rel_path)
        except ValueError:
            continue

        text = None
        if source_type == "git":
            commit = str(revision.get("commit") or "").strip()
            if commit:
                text = _git_show_text(root, commit=commit, rel_path=rel_path)

        if text is None:
            if not abs_path.exists():
                continue
            try:
                text = read_text_file(abs_path)
            except Exception:
                continue

        lines = text.splitlines(keepends=True)

        start_line = doc_meta.get("start_line")
        end_line = doc_meta.get("end_line")
        if start_line is not None and end_line is not None:
            try:
                ls = max(1, int(start_line))
                le = max(ls, int(end_line))
            except Exception:
                ls, le = 1, min(len(lines), 1)
            le = min(len(lines), le)
            snippet = "".join(lines[ls - 1 : le])
            line_start, line_end = ls, le
        else:
            match_idx = None
            qset = set(query_tokens)
            for i, line in enumerate(lines):
                if set(tokenize(line)) & qset:
                    match_idx = i
                    break
            if match_idx is None:
                match_idx = 0
            line_start, line_end, snippet = chunk_lines_around_match(lines, match_idx, window=snippet_window)

        chunk_hash = (
            doc_meta.get("chunk_sha256")
            or doc_meta.get("sha256")
            or doc_meta.get("file_sha256")
            or sha256_bytes(snippet.encode("utf-8"))
        )

        citation = Citation(
            source_id=doc_source_id,
            source_type=str(m.get("source_type") or "filesystem"),
            uri=str(m.get("uri") or ""),
            revision=m.get("revision") or {},
            artifact_path=rel_path,
            chunk_id=doc_id,
            retrieved_at=rfc3339_now(),
            loc={"start_line": line_start, "end_line": line_end},
            line_start=line_start,
            line_end=line_end,
            chunk_hash=chunk_hash,
            classification=classification,
            license=m.get("license"),
        )
        chunks.append(
            RetrievedChunk(
                path=rel_path,
                line_start=line_start,
                line_end=line_end,
                snippet=snippet,
                score=float(score),
                citation=citation,
            )
        )

    return chunks


def retrieve_sqlite_fts(
    *,
    index_dir: Path,
    index_data: dict,
    source_roots: dict[str, Path] | None = None,
    source_meta: dict[str, dict[str, Any]] | None = None,
    classification: str | None,
    question: str,
    top_k: int = 5,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    allowed_source_ids: list[str] | None = None,
    path_prefixes: list[str] | None = None,
    scopes: dict[str, tuple[list[str], list[str]]] | None = None,
) -> list[RetrievedChunk]:
    allowed = set(allowed_source_ids or [])
    prefixes = [Path(p).as_posix().lstrip("/") for p in (path_prefixes or [])]

    roots = {str(k): v.resolve() for k, v in (source_roots or {}).items()}
    if not roots:
        raise QueryError("No source_roots configured for retrieval.")

    meta_by_source: dict[str, dict[str, Any]] = {}
    if source_meta:
        meta_by_source = {str(k): (v if isinstance(v, dict) else {}) for k, v in source_meta.items()}

    sqlite_cfg = index_data.get("sqlite") if isinstance(index_data.get("sqlite"), dict) else {}
    db_rel = str(sqlite_cfg.get("path") or "fts.sqlite")
    table = str(sqlite_cfg.get("table") or "chunks")
    db_path = (index_dir / db_rel).resolve()
    if not db_path.exists():
        raise QueryError(f"SQLite FTS index database not found: {db_path}")

    query_tokens = tokenize(question)
    if not query_tokens:
        raise QueryError("Query produced no usable tokens; try using more specific keywords.")

    def _query_expansions(q: str) -> list[str]:
        ql = q.lower()
        # Heuristic query expansion for file-extension questions.
        # Example: "Where is foo.sys referenced?" tends to be answered well by
        # driver packaging/install manifests (.inf / installer definitions).
        if re.search(r"\b[a-z0-9_-]{2,}\.sys\b", ql):
            return ["driver", "inf"]
        return []

    def _run_query(fts_query: str, *, limit: int) -> list[tuple]:
        conn = sqlite3.connect(str(db_path))
        try:
            params: list[Any] = [fts_query]
            where = [f"{table} MATCH ?"]

            if allowed:
                where.append(f"source_id IN ({','.join(['?'] * len(allowed))})")
                params.extend(sorted(allowed))

            if prefixes:
                like_parts = []
                for p in prefixes:
                    like_parts.append("path LIKE ?")
                    params.append(f"{p}%")
                where.append("(" + " OR ".join(like_parts) + ")")

            params.append(int(max(1, limit)))
            sql = (
                f"SELECT chunk_id, source_id, path, start_line, end_line, file_sha256, chunk_sha256, bm25({table}) as bm25 "
                f"FROM {table} WHERE {' AND '.join(where)} ORDER BY bm25 ASC LIMIT ?"
            )
            cur = conn.execute(sql, params)
            return list(cur.fetchall())
        finally:
            conn.close()

    # Try an AND-like query first, then fall back to OR for recall. Apply a
    # small amount of query rewriting to improve precision on common codebase
    # patterns (e.g., "*.sys" driver references).
    results: list[tuple] = []
    extra_terms = _query_expansions(question)
    token_sets: list[list[str]] = []
    if extra_terms:
        token_sets.append(query_tokens + extra_terms)
    token_sets.append(query_tokens)

    queries: list[str] = []
    for toks in token_sets:
        deduped: list[str] = []
        seen: set[str] = set()
        for t in toks:
            if t in seen:
                continue
            seen.add(t)
            deduped.append(t)
        if not deduped:
            continue
        queries.append(" ".join(deduped))
        if len(deduped) > 1:
            queries.append(" OR ".join(deduped))

    for q in queries:
        results = _run_query(q, limit=max(20, top_k * 12))
        if results:
            break

    chunks: list[RetrievedChunk] = []
    seen_files: set[tuple[str, str]] = set()
    for chunk_id, source_id, rel_path, start_line, end_line, _file_sha, chunk_sha, bm25_score in results:
        if len(chunks) >= top_k:
            break

        doc_source_id = str(source_id or "")
        if allowed and doc_source_id not in allowed:
            continue

        rel_path_s = str(rel_path or "")
        if prefixes and not any(rel_path_s.startswith(p) for p in prefixes):
            continue
        file_key = (doc_source_id, rel_path_s)
        if file_key in seen_files:
            continue

        inc = include or ["**/*"]
        exc = exclude or []
        if scopes and doc_source_id in scopes:
            inc, exc = scopes[doc_source_id]

        if inc is not None or exc is not None:
            if not within_scope(rel_path_s, inc or ["**/*"], exc or []):
                continue

        root = roots.get(doc_source_id)
        if root is None:
            continue

        m = meta_by_source.get(doc_source_id) or {}
        source_type = str(m.get("source_type") or "filesystem")
        revision = m.get("revision") or {}

        try:
            abs_path = resolve_under_root(root, rel_path_s)
        except ValueError:
            continue

        text = None
        if source_type == "git":
            commit = str(revision.get("commit") or "").strip()
            if commit:
                text = _git_show_text(root, commit=commit, rel_path=rel_path_s)

        if text is None:
            if not abs_path.exists():
                continue
            try:
                text = read_text_file(abs_path)
            except Exception:
                continue

        lines = text.splitlines(keepends=True)
        try:
            ls = max(1, int(start_line or 1))
            le = max(ls, int(end_line or ls))
        except Exception:
            ls, le = 1, 1
        if le > len(lines):
            continue

        snippet = "".join(lines[ls - 1 : le])
        chunk_hash = str(chunk_sha or sha256_bytes(snippet.encode("utf-8")))

        # Convert bm25 to a "higher is better" score for consistency with other retrievers.
        try:
            score = -float(bm25_score)
        except Exception:
            score = 0.0

        citation = Citation(
            source_id=doc_source_id,
            source_type=source_type,
            uri=str(m.get("uri") or ""),
            revision=revision,
            artifact_path=rel_path_s,
            chunk_id=str(chunk_id or ""),
            retrieved_at=rfc3339_now(),
            loc={"start_line": ls, "end_line": le},
            line_start=ls,
            line_end=le,
            chunk_hash=chunk_hash,
            classification=classification,
            license=m.get("license"),
        )
        chunks.append(
            RetrievedChunk(
                path=rel_path_s,
                line_start=ls,
                line_end=le,
                snippet=snippet,
                score=score,
                citation=citation,
            )
        )
        seen_files.add(file_key)

    return chunks


def retrieve_vector(
    *,
    index_dir: Path,
    index_data: dict,
    source_roots: dict[str, Path] | None = None,
    source_meta: dict[str, dict[str, Any]] | None = None,
    classification: str | None,
    question: str,
    top_k: int = 5,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    allowed_source_ids: list[str] | None = None,
    path_prefixes: list[str] | None = None,
    scopes: dict[str, tuple[list[str], list[str]]] | None = None,
    query_vector: Any | None = None,
) -> list[RetrievedChunk]:
    allowed = set(allowed_source_ids or [])
    prefixes = [Path(p).as_posix().lstrip("/") for p in (path_prefixes or [])]

    roots = {str(k): v.resolve() for k, v in (source_roots or {}).items()}
    if not roots:
        raise QueryError("No source_roots configured for retrieval.")

    cfg = index_data.get("config") if isinstance(index_data.get("config"), dict) else {}
    embedding_cfg = cfg.get("embedding") if isinstance(cfg.get("embedding"), dict) else {}
    vector_cfg = cfg.get("vector") if isinstance(cfg.get("vector"), dict) else {}

    try:
        dims = int(embedding_cfg.get("dimensions") or 0)
    except Exception:
        dims = 0
    if dims <= 0:
        raise QueryError("Vector index missing config.embedding.dimensions.")

    metric = str(vector_cfg.get("metric") or "cosine").strip().lower()
    if metric not in ("cosine", "dot"):
        raise QueryError(f"Unsupported vector.metric: {metric!r}")

    vectors_rel = str(vector_cfg.get("vectors_path") or "vectors.jsonl")
    vectors_path = (index_dir / vectors_rel).resolve()
    if not vectors_path.exists():
        raise QueryError(f"Vector payload not found: {vectors_path}")

    normalize_query = metric == "cosine"
    if query_vector is not None:
        try:
            qvec = coerce_query_vector(query_vector, dims=dims, normalize=normalize_query)
        except Exception as e:
            raise QueryError(f"Invalid query_vector: {e}") from e
    else:
        model = str(embedding_cfg.get("model") or "hash-embedding-v1").strip()
        provider = str(embedding_cfg.get("provider") or "local").strip().lower()
        if model != "hash-embedding-v1" or provider not in ("local", "poc", "hash", "hashing"):
            raise QueryError(
                "Vector index requires caller-provided query_vector because this runtime "
                "does not have an embedder compatible with config.embedding."
            )

        params = embedding_cfg.get("params") if isinstance(embedding_cfg.get("params"), dict) else {}
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

        qvec = hash_embed(
            question,
            dims=dims,
            salt=salt,
            include_char_ngrams=include_char_ngrams,
            char_ngram=char_ngram,
            char_ngram_weight=char_ngram_weight,
        )
        if normalize_query and qvec:
            # hash_embed already normalizes; keep defensive for other embedders.
            qvec = coerce_query_vector(qvec, dims=dims, normalize=True)

    if not qvec:
        raise QueryError("Query produced no usable embedding; try using more specific terms.")

    docs = index_data.get("documents") if isinstance(index_data.get("documents"), dict) else {}
    if not docs:
        return []

    meta_by_source: dict[str, dict[str, Any]] = {}
    if source_meta:
        meta_by_source = {
            str(k): (v if isinstance(v, dict) else {}) for k, v in source_meta.items()
        }
    else:
        # Fallback to index data sources if runtime did not provide source_meta.
        for s in index_data.get("sources") or []:
            if not isinstance(s, dict):
                continue
            sid = str(s.get("source_id") or "")
            if not sid:
                continue
            meta_by_source[sid] = {
                "source_type": s.get("source_type") or "filesystem",
                "uri": s.get("uri") or "",
                "revision": s.get("revision") or {},
                "license": s.get("license"),
            }

    scored: list[tuple[float, str]] = []

    vfmt = str(vector_cfg.get("vector_format") or "").strip()
    suffix = vectors_path.suffix.lower()
    is_dense = (vfmt in ("dense-bin-v1", "dense-npy-v1")) or (suffix in (".bin", ".npy"))

    if is_dense:
        encoding = str(vector_cfg.get("encoding") or "row-major").strip().lower()
        if encoding != "row-major":
            raise QueryError(f"Unsupported vector.encoding: {encoding!r}")

        dtype = str(vector_cfg.get("dtype") or "float32").strip().lower()
        endianness = str(vector_cfg.get("endianness") or "little").strip().lower()
        chunk_id_order = str(vector_cfg.get("chunk_id_order") or "chunk_id_lex").strip()

        if chunk_id_order == "chunks_jsonl":
            chunk_ids: list[str] = []
            chunks_path = _descriptor_chunks_path(index_dir) or (index_dir / "chunks.jsonl").resolve()
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
                chunk_ids = []
            if not chunk_ids:
                chunk_ids = sorted([str(k) for k in docs.keys()])
        else:
            chunk_ids = sorted([str(k) for k in docs.keys()])

        try:
            reader = open_dense_vector_reader_from_file(
                vectors_path,
                dims=dims,
                dtype=dtype,
                endianness=endianness,
            )
        except Exception as e:
            raise QueryError(f"Failed to open dense vector payload {vectors_path}: {e}") from e

        with reader as r:
            rows = int(r.rows)
            if rows != len(chunk_ids):
                raise QueryError(
                    f"Vector payload row count mismatch: rows={rows} chunks={len(chunk_ids)} ({vectors_path})"
                )

            for row_idx, doc_id in enumerate(chunk_ids):
                meta = docs.get(doc_id) or {}
                if not isinstance(meta, dict):
                    continue

                doc_source_id = str(meta.get("source_id") or "repo")
                if allowed and doc_source_id not in allowed:
                    continue

                rel_path = str(meta.get("path") or "")
                if not rel_path:
                    continue
                if prefixes and not any(rel_path.startswith(p) for p in prefixes):
                    continue

                inc = include or ["**/*"]
                exc = exclude or []
                if scopes and doc_source_id in scopes:
                    inc, exc = scopes[doc_source_id]
                if inc is not None or exc is not None:
                    if not within_scope(rel_path, inc or ["**/*"], exc or []):
                        continue

                score = float(r.dot_sparse(int(row_idx), qvec))
                if score <= 0.0:
                    continue
                scored.append((score, str(doc_id)))
    else:
        vectors_by_id = read_vectors_jsonl(
            vectors_path,
            dims=dims,
            normalize=(metric == "cosine"),
        )

        for doc_id, meta in docs.items():
            if not isinstance(meta, dict):
                continue

            doc_source_id = str(meta.get("source_id") or "repo")
            if allowed and doc_source_id not in allowed:
                continue

            rel_path = str(meta.get("path") or "")
            if not rel_path:
                continue
            if prefixes and not any(rel_path.startswith(p) for p in prefixes):
                continue

            inc = include or ["**/*"]
            exc = exclude or []
            if scopes and doc_source_id in scopes:
                inc, exc = scopes[doc_source_id]
            if inc is not None or exc is not None:
                if not within_scope(rel_path, inc or ["**/*"], exc or []):
                    continue

            dvec = vectors_by_id.get(doc_id)
            if not dvec:
                continue

            score = float(sparse_dot(qvec, dvec))
            if score <= 0.0:
                continue
            scored.append((score, str(doc_id)))

    scored.sort(key=lambda x: (-x[0], x[1]))

    chunks: list[RetrievedChunk] = []
    for score, doc_id in scored:
        if len(chunks) >= top_k:
            break

        doc_meta = docs.get(doc_id) or {}
        if not isinstance(doc_meta, dict):
            continue

        doc_source_id = str(doc_meta.get("source_id") or "repo")
        if allowed and doc_source_id not in allowed:
            continue

        rel_path = str(doc_meta.get("path") or "")
        if not rel_path:
            continue

        root = roots.get(doc_source_id)
        if root is None:
            continue

        m = meta_by_source.get(doc_source_id) or {}
        source_type = str(m.get("source_type") or "filesystem")
        revision = m.get("revision") or {}

        try:
            abs_path = resolve_under_root(root, rel_path)
        except ValueError:
            continue

        text = None
        if source_type == "git":
            commit = str(revision.get("commit") or "").strip()
            if commit:
                text = _git_show_text(root, commit=commit, rel_path=rel_path)

        if text is None:
            if not abs_path.exists():
                continue
            try:
                text = read_text_file(abs_path)
            except Exception:
                continue

        lines = text.splitlines(keepends=True)

        start_line = doc_meta.get("start_line")
        end_line = doc_meta.get("end_line")
        try:
            ls = max(1, int(start_line or 1))
            le = max(ls, int(end_line or ls))
        except Exception:
            ls, le = 1, 1
        if le > len(lines):
            le = len(lines)
        snippet = "".join(lines[ls - 1 : le])

        chunk_hash = (
            doc_meta.get("chunk_sha256")
            or doc_meta.get("sha256")
            or doc_meta.get("file_sha256")
            or sha256_bytes(snippet.encode("utf-8"))
        )

        citation = Citation(
            source_id=doc_source_id,
            source_type=source_type,
            uri=str(m.get("uri") or ""),
            revision=revision,
            artifact_path=rel_path,
            chunk_id=str(doc_id),
            retrieved_at=rfc3339_now(),
            loc={"start_line": ls, "end_line": le},
            line_start=ls,
            line_end=le,
            chunk_hash=chunk_hash,
            classification=classification,
            license=m.get("license"),
        )
        chunks.append(
            RetrievedChunk(
                path=rel_path,
                line_start=ls,
                line_end=le,
                snippet=snippet,
                score=float(score),
                citation=citation,
            )
        )

    return chunks
