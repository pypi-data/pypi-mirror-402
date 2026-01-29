from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .errors import ECPError
from .maintenance import build_or_refresh
from .mcp_server import run_stdio_mcp_server
from .runtime import query_expert, status
from .profile_constraints import validate_profile_constraints
from .skill_loader import load_skill_bundle, schema_filename_for_version
from .evals import run_eval_suites
from .utils import load_dotenv, write_yaml, read_yaml, resolve_under_root

def _print(obj: object, *, as_json: bool) -> None:
    if as_json:
        sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=True) + "\n")
    else:
        if isinstance(obj, (dict, list)):
            sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=True) + "\n")
        else:
            sys.stdout.write(str(obj) + "\n")

def cmd_validate(args: argparse.Namespace) -> int:
    artifacts_report: dict | None = None
    schemas_report: dict[str, dict[str, str | None]] = {}
    warnings: list[str] = []
    schema_violations: list[str] = []
    strict_violations: list[str] = []
    profile_violations: list[str] = []
    strict = bool(getattr(args, "strict", False))
    with_artifacts = bool(getattr(args, "with_artifacts", False))

    schema_dir = Path(__file__).resolve().parent / "schemas"

    def _schema_meta(filename: str) -> dict[str, str | None]:
        try:
            schema = json.loads((schema_dir / filename).read_text(encoding="utf-8"))
        except Exception:
            return {"file": filename, "id": None}
        return {"file": filename, "id": schema.get("$id")}

    try:
        bundle = load_skill_bundle(Path(args.skill))
    except ECPError as e:
        schema_violations.append(str(e))
        all_errors = list(schema_violations)
        out = {
            "ok": False,
            "skill": None,
            "expert_id": None,
            "ecp_version": None,
            "profile": None,
            "profile_id": None,
            "schemas": schemas_report,
            "eval_suites": [],
            "strict": strict,
            "with_artifacts": with_artifacts,
            "warnings": warnings,
            "schema_violations": schema_violations,
            "strict_violations": strict_violations,
            "profile_violations": profile_violations,
            "errors": all_errors,
            "artifacts": artifacts_report,
        }
        _print(out, as_json=args.json)
        return 2

    try:
        m_fn = schema_filename_for_version(kind="manifest", version=str(bundle.manifest.get("ecp_version") or ""))
        p_fn = schema_filename_for_version(kind="policy", version=str(bundle.policy.get("policy_version") or ""))
        e_fn = schema_filename_for_version(kind="eval", version=str(bundle.manifest.get("ecp_version") or ""))
        schemas_report["expert/EXPERT.yaml"] = _schema_meta(m_fn)
        schemas_report["expert/maintenance/policy.json"] = _schema_meta(p_fn)
        schemas_report["expert/evals/*.yaml"] = _schema_meta(e_fn)
    except Exception:
        # Best-effort: load_skill_bundle already pins/validates the schema versions.
        pass

    _WIN_ABS_RE = re.compile(r"^[A-Za-z]:[\\/]")
    _WIN_DEVICE_PATH_RE = re.compile(r"^\\\\\\\\\\?\\\\[A-Za-z]:\\\\")
    _UNC_RE = re.compile(r"^(\\\\\\\\|//)[^/\\\\]+[/\\\\]")

    def _looks_like_absolute_local_path(s: str) -> bool:
        s = str(s or "")
        if not s:
            return False
        lower = s.lower()
        if lower.startswith("file:"):
            if lower.startswith("file:./") or lower.startswith("file:../"):
                return False
            return lower.startswith("file:/") or lower.startswith("file://")
        if _WIN_DEVICE_PATH_RE.match(s):
            return True
        if _WIN_ABS_RE.match(s):
            return True
        if _UNC_RE.match(s):
            return True
        return s.startswith("/")

    def _add_strict_error(field: str, *, expected: str, actual: object) -> None:
        strict_violations.append(f"{field}: expected {expected}, got {actual!r}")

    def _check_rel_posix_path(field: str, value: object, *, allow_dotdot: bool) -> None:
        s = str(value or "")
        if not s:
            _add_strict_error(field, expected="non-empty relative path", actual=value)
            return
        if "\\" in s:
            _add_strict_error(field, expected="POSIX-style '/' separators", actual=s)
        if _looks_like_absolute_local_path(s):
            _add_strict_error(field, expected="relative path (portable pack; no absolute machine paths)", actual=s)
        if not allow_dotdot:
            if s in (".", "..") or s.startswith("../") or s.startswith("..\\") or "/../" in s or "\\..\\" in s:
                _add_strict_error(field, expected="path that does not escape its root (no '..' segments)", actual=s)

    def _require_revision_keys(src_idx: int, src_type: str, rev: dict, keys: list[str]) -> None:
        for k in keys:
            if k not in rev or rev.get(k) in (None, "", []):
                _add_strict_error(
                    f"sources[{src_idx}].revision.{k}",
                    expected=f"required for {src_type} sources in --strict mode",
                    actual=rev.get(k, "<missing>"),
                )

    if strict:
        # Portable pack constraint: avoid embedding absolute build-machine paths.
        sources = bundle.manifest.get("sources") or []
        if isinstance(sources, list):
            for i, src in enumerate(sources):
                if not isinstance(src, dict):
                    continue
                src_type = str(src.get("type") or "")
                _check_rel_posix_path(f"sources[{i}].uri", src.get("uri"), allow_dotdot=True)

                rev = src.get("revision")
                if not isinstance(rev, dict):
                    _add_strict_error(
                        f"sources[{i}].revision",
                        expected="object with provenance fields",
                        actual=rev,
                    )
                    rev = {}

                # Required provenance fields (baseline; per source type).
                if src_type == "git":
                    _require_revision_keys(i, "git", rev, ["commit", "timestamp"])
                elif src_type == "filesystem":
                    _require_revision_keys(i, "filesystem", rev, ["hash", "timestamp"])
                elif src_type == "web":
                    _require_revision_keys(i, "web", rev, ["retrieved_at"])
                else:
                    if "timestamp" not in rev and "retrieved_at" not in rev:
                        _add_strict_error(
                            f"sources[{i}].revision",
                            expected="at least one time anchor (timestamp or retrieved_at)",
                            actual=rev,
                        )

        # Required artifact presence if declared in EXPERT.yaml.
        ctx = bundle.manifest.get("context") or {}
        artifacts = (ctx.get("artifacts") or {}) if isinstance(ctx, dict) else {}
        indexes = artifacts.get("indexes") or []
        if isinstance(indexes, list):
            for i, idx in enumerate(indexes):
                if not isinstance(idx, dict):
                    continue
                idx_path = idx.get("path")
                desc_rel = idx.get("descriptor")
                if idx_path is not None:
                    _check_rel_posix_path(f"context.artifacts.indexes[{i}].path", idx_path, allow_dotdot=False)
                    try:
                        resolved_dir = resolve_under_root(bundle.skill_root, str(idx_path))
                    except Exception as e:
                        _add_strict_error(
                            f"context.artifacts.indexes[{i}].path",
                            expected="relative path under the skill root",
                            actual=str(e),
                        )
                    else:
                        if not resolved_dir.exists():
                            _add_strict_error(
                                f"context.artifacts.indexes[{i}].path",
                                expected="existing directory (declared index artifact)",
                                actual=str(resolved_dir),
                            )
                        elif not resolved_dir.is_dir():
                            _add_strict_error(
                                f"context.artifacts.indexes[{i}].path",
                                expected="directory (declared index artifact)",
                                actual=str(resolved_dir),
                            )
                if desc_rel is not None:
                    _check_rel_posix_path(
                        f"context.artifacts.indexes[{i}].descriptor",
                        desc_rel,
                        allow_dotdot=False,
                    )
                    try:
                        resolved_desc = resolve_under_root(bundle.skill_root, str(desc_rel))
                    except Exception as e:
                        _add_strict_error(
                            f"context.artifacts.indexes[{i}].descriptor",
                            expected="relative path under the skill root",
                            actual=str(e),
                        )
                    else:
                        if not resolved_desc.exists():
                            _add_strict_error(
                                f"context.artifacts.indexes[{i}].descriptor",
                                expected="existing file (declared index descriptor)",
                                actual=str(resolved_desc),
                            )
                        elif not resolved_desc.is_file():
                            _add_strict_error(
                                f"context.artifacts.indexes[{i}].descriptor",
                                expected="file (declared index descriptor)",
                                actual=str(resolved_desc),
                            )

        summaries = artifacts.get("summaries") or []
        if isinstance(summaries, list):
            for i, s in enumerate(summaries):
                if not isinstance(s, dict):
                    continue
                s_path = s.get("path")
                if s_path is None:
                    continue
                _check_rel_posix_path(f"context.artifacts.summaries[{i}].path", s_path, allow_dotdot=False)
                try:
                    resolved = resolve_under_root(bundle.skill_root, str(s_path))
                except Exception as e:
                    _add_strict_error(
                        f"context.artifacts.summaries[{i}].path",
                        expected="relative path under the skill root",
                        actual=str(e),
                    )
                else:
                    if not resolved.exists():
                        _add_strict_error(
                            f"context.artifacts.summaries[{i}].path",
                            expected="existing file (declared summary artifact)",
                            actual=str(resolved),
                        )
                    elif not resolved.is_file():
                        _add_strict_error(
                            f"context.artifacts.summaries[{i}].path",
                            expected="file (declared summary artifact)",
                            actual=str(resolved),
                        )

        snapshots = artifacts.get("snapshots") or []
        if isinstance(snapshots, list):
            for i, snap in enumerate(snapshots):
                if not isinstance(snap, dict):
                    continue
                snap_path = snap.get("path")
                if snap_path is None:
                    continue
                _check_rel_posix_path(f"context.artifacts.snapshots[{i}].path", snap_path, allow_dotdot=False)
                try:
                    resolved = resolve_under_root(bundle.skill_root, str(snap_path))
                except Exception as e:
                    _add_strict_error(
                        f"context.artifacts.snapshots[{i}].path",
                        expected="relative path under the skill root",
                        actual=str(e),
                    )
                else:
                    if not resolved.exists():
                        _add_strict_error(
                            f"context.artifacts.snapshots[{i}].path",
                            expected="existing file or directory (declared snapshot artifact)",
                            actual=str(resolved),
                        )

        prov = artifacts.get("provenance") or {}
        if isinstance(prov, dict):
            for k in ("chunks_path", "build_info_path"):
                if not prov.get(k):
                    continue
                _check_rel_posix_path(f"context.artifacts.provenance.{k}", prov.get(k), allow_dotdot=False)
                try:
                    resolved = resolve_under_root(bundle.skill_root, str(prov.get(k)))
                except Exception as e:
                    _add_strict_error(
                        f"context.artifacts.provenance.{k}",
                        expected="relative path under the skill root",
                        actual=str(e),
                    )
                else:
                    if not resolved.exists():
                        _add_strict_error(
                            f"context.artifacts.provenance.{k}",
                            expected="existing file (declared provenance artifact)",
                            actual=str(resolved),
                        )

        maint = bundle.manifest.get("maintenance") or {}
        if isinstance(maint, dict):
            policy_path = maint.get("policy_path")
            if policy_path:
                _check_rel_posix_path("maintenance.policy_path", policy_path, allow_dotdot=False)

            playbook = maint.get("playbook_path")
            if playbook:
                _check_rel_posix_path("maintenance.playbook_path", playbook, allow_dotdot=False)
                try:
                    resolved = resolve_under_root(bundle.skill_root, str(playbook))
                except Exception as e:
                    _add_strict_error(
                        "maintenance.playbook_path",
                        expected="relative path under the skill root",
                        actual=str(e),
                    )
                else:
                    if not resolved.exists():
                        _add_strict_error(
                            "maintenance.playbook_path",
                            expected="existing file (declared playbook)",
                            actual=str(resolved),
                        )
                    elif not resolved.is_file():
                        _add_strict_error(
                            "maintenance.playbook_path",
                            expected="file (declared playbook)",
                            actual=str(resolved),
                        )

        evals = bundle.manifest.get("evals") or {}
        suites = (evals.get("suites") or []) if isinstance(evals, dict) else []
        if isinstance(suites, list):
            for i, s in enumerate(suites):
                if not isinstance(s, dict):
                    continue
                suite_path = s.get("path")
                if suite_path is None:
                    continue
                _check_rel_posix_path(f"evals.suites[{i}].path", suite_path, allow_dotdot=False)

        # Profile constraints (v0.3 direction): enforce only in --strict mode.
        prof_id, prof_violations, prof_schema_violations, prof_warnings = validate_profile_constraints(
            bundle,
            max_chunk_records=int(getattr(args, "max_chunks", 200) or 0),
        )
        profile_violations.extend(prof_violations)
        schema_violations.extend(prof_schema_violations)
        warnings.extend(prof_warnings)
    else:
        prof_id = None

    if with_artifacts:
        import jsonschema

        def _load_schema(filename: str) -> dict:
            return json.loads((schema_dir / filename).read_text(encoding="utf-8"))

        def _schema_errors(instance: object, schema: dict) -> list[str]:
            validator = jsonschema.Draft202012Validator(schema)
            errs = sorted(validator.iter_errors(instance), key=lambda e: e.path)
            out: list[str] = []
            for e in errs[:10]:
                loc = ".".join([str(p) for p in e.path]) if e.path else "<root>"
                out.append(f"{loc}: {e.message}")
            if len(errs) > 10:
                out.append(f"... ({len(errs) - 10} more)")
            return out

        idx_schema_fn = "ecp-index-descriptor.schema.json"
        kw_schema_fn = "ecp-keyword-index.schema.json"
        sqlite_schema_fn = "ecp-sqlite-fts-index.schema.json"
        vec_schema_fn = "ecp-vector-index.schema.json"
        chunk_schema_fn = "ecp-chunk-provenance.schema.json"
        pkg_schema_fn = "ecp-package.schema.json"

        idx_schema = _load_schema(idx_schema_fn)
        kw_schema = _load_schema(kw_schema_fn)
        sqlite_schema = _load_schema(sqlite_schema_fn)
        vec_schema = _load_schema(vec_schema_fn)
        chunk_schema = _load_schema(chunk_schema_fn)
        pkg_schema = _load_schema(pkg_schema_fn)

        schemas_report["expert/context/indexes/*/index.json"] = _schema_meta(idx_schema_fn)
        schemas_report["expert/context/indexes/*/index_data.json:keyword-index-v2"] = _schema_meta(kw_schema_fn)
        schemas_report["expert/context/indexes/*/index_data.json:sqlite-fts-index-v1"] = _schema_meta(sqlite_schema_fn)
        schemas_report["expert/context/indexes/*/index_data.json:vector-index-v1"] = _schema_meta(vec_schema_fn)
        schemas_report["expert/context/indexes/*/chunks.jsonl"] = _schema_meta(chunk_schema_fn)
        schemas_report["expert/package.json"] = _schema_meta(pkg_schema_fn)

        max_chunks = int(getattr(args, "max_chunks", 500) or 0)
        max_chunks = max(0, max_chunks)

        artifacts_report = {"ok": True, "indexes": [], "package": None}

        artifacts = ((bundle.manifest.get("context") or {}).get("artifacts") or {})
        indexes = artifacts.get("indexes") or []
        if isinstance(indexes, list):
            for idx in indexes:
                if not isinstance(idx, dict):
                    continue
                idx_id = str(idx.get("id") or "")
                idx_type = str(idx.get("type") or "")
                idx_out: dict = {
                    "id": idx_id,
                    "type": idx_type,
                    "ok": True,
                    "errors": [],
                }

                try:
                    idx_dir = (bundle.skill_root / Path(str(idx.get("path") or ""))).resolve()
                    desc_path = (bundle.skill_root / Path(str(idx.get("descriptor") or ""))).resolve()
                except Exception as e:
                    idx_out["ok"] = False
                    idx_out["errors"].append(f"failed to resolve index paths: {e}")
                    artifacts_report["ok"] = False
                    artifacts_report["indexes"].append(idx_out)
                    continue

                if not desc_path.exists():
                    idx_out["ok"] = False
                    idx_out["errors"].append(f"missing index descriptor: {desc_path}")
                    artifacts_report["ok"] = False
                    artifacts_report["indexes"].append(idx_out)
                    continue

                try:
                    desc = json.loads(desc_path.read_text(encoding="utf-8"))
                except Exception as e:
                    idx_out["ok"] = False
                    idx_out["errors"].append(f"failed to parse index descriptor: {e}")
                    artifacts_report["ok"] = False
                    artifacts_report["indexes"].append(idx_out)
                    continue

                desc_errs = _schema_errors(desc, idx_schema)
                if desc_errs:
                    idx_out["ok"] = False
                    idx_out["errors"].append(f"index descriptor schema errors: {desc_errs}")

                prov = desc.get("provenance") if isinstance(desc, dict) else None
                if not isinstance(prov, dict):
                    prov = {}

                index_data_rel = prov.get("index_data_path") or "index_data.json"
                chunks_rel = prov.get("chunks_path") or "chunks.jsonl"

                if strict:
                    _check_rel_posix_path(
                        f"indexes[{idx_id}].index.json.provenance.index_data_path",
                        index_data_rel,
                        allow_dotdot=False,
                    )
                    _check_rel_posix_path(
                        f"indexes[{idx_id}].index.json.provenance.chunks_path",
                        chunks_rel,
                        allow_dotdot=False,
                    )

                index_data_path = idx_dir / Path(str(index_data_rel))
                chunks_path = idx_dir / Path(str(chunks_rel))

                if index_data_path.exists():
                    try:
                        index_data = json.loads(index_data_path.read_text(encoding="utf-8"))
                    except Exception as e:
                        idx_out["ok"] = False
                        idx_out["errors"].append(f"failed to parse index_data.json: {e}")
                    else:
                        fmt = str(index_data.get("format") or "")
                        if fmt == "keyword-index-v2":
                            kw_errs = _schema_errors(index_data, kw_schema)
                            if kw_errs:
                                idx_out["ok"] = False
                                idx_out["errors"].append(f"index_data schema errors: {kw_errs}")
                            if strict and isinstance(index_data, dict):
                                for si, srec in enumerate(index_data.get("sources") or []):
                                    if isinstance(srec, dict):
                                        _check_rel_posix_path(
                                            f"indexes[{idx_id}].index_data.json.sources[{si}].uri",
                                            srec.get("uri"),
                                            allow_dotdot=True,
                                        )
                                docs = index_data.get("documents") or {}
                                if isinstance(docs, dict):
                                    checked = 0
                                    for _, drec in docs.items():
                                        if not isinstance(drec, dict):
                                            continue
                                        checked += 1
                                        if checked > 2000:
                                            break
                                        _check_rel_posix_path(
                                            f"indexes[{idx_id}].index_data.json.documents[].path",
                                            drec.get("path"),
                                            allow_dotdot=False,
                                        )
                        elif fmt == "sqlite-fts-index-v1":
                            fts_errs = _schema_errors(index_data, sqlite_schema)
                            if fts_errs:
                                idx_out["ok"] = False
                                idx_out["errors"].append(f"index_data schema errors: {fts_errs}")
                            sqlite_cfg = index_data.get("sqlite") if isinstance(index_data.get("sqlite"), dict) else {}
                            db_rel = sqlite_cfg.get("path") or "fts.sqlite"
                            if strict:
                                _check_rel_posix_path(
                                    f"indexes[{idx_id}].index_data.json.sqlite.path",
                                    db_rel,
                                    allow_dotdot=False,
                                )
                            db_path = idx_dir / Path(str(db_rel))
                            if not db_path.exists():
                                idx_out["ok"] = False
                                idx_out["errors"].append(f"missing sqlite fts db: {db_path}")
                        elif fmt == "vector-index-v1":
                            vec_errs = _schema_errors(index_data, vec_schema)
                            if vec_errs:
                                idx_out["ok"] = False
                                idx_out["errors"].append(f"index_data schema errors: {vec_errs}")
                            cfg = index_data.get("config") if isinstance(index_data.get("config"), dict) else {}
                            vcfg = cfg.get("vector") if isinstance(cfg.get("vector"), dict) else {}
                            vrel = str(vcfg.get("vectors_path") or "vectors.jsonl")
                            if strict:
                                _check_rel_posix_path(
                                    f"indexes[{idx_id}].index_data.json.config.vector.vectors_path",
                                    vrel,
                                    allow_dotdot=False,
                                )
                            vpath = idx_dir / Path(vrel)
                            if not vpath.exists():
                                idx_out["ok"] = False
                                idx_out["errors"].append(f"missing vectors payload: {vpath}")
                else:
                    idx_out["ok"] = False
                    idx_out["errors"].append(f"missing index_data.json: {index_data_path}")

                if chunks_path.exists():
                    try:
                        checked = 0
                        with chunks_path.open("r", encoding="utf-8") as f:
                            for line in f:
                                if max_chunks and checked >= max_chunks:
                                    break
                                s = line.strip()
                                if not s:
                                    continue
                                rec = json.loads(s)
                                rec_errs = _schema_errors(rec, chunk_schema)
                                if rec_errs:
                                    idx_out["ok"] = False
                                    idx_out["errors"].append(
                                        f"chunks.jsonl schema errors (line {checked + 1}): {rec_errs}"
                                    )
                                    break
                                if strict and isinstance(rec, dict):
                                    _check_rel_posix_path(
                                        f"indexes[{idx_id}].chunks.jsonl[{checked + 1}].uri",
                                        rec.get("uri"),
                                        allow_dotdot=True,
                                    )
                                    _check_rel_posix_path(
                                        f"indexes[{idx_id}].chunks.jsonl[{checked + 1}].artifact_path",
                                        rec.get("artifact_path"),
                                        allow_dotdot=False,
                                    )
                                checked += 1
                    except Exception as e:
                        idx_out["ok"] = False
                        idx_out["errors"].append(f"failed to validate chunks.jsonl: {e}")
                else:
                    idx_out["ok"] = False
                    idx_out["errors"].append(f"missing chunks.jsonl: {chunks_path}")

                if not idx_out["ok"]:
                    artifacts_report["ok"] = False
                artifacts_report["indexes"].append(idx_out)

        package_path = bundle.skill_root / "expert" / "package.json"
        if package_path.exists():
            try:
                pkg = json.loads(package_path.read_text(encoding="utf-8"))
            except Exception as e:
                artifacts_report["ok"] = False
                artifacts_report["package"] = {"ok": False, "errors": [f"failed to parse expert/package.json: {e}"]}
            else:
                pkg_errs = _schema_errors(pkg, pkg_schema)
                ok = not pkg_errs
                artifacts_report["package"] = {"ok": ok, "errors": pkg_errs}
                if not ok:
                    artifacts_report["ok"] = False
        else:
            artifacts_report["package"] = {"ok": True, "errors": []}

        if not artifacts_report.get("ok", True):
            schema_violations.append("artifact validation failed (use --json to inspect details)")

    all_errors: list[str] = []
    all_errors.extend(schema_violations)
    all_errors.extend(strict_violations)
    all_errors.extend(profile_violations)

    out = {
        "ok": len(all_errors) == 0,
        "skill": bundle.skill_frontmatter.get("name"),
        "expert_id": bundle.manifest.get("id"),
        "ecp_version": bundle.manifest.get("ecp_version"),
        "profile": bundle.manifest.get("profile"),
        "profile_id": prof_id,
        "schemas": schemas_report,
        "eval_suites": [s.suite_id for s in bundle.eval_suites],
        "strict": strict,
        "with_artifacts": with_artifacts,
        "warnings": warnings,
        "schema_violations": schema_violations,
        "strict_violations": strict_violations,
        "profile_violations": profile_violations,
        "errors": all_errors,
        "artifacts": artifacts_report,
    }
    _print(out, as_json=args.json)
    return 0 if out.get("ok") else 2

