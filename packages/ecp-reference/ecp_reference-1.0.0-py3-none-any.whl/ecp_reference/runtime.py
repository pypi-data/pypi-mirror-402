from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import QueryError
from .indexer import load_keyword_index, load_vector_index
from .maintenance import parse_file_uri
from .retriever import RetrievedChunk, retrieve, retrieve_sqlite_fts, retrieve_vector
from .sqlite_fts import load_sqlite_fts_index
from .skill_loader import SkillBundle, load_skill_bundle
from .synthesizer import synthesize_answer
from .utils import (
    Citation,
    append_jsonl,
    chunk_lines_around_match,
    read_text_file,
    rfc3339_now,
    resolve_under_root,
    sha256_bytes,
    tokenize,
)

def _get_primary_source(manifest: dict) -> dict:
    sources = manifest.get("sources") or []
    if not sources:
        raise QueryError("No sources configured in EXPERT.yaml.")
    return sources[0]


def _get_sources(manifest: dict) -> list[dict]:
    sources = manifest.get("sources") or []
    if not sources:
        raise QueryError("No sources configured in EXPERT.yaml.")
    return [s for s in sources if isinstance(s, dict)]

def _get_artifacts(manifest: dict) -> dict:
    return (manifest.get("context") or {}).get("artifacts") or {}

def _get_indexes(manifest: dict) -> list[dict]:
    indexes = (_get_artifacts(manifest).get("indexes") or [])
    return [i for i in indexes if isinstance(i, dict)]


def _index_backend(index_entry: dict) -> str:
    raw = (
        index_entry.get("backend")
        or index_entry.get("implementation")
        or index_entry.get("index_backend")
        or ""
    )
    backend = str(raw).strip().lower()
    if backend:
        return backend

    idx_type = str(index_entry.get("type") or "").strip().lower()
    if idx_type == "vector":
        return "vector"

    return ""


def _chunk_key(ch: RetrievedChunk) -> str:
    try:
        cid = getattr(getattr(ch, "citation", None), "chunk_id", None)
    except Exception:
        cid = None
    if isinstance(cid, str) and cid.strip():
        return cid.strip()
    sid = ""
    try:
        sid = str(getattr(getattr(ch, "citation", None), "source_id", "") or "")
    except Exception:
        sid = ""
    return f"{sid}::{ch.path}#L{int(ch.line_start)}-L{int(ch.line_end)}"


def _rrf_fuse(results: list[list[RetrievedChunk]], *, top_k: int, rrf_k: int = 60) -> list[RetrievedChunk]:
    """Reciprocal Rank Fusion over multiple ranked lists."""
    scores: dict[str, float] = {}
    best: dict[str, RetrievedChunk] = {}

    for lst in results:
        for rank, ch in enumerate(lst, start=1):
            key = _chunk_key(ch)
            scores[key] = scores.get(key, 0.0) + (1.0 / float(rrf_k + rank))
            best.setdefault(key, ch)

    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    out: list[RetrievedChunk] = []
    for key, _ in ordered:
        out.append(best[key])
        if len(out) >= int(max(1, top_k)):
            break
    return out

def _get_summaries(manifest: dict) -> list[dict]:
    summaries = (_get_artifacts(manifest).get("summaries") or [])
    return [s for s in summaries if isinstance(s, dict)]

ARTIFACT_SOURCE_ID = "ecp_artifacts"

def _artifact_revision_for_summaries(skill_root: Path, summaries: list[dict]) -> dict:
    """Compute a stable-ish revision for summary artifacts under the skill root."""
    files: list[dict[str, str]] = []
    for s in summaries:
        rel = s.get("path")
        if not rel:
            continue
        rel_posix = Path(str(rel)).as_posix()
        try:
            p = resolve_under_root(skill_root, str(rel))
        except ValueError:
            continue
        if not p.exists() or not p.is_file():
            continue
        try:
            h = sha256_bytes(p.read_bytes())
        except Exception:
            continue
        files.append({"path": rel_posix, "sha256": h})

    files.sort(key=lambda x: x["path"])
    blob = json.dumps({"files": files}, sort_keys=True).encode("utf-8")
    return {"hash": sha256_bytes(blob), "timestamp": rfc3339_now()}

