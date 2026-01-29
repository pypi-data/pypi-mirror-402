from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path
from typing import Any

from .errors import ECPError
from .skill_loader import SkillBundle, load_skill_bundle

_BACKUP_TS_RE = re.compile(r"^[^.]+\.(\d{8}T\d{6}Z)\..+$")


def _utcnow() -> _dt.datetime:
    return _dt.datetime.now(tz=_dt.timezone.utc)


def _parse_backup_ts(ts: str) -> _dt.datetime | None:
    try:
        dt = _dt.datetime.strptime(ts, "%Y%m%dT%H%M%SZ")
    except Exception:
        return None
    return dt.replace(tzinfo=_dt.timezone.utc)


def _parse_log_date(name: str) -> _dt.date | None:
    stem = Path(name).stem
    try:
        return _dt.date.fromisoformat(stem)
    except Exception:
        return None


def _prune_backup_dir(
    backup_dir: Path,
    *,
    max_backups: int | None,
    max_age_days: int | None,
    dry_run: bool,
) -> list[Path]:
    if not backup_dir.exists() or not backup_dir.is_dir():
        return []

    groups: dict[str, list[Path]] = {}
    ungrouped: list[Path] = []
    for p in backup_dir.iterdir():
        if not p.is_file():
            continue
        m = _BACKUP_TS_RE.match(p.name)
        if not m:
            ungrouped.append(p)
            continue
        ts = m.group(1)
        groups.setdefault(ts, []).append(p)

    now = _utcnow()
    ts_sorted = sorted(groups.keys(), reverse=True)
    keep_ts: set[str] = set(ts_sorted)

    if max_backups is not None:
        keep_ts = set(ts_sorted[: max(0, int(max_backups))])

    if max_age_days is not None:
        try:
            days = int(max_age_days)
        except Exception:
            days = 0
        if days >= 0:
            cutoff = now - _dt.timedelta(days=days)
            for ts in list(keep_ts):
                dt = _parse_backup_ts(ts)
                if dt is not None and dt < cutoff:
                    keep_ts.discard(ts)

    to_delete: list[Path] = []
    for ts, paths in groups.items():
        if ts in keep_ts:
            continue
        to_delete.extend(paths)

    if not dry_run:
        for p in to_delete:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                continue

    return sorted(to_delete)


def _prune_logs_dir(log_dir: Path, *, prune_after_days: int | None, dry_run: bool) -> list[Path]:
    if prune_after_days is None:
        return []
    if not log_dir.exists() or not log_dir.is_dir():
        return []

    try:
        days = int(prune_after_days)
    except Exception:
        return []
    if days < 0:
        return []

    cutoff = _utcnow().date() - _dt.timedelta(days=days)
    to_delete: list[Path] = []
    for p in log_dir.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() != ".jsonl":
            continue
        d = _parse_log_date(p.name)
        if d is None:
            continue
        if d < cutoff:
            to_delete.append(p)

    if not dry_run:
        for p in to_delete:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                continue

    return sorted(to_delete)


def prune_bundle(bundle: SkillBundle, *, dry_run: bool = False) -> dict[str, Any]:
    manifest = bundle.manifest
    policy = bundle.policy

    retention = policy.get("retention") or {}
    if not isinstance(retention, dict):
        retention = {}

    max_backups = retention.get("max_backups_per_index")
    max_age_days = retention.get("max_backup_age_days")

    prune_logs_after_days = retention.get("prune_logs_after_days")
    if prune_logs_after_days is None:
        logs_cfg = manifest.get("logs") or {}
        if not isinstance(logs_cfg, dict):
            logs_cfg = {}
        prune_logs_after_days = logs_cfg.get("retention_days")
    if prune_logs_after_days is None:
        security = manifest.get("security") or {}
        if isinstance(security, dict):
            prune_logs_after_days = security.get("retention_days")

    artifacts = ((manifest.get("context") or {}).get("artifacts") or {})
    indexes = artifacts.get("indexes") or []

    deleted_backups: list[str] = []
    for idx in indexes:
        if not isinstance(idx, dict):
            continue
        rel = idx.get("path")
        if not rel:
            continue
        index_dir = (bundle.skill_root / Path(str(rel))).resolve()
        backup_dir = index_dir / ".backup"
        deleted = _prune_backup_dir(
            backup_dir,
            max_backups=int(max_backups) if max_backups is not None else None,
            max_age_days=int(max_age_days) if max_age_days is not None else None,
            dry_run=dry_run,
        )
        deleted_backups += [p.relative_to(bundle.skill_root).as_posix() for p in deleted]

    logs_root = bundle.skill_root / "expert" / "logs"
    deleted_logs: list[str] = []
    for sub in ("queries", "updates"):
        deleted = _prune_logs_dir(
            logs_root / sub,
            prune_after_days=int(prune_logs_after_days) if prune_logs_after_days is not None else None,
            dry_run=dry_run,
        )
        deleted_logs += [p.relative_to(bundle.skill_root).as_posix() for p in deleted]

    return {
        "ok": True,
        "dry_run": dry_run,
        "deleted_backups": deleted_backups,
        "deleted_logs": deleted_logs,
    }


def prune_skill(skill_root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    try:
        bundle = load_skill_bundle(skill_root)
    except Exception as e:
        raise ECPError(str(e)) from e
    return prune_bundle(bundle, dry_run=dry_run)

