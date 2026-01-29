from __future__ import annotations

import json
import re
import subprocess
import zipfile
from pathlib import Path
from typing import Any, Iterable

from . import __version__
from .errors import ECPError
from .maintenance import parse_file_uri
from .profile_constraints import normalize_profile
from .skill_loader import load_skill_bundle
from .utils import rfc3339_now, sha256_bytes, sha256_file, within_scope

DEFAULT_EXCLUDE_GLOBS = [
    "**/.git/**",
    "**/__pycache__/**",
    "**/.env",
    "**/.env.*",
    "**/.DS_Store",
    "**/.backup/**",
    "expert/logs/**",
]

_GIT_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")


def _enforce_pack_git_commit_pinning(bundle: object) -> None:
    """Enforce provenance requirements that are mandatory for distributable packs."""
    try:
        profile_id = normalize_profile(getattr(bundle, "manifest", {}).get("profile"))
    except Exception:
        profile_id = None

    # Workstream B1: codebase packs must be commit-pinned for git sources.
    if profile_id != "codebase":
        return

    manifest = getattr(bundle, "manifest", {}) or {}
    sources = manifest.get("sources") or []
    if not isinstance(sources, list):
        return

    failures: list[str] = []

    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            continue

        stype = str(src.get("type") or "").strip().lower()
        if stype != "git":
            continue

        sid = str(src.get("source_id") or f"#{i}")
        uri = str(src.get("uri") or "").strip()
        rev = src.get("revision") if isinstance(src.get("revision"), dict) else {}
        commit = str(rev.get("commit") or "").strip()

        label = f"sources[{i}] (source_id={sid})"

        if not commit:
            failures.append(f"{label}: git source missing revision.commit")
            continue
        if commit.lower() == "head":
            failures.append(f"{label}: revision.commit must be a concrete commit hash, not 'HEAD'")
            continue
        if not _GIT_COMMIT_RE.match(commit):
            failures.append(
                f"{label}: revision.commit must be a git commit hash (7-40 hex chars); got {commit!r}"
            )
            continue

        # Best-effort local validation: ensure the commit exists in the referenced repo.
        if not uri:
            failures.append(f"{label}: git source missing uri (needed to validate revision.commit)")
            continue
        try:
            repo = parse_file_uri(uri, base_dir=getattr(bundle, "skill_root", None))
        except Exception as e:
            failures.append(f"{label}: could not resolve git uri {uri!r}: {e}")
            continue

        if not repo.exists():
            failures.append(f"{label}: git uri path not found: {repo}")
            continue

        try:
            p = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "--verify", f"{commit}^{{commit}}"],
                capture_output=True,
                timeout=20,
                text=True,
            )
        except Exception as e:
            failures.append(f"{label}: failed to validate git commit {commit!r} in {repo}: {e}")
            continue

        if p.returncode != 0:
            detail = (p.stderr or p.stdout or "").strip()
            suffix = f": {detail}" if detail else ""
            failures.append(f"{label}: revision.commit {commit!r} not found in repo {repo}{suffix}")

    if failures:
        skill_root = getattr(bundle, "skill_root", None)
        skill_hint = str(skill_root) if isinstance(skill_root, Path) else "<skill>"
        raise ECPError(
            "Refusing to package a 'codebase' profile skill without commit-pinned git sources.\n"
            "Fix: ensure each `sources[].type: git` has `sources[].revision.commit` set to a concrete commit hash "
            "(not 'HEAD'), then rerun `ecpctl pack`.\n"
            f"Tip: `ecpctl refresh --skill {skill_hint}` records `revision.commit` as `git rev-parse HEAD`.\n"
            "Failures:\n- " + "\n- ".join(failures)
        )


def _iter_skill_files(skill_root: Path) -> Iterable[Path]:
    for p in skill_root.rglob("*"):
        if p.is_file():
            yield p


def create_skill_package(
    skill_root: Path,
    *,
    out_path: Path,
    include_logs: bool = False,
    include_backups: bool = False,
    allow_secrets: bool = False,
    deterministic: bool = True,
) -> dict[str, Any]:
    bundle = load_skill_bundle(skill_root)
    skill_root = bundle.skill_root

    _enforce_pack_git_commit_pinning(bundle)

    contains_secrets = bool((bundle.manifest.get("security") or {}).get("contains_secrets", False))
    if contains_secrets and not allow_secrets:
        raise ECPError(
            "Refusing to package skill with security.contains_secrets=true. "
            "Override with --allow-secrets only if you have an encrypted/approved distribution channel."
        )

    excludes = list(DEFAULT_EXCLUDE_GLOBS)
    if include_logs:
        excludes = [x for x in excludes if x != "expert/logs/**"]
    if include_backups:
        excludes = [x for x in excludes if x != "**/.backup/**"]

    include = ["**/*"]
    included: list[tuple[str, Path]] = []
    total_bytes = 0
    for p in _iter_skill_files(skill_root):
        rel_posix = p.relative_to(skill_root).as_posix()
        if not within_scope(rel_posix, include, excludes):
            continue
        included.append((rel_posix, p))
        try:
            total_bytes += int(p.stat().st_size)
        except Exception:
            pass

    # Deterministic archive ordering (independent of filesystem traversal order).
    included.sort(key=lambda x: x[0])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    created_at = rfc3339_now()

    file_entries: list[dict[str, Any]] = []

    def _zipinfo(name: str) -> zipfile.ZipInfo:
        zi = zipfile.ZipInfo(name)
        if deterministic:
            zi.date_time = (1980, 1, 1, 0, 0, 0)
        zi.compress_type = zipfile.ZIP_DEFLATED
        return zi

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for rel_posix, abs_path in included:
            arcname = f"{skill_root.name}/{rel_posix}"
            zi = _zipinfo(arcname)
            h = sha256_file(abs_path)
            try:
                size = int(abs_path.stat().st_size)
            except Exception:
                size = None

            file_entries.append(
                {"path": rel_posix, "sha256": h, "size": size}
                if size is not None
                else {"path": rel_posix, "sha256": h}
            )

            with abs_path.open("rb") as src, z.open(zi, "w") as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)

        file_entries.sort(key=lambda x: x.get("path") or "")

        package = {
            "ecp_package_version": "1.0",
            "created_at": created_at,
            "created_by": {"tool": "ecpctl", "version": __version__},
            "skill_root_dir": skill_root.name,
            "skill_name": bundle.skill_frontmatter.get("name"),
            "ecp_version": bundle.manifest.get("ecp_version"),
            "excludes": excludes,
            "files": file_entries,
        }

        package_blob = json.dumps(package, indent=2, sort_keys=True).encode("utf-8")
        package_hash = sha256_bytes(package_blob)
        package["package_sha256"] = package_hash
        package_blob = json.dumps(package, indent=2, sort_keys=True).encode("utf-8")

        pkg_arcname = f"{skill_root.name}/expert/package.json"
        z.writestr(_zipinfo(pkg_arcname), package_blob)

    return {
        "ok": True,
        "package": str(out_path),
        "created_at": created_at,
        "skill": bundle.skill_frontmatter.get("name"),
        "ecp_version": bundle.manifest.get("ecp_version"),
        "included_files": len(included) + 1,  # + expert/package.json
        "included_bytes": total_bytes,
        "excluded_globs": excludes,
    }


