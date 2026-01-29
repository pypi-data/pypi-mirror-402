from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ecp_reference.indexer import SourceSpec, build_keyword_index_multi
from ecp_reference.profile_constraints import validate_profile_constraints
from ecp_reference.skill_loader import load_skill_bundle


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _minimal_skill_md(*, name: str) -> str:
    return (
        "---\n"
        f"name: {name}\n"
        "description: test skill\n"
        "---\n\n"
        "# Test Skill\n"
    )


def _minimal_policy_json(*, suite_id: str) -> str:
    return json.dumps(
        {
            "policy_version": "1.0",
            "budgets": {"max_update_duration_seconds": 60},
            "refresh_triggers": [{"type": "manual", "spec": "on-demand"}],
            "update_strategy": {
                "default": "incremental",
                "incremental": {"method": "file-manifest"},
                "rebuild": {"method": "full-scan"},
                "rebuild_thresholds": {},
            },
            "validation": {"eval_suites": [suite_id], "fail_action": "block"},
            "publishing": {"on_pass": "require_approval", "rollback_on_fail": True},
        },
        indent=2,
        sort_keys=True,
    )


def _minimal_eval_suite_yaml(*, suite_id: str) -> str:
    return (
        f"suite_id: {suite_id}\n"
        "suite_version: '1.0'\n"
        "cases:\n"
        "  - case_id: noop\n"
        "    mode: ephemeral\n"
        "    question: hi\n"
    )


def _write_index_artifacts(
    root: Path,
    *,
    index_id: str = "kw-v2",
    chunks_rel: str = "chunks.jsonl",
    chunk_records: list[dict] | None = None,
) -> Path:
    index_dir = root / "expert" / "context" / "indexes" / index_id
    index_dir.mkdir(parents=True, exist_ok=True)
    _write(
        index_dir / "index.json",
        json.dumps(
            {
                "index_id": index_id,
                "type": "keyword",
                "created_at": "2026-01-01T00:00:00Z",
                "retrieval_defaults": {"top_k": 8},
                "chunking": {"method": "line-window", "max_chars": 2000, "overlap_chars": 200},
                "provenance": {
                    "index_data_path": "index_data.json",
                    "chunks_path": chunks_rel,
                },
            },
            indent=2,
            sort_keys=True,
        ),
    )
    _write(index_dir / "index_data.json", "{}")
    records = chunk_records or []
    _write(index_dir / chunks_rel, "\n".join(json.dumps(r) for r in records) + ("\n" if records else ""))
    return index_dir