def cmd_status(args: argparse.Namespace) -> int:
    out = status(Path(args.skill))
    _print(out, as_json=args.json)
    return 0

def cmd_build(args: argparse.Namespace) -> int:
    res = build_or_refresh(
        Path(args.skill),
        run_evals=not args.no_evals,
        dry_run=args.dry_run,
        force_rebuild=bool(args.rebuild),
        generate_summaries=bool(getattr(args, "generate_summaries", False)),
        summary_llm=getattr(args, "summary_llm", None),
        summary_llm_model=getattr(args, "summary_llm_model", None),
        summary_llm_timeout=int(getattr(args, "summary_llm_timeout", 120) or 120),
    )
    _print(dataclass_to_dict(res), as_json=args.json)
    return 0

def cmd_refresh(args: argparse.Namespace) -> int:
    res = build_or_refresh(
        Path(args.skill),
        run_evals=not args.no_evals,
        dry_run=args.dry_run,
        force_rebuild=bool(args.rebuild),
        generate_summaries=bool(getattr(args, "generate_summaries", False)),
        summary_llm=getattr(args, "summary_llm", None),
        summary_llm_model=getattr(args, "summary_llm_model", None),
        summary_llm_timeout=int(getattr(args, "summary_llm_timeout", 120) or 120),
    )
    _print(dataclass_to_dict(res), as_json=args.json)
    return 0