def _retrieve_from_summaries(
    skill_root: Path,
    summaries: list[dict],
    *,
    question: str,
    source_meta: dict[str, dict[str, Any]],
    artifact_source_id: str,
    default_source_id: str,
    classification: str | None,
    top_k: int,
    allowed_source_ids: list[str] | None = None,
    path_prefixes: list[str] | None = None,
    snippet_window: int = 3,
) -> list[RetrievedChunk]:
    query_tokens = tokenize(question)
    if not query_tokens:
        raise QueryError("Query produced no usable tokens; try using more specific keywords.")

    allowed = set(allowed_source_ids or [])
    prefixes = [Path(p).as_posix().lstrip("/") for p in (path_prefixes or [])]  

    # Summary artifacts live under the skill root; treat them as `artifact` citations.
    # If the caller filters to non-artifact sources, skip summaries and allow fallback.
    if allowed and artifact_source_id not in allowed:
        return []

    qset = set(query_tokens)
    scored: list[tuple[float, dict]] = []
    for s in summaries:
        rel = s.get("path")
        if not rel:
            continue

        rel_posix = Path(str(rel)).as_posix()
        if prefixes and not any(rel_posix.startswith(p) for p in prefixes):
            continue

        sid = str(artifact_source_id or (s.get("source_id") or default_source_id))
        if allowed and sid not in allowed:
            continue
        try:
            summary_path = resolve_under_root(skill_root, str(rel))
        except ValueError:
            continue
        if not summary_path.exists():
            continue
        try:
            text = read_text_file(summary_path)
        except Exception:
            continue
        toks = set(tokenize(text))
        score = float(sum(1 for t in qset if t in toks))
        if score <= 0:
            continue
        scored.append((score, s))

    scored.sort(key=lambda x: x[0], reverse=True)

    chunks: list[RetrievedChunk] = []
    for score, s in scored[:top_k]:
        rel = str(s.get("path") or "")
        if not rel:
            continue
        try:
            summary_path = resolve_under_root(skill_root, rel)
        except ValueError:
            continue
        try:
            lines = read_text_file(summary_path).splitlines(keepends=True)
        except Exception:
            continue

        match_idx = None
        for i, line in enumerate(lines):
            if set(tokenize(line)) & qset:
                match_idx = i
                break
        if match_idx is None:
            match_idx = 0

        line_start, line_end, snippet = chunk_lines_around_match(lines, match_idx, window=snippet_window)
        rel_posix = Path(rel).as_posix()

        sid = str(artifact_source_id or (s.get("source_id") or default_source_id))
        meta = source_meta.get(sid) or {}
        stype = str(meta.get("source_type") or "filesystem")
        uri = str(meta.get("uri") or "")
        revision = meta.get("revision") or {}
        license = meta.get("license")

        citation = Citation(
            source_id=sid,
            source_type=stype,
            uri=uri,
            revision=revision,
            artifact_path=rel_posix,
            chunk_id=f"summary:{s.get('id') or rel_posix}",
            retrieved_at=rfc3339_now(),
            loc={"start_line": line_start, "end_line": line_end},
            line_start=line_start,
            line_end=line_end,
            chunk_hash=sha256_bytes(snippet.encode("utf-8")),
            classification=classification,
            license=license,
        )
        chunks.append(
            RetrievedChunk(
                path=rel_posix,
                line_start=line_start,
                line_end=line_end,
                snippet=snippet,
                score=score,
                citation=citation,
            )
        )

    return chunks