class TestConformanceProfileConstraints(unittest.TestCase):
    def test_conformance_profile_is_recognized_and_self_contained(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "conformance-skill"
            repo = root / "expert" / "sources" / "repo"
            _write(repo / "auth.py", "def login():\n    return 'ok'\n")

            index_dir = root / "expert" / "context" / "indexes" / "kw-v2"
            src = SourceSpec(
                source_id="repo",
                source_type="filesystem",
                source_uri="expert/sources/repo",
                source_root=repo,
                include=["**/*"],
                exclude=[],
                revision={"hash": "deadbeef", "timestamp": "2026-01-01T00:00:00Z"},
            )
            build_keyword_index_multi(index_id="kw-v2", sources=[src], out_dir=index_dir)

            _write(root / "SKILL.md", _minimal_skill_md(name=root.name))
            _write(
                root / "expert" / "maintenance" / "policy.json",
                _minimal_policy_json(suite_id="smoke"),
            )
            _write(
                root / "expert" / "evals" / "smoke.yaml",
                _minimal_eval_suite_yaml(suite_id="smoke"),
            )
            _write(
                root / "expert" / "EXPERT.yaml",
                (
                    "ecp_version: '1.0'\n"
                    f"id: {root.name}\n"
                    "profile: conformance\n"
                    "skill:\n"
                    f"  name: {root.name}\n"
                    "security:\n"
                    "  allow_remote_llm: false\n"
                    "sources:\n"
                    "  - source_id: repo\n"
                    "    type: filesystem\n"
                    "    uri: expert/sources/repo\n"
                    "    scope:\n"
                    "      include: ['**/*']\n"
                    "    revision:\n"
                    "      hash: deadbeef\n"
                    "      timestamp: '2026-01-01T00:00:00Z'\n"
                    "    refresh:\n"
                    "      strategy: none\n"
                    "context:\n"
                    "  strategy: hybrid\n"
                    "  artifacts:\n"
                    "    indexes:\n"
                    "      - id: kw-v2\n"
                    "        type: keyword\n"
                    "        path: expert/context/indexes/kw-v2\n"
                    "        descriptor: expert/context/indexes/kw-v2/index.json\n"
                    "maintenance:\n"
                    "  policy_path: expert/maintenance/policy.json\n"
                    "evals:\n"
                    "  suites:\n"
                    "    - suite_id: smoke\n"
                    "      path: expert/evals/smoke.yaml\n"
                ),
            )

            bundle = load_skill_bundle(root)
            prof_id, prof_violations, schema_violations, warnings = validate_profile_constraints(
                bundle
            )
            self.assertEqual(prof_id, "conformance")
            self.assertEqual(prof_violations, [])
            self.assertEqual(schema_violations, [])
            self.assertEqual(warnings, [])

    def test_docs_profile_requires_summaries(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "docs-skill"
            _write(root / "SKILL.md", _minimal_skill_md(name=root.name))
            _write(
                root / "expert" / "maintenance" / "policy.json",
                _minimal_policy_json(suite_id="smoke"),
            )
            _write(
                root / "expert" / "evals" / "smoke.yaml",
                _minimal_eval_suite_yaml(suite_id="smoke"),
            )
            _write(root / "expert" / "context" / "summaries" / "overview.md", "# Overview\n")

            _write(
                root / "expert" / "EXPERT.yaml",
                (
                    "ecp_version: '1.0'\n"
                    f"id: {root.name}\n"
                    "profile: docs\n"
                    "skill:\n"
                    f"  name: {root.name}\n"
                    "security:\n"
                    "  allow_remote_llm: false\n"
                    "sources:\n"
                    "  - source_id: repo\n"
                    "    type: filesystem\n"
                    "    uri: expert/sources/repo\n"
                    "    scope:\n"
                    "      include: ['**/*']\n"
                    "    revision:\n"
                    "      hash: deadbeef\n"
                    "      timestamp: '2026-01-01T00:00:00Z'\n"
                    "    refresh:\n"
                    "      strategy: none\n"
                    "context:\n"
                    "  strategy: snapshot\n"
                    "  artifacts:\n"
                    "    summaries:\n"
                    "      - id: overview\n"
                    "        type: overview\n"
                    "        path: expert/context/summaries/overview.md\n"
                    "maintenance:\n"
                    "  policy_path: expert/maintenance/policy.json\n"
                    "evals:\n"
                    "  suites:\n"
                    "    - suite_id: smoke\n"
                    "      path: expert/evals/smoke.yaml\n"
                ),
            )

            bundle = load_skill_bundle(root)
            prof_id, prof_violations, schema_violations, warnings = validate_profile_constraints(
                bundle
            )
            self.assertEqual(prof_id, "docs")
            self.assertEqual(prof_violations, [])
            self.assertEqual(schema_violations, [])
            self.assertEqual(warnings, [])

    def test_web_profile_requires_snapshots_and_indexes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "web-skill"
            _write(root / "SKILL.md", _minimal_skill_md(name=root.name))
            _write(
                root / "expert" / "maintenance" / "policy.json",
                _minimal_policy_json(suite_id="smoke"),
            )
            _write(
                root / "expert" / "evals" / "smoke.yaml",
                _minimal_eval_suite_yaml(suite_id="smoke"),
            )

            _write_index_artifacts(
                root,
                chunk_records=[
                    {
                        "chunk_id": "web::page.html#L1-L1",
                        "source_id": "web",
                        "uri": "https://example.com/page",
                        "artifact_path": "page.html",
                        "revision": {"retrieved_at": "2026-01-01T00:00:00Z"},
                        "loc": {"start_line": 1, "end_line": 1},
                        "chunk_hash": "deadbeef",
                    }
                ],
            )

            _write(
                root / "expert" / "EXPERT.yaml",
                (
                    "ecp_version: '1.0'\n"
                    f"id: {root.name}\n"
                    "profile: web\n"
                    "skill:\n"
                    f"  name: {root.name}\n"
                    "security:\n"
                    "  allow_remote_llm: false\n"
                    "sources:\n"
                    "  - source_id: web\n"
                    "    type: web\n"
                    "    uri: https://example.com\n"
                    "    scope:\n"
                    "      include: ['**/*']\n"
                    "    revision:\n"
                    "      retrieved_at: '2026-01-01T00:00:00Z'\n"
                    "    refresh:\n"
                    "      strategy: none\n"
                    "context:\n"
                    "  strategy: snapshot\n"
                    "  artifacts:\n"
                    "    snapshots:\n"
                    "      - id: web-snapshot\n"
                    "        path: expert/context/snapshots/web.tar\n"
                    "        format: tar\n"
                    "    indexes:\n"
                    "      - id: kw-v2\n"
                    "        type: keyword\n"
                    "        path: expert/context/indexes/kw-v2\n"
                    "        descriptor: expert/context/indexes/kw-v2/index.json\n"
                    "maintenance:\n"
                    "  policy_path: expert/maintenance/policy.json\n"
                    "evals:\n"
                    "  suites:\n"
                    "    - suite_id: smoke\n"
                    "      path: expert/evals/smoke.yaml\n"
                ),
            )

            bundle = load_skill_bundle(root)
            prof_id, prof_violations, schema_violations, warnings = validate_profile_constraints(
                bundle
            )
            self.assertEqual(prof_id, "web")
            self.assertEqual(prof_violations, [])
            self.assertEqual(schema_violations, [])
            self.assertEqual(warnings, [])

    def test_mixed_profile_requires_multiple_sources_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "mixed-skill"
            _write(root / "SKILL.md", _minimal_skill_md(name=root.name))
            _write(
                root / "expert" / "maintenance" / "policy.json",
                _minimal_policy_json(suite_id="smoke"),
            )
            _write(
                root / "expert" / "evals" / "smoke.yaml",
                _minimal_eval_suite_yaml(suite_id="smoke"),
            )
            _write(root / "expert" / "context" / "summaries" / "overview.md", "# Overview\n")

            _write_index_artifacts(
                root,
                chunk_records=[
                    {
                        "chunk_id": "repo::auth.py#L1-L1",
                        "source_id": "repo",
                        "uri": "expert/sources/repo",
                        "artifact_path": "auth.py",
                        "revision": {"hash": "deadbeef", "timestamp": "2026-01-01T00:00:00Z"},
                        "loc": {"start_line": 1, "end_line": 1},
                        "chunk_hash": "deadbeef",
                    },
                    {
                        "chunk_id": "web::page.html#L1-L1",
                        "source_id": "web",
                        "uri": "https://example.com/page",
                        "artifact_path": "page.html",
                        "revision": {"retrieved_at": "2026-01-01T00:00:00Z"},
                        "loc": {"start_line": 1, "end_line": 1},
                        "chunk_hash": "deadbeef",
                    },
                ],
            )

            _write(
                root / "expert" / "EXPERT.yaml",
                (
                    "ecp_version: '1.0'\n"
                    f"id: {root.name}\n"
                    "profile: mixed\n"
                    "skill:\n"
                    f"  name: {root.name}\n"
                    "security:\n"
                    "  allow_remote_llm: false\n"
                    "sources:\n"
                    "  - source_id: repo\n"
                    "    type: filesystem\n"
                    "    uri: expert/sources/repo\n"
                    "    scope:\n"
                    "      include: ['**/*']\n"
                    "    revision:\n"
                    "      hash: deadbeef\n"
                    "      timestamp: '2026-01-01T00:00:00Z'\n"
                    "    refresh:\n"
                    "      strategy: none\n"
                    "  - source_id: web\n"
                    "    type: web\n"
                    "    uri: https://example.com\n"
                    "    scope:\n"
                    "      include: ['**/*']\n"
                    "    revision:\n"
                    "      retrieved_at: '2026-01-01T00:00:00Z'\n"
                    "    refresh:\n"
                    "      strategy: none\n"
                    "context:\n"
                    "  strategy: hybrid\n"
                    "  artifacts:\n"
                    "    indexes:\n"
                    "      - id: kw-v2\n"
                    "        type: keyword\n"
                    "        path: expert/context/indexes/kw-v2\n"
                    "        descriptor: expert/context/indexes/kw-v2/index.json\n"
                    "    summaries:\n"
                    "      - id: overview\n"
                    "        type: overview\n"
                    "        path: expert/context/summaries/overview.md\n"
                    "maintenance:\n"
                    "  policy_path: expert/maintenance/policy.json\n"
                    "evals:\n"
                    "  suites:\n"
                    "    - suite_id: smoke\n"
                    "      path: expert/evals/smoke.yaml\n"
                ),
            )

            bundle = load_skill_bundle(root)
            prof_id, prof_violations, schema_violations, warnings = validate_profile_constraints(
                bundle
            )
            self.assertEqual(prof_id, "mixed")
            self.assertEqual(prof_violations, [])
            self.assertEqual(schema_violations, [])
            self.assertEqual(warnings, [])
