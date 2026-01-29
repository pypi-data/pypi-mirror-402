from __future__ import annotations

import datetime as _dt
import dataclasses
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from .errors import BuildError, RefreshError
from .indexer import (
    SourceSpec,
    build_keyword_index_multi,
    build_vector_index_multi,
    incremental_update_keyword_index_multi,
    incremental_update_vector_index_multi,
    load_keyword_index,
    load_vector_index,
)
from .sqlite_fts import (
    build_sqlite_fts_index_multi,
    incremental_update_sqlite_fts_index_multi,
    load_sqlite_fts_index,
)
from .skill_loader import SkillBundle, load_skill_bundle
from .utils import (
    append_jsonl,
    looks_like_text,
    normalize_posix,
    rfc3339_now,
    read_json,
    read_text_file,
    read_yaml,
    resolve_under_root,
    sha256_text,
    within_scope,
    write_json,
    write_yaml,
)

def parse_file_uri(uri: str, *, base_dir: Path | None = None) -> Path:
    """Parse file URI or path to Path, supporting both POSIX and Windows formats.

    Supports:
    - file:///abs/path (POSIX)
    - file://localhost/abs/path (POSIX with host)
    - file:///C:/path (Windows, RFC 8089 style)
    - file:///C%3A/path (Windows, URL-encoded colon)
    - file://C:/path (Windows, common but non-standard)
    - /abs/path (POSIX absolute)
    - C:/path or C:\\path (Windows absolute)
    - relative/path (relative; resolved against base_dir if provided)
    """
    import platform
    import urllib.parse

    if uri.startswith("file://"):
        # Strip scheme
        rest = uri[len("file://"):]

        # Handle localhost prefix
        if rest.startswith("localhost/"):
            rest = rest[len("localhost"):]  # Keep the leading /

        # URL-decode the path (handles %3A for colon, %20 for space, etc.)
        rest = urllib.parse.unquote(rest)

        # Windows: file:///C:/path or file:///C|/path
        # After stripping file://, rest is /C:/path or /C|/path
        if len(rest) >= 3 and rest[0] == "/" and rest[2] in (":", "|"):
            # /C:/path -> C:/path
            drive_letter = rest[1]
            path_part = rest[3:] if len(rest) > 3 else ""
            return Path(f"{drive_letter}:{path_part}").resolve()

        # Windows: file://C:/path (non-standard but common)
        # After stripping file://, rest is C:/path
        if len(rest) >= 2 and rest[1] in (":", "|") and rest[0].isalpha():
            drive_letter = rest[0]
            path_part = rest[2:] if len(rest) > 2 else ""
            return Path(f"{drive_letter}:{path_part}").resolve()

        # POSIX: file:///abs/path -> rest is /abs/path
        if rest.startswith("/"):
            # On Windows, /abs/path is ambiguous - treat as relative to current drive
            if platform.system() == "Windows":
                return Path(rest[1:]).resolve() if len(rest) > 1 else Path(".").resolve()
            return Path(rest).resolve()

        # Fallback: treat as relative path
        rel_path = Path(rest)
        if not rel_path.is_absolute() and base_dir is not None:
            return (base_dir / rel_path).resolve()
        return rel_path.resolve()

    # Not a file:// URI - could be absolute or relative path
    p = Path(uri)
    if not p.is_absolute() and base_dir is not None:
        return (base_dir / p).resolve()
    return p.resolve()

GIT_TIMEOUT_SECONDS = 60  # Timeout for git operations

def _run_git(repo: Path, args: list[str], *, timeout: int = GIT_TIMEOUT_SECONDS) -> str:
    """Run a git command with timeout protection."""
    try:
        p = subprocess.run(
            ["git", "-C", str(repo)] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        raise RefreshError(f"git command timed out after {timeout}s: git {' '.join(args)}") from e
    if p.returncode != 0:
        raise RefreshError(f"git command failed: git {' '.join(args)}\n{p.stderr.strip()}")
    return p.stdout.strip()

def is_git_repo(path: Path) -> bool:
    """Check if path is inside a git repository."""
    try:
        _ = _run_git(path, ["rev-parse", "--is-inside-work-tree"], timeout=5)
        return True
    except (RefreshError, OSError):
        # RefreshError: git command failed or timed out
        # OSError: git executable not found
        return False

def git_head_revision(repo: Path, *, timeout: int = GIT_TIMEOUT_SECONDS) -> dict:
    commit = _run_git(repo, ["rev-parse", "HEAD"], timeout=timeout)
    try:
        branch = _run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"], timeout=timeout)
    except Exception:
        branch = None
    return {"commit": commit, "branch": branch, "timestamp": rfc3339_now()}     

def git_changed_files(
    repo: Path,
    old_commit: str,
    new_commit: str = "HEAD",
    *,
    timeout: int = GIT_TIMEOUT_SECONDS,
) -> tuple[list[str], list[str]]:
    # Returns (changed_or_added, removed)
    out = _run_git(repo, ["diff", "--name-status", f"{old_commit}..{new_commit}"], timeout=timeout)
    changed: list[str] = []
    removed: list[str] = []
    for line in out.splitlines():
        # Format: <status>\t<path> (status can be M/A/D/R...)
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0].strip()
        if status.startswith("D"):
            if len(parts) >= 2:
                removed.append(parts[1])
        elif status.startswith("R"):
            # Rename: R<score>\t<old>\t<new>
            if len(parts) >= 3:
                removed.append(parts[1])
                changed.append(parts[2])
            elif len(parts) >= 2:
                changed.append(parts[1])
        elif status.startswith("C"):
            # Copy: C<score>\t<old>\t<new>
            if len(parts) >= 3:
                changed.append(parts[2])
            elif len(parts) >= 2:
                changed.append(parts[1])
        else:
            # Treat as changed (includes A/M/T/U/etc)
            if len(parts) >= 2:
                changed.append(parts[1])
    # Normalize to posix
    changed = [Path(p).as_posix() for p in changed]
    removed = [Path(p).as_posix() for p in removed]
    return changed, removed

def filesystem_manifest(
    repo: Path,
    *,
    include: list[str],
    exclude: list[str],
    max_file_bytes: int,
    deadline: float | None = None,
) -> dict[str, dict]:
    """Compute a file manifest for non-git sources."""
    from .utils import iter_files, within_scope, looks_like_text

    manifest: dict[str, dict] = {}
    for p in iter_files(repo):
        if deadline is not None and time.monotonic() > deadline:
            raise BuildError("Update exceeded max_update_duration_seconds.")
        rel = normalize_posix(p.relative_to(repo))
        if not within_scope(rel, include, exclude):
            continue
        try:
            st = p.stat()
        except Exception:
            continue
        if st.st_size > max_file_bytes:
            manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "too_large"}
            continue
        if not looks_like_text(p):
            manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "binary_or_non_utf8"}
            continue
        try:
            manifest[rel] = {
                "sha256": sha256_text(read_text_file(p)),
                "size": st.st_size,
                "skipped": None,
            }
        except Exception:
            manifest[rel] = {"sha256": None, "size": st.st_size, "skipped": "read_error"}
    return manifest

def diff_file_manifests(old: dict, new: dict) -> tuple[list[str], list[str]]:
    old_keys = set(old.keys())
    new_keys = set(new.keys())
    removed = sorted(old_keys - new_keys)
    added = sorted(new_keys - old_keys)
    changed = []
    for k in sorted(old_keys & new_keys):
        if old[k].get("sha256") != new[k].get("sha256"):
            changed.append(k)
    return sorted(set(changed + added)), removed

@dataclasses.dataclass
class RefreshResult:
    strategy: str
    changed_files: list[str]
    removed_files: list[str]
    as_of: dict
    eval_passed: bool
    eval_report: dict | None
    message: str

def _get_primary_source(manifest: dict) -> dict:
    sources = manifest.get("sources") or []
    if not sources:
        raise BuildError("EXPERT.yaml must declare at least one source in sources[].")
    return sources[0]

def _get_artifacts(manifest: dict) -> dict:
    return (manifest.get("context") or {}).get("artifacts") or {}

def _get_indexes(manifest: dict) -> list[dict]:
    indexes = (_get_artifacts(manifest).get("indexes") or [])
    return [i for i in indexes if isinstance(i, dict)]

def _get_summaries(manifest: dict) -> list[dict]:
    summaries = (_get_artifacts(manifest).get("summaries") or [])
    return [s for s in summaries if isinstance(s, dict)]

def _get_primary_index(manifest: dict) -> dict | None:
    idxs = _get_indexes(manifest)
    return idxs[0] if idxs else None


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

    # Default backend based on declared index type.
    idx_type = str(index_entry.get("type") or "").strip().lower()
    if idx_type == "vector":
        return "vector"

    return ""

def _resolve_index_dir(skill_root: Path, index_entry: dict) -> Path:
    # index_entry.path points to directory
    rel = index_entry.get("path")
    if not rel:
        raise BuildError("Index artifact entry missing required 'path'.")       
    try:
        return resolve_under_root(skill_root, str(rel))
    except ValueError as e:
        raise BuildError(str(e)) from e