def cmd_query(args: argparse.Namespace) -> int:
    query_vector = None
    qvf = getattr(args, "query_vector_file", None)
    if qvf:
        try:
            query_vector = json.loads(Path(str(qvf)).read_text(encoding="utf-8"))
        except Exception as e:
            raise ECPError(f"Failed to parse --query-vector-file {qvf!r} as JSON: {e}") from e

    out = query_expert(
        Path(args.skill),
        question=args.question,
        mode=args.mode,
        top_k=args.top_k,
        source_ids=args.source_id,
        path_prefixes=args.path_prefix,
        llm=args.llm,
        llm_model=args.llm_model,
        llm_timeout_seconds=args.llm_timeout_seconds,
        query_vector=query_vector,
    )
    if args.json:
        _print(out, as_json=True)
    else:
        # Print the answer only for human readability, followed by citations summary.
        sys.stdout.write(out.get("answer", "") + "\n")
        sys.stdout.write("\nCitations:\n")
        for c in out.get("citations", []):
            sid = c.get("source_id")
            ap = c.get("artifact_path")
            ls = c.get("line_start")
            le = c.get("line_end")
            src = f"{sid}:" if sid else ""
            sys.stdout.write(f"- {src}{ap} (lines {ls}-{le})\n")
    return 0

def cmd_run_evals(args: argparse.Namespace) -> int:
    bundle = load_skill_bundle(Path(args.skill))
    suite_ids = args.suite_id if args.suite_id else None
    report = run_eval_suites(bundle, suite_ids=suite_ids)
    _print(report, as_json=args.json)
    return 0 if report.get("passed") else 2

