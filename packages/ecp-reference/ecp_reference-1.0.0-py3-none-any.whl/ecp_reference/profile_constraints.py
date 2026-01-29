from __future__ import annotations

import json
import re
from pathlib import Path

from .skill_loader import SkillBundle
from .utils import resolve_under_root

# Normative-ish profile constraints (v0.3 direction).
# These are enforced only by `ecpctl validate --strict`.

_REVISION_REQUIRED_KEYS_BY_SOURCE_TYPE: dict[str, tuple[str, ...]] = {
    "git": ("commit", "timestamp"),
    "filesystem": ("hash", "timestamp"),
    "web": ("retrieved_at",),
}

_GIT_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")

# Constraint table: keep this deliberately small and testable by static validation.
PROFILE_REQUIREMENTS: dict[str, dict[str, object]] = {
    "conformance": {
        "required_source_types_any": ("filesystem", "artifact"),
        "required_artifacts": ("indexes",),
        "required_index_files": ("index_data.json", "chunks.jsonl"),
        "require_chunk_revision_fields": True,
        "enforce_remote_llm_allowlist": True,
    },
    "codebase": {
        "required_source_types_any": ("git", "filesystem"),
        "required_artifacts": ("indexes",),
        "required_index_files": ("index_data.json", "chunks.jsonl"),
        "require_chunk_revision_fields": True,
        "enforce_remote_llm_allowlist": True,
    },
    "docs": {
        "required_source_types_any": ("filesystem", "git", "web"),
        "required_artifacts": ("summaries",),
        "enforce_remote_llm_allowlist": True,
    },
    "web": {
        "required_source_types_any": ("web",),
        "required_artifacts": ("snapshots", "indexes"),
        "required_index_files": ("index_data.json", "chunks.jsonl"),
        "require_chunk_revision_fields": True,
        "enforce_remote_llm_allowlist": True,
    },
    "mixed": {
        "min_sources": 2,
        "required_artifacts": ("indexes", "summaries"),
        "required_index_files": ("index_data.json", "chunks.jsonl"),
        "require_chunk_revision_fields": True,
        "enforce_remote_llm_allowlist": True,
    },
}


def normalize_profile(profile: object) -> str | None:
    if isinstance(profile, str):
        p = profile.strip().lower()
        return p or None
    if isinstance(profile, dict):
        for k in ("id", "name", "profile"):
            v = profile.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip().lower()
    return None