def build_or_refresh(
    skill_root: Path,
    *,
    run_evals: bool = True,
    dry_run: bool = False,
    force_rebuild: bool = False,
    generate_summaries: bool = False,
    summary_llm: str | None = None,
    summary_llm_model: str | None = None,
    summary_llm_timeout: int = 120,
) -> RefreshResult:
    bundle = load_skill_bundle(skill_root)
    manifest = bundle.manifest
    policy = bundle.policy
    return _build_or_refresh_v2(
        bundle,
        run_evals=run_evals,
        dry_run=dry_run,
        force_rebuild=force_rebuild,
        generate_summaries=generate_summaries,
        summary_llm=summary_llm,
        summary_llm_model=summary_llm_model,
        summary_llm_timeout=summary_llm_timeout,
    )

    primary_source = _get_primary_source(manifest)
    source_type = primary_source.get("type")
    source_uri = primary_source.get("uri")
    if not source_uri:
        raise BuildError("Primary source missing uri.")
    repo = parse_file_uri(source_uri, base_dir=bundle.skill_root)

    scope = primary_source.get("scope") or {}
    include = scope.get("include") or ["**/*"]
    exclude = scope.get("exclude") or []

    security = manifest.get("security") or {}
    classification = security.get("classification")
    license = security.get("license")

    # Determine index
    idx_entry = _get_primary_index(manifest)
    if idx_entry is None:
        # Summaries-only packs are valid per spec, but this PoC runtime has no summary builder.
        # Treat build/refresh as a no-op aside from running evals/logging.
        as_of = primary_source.get("revision") or {}

        eval_passed = True
        eval_report: dict | None = None
        if run_evals:
            try:
                from .evals import run_eval_suites

                suites_to_run = (policy.get("validation") or {}).get("eval_suites") or []
                eval_report = run_eval_suites(bundle, suite_ids=suites_to_run)
                eval_passed = bool(eval_report.get("passed", False))
            except Exception as e:
                eval_passed = False
                eval_report = {"passed": False, "error": str(e)}

        message = "No indexes configured; build/refresh is a no-op for summaries-only packs."

        logs_root = bundle.skill_root / "expert" / "logs"
        raw_logs_cfg = manifest.get("logs")
        has_logs_cfg = isinstance(raw_logs_cfg, dict)
        logs_cfg = raw_logs_cfg if has_logs_cfg else {}
        logs_enabled = bool(logs_cfg.get("enabled", False)) or (
            (not has_logs_cfg) and logs_root.exists()
        )
        if logs_enabled:
            log_dir = logs_root / "updates"
            day = rfc3339_now()[:10]
            append_jsonl(
                log_dir / f"{day}.jsonl",
                {
                    "timestamp": rfc3339_now(),
                    "operation": "refresh",
                    "strategy": "noop",
                    "changed_files": [],
                    "removed_files": [],
                    "as_of": as_of,
                    "eval_report": eval_report,
                    "message": message,
                },
            )

        return RefreshResult(
            strategy="noop",
            changed_files=[],
            removed_files=[],
            as_of=as_of,
            eval_passed=eval_passed,
            eval_report=eval_report,
            message=message,
        )

    index_id = idx_entry.get("id", "keyword-v1")
    index_dir = _resolve_index_dir(bundle.skill_root, idx_entry)
    backend = _index_backend(idx_entry)

    budgets = policy.get("budgets") or {}
    max_changed_files_budget = budgets.get("max_changed_files")
    max_update_duration_seconds = budgets.get("max_update_duration_seconds")

    deadline: float | None = None
    if max_update_duration_seconds is not None:
        try:
            seconds = int(max_update_duration_seconds)
        except Exception:
            seconds = None
        if seconds is not None and seconds > 0:
            deadline = time.monotonic() + seconds

    update_strategy = policy.get("update_strategy") or {}
    default_strategy = update_strategy.get("default") or "incremental"
    if default_strategy not in ("incremental", "rebuild"):
        raise BuildError(f"Invalid policy.update_strategy.default: {default_strategy}")

    rebuild_thresholds = update_strategy.get("rebuild_thresholds") or {}
    changed_files_gt = rebuild_thresholds.get("changed_files_gt")
    if changed_files_gt is None:
        changed_files_gt = rebuild_thresholds.get("changed_files")
    threshold_changed_files = int(changed_files_gt) if changed_files_gt is not None else None
    days_since_full_rebuild_gt = rebuild_thresholds.get("days_since_full_rebuild_gt")

    git_timeout = GIT_TIMEOUT_SECONDS
    if deadline is not None:
        git_timeout = max(1, min(GIT_TIMEOUT_SECONDS, int(max_update_duration_seconds)))

    # Backup current state for rollback (keep it adjacent to the configured index path).
    backup_dir = index_dir / ".backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = rfc3339_now().replace(":", "").replace("-", "")
    backup_index = backup_dir / f"index_data.{ts}.json"
    backup_manifest = backup_dir / f"EXPERT.{ts}.yaml"
    backup_file_manifest = backup_dir / f"file_manifest.{ts}.json"        
    backup_descriptor = backup_dir / f"index.{ts}.json"
    backup_chunks = backup_dir / f"chunks.{ts}.jsonl"
    backup_build_info = backup_dir / f"build_info.{ts}.json"
    backup_sqlite = backup_dir / f"fts.{ts}.sqlite"
    backup_vectors = backup_dir / f"vectors.{ts}.jsonl"

    index_data_path = index_dir / "index_data.json"
    descriptor_path = index_dir / "index.json"
    file_manifest_path = index_dir / "file_manifest.json"
    chunks_path = index_dir / "chunks.jsonl"
    build_info_path = index_dir / "build_info.json"

    exists = index_data_path.exists()
    strategy = "rebuild" if not exists else default_strategy

    max_file_bytes_for_manifest = 512_000
    index_data_meta: dict | None = None
    if exists:
        try:
            index_data_meta = load_keyword_index(index_dir)
            max_file_bytes_for_manifest = int((index_data_meta.get("config") or {}).get("max_file_bytes", max_file_bytes_for_manifest))
        except Exception:
            # Corrupt/missing index data - force rebuild.
            index_data_meta = None
            strategy = "rebuild"

    changed_files: list[str] = []
    removed_files: list[str] = []
    new_manifest: dict[str, dict] | None = None

    # Detect changes (incremental only)
    if exists and strategy == "incremental":
        incremental_method = (update_strategy.get("incremental") or {}).get("method")
        if not incremental_method:
            incremental_method = (((primary_source.get("refresh") or {}).get("incremental") or {}).get("method"))
        if not incremental_method:
            incremental_method = "git-diff" if (is_git_repo(repo) and source_type == "git") else "file-manifest"

        if incremental_method == "git-diff" and is_git_repo(repo) and source_type == "git":
            old_commit = (primary_source.get("revision") or {}).get("commit")
            if not old_commit or old_commit in ("HEAD", "head"):
                # No stable baseline -> force rebuild.
                strategy = "rebuild"
            else:
                try:
                    changed_files, removed_files = git_changed_files(repo, old_commit, "HEAD", timeout=git_timeout)
                except Exception:
                    strategy = "rebuild"
        else:
            # Filesystem diff via manifests (default, also used for non-git sources)
            old_manifest = {}
            if file_manifest_path.exists():
                old_manifest = read_json(file_manifest_path)
            new_manifest = filesystem_manifest(
                repo,
                include=include,
                exclude=exclude,
                max_file_bytes=max_file_bytes_for_manifest,
                deadline=deadline,
            )
            changed_files, removed_files = diff_file_manifests(old_manifest, new_manifest)

        changed_count = len(changed_files) + len(removed_files)
        if threshold_changed_files is not None and changed_count > threshold_changed_files:
            strategy = "rebuild"

        if max_changed_files_budget is not None:
            try:
                max_changed_files_int = int(max_changed_files_budget)
            except Exception:
                max_changed_files_int = None
            if max_changed_files_int is not None and max_changed_files_int >= 0 and changed_count > max_changed_files_int:
                strategy = "rebuild"

        if days_since_full_rebuild_gt is not None and index_data_meta is not None:
            try:
                threshold_days = int(days_since_full_rebuild_gt)
                created_at = index_data_meta.get("created_at")
                if created_at:
                    created_dt = _dt.datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
                    now_dt = _dt.datetime.now(tz=_dt.timezone.utc)
                    if (now_dt - created_dt).days > threshold_days:
                        strategy = "rebuild"
            except Exception:
                pass

    # Determine revision to record
    if is_git_repo(repo) and source_type == "git":
        as_of = git_head_revision(repo, timeout=git_timeout)
    else:
        # Deterministic-ish revision for filesystem sources
        # Use a hash over file_manifest (paths + hashes)
        if new_manifest is None:
            new_manifest = filesystem_manifest(
                repo,
                include=include,
                exclude=exclude,
                max_file_bytes=max_file_bytes_for_manifest,
                deadline=deadline,
            )
        import hashlib, json
        blob = json.dumps(new_manifest, sort_keys=True).encode("utf-8")
        as_of = {"hash": hashlib.sha256(blob).hexdigest(), "timestamp": rfc3339_now()}

    if dry_run:
        return RefreshResult(
            strategy=strategy,
            changed_files=changed_files,
            removed_files=removed_files,
            as_of=as_of,
            eval_passed=True,
            eval_report=None,
            message="dry_run: no changes applied",
        )

    # Backup for rollback
    write_yaml(backup_manifest, manifest)
    if exists:
        shutil.copy(index_data_path, backup_index)
        if descriptor_path.exists():
            shutil.copy(descriptor_path, backup_descriptor)
        if file_manifest_path.exists():
            shutil.copy(file_manifest_path, backup_file_manifest)
        if chunks_path.exists():
            shutil.copy(chunks_path, backup_chunks)
        if build_info_path.exists():
            shutil.copy(build_info_path, backup_build_info)
        if sqlite_path is not None and sqlite_path.exists():
            shutil.copy(sqlite_path, backup_sqlite)
        if vectors_path is not None and vectors_path.exists():
            shutil.copy(vectors_path, backup_vectors)

    # Apply build/update
    if strategy == "rebuild":
        build_keyword_index(
            index_id=index_id,
            source_id=primary_source.get("source_id", "repo"),
            source_type=source_type or "filesystem",
            source_uri=source_uri,
            source_root=repo,
            include=include,
            exclude=exclude,
            out_dir=index_dir,
            source_revision=as_of,
            classification=classification,
            license=license,
            deadline=deadline,
        )
        changed_files = ["<rebuild>"]
        removed_files = []
    else:
        index_data = load_keyword_index(index_dir)
        index_data.setdefault("source", {})
        if isinstance(index_data.get("source"), dict):
            index_data["source"].update(
                {
                    "source_id": primary_source.get("source_id", "repo"),
                    "source_type": source_type or "filesystem",
                    "uri": source_uri,
                    "classification": classification,
                    "license": license,
                }
            )
        incremental_update_keyword_index(
            index_data=index_data,
            source_root=repo,
            include=include,
            exclude=exclude,
            changed_files=changed_files,
            removed_files=removed_files,
            source_revision=as_of,
            deadline=deadline,
        )
        save_keyword_index(index_dir, index_data)

        # Update file manifest (filesystem mode)
        if not (is_git_repo(repo) and source_type == "git"):
            if new_manifest is None:
                max_file_bytes = int((index_data.get("config") or {}).get("max_file_bytes", max_file_bytes_for_manifest))
                new_manifest = filesystem_manifest(
                    repo,
                    include=include,
                    exclude=exclude,
                    max_file_bytes=max_file_bytes,
                    deadline=deadline,
                )
            write_json(file_manifest_path, new_manifest)

    # Update manifest revision for primary source
    primary_source.setdefault("revision", {})
    primary_source["revision"].update(as_of)
    manifest.setdefault("sources", [primary_source])
    # Persist updated manifest in-place
    write_yaml(bundle.expert_yaml_path, manifest)

    # Run evals if requested
    eval_passed = True
    eval_report: dict | None = None
    if run_evals:
        try:
            from .evals import run_eval_suites
            suites_to_run = (policy.get("validation") or {}).get("eval_suites") or []
            eval_report = run_eval_suites(bundle, suite_ids=suites_to_run)
            eval_passed = bool(eval_report.get("passed", False))
        except Exception as e:
            eval_passed = False
            eval_report = {"passed": False, "error": str(e)}

    # Handle failures according to policy
    validation = policy.get("validation") or {}
    fail_action = validation.get("fail_action", "block")
    if fail_action not in ("block", "warn", "rollback"):
        raise BuildError(f"Invalid policy.validation.fail_action: {fail_action}")

    publishing = policy.get("publishing") or {}
    rollback_on_fail = bool(publishing.get("rollback_on_fail", True))
    on_pass = publishing.get("on_pass", "auto_publish")
    if on_pass not in ("auto_publish", "require_approval"):
        raise BuildError(f"Invalid policy.publishing.on_pass: {on_pass}")

    operation = "build" if not exists else "refresh"
    rolled_back = False

    if not eval_passed:
        if fail_action == "warn":
            message = f"{operation} failed evals (fail_action=warn); changes left in place."
        else:
            should_rollback = fail_action == "rollback" or (fail_action == "block" and rollback_on_fail)
            if should_rollback:
                # Restore manifest
                prior_manifest = read_yaml(backup_manifest)
                write_yaml(bundle.expert_yaml_path, prior_manifest)

                if exists:
                    # Restore prior artifacts
                    shutil.copy(backup_index, index_data_path)
                    if backup_descriptor.exists():
                        shutil.copy(backup_descriptor, descriptor_path)
                    if backup_file_manifest.exists():
                        shutil.copy(backup_file_manifest, file_manifest_path)
                    if backup_chunks.exists():
                        shutil.copy(backup_chunks, chunks_path)
                    if backup_build_info.exists():
                        shutil.copy(backup_build_info, build_info_path)
                else:
                    # No prior state -> remove newly built artifacts
                    index_data_path.unlink(missing_ok=True)
                    descriptor_path.unlink(missing_ok=True)
                    file_manifest_path.unlink(missing_ok=True)
                    chunks_path.unlink(missing_ok=True)
                    build_info_path.unlink(missing_ok=True)

                rolled_back = True
                message = f"{operation} failed evals; rolled back (fail_action={fail_action})."
            else:
                message = f"{operation} failed evals (fail_action={fail_action}); changes left in place."
    else:
        message = f"{operation} succeeded."
        if on_pass == "require_approval":
            message = f"{operation} succeeded; publishing requires approval."

    # Write update log (optional)
    logs_root = bundle.skill_root / "expert" / "logs"
    raw_logs_cfg = manifest.get("logs")
    has_logs_cfg = isinstance(raw_logs_cfg, dict)
    logs_cfg = raw_logs_cfg if has_logs_cfg else {}
    logs_enabled = bool(logs_cfg.get("enabled", False)) or (
        (not has_logs_cfg) and logs_root.exists()
    )
    if logs_enabled:
        log_dir = logs_root / "updates"
        day = rfc3339_now()[:10]
        log_path = log_dir / f"{day}.jsonl"
        append_jsonl(
            log_path,
            {
                "timestamp": rfc3339_now(),
                "operation": operation,
                "strategy": strategy,
                "changed_files": changed_files,
                "removed_files": removed_files,
                "as_of": as_of,
                "eval_report": eval_report,
                "fail_action": fail_action,
                "rollback_on_fail": rollback_on_fail,
                "rolled_back": rolled_back,
                "publish": on_pass,
                "message": message,
            },
        )

    # Optional retention cleanup (spec v1.0 Section 7.6).
    retention_cfg = policy.get("retention")
    if not dry_run and isinstance(retention_cfg, dict) and retention_cfg:
        try:
            from .retention import prune_bundle

            report = prune_bundle(bundle, dry_run=False)
            pruned = len(report.get("deleted_backups") or []) + len(report.get("deleted_logs") or [])
            if pruned:
                message = f"{message} (pruned {pruned} files)"
        except Exception:
            pass

    return RefreshResult(
        strategy=strategy,
        changed_files=changed_files,
        removed_files=removed_files,
        as_of=as_of,
        eval_passed=eval_passed,
        eval_report=eval_report,
        message=message,
    )