def cmd_set_source(args: argparse.Namespace) -> int:
    # Convenience for PoC: update sources[0].uri in expert/EXPERT.yaml.
    skill_root = Path(args.skill).resolve()
    expert_path = skill_root / "expert" / "EXPERT.yaml"
    manifest = read_yaml(expert_path)
    if not isinstance(manifest, dict):
        raise ECPError("EXPERT.yaml did not parse to an object.")
    sources = manifest.get("sources") or []
    if not sources:
        raise ECPError("EXPERT.yaml has no sources[] to update.")
    if args.source_id:
        updated = False
        for s in sources:
            if isinstance(s, dict) and s.get("source_id") == args.source_id:
                s["uri"] = args.uri
                updated = True
                break
        if not updated:
            raise ECPError(f"No sources[] entry matched source_id={args.source_id}")
    else:
        sources[0]["uri"] = args.uri
    manifest["sources"] = sources
    write_yaml(expert_path, manifest)
    _print(
        {"ok": True, "updated": str(expert_path), "uri": args.uri, "source_id": args.source_id},
        as_json=args.json,
    )
    return 0

def cmd_mcp(args: argparse.Namespace) -> int:
    run_stdio_mcp_server(Path(args.skill))
    return 0

def cmd_pack(args: argparse.Namespace) -> int:
    from .packaging import create_skill_package

    out_path = Path(args.out) if args.out else Path(f"{Path(args.skill).name}.zip")
    res = create_skill_package(
        Path(args.skill),
        out_path=out_path,
        include_logs=bool(args.include_logs),
        include_backups=bool(args.include_backups),
        allow_secrets=bool(args.allow_secrets),
        deterministic=not bool(args.non_deterministic),
    )
    _print(res, as_json=args.json)
    return 0

