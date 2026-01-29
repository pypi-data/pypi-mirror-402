from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ecp_reference.errors import QueryError
from ecp_reference.runtime import query_expert


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _minimal_skill_md(*, name: str) -> str:
    return f"""---
name: {name}
description: A test skill
version: "1.0"
---
# {name}
"""


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
    )


def _minimal_eval_suite_yaml() -> str:
    return """suite_id: smoke
suite_version: '1.0'
cases:
  - case_id: noop
    mode: ephemeral
    question: hi
"""


def _expert_yaml(*, skill_name: str, allow_remote_llm: bool, allowed_remote_llm_providers: list[str]) -> str:
    providers_yaml = "\n".join([f"    - {p}" for p in allowed_remote_llm_providers])
    return f"""ecp_version: "1.0"
id: test-expert
profile: codebase
skill:
  name: {skill_name}
description: A test expert
security:
  allow_remote_llm: {str(bool(allow_remote_llm)).lower()}
  allowed_remote_llm_providers:
{providers_yaml}
sources:
  - source_id: main
    type: filesystem
    uri: file:./source
    scope:
      include: ['**/*']
      exclude: ['**/.git/**']
    revision:
      hash: abc123
      timestamp: '2026-01-01T00:00:00Z'
    refresh:
      strategy: none
context:
  strategy: hybrid
  artifacts:
    indexes:
      - id: keyword-v1
        type: keyword
        path: expert/context/indexes/keyword-v1
        descriptor: expert/context/indexes/keyword-v1/index.json
maintenance:
  policy_path: expert/maintenance/policy.json
evals:
  suites:
    - suite_id: smoke
      path: expert/evals/smoke.yaml
"""


def _create_test_skill(
    tmp: Path,
    *,
    allow_remote_llm: bool,
    allowed_remote_llm_providers: list[str],
) -> Path:
    skill_root = tmp / "test-skill"
    _write(skill_root / "SKILL.md", _minimal_skill_md(name=skill_root.name))
    _write(
        skill_root / "expert" / "EXPERT.yaml",
        _expert_yaml(
            skill_name=skill_root.name,
            allow_remote_llm=allow_remote_llm,
            allowed_remote_llm_providers=allowed_remote_llm_providers,
        ),
    )
    _write(skill_root / "expert" / "maintenance" / "policy.json", _minimal_policy_json())
    _write(skill_root / "expert" / "evals" / "smoke.yaml", _minimal_eval_suite_yaml())

    (skill_root / "source").mkdir(parents=True, exist_ok=True)
    _write(skill_root / "source" / "main.py", "def main():\n    print('hello')\n")

    index_dir = skill_root / "expert" / "context" / "indexes" / "keyword-v1"
    index_dir.mkdir(parents=True, exist_ok=True)
    _write(index_dir / "index.json", json.dumps({"index_id": "keyword-v1", "type": "keyword"}))
    _write(
        index_dir / "index_data.json",
        json.dumps(
            {
                "format": "keyword-index-v2",
                "documents": {"main.py": {"path": "main.py", "source_id": "main"}},
                "doc_terms": {"main.py": {"hello": 1}},
                "terms": {"hello": {"df": 1, "postings": [["main.py", 1]]}},
            }
        ),
    )
    return skill_root


class TestQueryLLMSecurity(unittest.TestCase):
    def test_query_allows_ollama_when_remote_allowlist_excludes_it(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _create_test_skill(
                Path(tmp_dir),
                allow_remote_llm=True,
                allowed_remote_llm_providers=["openrouter"],
            )

            def _fake_synthesize_answer(**kwargs):
                self.assertEqual(kwargs.get("llm"), "ollama")
                return ("ok", {"provider": "ollama", "method": "llm"})

            with patch("ecp_reference.runtime.synthesize_answer", side_effect=_fake_synthesize_answer):
                resp = query_expert(root, question="hello", mode="ephemeral", top_k=1, llm="ollama")

            self.assertEqual(resp.get("answer"), "ok")

    def test_query_blocks_openrouter_when_not_in_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = _create_test_skill(
                Path(tmp_dir),
                allow_remote_llm=True,
                allowed_remote_llm_providers=["anthropic"],
            )

            with patch("ecp_reference.runtime.synthesize_answer", return_value=("ok", {"provider": "openrouter"})):
                with self.assertRaises(QueryError) as ctx:
                    query_expert(root, question="hello", mode="ephemeral", top_k=1, llm="openrouter")

            self.assertIn("allowed_remote_llm_providers", str(ctx.exception))
