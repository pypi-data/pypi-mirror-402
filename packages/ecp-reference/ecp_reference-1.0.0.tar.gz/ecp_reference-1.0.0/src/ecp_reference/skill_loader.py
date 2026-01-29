from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from .errors import (
    EvalValidationError,
    ManifestValidationError,
    PolicyValidationError,
    SkillFormatError,
)
from .utils import read_json, read_yaml, resolve_under_root

@dataclasses.dataclass
class LoadedEvalSuite:
    suite_id: str
    path: Path
    data: dict

@dataclasses.dataclass
class SkillBundle:
    skill_root: Path
    skill_md_path: Path
    skill_frontmatter: dict
    expert_yaml_path: Path
    manifest: dict
    policy_path: Path
    policy: dict
    eval_suites: list[LoadedEvalSuite]

def _load_schema(schema_path: Path) -> dict:
    return json.loads(schema_path.read_text(encoding="utf-8"))

def schema_filename_for_version(*, kind: str, version: str) -> str:
    version = str(version or "").strip()
    if kind == "manifest":
        filename = {
            "1.0": "ecp-manifest.schema.json",
        }.get(version)
    elif kind == "policy":
        filename = {
            "1.0": "ecp-policy.schema.json",
        }.get(version)
    elif kind == "eval":
        filename = {
            "1.0": "ecp-eval-suite.schema.json",
        }.get(version)
    else:
        raise SkillFormatError(f"Unknown schema kind: {kind}")

    if not filename:
        raise SkillFormatError(
            f"Unsupported ECP {kind} schema version: {version!r}. Supported: 1.0"
        )

    return filename

def _schema_for_version(*, schema_dir: Path, kind: str, version: str) -> dict:
    filename = schema_filename_for_version(kind=kind, version=version)
    return _load_schema(schema_dir / filename)

def _validate_json_schema(instance: Any, schema: dict, *, error_cls: type[Exception]) -> None:
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        lines = []
        for e in errors[:10]:
            loc = ".".join([str(p) for p in e.path]) if e.path else "<root>"
            lines.append(f"- {loc}: {e.message}")
        if len(errors) > 10:
            lines.append(f"... ({len(errors) - 10} more)")
        raise error_cls("Schema validation failed:\n" + "\n".join(lines))

def _parse_skill_frontmatter(skill_md: str) -> dict:
    # Agent Skills uses YAML frontmatter in SKILL.md.
    # We implement a permissive parser: if frontmatter is missing, error.
    lines = skill_md.splitlines(keepends=True)
    if not lines or not lines[0].strip() == "---":
        raise SkillFormatError("SKILL.md must start with YAML frontmatter delimited by '---' lines.")
    # Find second delimiter
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise SkillFormatError("SKILL.md frontmatter must end with a second '---' line.")
    fm_text = "".join(lines[1:end])
    try:
        fm = yaml.safe_load(fm_text) or {}
    except Exception as e:
        raise SkillFormatError(f"Failed to parse SKILL.md YAML frontmatter: {e}") from e
    if not isinstance(fm, dict):
        raise SkillFormatError("SKILL.md YAML frontmatter must be a mapping/object.")
    return fm