def cmd_verify_pack(args: argparse.Namespace) -> int:
    from .packaging import verify_skill_package

    res = verify_skill_package(Path(args.package), validate=not bool(args.no_validate))
    _print(res, as_json=args.json)
    return 0 if res.get("ok") else 2

def cmd_prune(args: argparse.Namespace) -> int:
    from .retention import prune_skill

    res = prune_skill(Path(args.skill), dry_run=bool(args.dry_run))
    _print(res, as_json=args.json)
    return 0

def cmd_generate_summaries(args: argparse.Namespace) -> int:
    from .summary_generator import generate_summaries

    bundle = load_skill_bundle(Path(args.skill))
    res = generate_summaries(
        skill_root=Path(args.skill).resolve(),
        bundle=bundle,
        llm=args.llm,
        llm_model=args.llm_model,
        llm_timeout_seconds=args.llm_timeout,
        summary_ids=args.summary_id,
        dry_run=bool(args.dry_run),
    )
    _print(dataclass_to_dict(res), as_json=args.json)
    return 0 if not res.failed else 1

def dataclass_to_dict(obj: object) -> dict:
    import dataclasses
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    return {"result": obj}

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ecpctl",
        description="ECP reference implementation CLI (v1.0)",
    )
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("validate", help="Validate SKILL.md + ECP artifacts against schemas")
    sp.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sp.add_argument("--skill", required=True, help="Path to the skill directory")
    sp.add_argument(
        "--strict",
        action="store_true",
        help="Enforce portability + provenance requirements (fails CI on any strict error)",
    )
    sp.add_argument(
        "--with-artifacts",
        action="store_true",
        help="Also validate referenced index artifacts (index.json/index_data.json/chunks.jsonl) when present",
    )
    sp.add_argument(
        "--max-chunks",
        type=int,
        default=500,
        help="Max chunks.jsonl records to schema-validate per index when using --with-artifacts (0 = all)",
    )
    sp.set_defaults(func=cmd_validate)

    sp = sub.add_parser("status", help="Show basic skill/expert status")
    sp.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sp.add_argument("--skill", required=True, help="Path to the skill directory")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("build", help="Build context artifacts (rebuild if none exist)")
    sp.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sp.add_argument("--skill", required=True, help="Path to the skill directory")
    sp.add_argument("--no-evals", action="store_true", help="Skip running evals after build")
    sp.add_argument("--rebuild", action="store_true", help="Force a full rebuild even if an index exists")
    sp.add_argument("--dry-run", action="store_true", help="Detect strategy/changes but do not modify files")
    sp.add_argument("--generate-summaries", action="store_true", help="Generate LLM-powered summaries during build")
    sp.add_argument(
        "--summary-llm",
        choices=["none", "openrouter", "ollama"],
        default="none",
        help="LLM provider for summary generation (default: none)",
    )
    sp.add_argument("--summary-llm-model", help="Model for summary generation")
    sp.add_argument("--summary-llm-timeout", type=int, default=120, help="Timeout for summary LLM requests (default: 120)")
    sp.set_defaults(func=cmd_build)

    sp = sub.add_parser("refresh", help="Refresh context artifacts (incremental if possible)")
    sp.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sp.add_argument("--skill", required=True, help="Path to the skill directory")
    sp.add_argument("--no-evals", action="store_true", help="Skip running evals after refresh")
    sp.add_argument("--rebuild", action="store_true", help="Force a full rebuild instead of incremental refresh")
    sp.add_argument("--dry-run", action="store_true", help="Detect strategy/changes but do not modify files")
    sp.add_argument("--generate-summaries", action="store_true", help="Generate LLM-powered summaries during refresh")
    sp.add_argument(
        "--summary-llm",
        choices=["none", "openrouter", "ollama"],
        default="none",
        help="LLM provider for summary generation (default: none)",
    )
    sp.add_argument("--summary-llm-model", help="Model for summary generation")
    sp.add_argument("--summary-llm-timeout", type=int, default=120, help="Timeout for summary LLM requests (default: 120)")
    sp.set_defaults(func=cmd_refresh)

    sp = sub.add_parser("query", help="Query the expert against its persistent context")
    sp.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sp.add_argument("--skill", required=True, help="Path to the skill directory")
    sp.add_argument("--mode", default="ephemeral", choices=["ephemeral", "persistent", "summarized"])
    sp.add_argument("--top-k", type=int, default=5, help="Number of files/snippets to retrieve")
    sp.add_argument("--source-id", action="append", help="Restrict retrieval to a specific source_id (repeatable)")
    sp.add_argument("--path-prefix", action="append", help="Restrict retrieval to paths under this prefix (repeatable)")
    sp.add_argument(
        "--query-vector-file",
        help="Path to a JSON file containing a dense [float,...] or sparse [[i,value],...] query embedding for vector indexes.",
    )
    sp.add_argument(
        "--llm",
        default="none",
        choices=["none", "openrouter", "ollama"],
        help="Optional LLM synthesis provider for the answer (default: none).",
    )
    sp.add_argument(
        "--llm-model",
        help="Model name for --llm openrouter (default: $OPENROUTER_MODEL or xiaomi/mimo-v2-flash:free).",
    )
    sp.add_argument(
        "--llm-timeout-seconds",
        type=int,
        default=60,
        help="Timeout for remote LLM requests (default: 60).",
    )
    sp.add_argument("question", help="The question to ask the expert")     
    sp.set_defaults(func=cmd_query)

    sp = sub.add_parser("run-evals", help="Run eval suites declared in EXPERT.yaml")
    sp.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sp.add_argument("--skill", required=True, help="Path to the skill directory")
    sp.add_argument("--suite-id", action="append", help="Suite id(s) to run (defaults to policy.validation.eval_suites)")
    sp.set_defaults(func=cmd_run_evals)

    sp = sub.add_parser("set-source", help="Update sources[0].uri in expert/EXPERT.yaml (PoC convenience)")
    sp.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sp.add_argument("--skill", required=True, help="Path to the skill directory")
    sp.add_argument("--source-id", help="source_id in EXPERT.yaml to update (defaults to first entry)")
    sp.add_argument("--uri", required=True, help="New source URI, e.g. file:///abs/path/to/repo")
    sp.set_defaults(func=cmd_set_source)

    sp = sub.add_parser("mcp", help="Run an MCP-compatible stdio server exposing expert.* tools")
    sp.add_argument("--skill", required=True, help="Path to the skill directory")
    sp.set_defaults(func=cmd_mcp)

    sp = sub.add_parser("pack", help="Create a ZIP package for an ECP-enabled skill")
    sp.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sp.add_argument("--skill", required=True, help="Path to the skill directory")
    sp.add_argument("--out", help="Output zip path (default: <skill_dir_name>.zip)")
    sp.add_argument("--include-logs", action="store_true", help="Include expert/logs/** in the zip")
    sp.add_argument("--include-backups", action="store_true", help="Include **/.backup/** in the zip")
    sp.add_argument(
        "--allow-secrets",
        action="store_true",
        help="Allow packaging when security.contains_secrets=true (dangerous; use encrypted/approved channels)",
    )
    sp.add_argument("--non-deterministic", action="store_true", help="Do not force deterministic zip timestamps")
    sp.set_defaults(func=cmd_pack)

    sp = sub.add_parser("verify-pack", help="Verify an ECP ZIP package created by ecpctl pack")
    sp.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sp.add_argument("--package", required=True, help="Path to the zip package")
    sp.add_argument("--no-validate", action="store_true", help="Skip schema validation after extraction")
    sp.set_defaults(func=cmd_verify_pack)

    sp = sub.add_parser("prune", help="Apply retention rules to backups/logs (best-effort)")
    sp.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sp.add_argument("--skill", required=True, help="Path to the skill directory")
    sp.add_argument("--dry-run", action="store_true", help="Preview deletions without removing files")
    sp.set_defaults(func=cmd_prune)

    sp = sub.add_parser("generate-summaries", help="Generate LLM-powered summaries for a skill")
    sp.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    sp.add_argument("--skill", required=True, help="Path to the skill directory")
    sp.add_argument(
        "--llm",
        required=True,
        choices=["openrouter", "ollama"],
        help="LLM provider for summary generation",
    )
    sp.add_argument("--llm-model", help="Model for summary generation")
    sp.add_argument("--llm-timeout", type=int, default=120, help="Timeout for LLM requests (default: 120)")
    sp.add_argument("--summary-id", action="append", help="Specific summary ID(s) to generate (repeatable)")
    sp.add_argument("--dry-run", action="store_true", help="Preview generation without writing files")
    sp.set_defaults(func=cmd_generate_summaries)

    return p

def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    p = build_parser()
    args = p.parse_args(argv)
    load_dotenv(Path(".env"))
    try:
        return int(args.func(args))
    except ECPError as e:
        sys.stderr.write(f"ERROR: {e}\n")
        return 2
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted.\n")
        return 130

if __name__ == "__main__":
    raise SystemExit(main())