def validate_profile_constraints(
    bundle: SkillBundle,
    *,
    max_chunk_records: int = 200,
) -> tuple[str | None, list[str], list[str], list[str]]:
    """Return (profile_id, profile_violations, schema_violations, warnings)."""
    profile_id = normalize_profile(bundle.manifest.get("profile"))
    if not profile_id:
        return None, [], [], []

    req = PROFILE_REQUIREMENTS.get(profile_id)
    if req is None:
        return profile_id, [], [], [f"unknown profile '{profile_id}'; no strict profile constraints enforced"]

    profile_violations: list[str] = []
    schema_violations: list[str] = []
    warnings: list[str] = []

    sources = bundle.manifest.get("sources") or []
    if not isinstance(sources, list):
        sources = []

    source_types: list[str] = []
    source_type_by_id: dict[str, str] = {}
    for s in sources:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("source_id") or "").strip()
        st = str(s.get("type") or "").strip()
        if st:
            source_types.append(st)
        if sid and st:
            source_type_by_id[sid] = st

    # Source-level provenance fields.
    for i, s in enumerate(sources):
        if not isinstance(s, dict):
            continue
        st = str(s.get("type") or "").strip()
        if not st:
            continue
        rev = s.get("revision") if isinstance(s.get("revision"), dict) else {}
        required_keys = _REVISION_REQUIRED_KEYS_BY_SOURCE_TYPE.get(st)
        if required_keys:
            for k in required_keys:
                if k not in rev or rev.get(k) in (None, "", []):
                    profile_violations.append(
                        f"profile '{profile_id}' requires sources[{i}].revision.{k} for {st} sources"
                    )

        # Conformance packs are intended to be self-contained and runnable offline.
        if profile_id == "conformance":
            if st not in ("filesystem", "artifact"):
                profile_violations.append(
                    f"profile '{profile_id}' requires sources[{i}].type to be 'filesystem' or 'artifact' (got {st!r})"
                )

            uri = s.get("uri")
            uri_s = str(uri or "").strip()
            if not uri_s:
                profile_violations.append(f"profile '{profile_id}' requires sources[{i}].uri to be set")
            else:
                if "://" in uri_s or uri_s.lower().startswith("file:"):
                    profile_violations.append(
                        f"profile '{profile_id}' requires sources[{i}].uri to be a relative path under the skill root (no URI scheme): {uri_s!r}"
                    )
                if any(part == ".." for part in Path(uri_s).parts):
                    profile_violations.append(
                        f"profile '{profile_id}' requires sources[{i}].uri to not contain '..' path segments: {uri_s!r}"
                    )
                else:
                    try:
                        resolved = resolve_under_root(bundle.skill_root, uri_s)
                    except Exception as e:
                        profile_violations.append(
                            f"profile '{profile_id}' requires sources[{i}].uri to resolve under the skill root: {e}"
                        )
                    else:
                        if not resolved.exists():
                            profile_violations.append(
                                f"profile '{profile_id}' requires sources[{i}].uri to exist under the skill root: {resolved}"
                            )

        # Workstream B1: codebase packs must be commit-pinned (no symbolic refs like HEAD).
        if profile_id == "codebase" and st == "git":
            commit = str(rev.get("commit") or "").strip()
            if not commit:
                profile_violations.append(
                    f"profile '{profile_id}' requires sources[{i}].revision.commit to be set for git sources"
                )
            elif commit.lower() == "head":
                profile_violations.append(
                    f"profile '{profile_id}' requires sources[{i}].revision.commit to be a concrete commit hash (not 'HEAD')"
                )
            elif not _GIT_COMMIT_RE.match(commit):
                profile_violations.append(
                    f"profile '{profile_id}' requires sources[{i}].revision.commit to be a git commit hash (7-40 hex chars); got {commit!r}"
                )

    min_sources = int(req.get("min_sources") or 0)
    if min_sources and len(source_types) < min_sources:
        profile_violations.append(f"profile '{profile_id}' requires at least {min_sources} sources (got {len(source_types)})")

    required_source_types_any = req.get("required_source_types_any")
    if isinstance(required_source_types_any, (tuple, list)):
        required = {str(t) for t in required_source_types_any if t is not None}
        if required and not any(t in required for t in source_types):
            profile_violations.append(
                f"profile '{profile_id}' requires at least one sources[].type in {sorted(required)} (got {sorted(set(source_types))})"
            )

    ctx = bundle.manifest.get("context") or {}
    artifacts = (ctx.get("artifacts") or {}) if isinstance(ctx, dict) else {}
    indexes = artifacts.get("indexes") or []
    summaries = artifacts.get("summaries") or []
    snapshots = artifacts.get("snapshots") or []

    required_artifacts = req.get("required_artifacts")
    if isinstance(required_artifacts, (tuple, list)):
        required = {str(x) for x in required_artifacts if x is not None}
        if "indexes" in required and not (isinstance(indexes, list) and len(indexes) > 0):
            profile_violations.append(f"profile '{profile_id}' requires at least one context.artifacts.indexes[] entry")
        if "summaries" in required and not (isinstance(summaries, list) and len(summaries) > 0):
            profile_violations.append(f"profile '{profile_id}' requires at least one context.artifacts.summaries[] entry")
        if "snapshots" in required and not (isinstance(snapshots, list) and len(snapshots) > 0):
            profile_violations.append(f"profile '{profile_id}' requires at least one context.artifacts.snapshots[] entry")

    security = bundle.manifest.get("security") or {}
    if isinstance(security, dict) and bool(req.get("enforce_remote_llm_allowlist", False)):
        allow_remote_llm = bool(security.get("allow_remote_llm", False))
        if profile_id == "conformance" and allow_remote_llm:
            profile_violations.append("security.allow_remote_llm: must be false for profile 'conformance'")
        if allow_remote_llm:
            providers = security.get("allowed_remote_llm_providers")
            if not isinstance(providers, list) or not any(str(p or "").strip() for p in providers):
                profile_violations.append(
                    "security.allowed_remote_llm_providers: required and must be non-empty when security.allow_remote_llm=true"
                )
        if bool(security.get("contains_secrets", False)) and allow_remote_llm:
            profile_violations.append(
                "security.allow_remote_llm: must be false when security.contains_secrets=true"
            )

    required_index_files = req.get("required_index_files")
    require_chunk_revision_fields = bool(req.get("require_chunk_revision_fields", False))
    if (
        isinstance(required_index_files, (tuple, list))
        and isinstance(indexes, list)
        and (required_index_files or require_chunk_revision_fields)
    ):
        required_files = {str(x) for x in required_index_files if x is not None}
        max_chunk_records = max(0, int(max_chunk_records))
        max_chunk_records = min(max_chunk_records, 10_000)

        for i, idx in enumerate(indexes):
            if not isinstance(idx, dict):
                continue
            idx_id = str(idx.get("id") or f"#{i}")

            path_rel = idx.get("path")
            desc_rel = idx.get("descriptor")
            if not path_rel or not desc_rel:
                continue

            try:
                idx_dir = resolve_under_root(bundle.skill_root, str(path_rel))
            except Exception as e:
                profile_violations.append(f"context.artifacts.indexes[{i}].path: {e}")
                continue

            try:
                desc_path = resolve_under_root(bundle.skill_root, str(desc_rel))
            except Exception as e:
                profile_violations.append(f"context.artifacts.indexes[{i}].descriptor: {e}")
                continue

            if not idx_dir.exists() or not idx_dir.is_dir():
                profile_violations.append(f"indexes[{idx_id}]: missing index directory: {idx_dir}")
                continue

            if not desc_path.exists() or not desc_path.is_file():
                profile_violations.append(f"indexes[{idx_id}]: missing index descriptor file: {desc_path}")
                continue

            try:
                desc = json.loads(desc_path.read_text(encoding="utf-8"))
            except Exception as e:
                schema_violations.append(f"indexes[{idx_id}].index.json: failed to parse JSON: {e}")
                continue
            if not isinstance(desc, dict):
                schema_violations.append(f"indexes[{idx_id}].index.json: expected object, got {type(desc).__name__}")
                continue

            prov = desc.get("provenance") if isinstance(desc.get("provenance"), dict) else {}
            index_data_rel = prov.get("index_data_path") or "index_data.json"
            chunks_rel = prov.get("chunks_path") or "chunks.jsonl"

            index_data_path = None
            chunks_path = None
            try:
                index_data_path = resolve_under_root(idx_dir, str(index_data_rel))
            except Exception as e:
                profile_violations.append(f"indexes[{idx_id}].index.json.provenance.index_data_path: {e}")
            try:
                chunks_path = resolve_under_root(idx_dir, str(chunks_rel))
            except Exception as e:
                profile_violations.append(f"indexes[{idx_id}].index.json.provenance.chunks_path: {e}")

            if "index_data.json" in required_files and index_data_path is not None and not index_data_path.exists():
                profile_violations.append(f"indexes[{idx_id}]: missing required artifact: {index_data_path}")
            if "chunks.jsonl" in required_files and chunks_path is not None and not chunks_path.exists():
                profile_violations.append(f"indexes[{idx_id}]: missing required artifact: {chunks_path}")

            if require_chunk_revision_fields and chunks_path is not None and chunks_path.exists() and max_chunk_records:
                checked = 0
                missing_examples = 0
                try:
                    with chunks_path.open("r", encoding="utf-8") as f:
                        for line in f:
                            if checked >= max_chunk_records:
                                break
                            s = line.strip()
                            if not s:
                                continue
                            checked += 1
                            try:
                                rec = json.loads(s)
                            except Exception as e:
                                schema_violations.append(
                                    f"indexes[{idx_id}].chunks.jsonl: line {checked}: invalid JSON: {e}"
                                )
                                break
                            if not isinstance(rec, dict):
                                schema_violations.append(
                                    f"indexes[{idx_id}].chunks.jsonl: line {checked}: expected object, got {type(rec).__name__}"
                                )
                                break

                            sid = str(rec.get("source_id") or "").strip()
                            st = source_type_by_id.get(sid)
                            if not st:
                                continue
                            required_keys = _REVISION_REQUIRED_KEYS_BY_SOURCE_TYPE.get(st)
                            if not required_keys:
                                continue
                            rev = rec.get("revision") if isinstance(rec.get("revision"), dict) else {}
                            for k in required_keys:
                                if k not in rev or rev.get(k) in (None, "", []):
                                    if missing_examples < 20:
                                        profile_violations.append(
                                            f"indexes[{idx_id}].chunks.jsonl: line {checked}: missing revision.{k} for {st} source_id={sid}"
                                        )
                                        missing_examples += 1
                                    break
                except Exception as e:
                    schema_violations.append(f"indexes[{idx_id}].chunks.jsonl: failed to read: {e}")

    return profile_id, profile_violations, schema_violations, warnings