def _build_or_refresh_v2_multi_indexes(
    bundle: SkillBundle,
    *,
    sources_raw: list[Any],
    sources: list[dict[str, Any]],
    idx_entries: list[dict[str, Any]],
    run_evals: bool,
    dry_run: bool,
    force_rebuild: bool,
    generate_summaries: bool = False,
    summary_llm: str | None = None,
    summary_llm_model: str | None = None,
    summary_llm_timeout: int = 120,
) -> RefreshResult:
    manifest = bundle.manifest
    policy = bundle.policy

    budgets = policy.get("budgets") or {}
    max_changed_files_budget = budgets.get("max_changed_files")
    max_update_duration_seconds = budgets.get("max_update_duration_seconds")

    deadline: float | None = None
    if max_update_duration_seconds is not None:
        try:
            seconds = int(max_update_duration_seconds)
        except Exception:
            seconds = None
        if seconds is not None and seconds > 0:
            deadline = time.monotonic() + seconds

    update_strategy = policy.get("update_strategy") or {}
    default_strategy = update_strategy.get("default") or "incremental"
    if default_strategy not in ("incremental", "rebuild"):
        raise BuildError(f"Invalid policy.update_strategy.default: {default_strategy}")

    rebuild_thresholds = update_strategy.get("rebuild_thresholds") or {}
    changed_files_gt = rebuild_thresholds.get("changed_files_gt")
    if changed_files_gt is None:
        changed_files_gt = rebuild_thresholds.get("changed_files")
    threshold_changed_files = int(changed_files_gt) if changed_files_gt is not None else None
    days_since_full_rebuild_gt = rebuild_thresholds.get("days_since_full_rebuild_gt")

    git_timeout = GIT_TIMEOUT_SECONDS
    if deadline is not None:
        try:
            git_timeout = max(
                1, min(GIT_TIMEOUT_SECONDS, int(max_update_duration_seconds))
            )
        except Exception:
            pass

    def _collect_index_state(idx_entry: dict[str, Any]) -> dict[str, Any]:
        index_id = str(idx_entry.get("id") or "keyword-v1")
        index_dir = _resolve_index_dir(bundle.skill_root, idx_entry)
        backend = _index_backend(idx_entry)

        index_data_path = index_dir / "index_data.json"
        file_manifest_path = index_dir / "file_manifest.json"
        descriptor_path = index_dir / "index.json"
        chunks_path = index_dir / "chunks.jsonl"
        build_info_path = index_dir / "build_info.json"

        exists = index_data_path.exists()
        strategy = "rebuild" if not exists else default_strategy
        if force_rebuild:
            strategy = "rebuild"

        index_data_meta: dict | None = None
        if exists:
            try:
                if backend == "sqlite-fts":
                    index_data_meta = load_sqlite_fts_index(index_dir)
                elif backend == "vector":
                    index_data_meta = load_vector_index(index_dir)
                    if index_data_meta.get("format") != "vector-index-v1":
                        strategy = "rebuild"
                else:
                    index_data_meta = load_keyword_index(index_dir)
                    if index_data_meta.get("format") != "keyword-index-v2":     
                        strategy = "rebuild"
            except Exception:
                index_data_meta = None
                strategy = "rebuild"

        max_file_bytes_for_manifest = 512_000
        if isinstance(index_data_meta, dict):
            try:
                max_file_bytes_for_manifest = int(
                    (index_data_meta.get("config") or {}).get(
                        "max_file_bytes", max_file_bytes_for_manifest
                    )
                )
            except Exception:
                max_file_bytes_for_manifest = 512_000

        max_files_for_index = 20_000
        if isinstance(index_data_meta, dict):
            try:
                max_files_for_index = int(
                    (index_data_meta.get("config") or {}).get(
                        "max_files", max_files_for_index
                    )
                )
            except Exception:
                max_files_for_index = 20_000

        sqlite_cfg: dict[str, Any] = {}
        db_filename = "fts.sqlite"
        table = "chunks"
        if backend == "sqlite-fts" and isinstance(index_data_meta, dict):
            sqlite_cfg = (
                index_data_meta.get("sqlite")
                if isinstance(index_data_meta.get("sqlite"), dict)
                else {}
            )
            db_filename = str(sqlite_cfg.get("path") or db_filename)
            table = str(sqlite_cfg.get("table") or table)
        sqlite_path: Path | None = (
            (index_dir / db_filename) if backend == "sqlite-fts" else None      
        )

        vectors_path: Path | None = None
        if backend == "vector":
            vec_cfg_entry = (
                idx_entry.get("vector") if isinstance(idx_entry.get("vector"), dict) else {}
            )
            vec_cfg_data: dict[str, Any] = {}
            if isinstance(index_data_meta, dict):
                cfg = index_data_meta.get("config") if isinstance(index_data_meta.get("config"), dict) else {}
                vec_cfg_data = cfg.get("vector") if isinstance(cfg.get("vector"), dict) else {}
            vectors_rel = str(
                (vec_cfg_entry or {}).get("vectors_path")
                or (vec_cfg_data or {}).get("vectors_path")
                or "vectors.jsonl"
            )
            if not vectors_rel:
                vectors_rel = "vectors.jsonl"
            vectors_path = index_dir / vectors_rel

        old_file_manifests: dict[str, dict[str, dict[str, Any]]] = {}
        if file_manifest_path.exists():
            try:
                raw = read_json(file_manifest_path)
                if isinstance(raw, dict) and isinstance(raw.get("sources"), dict):
                    for sid, m in raw.get("sources", {}).items():
                        if isinstance(m, dict):
                            old_file_manifests[str(sid)] = m
                elif isinstance(raw, dict):
                    old_file_manifests[sources[0]["source_id"]] = raw
            except Exception:
                old_file_manifests = {}

        changes_by_source: dict[str, dict[str, list[str]]] = {
            s["source_id"]: {"changed_files": [], "removed_files": []} for s in sources
        }
        new_file_manifests: dict[str, dict[str, dict[str, Any]]] = {
            sid: dict(m) for sid, m in old_file_manifests.items()
        }

        if exists and strategy == "incremental":
            for s in sources:
                sid = s["source_id"]
                stype = s["type"]
                root: Path = s["root"]
                include = s["include"]
                exclude = s["exclude"]

                incremental_method = (update_strategy.get("incremental") or {}).get(
                    "method"
                )
                if not incremental_method:
                    incremental_method = (
                        (s.get("refresh") or {}).get("incremental") or {}
                    ).get("method")
                if not incremental_method:
                    incremental_method = (
                        "git-diff"
                        if (stype == "git" and is_git_repo(root))
                        else "file-manifest"
                    )

                if incremental_method == "git-diff" and stype == "git" and is_git_repo(
                    root
                ):
                    old_commit = (s.get("revision") or {}).get("commit")
                    if not old_commit or str(old_commit).lower() in ("head", "HEAD"):
                        strategy = "rebuild"
                        break
                    try:
                        changed, removed = git_changed_files(
                            root, str(old_commit), "HEAD", timeout=git_timeout
                        )
                    except Exception:
                        strategy = "rebuild"
                        break

                    changed = [p for p in changed if within_scope(p, include, exclude)]
                    removed = [p for p in removed if within_scope(p, include, exclude)]

                    changes_by_source[sid] = {
                        "changed_files": changed,
                        "removed_files": removed,
                    }

                    mf = dict(old_file_manifests.get(sid) or {})
                    for r in removed:
                        mf.pop(r, None)
                    for rel in changed:
                        abs_path = root / rel
                        if not abs_path.exists():
                            mf.pop(rel, None)
                            continue
                        try:
                            st = abs_path.stat()
                        except Exception:
                            continue
                        if st.st_size > max_file_bytes_for_manifest:
                            mf[rel] = {
                                "sha256": None,
                                "size": st.st_size,
                                "skipped": "too_large",
                            }
                            continue
                        if not looks_like_text(abs_path):
                            mf[rel] = {
                                "sha256": None,
                                "size": st.st_size,
                                "skipped": "binary_or_non_utf8",
                            }
                            continue
                        try:
                            mf[rel] = {
                                "sha256": sha256_text(read_text_file(abs_path)),
                                "size": st.st_size,
                                "skipped": None,
                            }
                        except Exception:
                            mf[rel] = {
                                "sha256": None,
                                "size": st.st_size,
                                "skipped": "read_error",
                            }

                    new_file_manifests[sid] = mf
                else:
                    old_manifest = old_file_manifests.get(sid) or {}
                    new_manifest = filesystem_manifest(
                        root,
                        include=include,
                        exclude=exclude,
                        max_file_bytes=max_file_bytes_for_manifest,
                        deadline=deadline,
                    )
                    changed, removed = diff_file_manifests(old_manifest, new_manifest)
                    changes_by_source[sid] = {
                        "changed_files": changed,
                        "removed_files": removed,
                    }
                    new_file_manifests[sid] = new_manifest

            changed_count = sum(
                len(v.get("changed_files", [])) + len(v.get("removed_files", []))
                for v in changes_by_source.values()
            )
            if threshold_changed_files is not None and changed_count > threshold_changed_files:
                strategy = "rebuild"

            if max_changed_files_budget is not None:
                try:
                    max_changed_files_int = int(max_changed_files_budget)
                except Exception:
                    max_changed_files_int = None
                if (
                    max_changed_files_int is not None
                    and max_changed_files_int >= 0
                    and changed_count > max_changed_files_int
                ):
                    strategy = "rebuild"

            if days_since_full_rebuild_gt is not None and index_data_meta is not None:
                try:
                    threshold_days = int(days_since_full_rebuild_gt)
                    created_at = index_data_meta.get("created_at")
                    if created_at:
                        created_dt = _dt.datetime.fromisoformat(
                            str(created_at).replace("Z", "+00:00")
                        )
                        now_dt = _dt.datetime.now(tz=_dt.timezone.utc)
                        if (now_dt - created_dt).days > threshold_days:
                            strategy = "rebuild"
                except Exception:
                    pass

        return {
            "entry": idx_entry,
            "index_id": index_id,
            "backend": backend,
            "index_dir": index_dir,
            "index_data_path": index_data_path,
            "file_manifest_path": file_manifest_path,
            "descriptor_path": descriptor_path,
            "chunks_path": chunks_path,
            "build_info_path": build_info_path,
            "sqlite_path": sqlite_path,
            "vectors_path": vectors_path,
            "sqlite_db_filename": db_filename,
            "sqlite_table": table,
            "exists": exists,
            "strategy": strategy,
            "index_data_meta": index_data_meta,
            "max_file_bytes": max_file_bytes_for_manifest,
            "max_files": max_files_for_index,
            "changes_by_source": changes_by_source,
            "new_file_manifests": new_file_manifests,
        }

    index_states = [_collect_index_state(idx) for idx in idx_entries]

    primary_state = index_states[0]
    primary_new_file_manifests = primary_state["new_file_manifests"]
    primary_max_file_bytes = int(primary_state["max_file_bytes"] or 512_000)

    as_of: dict[str, dict] = {}
    for s in sources:
        sid = s["source_id"]
        stype = s["type"]
        root: Path = s["root"]

        if is_git_repo(root) and stype == "git":
            as_of[sid] = git_head_revision(root, timeout=git_timeout)
            continue

        if sid not in primary_new_file_manifests:
            primary_new_file_manifests[sid] = filesystem_manifest(
                root,
                include=s["include"],
                exclude=s["exclude"],
                max_file_bytes=primary_max_file_bytes,
                deadline=deadline,
            )

        import hashlib
        import json as _json

        blob = _json.dumps(primary_new_file_manifests[sid], sort_keys=True).encode(
            "utf-8"
        )
        as_of[sid] = {"hash": hashlib.sha256(blob).hexdigest(), "timestamp": rfc3339_now()}

    def _changed_removed_for_state(state: dict[str, Any]) -> tuple[list[str], list[str]]:
        if state.get("strategy") == "rebuild":
            return ["<rebuild>"], []
        if not state.get("exists"):
            return [], []
        changed_files: list[str] = []
        removed_files: list[str] = []
        for sid, v in (state.get("changes_by_source") or {}).items():
            changed_files += [f"{sid}:{p}" for p in v.get("changed_files", [])]
            removed_files += [f"{sid}:{p}" for p in v.get("removed_files", [])]
        return changed_files, removed_files

    any_rebuild = any(s.get("strategy") == "rebuild" for s in index_states)
    strategies = {str(s.get("strategy") or "") for s in index_states}
    overall_strategy = strategies.pop() if len(strategies) == 1 else "mixed"

    if dry_run:
        changed_files: list[str] = []
        removed_files: list[str] = []
        if any_rebuild:
            changed_files = ["<rebuild>"]
        else:
            changed_set: set[str] = set()
            removed_set: set[str] = set()
            for st in index_states:
                ch, rm = _changed_removed_for_state(st)
                changed_set.update(ch)
                removed_set.update(rm)
            changed_files = sorted(changed_set)
            removed_files = sorted(removed_set)

        details = ", ".join(
            f"{str(s.get('index_id') or '<index>')}={str(s.get('strategy') or '')}"
            for s in index_states
        )
        return RefreshResult(
            strategy=overall_strategy,
            changed_files=changed_files,
            removed_files=removed_files,
            as_of=as_of,
            eval_passed=True,
            eval_report=None,
            message=f"dry_run: no changes applied (indexes: {details})",
        )

    ts = rfc3339_now().replace(":", "").replace("-", "")
    backup_manifest_path: Path | None = None

    backup_states: list[dict[str, Any]] = []
    for st in index_states:
        index_dir: Path = st["index_dir"]
        backup_dir = index_dir / ".backup"
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_index = backup_dir / f"index_data.{ts}.json"
        backup_manifest = backup_dir / f"EXPERT.{ts}.yaml"
        backup_file_manifest = backup_dir / f"file_manifest.{ts}.json"
        backup_descriptor = backup_dir / f"index.{ts}.json"
        backup_chunks = backup_dir / f"chunks.{ts}.jsonl"
        backup_build_info = backup_dir / f"build_info.{ts}.json"
        backup_sqlite = backup_dir / f"fts.{ts}.sqlite"
        backup_vectors = backup_dir / f"vectors.{ts}.jsonl"

        if backup_manifest_path is None:
            backup_manifest_path = backup_manifest

        write_yaml(backup_manifest, manifest)

        if st.get("exists"):
            shutil.copy(st["index_data_path"], backup_index)
            if Path(st["descriptor_path"]).exists():
                shutil.copy(st["descriptor_path"], backup_descriptor)
            if Path(st["file_manifest_path"]).exists():
                shutil.copy(st["file_manifest_path"], backup_file_manifest)
            if Path(st["chunks_path"]).exists():
                shutil.copy(st["chunks_path"], backup_chunks)
            if Path(st["build_info_path"]).exists():
                shutil.copy(st["build_info_path"], backup_build_info)
            sqlite_path = st.get("sqlite_path")
            if sqlite_path is not None and Path(sqlite_path).exists():
                shutil.copy(sqlite_path, backup_sqlite)
            vectors_path = st.get("vectors_path")
            if vectors_path is not None and Path(vectors_path).exists():
                shutil.copy(vectors_path, backup_vectors)

        backup_states.append(
            {
                "exists": bool(st.get("exists")),
                "index_data_path": st["index_data_path"],
                "file_manifest_path": st["file_manifest_path"],
                "descriptor_path": st["descriptor_path"],
                "chunks_path": st["chunks_path"],
                "build_info_path": st["build_info_path"],
                "sqlite_path": st.get("sqlite_path"),
                "vectors_path": st.get("vectors_path"),
                "backup_index": backup_index,
                "backup_file_manifest": backup_file_manifest,
                "backup_descriptor": backup_descriptor,
                "backup_chunks": backup_chunks,
                "backup_build_info": backup_build_info,
                "backup_sqlite": backup_sqlite,
                "backup_vectors": backup_vectors,
            }
        )

    def _rollback_all() -> None:
        try:
            if backup_manifest_path is not None and backup_manifest_path.exists():
                prior_manifest = read_yaml(backup_manifest_path)
                write_yaml(bundle.expert_yaml_path, prior_manifest)
        except Exception:
            pass

        for bs in backup_states:
            try:
                sqlite_path = bs.get("sqlite_path")
                vectors_path = bs.get("vectors_path")
                if bs.get("exists"):
                    shutil.copy(bs["backup_index"], bs["index_data_path"])
                    if bs["backup_descriptor"].exists():
                        shutil.copy(bs["backup_descriptor"], bs["descriptor_path"])
                    if bs["backup_file_manifest"].exists():
                        shutil.copy(bs["backup_file_manifest"], bs["file_manifest_path"])
                    if bs["backup_chunks"].exists():
                        shutil.copy(bs["backup_chunks"], bs["chunks_path"])
                    if bs["backup_build_info"].exists():
                        shutil.copy(bs["backup_build_info"], bs["build_info_path"])
                    if sqlite_path is not None:
                        if bs["backup_sqlite"].exists():
                            shutil.copy(bs["backup_sqlite"], sqlite_path)       
                        else:
                            Path(sqlite_path).unlink(missing_ok=True)
                    if vectors_path is not None:
                        if bs["backup_vectors"].exists():
                            shutil.copy(bs["backup_vectors"], vectors_path)
                        else:
                            Path(vectors_path).unlink(missing_ok=True)
                else:
                    Path(bs["index_data_path"]).unlink(missing_ok=True)
                    Path(bs["descriptor_path"]).unlink(missing_ok=True)
                    Path(bs["file_manifest_path"]).unlink(missing_ok=True)      
                    Path(bs["chunks_path"]).unlink(missing_ok=True)
                    Path(bs["build_info_path"]).unlink(missing_ok=True)
                    if sqlite_path is not None:
                        Path(sqlite_path).unlink(missing_ok=True)
                    if vectors_path is not None:
                        Path(vectors_path).unlink(missing_ok=True)
            except Exception:
                continue

    source_specs: list[SourceSpec] = []
    for s in sources:
        source_specs.append(
            SourceSpec(
                source_id=s["source_id"],
                source_type=s["type"],
                source_uri=s["uri"],
                source_root=s["root"],
                include=s["include"],
                exclude=s["exclude"],
                revision=as_of.get(s["source_id"], {}),
                classification=s.get("classification"),
                license=s.get("license"),
            )
        )

    index_results: list[dict[str, Any]] = []
    try:
        for st in index_states:
            idx_entry = st["entry"]
            index_id = st["index_id"]
            index_dir: Path = st["index_dir"]
            backend = st["backend"]
            max_file_bytes_for_manifest = int(st["max_file_bytes"] or 512_000)
            max_files_for_index = int(st["max_files"] or 20_000)
            strategy = str(st.get("strategy") or "rebuild")

            chunking_cfg = idx_entry.get("chunking") or {}
            try:
                chunk_max_chars = int(chunking_cfg.get("max_chars") or 4000)
            except Exception:
                chunk_max_chars = 4000
            try:
                chunk_overlap_chars = int(chunking_cfg.get("overlap_chars") or 200)
            except Exception:
                chunk_overlap_chars = 200
            chunk_max_chars = max(1, min(chunk_max_chars, max_file_bytes_for_manifest))
            chunk_overlap_chars = max(0, min(chunk_overlap_chars, chunk_max_chars - 1))

            if strategy == "rebuild":
                if backend == "sqlite-fts":
                    build_sqlite_fts_index_multi(
                        index_id=index_id,
                        sources=source_specs,
                        out_dir=index_dir,
                        max_file_bytes=max_file_bytes_for_manifest,
                        max_files=max_files_for_index,
                        chunk_max_chars=chunk_max_chars,
                        chunk_overlap_chars=chunk_overlap_chars,
                        deadline=deadline,
                        created_at=rfc3339_now(),
                        db_filename=str(st.get("sqlite_db_filename") or "fts.sqlite"),
                        table=str(st.get("sqlite_table") or "chunks"),
                    )
                elif backend == "vector":
                    embedding_cfg = (
                        idx_entry.get("embedding")
                        if isinstance(idx_entry.get("embedding"), dict)
                        else None
                    )
                    vector_cfg = (
                        idx_entry.get("vector")
                        if isinstance(idx_entry.get("vector"), dict)
                        else None
                    )
                    build_vector_index_multi(
                        index_id=index_id,
                        sources=source_specs,
                        out_dir=index_dir,
                        max_file_bytes=max_file_bytes_for_manifest,
                        max_files=max_files_for_index,
                        chunk_max_chars=chunk_max_chars,
                        chunk_overlap_chars=chunk_overlap_chars,
                        embedding=embedding_cfg,
                        vector=vector_cfg,
                        deadline=deadline,
                        created_at=rfc3339_now(),
                    )
                else:
                    build_keyword_index_multi(
                        index_id=index_id,
                        sources=source_specs,
                        out_dir=index_dir,
                        max_file_bytes=max_file_bytes_for_manifest,
                        max_files=max_files_for_index,
                        chunk_max_chars=chunk_max_chars,
                        chunk_overlap_chars=chunk_overlap_chars,
                        deadline=deadline,
                        created_at=rfc3339_now(),
                    )
                changed_files, removed_files = ["<rebuild>"], []
            else:
                if backend == "sqlite-fts":
                    index_data = load_sqlite_fts_index(index_dir)
                    incremental_update_sqlite_fts_index_multi(
                        index_dir=index_dir,
                        index_data=index_data,
                        sources=source_specs,
                        changes=st["changes_by_source"],
                        file_manifests=st["new_file_manifests"],
                        max_file_bytes=max_file_bytes_for_manifest,
                        deadline=deadline,
                    )
                elif backend == "vector":
                    index_data = load_vector_index(index_dir)
                    incremental_update_vector_index_multi(
                        index_dir=index_dir,
                        index_data=index_data,
                        sources=source_specs,
                        changes=st["changes_by_source"],
                        file_manifests=st["new_file_manifests"],
                        max_file_bytes=max_file_bytes_for_manifest,
                        deadline=deadline,
                    )
                else:
                    index_data = load_keyword_index(index_dir)
                    incremental_update_keyword_index_multi(
                        index_dir=index_dir,
                        index_data=index_data,
                        sources=source_specs,
                        changes=st["changes_by_source"],
                        file_manifests=st["new_file_manifests"],
                        max_file_bytes=max_file_bytes_for_manifest,
                        deadline=deadline,
                    )
                changed_files, removed_files = _changed_removed_for_state(st)

            index_results.append(
                {
                    "index_id": index_id,
                    "backend": backend,
                    "path": str(idx_entry.get("path") or ""),
                    "strategy": strategy,
                    "changed_files": changed_files,
                    "removed_files": removed_files,
                }
            )

        for s in sources_raw:
            if not isinstance(s, dict):
                continue
            sid = str(s.get("source_id") or "")
            if sid and sid in as_of:
                s["revision"] = as_of[sid]
        manifest["sources"] = sources_raw
        write_yaml(bundle.expert_yaml_path, manifest)
    except BuildError:
        _rollback_all()
        raise
    except Exception as e:
        _rollback_all()
        raise BuildError(str(e)) from e

    eval_passed = True
    eval_report: dict | None = None
    if run_evals:
        try:
            from .evals import run_eval_suites

            suites_to_run = (policy.get("validation") or {}).get("eval_suites") or []
            eval_report = run_eval_suites(bundle, suite_ids=suites_to_run)
            eval_passed = bool(eval_report.get("passed", False))
        except Exception as e:
            eval_passed = False
            eval_report = {"passed": False, "error": str(e)}

    validation = policy.get("validation") or {}
    fail_action = validation.get("fail_action", "block")
    if fail_action not in ("block", "warn", "rollback"):
        raise BuildError(f"Invalid policy.validation.fail_action: {fail_action}")

    publishing = policy.get("publishing") or {}
    rollback_on_fail = bool(publishing.get("rollback_on_fail", True))
    on_pass = publishing.get("on_pass", "auto_publish")
    if on_pass not in ("auto_publish", "require_approval"):
        raise BuildError(f"Invalid policy.publishing.on_pass: {on_pass}")

    operation = "build" if any(not bool(s.get("exists")) for s in index_states) else "refresh"
    rolled_back = False

    if not eval_passed:
        if fail_action == "warn":
            message = f"{operation} failed evals (fail_action=warn); changes left in place."
        else:
            should_rollback = fail_action == "rollback" or (
                fail_action == "block" and rollback_on_fail
            )
            if should_rollback:
                _rollback_all()
                rolled_back = True
                message = f"{operation} failed evals; rolled back (fail_action={fail_action})."
            else:
                message = f"{operation} failed evals (fail_action={fail_action}); changes left in place."
    else:
        message = f"{operation} succeeded."
        if on_pass == "require_approval":
            message = f"{operation} succeeded; publishing requires approval."

    if any_rebuild:
        changed_files = ["<rebuild>"]
        removed_files = []
    else:
        changed_set: set[str] = set()
        removed_set: set[str] = set()
        for r in index_results:
            for p in r.get("changed_files", []) or []:
                changed_set.add(str(p))
            for p in r.get("removed_files", []) or []:
                removed_set.add(str(p))
        changed_files = sorted(changed_set)
        removed_files = sorted(removed_set)

    logs_root = bundle.skill_root / "expert" / "logs"
    raw_logs_cfg = manifest.get("logs")
    has_logs_cfg = isinstance(raw_logs_cfg, dict)
    logs_cfg = raw_logs_cfg if has_logs_cfg else {}
    logs_enabled = bool(logs_cfg.get("enabled", False)) or (
        (not has_logs_cfg) and logs_root.exists()
    )
    if logs_enabled:
        log_dir = logs_root / "updates"
        day = rfc3339_now()[:10]
        log_path = log_dir / f"{day}.jsonl"
        append_jsonl(
            log_path,
            {
                "timestamp": rfc3339_now(),
                "operation": operation,
                "strategy": overall_strategy,
                "changed_files": changed_files,
                "removed_files": removed_files,
                "as_of": as_of,
                "eval_report": eval_report,
                "fail_action": fail_action,
                "rollback_on_fail": rollback_on_fail,
                "rolled_back": rolled_back,
                "publish": on_pass,
                "message": message,
                "indexes": index_results,
            },
        )

    # Generate summaries if requested
    summary_result = None
    if generate_summaries and summary_llm and summary_llm != "none":
        try:
            from .summary_generator import generate_summaries as gen_summaries

            summary_result = gen_summaries(
                skill_root=bundle.skill_root,
                bundle=bundle,
                llm=summary_llm,
                llm_model=summary_llm_model,
                llm_timeout_seconds=summary_llm_timeout,
                dry_run=dry_run,
            )
            if summary_result.generated:
                message = f"{message}; summaries generated: {len(summary_result.generated)}"
            if summary_result.failed:
                message = f"{message}; summary failures: {len(summary_result.failed)}"
        except Exception as e:
            message = f"{message}; summary generation error: {e}"

    return RefreshResult(
        strategy=overall_strategy,
        changed_files=changed_files,
        removed_files=removed_files,
        as_of=as_of,
        eval_passed=eval_passed,
        eval_report=eval_report,
        message=message,
    )