def _append_qa_log(
    skill_root: Path,
    summaries: list[dict],
    *,
    question: str,
    answer: str,
    citations: list[dict],
    as_of: dict,
    contains_secrets: bool,
) -> None:
    if contains_secrets:
        return

    target: dict | None = None
    for s in summaries:
        if isinstance(s, dict) and s.get("id") == "qa-log":
            target = s
            break
    if target is None:
        for s in summaries:
            if isinstance(s, dict) and s.get("type") == "topic":
                target = s
                break
    if not target:
        return

    rel = target.get("path")
    if not rel:
        return
    try:
        path = resolve_under_root(skill_root, str(rel))
    except ValueError:
        return

    def _revision_ref(rev: Any) -> str:
        if not isinstance(rev, dict):
            return ""
        for k in ("commit", "hash", "etag", "retrieved_at", "timestamp"):
            v = rev.get(k)
            if v:
                return f"{k}={v}"
        return ""

    ts = rfc3339_now()
    lines: list[str] = []
    lines.append(f"## {ts}")
    lines.append("")
    lines.append(f"Q: {question}")
    lines.append("")
    lines.append("A:")
    lines.append("")
    lines.append(answer.rstrip())
    lines.append("")

    sources = as_of.get("sources") if isinstance(as_of, dict) else None
    if isinstance(sources, list) and sources:
        lines.append("As of:")
        for entry in sources:
            if not isinstance(entry, dict):
                continue
            sid = entry.get("source_id")
            ref = _revision_ref(entry.get("revision"))
            if sid and ref:
                lines.append(f"- {sid} ({ref})")
            elif sid:
                lines.append(f"- {sid}")
        lines.append("")

    cite_lines = []
    for c in citations:
        if not isinstance(c, dict):
            continue
        sid = c.get("source_id")
        ap = c.get("artifact_path")
        ls = c.get("line_start")
        le = c.get("line_end")
        if sid and ap and ls and le:
            cite_lines.append(f"- {sid}:{ap}#L{ls}-L{le}")
        elif sid and ap:
            cite_lines.append(f"- {sid}:{ap}")
        elif ap:
            cite_lines.append(f"- {ap}")

    if cite_lines:
        lines.append("Citations:")
        lines.extend(cite_lines)
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(lines).rstrip() + "\n")

