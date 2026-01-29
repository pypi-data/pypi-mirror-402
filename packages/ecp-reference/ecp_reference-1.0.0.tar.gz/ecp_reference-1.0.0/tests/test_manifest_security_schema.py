from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ecp_reference.errors import ManifestValidationError
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


def _minimal_policy_json() -> str:
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
            "validation": {"eval_suites": ["smoke"], "fail_action": "block"},
            "publishing": {"on_pass": "require_approval", "rollback_on_fail": True},
        },
        indent=2,
        sort_keys=True,
    )


def _minimal_eval_suite_yaml() -> str:
    return (
        "suite_id: smoke\n"
        "suite_version: '1.0'\n"
        "cases:\n"
        "  - case_id: noop\n"
        "    mode: ephemeral\n"
        "    question: hi\n"
    )


class TestManifestSecuritySchema(unittest.TestCase):
    def test_allow_remote_llm_requires_allowlist(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "skill"
            _write(root / "SKILL.md", _minimal_skill_md(name=root.name))
            _write(root / "expert" / "maintenance" / "policy.json", _minimal_policy_json())
            _write(root / "expert" / "evals" / "smoke.yaml", _minimal_eval_suite_yaml())

            _write(
                root / "expert" / "EXPERT.yaml",
                (
                    "ecp_version: '1.0'\n"
                    f"id: {root.name}\n"
                    "skill:\n"
                    f"  name: {root.name}\n"
                    "security:\n"
                    "  allow_remote_llm: true\n"
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

            with self.assertRaises(ManifestValidationError):
                load_skill_bundle(root)

    def test_allow_remote_llm_with_allowlist_passes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "skill"
            _write(root / "SKILL.md", _minimal_skill_md(name=root.name))
            _write(root / "expert" / "maintenance" / "policy.json", _minimal_policy_json())
            _write(root / "expert" / "evals" / "smoke.yaml", _minimal_eval_suite_yaml())

            _write(
                root / "expert" / "EXPERT.yaml",
                (
                    "ecp_version: '1.0'\n"
                    f"id: {root.name}\n"
                    "skill:\n"
                    f"  name: {root.name}\n"
                    "security:\n"
                    "  allow_remote_llm: true\n"
                    "  allowed_remote_llm_providers:\n"
                    "    - openrouter\n"
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
            self.assertEqual(bundle.manifest.get("security", {}).get("allow_remote_llm"), True)