def _build_or_refresh_v2(
    bundle: SkillBundle,
    *,
    run_evals: bool,
    dry_run: bool,
    force_rebuild: bool,
    generate_summaries: bool = False,
    summary_llm: str | None = None,
    summary_llm_model: str | None = None,
    summary_llm_timeout: int = 120,
) -> RefreshResult:
    manifest = bundle.manifest
    policy = bundle.policy

    sources_raw = manifest.get("sources") or []
    if not isinstance(sources_raw, list) or not sources_raw:
        raise BuildError("EXPERT.yaml must declare at least one source in sources[].")

    security = manifest.get("security") or {}
    classification = security.get("classification")
    license = security.get("license")

    sources: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for i, s in enumerate(sources_raw):
        if not isinstance(s, dict):
            continue
        source_id = str(s.get("source_id") or f"source{i}")
        if source_id in seen_ids:
            raise BuildError(f"Duplicate source_id in EXPERT.yaml sources[]: {source_id}")
        seen_ids.add(source_id)

        source_type = str(s.get("type") or "filesystem")
        source_uri = s.get("uri")
        if not source_uri:
            raise BuildError(f"Source '{source_id}' missing required uri.")
        source_root = parse_file_uri(str(source_uri), base_dir=bundle.skill_root)

        scope = s.get("scope") or {}
        include = scope.get("include") or ["**/*"]
        exclude = scope.get("exclude") or []

        sources.append(
            {
                "source_id": source_id,
                "type": source_type,
                "uri": str(source_uri),
                "classification": s.get("classification") or classification,
                "license": s.get("license") or license,
                "root": source_root,
                "include": list(include),
                "exclude": list(exclude),
                "refresh": s.get("refresh") or {},
                "revision": s.get("revision") or {},
            }
        )

    idx_entries = _get_indexes(manifest)
    if not idx_entries:
        as_of = {s["source_id"]: (s.get("revision") or {}) for s in sources}

        eval_passed = True
        eval_report: dict | None = None
        if run_evals:
            try:
                from .evals import run_eval_suites

                suites_to_run = (policy.get("validation") or {}).get("eval_suites") or []
                eval_report = run_eval_suites(bundle, suite_ids=suites_to_run)
                eval_passed = bool(eval_report.get("passed", False))
            except Exception as e:
                eval_passed = False
                eval_report = {"passed": False, "error": str(e)}

        message = "No indexes configured; build/refresh is a no-op for summaries-only packs."

        logs_root = bundle.skill_root / "expert" / "logs"
        raw_logs_cfg = manifest.get("logs")
        has_logs_cfg = isinstance(raw_logs_cfg, dict)
        logs_cfg = raw_logs_cfg if has_logs_cfg else {}
        logs_enabled = bool(logs_cfg.get("enabled", False)) or (
            (not has_logs_cfg) and logs_root.exists()
        )
        if logs_enabled:
            log_dir = logs_root / "updates"
            day = rfc3339_now()[:10]
            append_jsonl(
                log_dir / f"{day}.jsonl",
                {
                    "timestamp": rfc3339_now(),
                    "operation": "refresh",
                    "strategy": "noop",
                    "changed_files": [],
                    "removed_files": [],
                    "as_of": as_of,
                    "eval_report": eval_report,
                    "message": message,
                },
            )

        return RefreshResult(
            strategy="noop",
            changed_files=[],
            removed_files=[],
            as_of=as_of,
            eval_passed=eval_passed,
            eval_report=eval_report,
            message=message,
        )

    if len(idx_entries) > 1:
        return _build_or_refresh_v2_multi_indexes(
            bundle,
            sources_raw=sources_raw,
            sources=sources,
            idx_entries=idx_entries,
            run_evals=run_evals,
            dry_run=dry_run,
            force_rebuild=force_rebuild,
            generate_summaries=generate_summaries,
            summary_llm=summary_llm,
            summary_llm_model=summary_llm_model,
            summary_llm_timeout=summary_llm_timeout,
        )

    primary_idx_entry = idx_entries[0]
    index_id = primary_idx_entry.get("id", "keyword-v1")
    index_dir = _resolve_index_dir(bundle.skill_root, primary_idx_entry)
    backend = _index_backend(primary_idx_entry)

    budgets = policy.get("budgets") or {}
    max_changed_files_budget = budgets.get("max_changed_files")
    max_update_duration_seconds = budgets.get("max_update_duration_seconds")

    deadline: float | None = None
    if max_update_duration_seconds is not None:
        try:
            seconds = int(max_update_duration_seconds)
        except Exception:
            seconds = None
        if seconds is not None and seconds > 0:
            deadline = time.monotonic() + seconds

    update_strategy = policy.get("update_strategy") or {}
    default_strategy = update_strategy.get("default") or "incremental"
    if default_strategy not in ("incremental", "rebuild"):
        raise BuildError(f"Invalid policy.update_strategy.default: {default_strategy}")

    rebuild_thresholds = update_strategy.get("rebuild_thresholds") or {}
    changed_files_gt = rebuild_thresholds.get("changed_files_gt")
    if changed_files_gt is None:
        changed_files_gt = rebuild_thresholds.get("changed_files")
    threshold_changed_files = int(changed_files_gt) if changed_files_gt is not None else None
    days_since_full_rebuild_gt = rebuild_thresholds.get("days_since_full_rebuild_gt")

    git_timeout = GIT_TIMEOUT_SECONDS
    if deadline is not None:
        try:
            git_timeout = max(1, min(GIT_TIMEOUT_SECONDS, int(max_update_duration_seconds)))
        except Exception:
            pass

    index_data_path = index_dir / "index_data.json"
    file_manifest_path = index_dir / "file_manifest.json"
    descriptor_path = index_dir / "index.json"
    chunks_path = index_dir / "chunks.jsonl"
    build_info_path = index_dir / "build_info.json"

    exists = index_data_path.exists()
    strategy = "rebuild" if not exists else default_strategy
    if force_rebuild:
        strategy = "rebuild"

    index_data_meta: dict | None = None
    if exists:
        try:
            if backend == "sqlite-fts":
                index_data_meta = load_sqlite_fts_index(index_dir)
            elif backend == "vector":
                index_data_meta = load_vector_index(index_dir)
                if index_data_meta.get("format") != "vector-index-v1":
                    strategy = "rebuild"
            else:
                index_data_meta = load_keyword_index(index_dir)
                if index_data_meta.get("format") != "keyword-index-v2":
                    strategy = "rebuild"
        except Exception:
            index_data_meta = None
            strategy = "rebuild"

    max_file_bytes_for_manifest = 512_000
    if isinstance(index_data_meta, dict):
        try:
            max_file_bytes_for_manifest = int((index_data_meta.get("config") or {}).get("max_file_bytes", max_file_bytes_for_manifest))
        except Exception:
            max_file_bytes_for_manifest = 512_000

    sqlite_path: Path | None = None
    if backend == "sqlite-fts":
        db_filename = "fts.sqlite"
        if isinstance(index_data_meta, dict):
            sqlite_cfg = index_data_meta.get("sqlite") if isinstance(index_data_meta.get("sqlite"), dict) else {}
            db_filename = str(sqlite_cfg.get("path") or db_filename)
        sqlite_path = index_dir / db_filename

    vectors_path: Path | None = None
    if backend == "vector":
        vectors_rel = "vectors.jsonl"
        if isinstance(primary_idx_entry.get("vector"), dict):
            vectors_rel = str(primary_idx_entry.get("vector", {}).get("vectors_path") or vectors_rel)
        if isinstance(index_data_meta, dict):
            cfg = index_data_meta.get("config") if isinstance(index_data_meta.get("config"), dict) else {}
            if isinstance(cfg.get("vector"), dict):
                vectors_rel = str(cfg.get("vector", {}).get("vectors_path") or vectors_rel)
        if not vectors_rel:
            vectors_rel = "vectors.jsonl"
        vectors_path = index_dir / vectors_rel

    max_files_for_index = 20_000
    if isinstance(index_data_meta, dict):
        try:
            max_files_for_index = int((index_data_meta.get("config") or {}).get("max_files", max_files_for_index))
        except Exception:
            max_files_for_index = 20_000

    old_file_manifests: dict[str, dict[str, dict[str, Any]]] = {}
    if file_manifest_path.exists():
        try:
            raw = read_json(file_manifest_path)
            if isinstance(raw, dict) and isinstance(raw.get("sources"), dict):
                for sid, m in raw.get("sources", {}).items():
                    if isinstance(m, dict):
                        old_file_manifests[str(sid)] = m
            elif isinstance(raw, dict):
                old_file_manifests[sources[0]["source_id"]] = raw
        except Exception:
            old_file_manifests = {}

    changes_by_source: dict[str, dict[str, list[str]]] = {s["source_id"]: {"changed_files": [], "removed_files": []} for s in sources}
    new_file_manifests: dict[str, dict[str, dict[str, Any]]] = {sid: dict(m) for sid, m in old_file_manifests.items()}

    if exists and strategy == "incremental":
        for s in sources:
            sid = s["source_id"]
            stype = s["type"]
            root: Path = s["root"]
            include = s["include"]
            exclude = s["exclude"]

            incremental_method = (update_strategy.get("incremental") or {}).get("method")
            if not incremental_method:
                incremental_method = ((s.get("refresh") or {}).get("incremental") or {}).get("method")
            if not incremental_method:
                incremental_method = "git-diff" if (stype == "git" and is_git_repo(root)) else "file-manifest"

            if incremental_method == "git-diff" and stype == "git" and is_git_repo(root):
                old_commit = (s.get("revision") or {}).get("commit")
                if not old_commit or str(old_commit).lower() in ("head", "HEAD"):
                    strategy = "rebuild"
                    break
                try:
                    changed, removed = git_changed_files(root, str(old_commit), "HEAD", timeout=git_timeout)
                except Exception:
                    strategy = "rebuild"
                    break

                changed = [p for p in changed if within_scope(p, include, exclude)]
                removed = [p for p in removed if within_scope(p, include, exclude)]

                changes_by_source[sid] = {"changed_files": changed, "removed_files": removed}

                mf = dict(old_file_manifests.get(sid) or {})
                for r in removed:
                    mf.pop(r, None)
                for rel in changed:
                    abs_path = root / rel
                    if not abs_path.exists():
                        mf.pop(rel, None)
                        continue
                    try:
                        st = abs_path.stat()
                    except Exception:
                        continue
                    if st.st_size > max_file_bytes_for_manifest:
                        mf[rel] = {"sha256": None, "size": st.st_size, "skipped": "too_large"}
                        continue
                    if not looks_like_text(abs_path):
                        mf[rel] = {"sha256": None, "size": st.st_size, "skipped": "binary_or_non_utf8"}
                        continue
                    try:
                        mf[rel] = {
                            "sha256": sha256_text(read_text_file(abs_path)),
                            "size": st.st_size,
                            "skipped": None,
                        }
                    except Exception:
                        mf[rel] = {"sha256": None, "size": st.st_size, "skipped": "read_error"}

                new_file_manifests[sid] = mf
            else:
                old_manifest = old_file_manifests.get(sid) or {}
                new_manifest = filesystem_manifest(
                    root,
                    include=include,
                    exclude=exclude,
                    max_file_bytes=max_file_bytes_for_manifest,
                    deadline=deadline,
                )
                changed, removed = diff_file_manifests(old_manifest, new_manifest)
                changes_by_source[sid] = {"changed_files": changed, "removed_files": removed}
                new_file_manifests[sid] = new_manifest

        changed_count = sum(
            len(v.get("changed_files", [])) + len(v.get("removed_files", [])) for v in changes_by_source.values()
        )
        if threshold_changed_files is not None and changed_count > threshold_changed_files:
            strategy = "rebuild"

        if max_changed_files_budget is not None:
            try:
                max_changed_files_int = int(max_changed_files_budget)
            except Exception:
                max_changed_files_int = None
            if max_changed_files_int is not None and max_changed_files_int >= 0 and changed_count > max_changed_files_int:
                strategy = "rebuild"

        if days_since_full_rebuild_gt is not None and index_data_meta is not None:
            try:
                threshold_days = int(days_since_full_rebuild_gt)
                created_at = index_data_meta.get("created_at")
                if created_at:
                    created_dt = _dt.datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
                    now_dt = _dt.datetime.now(tz=_dt.timezone.utc)
                    if (now_dt - created_dt).days > threshold_days:
                        strategy = "rebuild"
            except Exception:
                pass

    as_of: dict[str, dict] = {}
    for s in sources:
        sid = s["source_id"]
        stype = s["type"]
        root: Path = s["root"]

        if is_git_repo(root) and stype == "git":
            as_of[sid] = git_head_revision(root, timeout=git_timeout)
            continue

        if sid not in new_file_manifests:
            new_file_manifests[sid] = filesystem_manifest(
                root,
                include=s["include"],
                exclude=s["exclude"],
                max_file_bytes=max_file_bytes_for_manifest,
                deadline=deadline,
            )
        import hashlib
        import json as _json

        blob = _json.dumps(new_file_manifests[sid], sort_keys=True).encode("utf-8")
        as_of[sid] = {"hash": hashlib.sha256(blob).hexdigest(), "timestamp": rfc3339_now()}

    if dry_run:
        changed_files = []
        removed_files = []
        if strategy == "rebuild":
            changed_files = ["<rebuild>"]
        elif exists:
            for sid, v in changes_by_source.items():
                changed_files += [f"{sid}:{p}" for p in v.get("changed_files", [])]
                removed_files += [f"{sid}:{p}" for p in v.get("removed_files", [])]
        return RefreshResult(
            strategy=strategy,
            changed_files=changed_files,
            removed_files=removed_files,
            as_of=as_of,
            eval_passed=True,
            eval_report=None,
            message="dry_run: no changes applied",
        )

    backup_dir = index_dir / ".backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = rfc3339_now().replace(":", "").replace("-", "")
    backup_index = backup_dir / f"index_data.{ts}.json"
    backup_manifest = backup_dir / f"EXPERT.{ts}.yaml"
    backup_file_manifest = backup_dir / f"file_manifest.{ts}.json"
    backup_descriptor = backup_dir / f"index.{ts}.json"
    backup_chunks = backup_dir / f"chunks.{ts}.jsonl"
    backup_build_info = backup_dir / f"build_info.{ts}.json"
    backup_sqlite = backup_dir / f"fts.{ts}.sqlite"

    write_yaml(backup_manifest, manifest)
    if exists:
        shutil.copy(index_data_path, backup_index)
        if descriptor_path.exists():
            shutil.copy(descriptor_path, backup_descriptor)
        if file_manifest_path.exists():
            shutil.copy(file_manifest_path, backup_file_manifest)
        if chunks_path.exists():
            shutil.copy(chunks_path, backup_chunks)
        if build_info_path.exists():
            shutil.copy(build_info_path, backup_build_info)
        if sqlite_path is not None and sqlite_path.exists():
            shutil.copy(sqlite_path, backup_sqlite)

    chunking_cfg = primary_idx_entry.get("chunking") or {}
    try:
        chunk_max_chars = int(chunking_cfg.get("max_chars") or 4000)
    except Exception:
        chunk_max_chars = 4000
    try:
        chunk_overlap_chars = int(chunking_cfg.get("overlap_chars") or 200)
    except Exception:
        chunk_overlap_chars = 200
    chunk_max_chars = max(1, min(chunk_max_chars, max_file_bytes_for_manifest))
    chunk_overlap_chars = max(0, min(chunk_overlap_chars, chunk_max_chars - 1))

    source_specs: list[SourceSpec] = []
    for s in sources:
        source_specs.append(
            SourceSpec(
                source_id=s["source_id"],
                source_type=s["type"],
                source_uri=s["uri"],
                source_root=s["root"],
                include=s["include"],
                exclude=s["exclude"],
                revision=as_of.get(s["source_id"], {}),
                classification=s.get("classification"),
                license=s.get("license"),
            )
        )

    if strategy == "rebuild":
        if backend == "sqlite-fts":
            build_sqlite_fts_index_multi(
                index_id=index_id,
                sources=source_specs,
                out_dir=index_dir,
                max_file_bytes=max_file_bytes_for_manifest,
                max_files=max_files_for_index,
                chunk_max_chars=chunk_max_chars,
                chunk_overlap_chars=chunk_overlap_chars,
                deadline=deadline,
                created_at=rfc3339_now(),
            )
        elif backend == "vector":
            embedding_cfg = (
                primary_idx_entry.get("embedding")
                if isinstance(primary_idx_entry.get("embedding"), dict)
                else None
            )
            vector_cfg = (
                primary_idx_entry.get("vector")
                if isinstance(primary_idx_entry.get("vector"), dict)
                else None
            )
            build_vector_index_multi(
                index_id=index_id,
                sources=source_specs,
                out_dir=index_dir,
                max_file_bytes=max_file_bytes_for_manifest,
                max_files=max_files_for_index,
                chunk_max_chars=chunk_max_chars,
                chunk_overlap_chars=chunk_overlap_chars,
                embedding=embedding_cfg,
                vector=vector_cfg,
                deadline=deadline,
                created_at=rfc3339_now(),
            )
        else:
            build_keyword_index_multi(
                index_id=index_id,
                sources=source_specs,
                out_dir=index_dir,
                max_file_bytes=max_file_bytes_for_manifest,
                chunk_max_chars=chunk_max_chars,
                chunk_overlap_chars=chunk_overlap_chars,
                deadline=deadline,
                created_at=rfc3339_now(),
            )
        changed_files = ["<rebuild>"]
        removed_files = []
    else:
        if backend == "sqlite-fts":
            index_data = load_sqlite_fts_index(index_dir)
            incremental_update_sqlite_fts_index_multi(
                index_dir=index_dir,
                index_data=index_data,
                sources=source_specs,
                changes=changes_by_source,
                file_manifests=new_file_manifests,
                max_file_bytes=max_file_bytes_for_manifest,
                deadline=deadline,
            )
        elif backend == "vector":
            index_data = load_vector_index(index_dir)
            incremental_update_vector_index_multi(
                index_dir=index_dir,
                index_data=index_data,
                sources=source_specs,
                changes=changes_by_source,
                file_manifests=new_file_manifests,
                max_file_bytes=max_file_bytes_for_manifest,
                deadline=deadline,
            )
        else:
            index_data = load_keyword_index(index_dir)
            incremental_update_keyword_index_multi(
                index_dir=index_dir,
                index_data=index_data,
                sources=source_specs,
                changes=changes_by_source,
                file_manifests=new_file_manifests,
                max_file_bytes=max_file_bytes_for_manifest,
                deadline=deadline,
            )
        changed_files = []
        removed_files = []
        for sid, v in changes_by_source.items():
            changed_files += [f"{sid}:{p}" for p in v.get("changed_files", [])]
            removed_files += [f"{sid}:{p}" for p in v.get("removed_files", [])]

    for s in sources_raw:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("source_id") or "")
        if sid and sid in as_of:
            s["revision"] = as_of[sid]
    manifest["sources"] = sources_raw
    write_yaml(bundle.expert_yaml_path, manifest)

    eval_passed = True
    eval_report: dict | None = None
    if run_evals:
        try:
            from .evals import run_eval_suites

            suites_to_run = (policy.get("validation") or {}).get("eval_suites") or []
            eval_report = run_eval_suites(bundle, suite_ids=suites_to_run)
            eval_passed = bool(eval_report.get("passed", False))
        except Exception as e:
            eval_passed = False
            eval_report = {"passed": False, "error": str(e)}

    validation = policy.get("validation") or {}
    fail_action = validation.get("fail_action", "block")
    if fail_action not in ("block", "warn", "rollback"):
        raise BuildError(f"Invalid policy.validation.fail_action: {fail_action}")

    publishing = policy.get("publishing") or {}
    rollback_on_fail = bool(publishing.get("rollback_on_fail", True))
    on_pass = publishing.get("on_pass", "auto_publish")
    if on_pass not in ("auto_publish", "require_approval"):
        raise BuildError(f"Invalid policy.publishing.on_pass: {on_pass}")

    operation = "build" if not exists else "refresh"
    rolled_back = False

    if not eval_passed:
        if fail_action == "warn":
            message = f"{operation} failed evals (fail_action=warn); changes left in place."
        else:
            should_rollback = fail_action == "rollback" or (fail_action == "block" and rollback_on_fail)
            if should_rollback:
                prior_manifest = read_yaml(backup_manifest)
                write_yaml(bundle.expert_yaml_path, prior_manifest)

                if exists:
                    shutil.copy(backup_index, index_data_path)
                    if backup_descriptor.exists():
                        shutil.copy(backup_descriptor, descriptor_path)
                    if backup_file_manifest.exists():
                        shutil.copy(backup_file_manifest, file_manifest_path)
                    if backup_chunks.exists():
                        shutil.copy(backup_chunks, chunks_path)
                    if backup_build_info.exists():
                        shutil.copy(backup_build_info, build_info_path)
                    if sqlite_path is not None:
                        if backup_sqlite.exists():
                            shutil.copy(backup_sqlite, sqlite_path)
                        else:
                            sqlite_path.unlink(missing_ok=True)
                    if vectors_path is not None:
                        if backup_vectors.exists():
                            shutil.copy(backup_vectors, vectors_path)
                        else:
                            vectors_path.unlink(missing_ok=True)
                else:
                    index_data_path.unlink(missing_ok=True)
                    descriptor_path.unlink(missing_ok=True)
                    file_manifest_path.unlink(missing_ok=True)
                    chunks_path.unlink(missing_ok=True)
                    build_info_path.unlink(missing_ok=True)
                    if sqlite_path is not None:
                        sqlite_path.unlink(missing_ok=True)
                    if vectors_path is not None:
                        vectors_path.unlink(missing_ok=True)

                rolled_back = True
                message = f"{operation} failed evals; rolled back (fail_action={fail_action})."
            else:
                message = f"{operation} failed evals (fail_action={fail_action}); changes left in place."
    else:
        message = f"{operation} succeeded."
        if on_pass == "require_approval":
            message = f"{operation} succeeded; publishing requires approval."

    logs_root = bundle.skill_root / "expert" / "logs"
    raw_logs_cfg = manifest.get("logs")
    has_logs_cfg = isinstance(raw_logs_cfg, dict)
    logs_cfg = raw_logs_cfg if has_logs_cfg else {}
    logs_enabled = bool(logs_cfg.get("enabled", False)) or (
        (not has_logs_cfg) and logs_root.exists()
    )
    if logs_enabled:
        log_dir = logs_root / "updates"
        day = rfc3339_now()[:10]
        log_path = log_dir / f"{day}.jsonl"
        append_jsonl(
            log_path,
            {
                "timestamp": rfc3339_now(),
                "operation": operation,
                "strategy": strategy,
                "changed_files": changed_files,
                "removed_files": removed_files,
                "as_of": as_of,
                "eval_report": eval_report,
                "fail_action": fail_action,
                "rollback_on_fail": rollback_on_fail,
                "rolled_back": rolled_back,
                "publish": on_pass,
                "message": message,
            },
        )

    # Generate summaries if requested
    summary_result = None
    if generate_summaries and summary_llm and summary_llm != "none":
        try:
            from .summary_generator import generate_summaries as gen_summaries

            summary_result = gen_summaries(
                skill_root=bundle.skill_root,
                bundle=bundle,
                llm=summary_llm,
                llm_model=summary_llm_model,
                llm_timeout_seconds=summary_llm_timeout,
                dry_run=dry_run,
            )
            if summary_result.generated:
                message = f"{message}; summaries generated: {len(summary_result.generated)}"
            if summary_result.failed:
                message = f"{message}; summary failures: {len(summary_result.failed)}"
        except Exception as e:
            message = f"{message}; summary generation error: {e}"

    return RefreshResult(
        strategy=strategy,
        changed_files=changed_files,
        removed_files=removed_files,
        as_of=as_of,
        eval_passed=eval_passed,
        eval_report=eval_report,
        message=message,
    )