def _read_package_json(z: zipfile.ZipFile) -> tuple[str, dict[str, Any]]:
    candidates = [n for n in z.namelist() if n.endswith("/expert/package.json")]
    if not candidates:
        raise ECPError("Package missing expert/package.json.")
    if len(candidates) > 1:
        raise ECPError(f"Package has multiple expert/package.json entries: {candidates}")
    name = candidates[0]
    raw = z.read(name)
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise ECPError(f"Failed to parse expert/package.json: {e}") from e
    if not isinstance(data, dict):
        raise ECPError("expert/package.json must be a JSON object.")
    return name, data


def verify_skill_package(package_path: Path, *, validate: bool = True) -> dict[str, Any]:
    package_path = package_path.resolve()
    if not package_path.exists():
        raise ECPError(f"Package not found: {package_path}")

    with zipfile.ZipFile(package_path, "r") as z:
        pkg_path, pkg = _read_package_json(z)

        failures: list[str] = []

        # Validate package manifest schema and its self-hash.
        if validate:
            try:
                import jsonschema

                schema_path = Path(__file__).resolve().parent / "schemas" / "ecp-package.schema.json"
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                validator = jsonschema.Draft202012Validator(schema)
                errors = sorted(validator.iter_errors(pkg), key=lambda e: e.path)
                for e in errors[:10]:
                    loc = ".".join([str(p) for p in e.path]) if e.path else "<root>"
                    failures.append(f"package.json schema: {loc}: {e.message}")
                if len(errors) > 10:
                    failures.append(f"package.json schema: ... ({len(errors) - 10} more)")
            except Exception as e:
                failures.append(f"package.json schema validation failed: {e}")

        expected_pkg_sha = str(pkg.get("package_sha256") or "").strip()
        if not expected_pkg_sha:
            failures.append("expert/package.json missing package_sha256.")
        else:
            try:
                pkg_no_sha = dict(pkg)
                pkg_no_sha.pop("package_sha256", None)
                blob = json.dumps(pkg_no_sha, indent=2, sort_keys=True).encode("utf-8")
                got_sha = sha256_bytes(blob)
                if got_sha != expected_pkg_sha:
                    failures.append(
                        f"package_sha256 mismatch: expected {expected_pkg_sha}, got {got_sha}"
                    )
            except Exception as e:
                failures.append(f"failed to verify package_sha256: {e}")

        root_dir = str(pkg.get("skill_root_dir") or "").strip().strip("/")
        if not root_dir:
            raise ECPError("expert/package.json missing skill_root_dir.")

        files = pkg.get("files")
        if not isinstance(files, list):
            raise ECPError("expert/package.json files must be an array.")

        checked = 0
        for entry in files:
            if not isinstance(entry, dict):
                continue
            rel = entry.get("path")
            expected = entry.get("sha256")
            if not rel or not expected:
                continue
            arcname = f"{root_dir}/{Path(str(rel)).as_posix()}"
            try:
                with z.open(arcname, "r") as f:
                    import hashlib

                    h = hashlib.sha256()
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        h.update(chunk)
                got = h.hexdigest()
            except KeyError:
                failures.append(f"missing file in zip: {arcname}")
                continue
            except Exception as e:
                failures.append(f"failed to hash {arcname}: {e}")
                continue

            checked += 1
            if str(got) != str(expected):
                failures.append(f"sha256 mismatch for {arcname}: expected {expected}, got {got}")

        validated = False
        if validate and not failures:
            import tempfile

            with tempfile.TemporaryDirectory(prefix=".ecp_verify_", dir=str(Path.cwd())) as td:
                td_path = Path(td)
                z.extractall(td_path)
                extracted_root = td_path / root_dir
                _ = load_skill_bundle(extracted_root)
                validated = True

    return {
        "ok": len(failures) == 0,
        "package": str(package_path),
        "package_json": pkg_path,
        "checked_files": checked,
        "validated": validated,
        "failures": failures,
    }