def query_expert(
    skill_root: Path,
    *,
    question: str,
    mode: str = "ephemeral",
    top_k: int = 5,
    source_ids: list[str] | None = None,
    path_prefixes: list[str] | None = None,
    llm: str | None = None,
    llm_model: str | None = None,
    llm_timeout_seconds: int = 60,
    query_vector: Any | None = None,
) -> dict:
    bundle = load_skill_bundle(skill_root)
    manifest = bundle.manifest

    sources = _get_sources(manifest)

    security = manifest.get("security") or {}
    classification = security.get("classification")
    license = security.get("license")
    contains_secrets = bool(security.get("contains_secrets", False))
    allow_remote_llm = bool(security.get("allow_remote_llm", False))
    allowed_remote_llm_providers = security.get("allowed_remote_llm_providers") or []
    if not isinstance(allowed_remote_llm_providers, list):
        allowed_remote_llm_providers = [str(allowed_remote_llm_providers)]

    source_roots: dict[str, Path] = {}
    source_meta: dict[str, dict[str, Any]] = {}
    scopes: dict[str, tuple[list[str], list[str]]] = {}
    manifest_source_ids: list[str] = []

    for i, src in enumerate(sources):
        sid = str(src.get("source_id") or f"source{i}")
        stype = str(src.get("type") or "filesystem")
        uri = src.get("uri")
        if not uri:
            raise QueryError(f"Source '{sid}' missing uri.")
        root = parse_file_uri(str(uri), base_dir=bundle.skill_root)

        scope = src.get("scope") or {}
        include = scope.get("include") or ["**/*"]
        exclude = scope.get("exclude") or []

        src_license = src.get("license") or license
        src_classification = src.get("classification") or classification

        source_roots[sid] = root
        manifest_source_ids.append(sid)
        source_meta[sid] = {
            "source_type": stype,
            "uri": str(uri),
            "revision": src.get("revision") or {},
            "license": src_license,
            "classification": src_classification,
        }
        scopes[sid] = (list(include), list(exclude))

    indexes = _get_indexes(manifest)
    summaries = _get_summaries(manifest)

    # Provide a conventional `artifact` source for summary artifacts under the skill root.
    if summaries:
        source_roots[ARTIFACT_SOURCE_ID] = bundle.skill_root
        source_meta[ARTIFACT_SOURCE_ID] = {
            "source_type": "artifact",
            "uri": ".",
            "revision": _artifact_revision_for_summaries(bundle.skill_root, summaries),
            "license": license,
            "classification": classification,
        }
        scopes[ARTIFACT_SOURCE_ID] = (["expert/context/**"], [])

    mode = str(mode or "ephemeral")
    primary = sources[0] if sources else {}
    default_source_id = (
        str(primary.get("source_id") or "repo") if isinstance(primary, dict) else "repo"
    )

    def _retrieve_from_index() -> list[RetrievedChunk]:
        per_index: list[list[RetrievedChunk]] = []
        per_index_top_k = max(8, int(top_k))
        errors: list[str] = []
        successful = 0

        for idx_entry in indexes:
            idx_id = str(idx_entry.get("id") or "")
            try:
                idx_path = idx_entry.get("path")
                if not idx_path:
                    raise QueryError("Index missing path.")
                backend = _index_backend(idx_entry)
                try:
                    index_dir = resolve_under_root(bundle.skill_root, str(idx_path))
                except ValueError as e:
                    raise QueryError(str(e)) from e

                if backend == "sqlite-fts":
                    index_data = load_sqlite_fts_index(index_dir)
                    chunks = retrieve_sqlite_fts(
                        index_dir=index_dir,
                        index_data=index_data,
                        source_roots=source_roots,
                        source_meta=source_meta,
                        classification=classification,
                        question=question,
                        top_k=per_index_top_k,
                        allowed_source_ids=source_ids,
                        path_prefixes=path_prefixes,
                        scopes=scopes,
                    )
                elif backend == "vector":
                    index_data = load_vector_index(index_dir)
                    chunks = retrieve_vector(
                        index_dir=index_dir,
                        index_data=index_data,
                        source_roots=source_roots,
                        source_meta=source_meta,
                        classification=classification,
                        question=question,
                        top_k=per_index_top_k,
                        allowed_source_ids=source_ids,
                        path_prefixes=path_prefixes,
                        scopes=scopes,
                        query_vector=query_vector,
                    )
                else:
                    index_data = load_keyword_index(index_dir)
                    chunks = retrieve(
                        index_data=index_data,
                        source_roots=source_roots,
                        source_meta=source_meta,
                        classification=classification,
                        question=question,
                        top_k=per_index_top_k,
                        allowed_source_ids=source_ids,
                        path_prefixes=path_prefixes,
                        scopes=scopes,
                    )

                successful += 1
                if chunks:
                    per_index.append(chunks)
            except Exception as e:
                label = idx_id or "<index>"
                errors.append(f"{label}: {e}")
                continue

        if successful == 0 and errors:
            suffix = "" if len(errors) <= 3 else f"; ... ({len(errors)} total)"
            raise QueryError("All configured indexes failed: " + "; ".join(errors[:3]) + suffix)

        if not per_index:
            return []
        if len(per_index) == 1:
            return per_index[0][: int(max(1, top_k))]

        return _rrf_fuse(per_index, top_k=int(top_k))

    def _retrieve_from_summary_artifacts() -> list[RetrievedChunk]:
        return _retrieve_from_summaries(
            bundle.skill_root,
            summaries,
            question=question,
            source_meta=source_meta,
            artifact_source_id=ARTIFACT_SOURCE_ID,
            default_source_id=default_source_id,
            classification=classification,
            top_k=top_k,
            allowed_source_ids=source_ids,
            path_prefixes=path_prefixes,
        )

    if mode == "summarized":
        if summaries:
            chunks = _retrieve_from_summary_artifacts()
            if not chunks and indexes:
                chunks = _retrieve_from_index()
        elif indexes:
            chunks = _retrieve_from_index()
        else:
            raise QueryError("ECP skill must declare at least one context artifact: indexes[] or summaries[].")
    else:
        if indexes:
            chunks = _retrieve_from_index()
        elif summaries:
            chunks = _retrieve_from_summary_artifacts()
        else:
            raise QueryError("ECP skill must declare at least one context artifact: indexes[] or summaries[].")

    used_source_ids = {
        str(getattr(ch.citation, "source_id", ""))
        for ch in chunks
        if getattr(ch, "citation", None) is not None
    }

    as_of_sources: list[dict[str, Any]] = []
    for sid in manifest_source_ids:
        meta = source_meta.get(sid) or {}
        as_of_sources.append({"source_id": sid, "revision": (meta.get("revision") or {})})

    if summaries and ARTIFACT_SOURCE_ID in used_source_ids:
        meta = source_meta.get(ARTIFACT_SOURCE_ID) or {}
        as_of_sources.append(
            {"source_id": ARTIFACT_SOURCE_ID, "revision": (meta.get("revision") or {})}
        )

    as_of = {"sources": as_of_sources} if as_of_sources else {"timestamp": rfc3339_now()}
    llm_norm = (llm or "").strip().lower()
    if llm_norm in ("", "none"):
        llm_norm = ""
    if llm_norm:
        is_remote_provider = llm_norm not in ("ollama",)
        if is_remote_provider:
            if contains_secrets:
                raise QueryError("Remote LLM synthesis is disabled because security.contains_secrets=true.")
            if not allow_remote_llm:
                raise QueryError(
                    "Remote LLM synthesis is disabled for this pack. "
                    "Set security.allow_remote_llm: true in EXPERT.yaml to override."
                )
            allowed = {str(p).strip().lower() for p in allowed_remote_llm_providers if str(p).strip()}
            if allowed and llm_norm not in allowed:
                raise QueryError(
                    f"Remote LLM provider {llm_norm!r} is not in security.allowed_remote_llm_providers: {sorted(allowed)}"
                )

    answer, synthesis = synthesize_answer(
        question=question,
        chunks=chunks,
        as_of=as_of,
        mode=mode,
        llm=llm_norm,
        llm_model=llm_model,
        llm_timeout_seconds=llm_timeout_seconds,
    )

    citations_raw = [c.to_dict()["citation"] for c in chunks]  # citations only
    citations: list[dict] = []
    seen_citations: set[tuple] = set()
    for c in citations_raw:
        if not isinstance(c, dict):
            continue
        key = (
            c.get("source_id"),
            c.get("artifact_path"),
            c.get("chunk_id"),
            c.get("line_start"),
            c.get("line_end"),
        )
        if key in seen_citations:
            continue
        seen_citations.add(key)
        citations.append(c)
    chunk_dicts = [c.to_dict() for c in chunks]

    out = {
        "mode": mode,
        "question": question,
        "as_of": as_of,
        "answer": answer,
        "synthesis": synthesis,
        "citations": citations,
        "chunks": chunk_dicts,
    }

    # Optional query logging (spec §9).
    logs_root = bundle.skill_root / "expert" / "logs"
    raw_logs_cfg: Any = manifest.get("logs")
    has_logs_cfg = isinstance(raw_logs_cfg, dict)
    logs_cfg: dict[str, Any] = raw_logs_cfg if has_logs_cfg else {}
    logs_enabled = bool(logs_cfg.get("enabled", False)) or (
        (not has_logs_cfg) and logs_root.exists()
    )
    if mode == "persistent":
        _append_qa_log(
            bundle.skill_root,
            summaries,
            question=question,
            answer=answer,
            citations=citations,
            as_of=as_of,
            contains_secrets=contains_secrets,
        )
    if logs_enabled:
        day = rfc3339_now()[:10]
        cited_paths = [
            f"{c.get('source_id')}:{c.get('artifact_path')}"
            for c in citations
            if isinstance(c, dict) and c.get("artifact_path") is not None
        ]
        store_question = (
            (bool(logs_cfg.get("store_question", False)) or mode == "persistent")
            and not contains_secrets
        )
        store_answer = (
            (bool(logs_cfg.get("store_answer", False)) or mode == "persistent")
            and not contains_secrets
        )

        record: dict[str, Any] = {
            "timestamp": rfc3339_now(),
            "operation": "query",
            "mode": mode,
            "synthesis": synthesis,
            "top_k": top_k,
            "question_sha256": sha256_bytes(question.encode("utf-8")),
            "answer_sha256": sha256_bytes(answer.encode("utf-8")),
            "as_of": as_of,
            "citations": cited_paths,
        }
        if store_question:
            record["question"] = question
        if store_answer:
            record["answer"] = answer

        append_jsonl(
            logs_root / "queries" / f"{day}.jsonl",
            record,
        )

    return out

def status(skill_root: Path) -> dict:
    bundle = load_skill_bundle(skill_root)
    manifest = bundle.manifest
    sources = _get_sources(manifest)
    indexes = _get_indexes(manifest)
    summaries = _get_summaries(manifest)

    sources_out: list[dict[str, Any]] = []
    for i, s in enumerate(sources):
        sid = str(s.get("source_id") or f"source{i}")
        sources_out.append(
            {"source_id": sid, "type": s.get("type"), "uri": s.get("uri"), "revision": s.get("revision")}
        )
    return {
        "skill": bundle.skill_frontmatter.get("name"),
        "expert_id": manifest.get("id"),
        "ecp_version": manifest.get("ecp_version"),
        "source": sources_out[0] if sources_out else None,
        "sources": sources_out,
        "index": (
            {"id": indexes[0].get("id"), "path": indexes[0].get("path"), "type": indexes[0].get("type")}
            if indexes
            else None
        ),
        "summaries": [{"id": s.get("id"), "path": s.get("path"), "type": s.get("type")} for s in summaries],
        "policy_path": manifest.get("maintenance", {}).get("policy_path"),
        "eval_suites": [s.suite_id for s in bundle.eval_suites],
    }