def load_skill_bundle(skill_root: Path) -> SkillBundle:
    skill_root = skill_root.resolve()
    if not skill_root.exists() or not skill_root.is_dir():
        raise SkillFormatError(f"Skill root does not exist or is not a directory: {skill_root}")

    skill_md_path = skill_root / "SKILL.md"
    if not skill_md_path.exists():
        raise SkillFormatError(f"Missing required SKILL.md at: {skill_md_path}")

    fm = _parse_skill_frontmatter(skill_md_path.read_text(encoding="utf-8"))
    if "name" not in fm or not fm["name"]:
        raise SkillFormatError("SKILL.md frontmatter must include a non-empty 'name' field.")
    if "description" not in fm or not fm["description"]:
        raise SkillFormatError("SKILL.md frontmatter must include a non-empty 'description' field.")

    dir_name = skill_root.name
    if fm["name"] != dir_name:
        raise SkillFormatError(f"Skill directory name '{dir_name}' must match SKILL.md frontmatter name '{fm['name']}'.")

    expert_yaml_path = skill_root / "expert" / "EXPERT.yaml"
    if not expert_yaml_path.exists():
        raise SkillFormatError(f"Missing required expert/EXPERT.yaml at: {expert_yaml_path}")

    try:
        manifest = read_yaml(expert_yaml_path)
    except Exception as e:
        raise ManifestValidationError(f"Failed to parse EXPERT.yaml: {expert_yaml_path}: {e}") from e
    if not isinstance(manifest, dict):
        raise ManifestValidationError("EXPERT.yaml must parse to a mapping/object.")

    # Validate manifest against schema
    schema_dir = Path(__file__).resolve().parent / "schemas"
    manifest_schema = _schema_for_version(
        schema_dir=schema_dir,
        kind="manifest",
        version=str(manifest.get("ecp_version") or ""),
    )
    _validate_json_schema(manifest, manifest_schema, error_cls=ManifestValidationError)

    # Cross-check linkage
    skill_name = manifest.get("skill", {}).get("name")
    if skill_name != fm["name"]:
        raise ManifestValidationError(f"EXPERT.yaml skill.name '{skill_name}' must match SKILL.md name '{fm['name']}'.")

    # Validate declared artifact paths are safely under the skill root.
    artifacts = ((manifest.get("context") or {}).get("artifacts") or {})
    indexes = artifacts.get("indexes") or []
    for idx in indexes:
        if not isinstance(idx, dict):
            continue
        idx_id = idx.get("id")
        if idx_id and ("/" in idx_id or "\\" in idx_id or idx_id in (".", "..")):
            raise ManifestValidationError(f"Invalid index id (must be a simple token): {idx_id}")
        for field in ("path", "descriptor"):
            rel = idx.get(field)
            if not rel:
                continue
            try:
                _ = resolve_under_root(skill_root, str(rel))
            except ValueError as e:
                raise ManifestValidationError(f"context.artifacts.indexes[].{field}: {e}") from e

    summaries = artifacts.get("summaries") or []
    for s in summaries:
        if not isinstance(s, dict):
            continue
        rel = s.get("path")
        if not rel:
            continue
        try:
            _ = resolve_under_root(skill_root, str(rel))
        except ValueError as e:
            raise ManifestValidationError(f"context.artifacts.summaries[].path: {e}") from e

    policy_rel = manifest.get("maintenance", {}).get("policy_path")
    if not policy_rel:
        raise ManifestValidationError("EXPERT.yaml maintenance.policy_path is required.")
    try:
        policy_path = resolve_under_root(skill_root, str(policy_rel))
    except ValueError as e:
        raise PolicyValidationError(str(e)) from e
    if not policy_path.exists():
        raise PolicyValidationError(f"Missing policy.json at: {policy_path}")   

    try:
        policy = read_json(policy_path)
    except Exception as e:
        raise PolicyValidationError(f"Failed to parse policy.json: {policy_path}: {e}") from e
    schema_policy = _schema_for_version(
        schema_dir=schema_dir,
        kind="policy",
        version=str(policy.get("policy_version") or ""),
    )
    _validate_json_schema(policy, schema_policy, error_cls=PolicyValidationError)

    # Load eval suites
    suites = manifest.get("evals", {}).get("suites", [])
    eval_schema = _schema_for_version(
        schema_dir=schema_dir,
        kind="eval",
        version=str(manifest.get("ecp_version") or ""),
    )
    loaded_suites: list[LoadedEvalSuite] = []
    for s in suites:
        suite_id = s.get("suite_id")
        rel_path = s.get("path")
        if not suite_id or not rel_path:
            raise EvalValidationError("Each eval suite entry in EXPERT.yaml must include suite_id and path.")
        try:
            suite_path = resolve_under_root(skill_root, str(rel_path))
        except ValueError as e:
            raise EvalValidationError(str(e)) from e
        if not suite_path.exists():
            raise EvalValidationError(f"Missing eval suite file: {suite_path}") 
        try:
            data = read_yaml(suite_path)
        except Exception as e:
            raise EvalValidationError(f"Failed to parse eval suite YAML: {suite_path}: {e}") from e
        if not isinstance(data, dict):
            raise EvalValidationError(f"Eval suite must be a mapping/object: {suite_path}")
        _validate_json_schema(data, eval_schema, error_cls=EvalValidationError)
        # suite_id should match file content, if present.
        if data.get("suite_id") != suite_id:
            raise EvalValidationError(
                f"Eval suite id mismatch: EXPERT.yaml references '{suite_id}' but file declares '{data.get('suite_id')}'."
            )
        loaded_suites.append(LoadedEvalSuite(suite_id=suite_id, path=suite_path, data=data))

    if not loaded_suites:
        raise EvalValidationError("At least one eval suite MUST be declared in EXPERT.yaml (evals.suites).")

    return SkillBundle(
        skill_root=skill_root,
        skill_md_path=skill_md_path,
        skill_frontmatter=fm,
        expert_yaml_path=expert_yaml_path,
        manifest=manifest,
        policy_path=policy_path,
        policy=policy,
        eval_suites=loaded_suites,
    )
