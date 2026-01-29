from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ecp_reference.errors import EvalValidationError, ManifestValidationError
from ecp_reference.skill_loader import load_skill_bundle


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _minimal_skill_md(*, name: str) -> str:
    return (
        "---\n"
        f"name: {name}\n"
        "description: test skill\n"
        "---\n"
        "\n"
        f"# {name}\n"
    )


class TestYamlErrorHandling(unittest.TestCase):
    def test_invalid_expert_yaml_is_reported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "bad-skill"
            root.mkdir(parents=True, exist_ok=True)

            _write(root / "SKILL.md", _minimal_skill_md(name="bad-skill"))
            _write(root / "expert" / "EXPERT.yaml", "ecp_version: '1.0'\nid: bad-skill\ncontext: [\n")

            with self.assertRaises(ManifestValidationError) as ctx:
                load_skill_bundle(root)
            self.assertIn("failed to parse expert.yaml", str(ctx.exception).lower())

    def test_invalid_eval_suite_yaml_is_reported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "bad-evals"
            root.mkdir(parents=True, exist_ok=True)

            _write(root / "SKILL.md", _minimal_skill_md(name="bad-evals"))

            _write(
                root / "expert" / "EXPERT.yaml",
                "\n".join(
                    [
                        "ecp_version: '1.0'",
                        "id: bad-evals",
                        "skill:",
                        "  name: bad-evals",
                        "sources:",
                        "  - source_id: repo",
                        "    type: filesystem",
                        "    uri: repo",
                        "    scope:",
                        "      include: ['**/*']",
                        "    revision:",
                        "      hash: deadbeef",
                        "      timestamp: '2026-01-01T00:00:00Z'",
                        "    refresh:",
                        "      strategy: none",
                        "      incremental: {}",
                        "      rebuild: {}",
                        "context:",
                        "  strategy: snapshot",
                        "  artifacts:",
                        "    summaries:",
                        "      - id: repo-overview",
                        "        type: overview",
                        "        path: expert/context/summaries/repo-overview.md",
                        "maintenance:",
                        "  policy_path: expert/maintenance/policy.json",
                        "evals:",
                        "  suites:",
                        "    - suite_id: smoke",
                        "      path: expert/evals/smoke.yaml",
                        "",
                    ]
                ),
            )

            _write(
                root / "expert" / "maintenance" / "policy.json",
                "\n".join(
                    [
                        "{",
                        '  "policy_version": "1.0",',
                        '  "budgets": {"max_update_duration_seconds": 0},',
                        '  "refresh_triggers": [{"type": "manual", "spec": "on-demand"}],',
                        '  "update_strategy": {',
                        '    "default": "incremental",',
                        '    "incremental": {"method": "none"},',
                        '    "rebuild": {"method": "full-scan"},',
                        '    "rebuild_thresholds": {}',
                        "  },",
                        '  "validation": {"eval_suites": ["smoke"], "fail_action": "block"},',
                        '  "publishing": {"on_pass": "auto_publish", "rollback_on_fail": true}',
                        "}",
                        "",
                    ]
                ),
            )

            # Intentionally malformed YAML.
            _write(root / "expert" / "evals" / "smoke.yaml", "suite_id: smoke\nsuite_version: '1.0'\ncases: [\n")

            with self.assertRaises(EvalValidationError) as ctx:
                load_skill_bundle(root)
            self.assertIn("failed to parse eval suite yaml", str(ctx.exception).lower())

    def test_cli_validate_does_not_crash_on_yaml_errors(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "bad-skill"
            root.mkdir(parents=True, exist_ok=True)
            _write(root / "SKILL.md", _minimal_skill_md(name="bad-skill"))
            _write(root / "expert" / "EXPERT.yaml", "ecp_version: '1.0'\nid: bad-skill\ncontext: [\n")

            repo_root = Path(__file__).resolve().parents[1]
            env = os.environ.copy()
            env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")

            p = subprocess.run(
                [sys.executable, "-m", "ecp_reference.cli", "validate", "--skill", str(root)],
                cwd=str(repo_root),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(p.returncode, 2)
            self.assertIn("failed to parse expert.yaml", (p.stdout + p.stderr).lower())
