from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from ecp_reference.errors import QueryError
from ecp_reference.skill_loader import SkillBundle, load_skill_bundle
from ecp_reference.summary_generator import (
    SummaryGenerationResult,
    _check_llm_security,
    _format_chunks_for_prompt,
    _build_dir_tree,
    generate_summaries,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _minimal_skill_md() -> str:
    return """---
name: test-skill
description: A test skill for summary generation
version: "1.0"
---
# Test Skill

A test skill for summary generation.
"""


def _minimal_expert_yaml(*, with_summaries: bool = True, with_secrets: bool = False, allow_remote_llm: bool = True) -> str:
    summaries_block = ""
    if with_summaries:
        summaries_block = """    summaries:
      - id: repo-overview
        type: overview
        path: expert/context/summaries/overview.md
      - id: architecture
        type: hierarchical
        path: expert/context/summaries/architecture.md"""

    security_block = ""
    if with_secrets or not allow_remote_llm:
        security_items = []
        if with_secrets:
            security_items.append("  contains_secrets: true")
        if not allow_remote_llm:
            security_items.append("  allow_remote_llm: false")
        security_block = "security:\n" + "\n".join(security_items)

    return f"""ecp_version: "1.0"
id: test-expert
profile: codebase
skill:
  name: test-skill
description: A test expert
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
{summaries_block}
maintenance:
  policy_path: expert/maintenance/policy.json
evals:
  suites:
    - suite_id: smoke
      path: expert/evals/smoke.yaml
{security_block}
"""


def _minimal_policy_json() -> str:
    return json.dumps({
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
    }, indent=2)


def _minimal_eval_suite_yaml() -> str:
    return """suite_id: smoke
suite_version: '1.0'
cases:
  - case_id: noop
    mode: ephemeral
    question: hi
"""


def _create_test_skill(tmp: Path, *, with_summaries: bool = True, with_secrets: bool = False,
                       allow_remote_llm: bool = True, with_chunks: bool = True) -> Path:
    """Create a minimal test skill structure."""
    skill_root = tmp / "test-skill"

    _write(skill_root / "SKILL.md", _minimal_skill_md())
    _write(skill_root / "expert" / "EXPERT.yaml",
           _minimal_expert_yaml(with_summaries=with_summaries, with_secrets=with_secrets,
                              allow_remote_llm=allow_remote_llm))
    _write(skill_root / "expert" / "maintenance" / "policy.json", _minimal_policy_json())
    _write(skill_root / "expert" / "evals" / "smoke.yaml", _minimal_eval_suite_yaml())

    # Create source directory
    (skill_root / "source").mkdir(parents=True, exist_ok=True)
    _write(skill_root / "source" / "main.py", "def main():\n    print('Hello')\n")

    # Create index directory
    index_dir = skill_root / "expert" / "context" / "indexes" / "keyword-v1"
    index_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal index descriptor
    _write(index_dir / "index.json", json.dumps({
        "index_id": "keyword-v1",
        "index_type": "keyword",
        "version": "1.0",
    }))

    # Create minimal index_data.json
    _write(index_dir / "index_data.json", json.dumps({
        "format": "keyword-index-v2",
        "sources": [{"source_id": "main", "uri": "file:./source"}],
        "documents": {},
    }))

    # Create chunks if requested
    if with_chunks:
        chunks = [
            {
                "chunk_id": "1",
                "uri": "file:./source/main.py",
                "artifact_path": "source/main.py",
                "line_start": 1,
                "line_end": 2,
                "content": "def main():\n    print('Hello')\n",
            }
        ]
        with (index_dir / "chunks.jsonl").open("w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk) + "\n")

    return skill_root


class TestSecurityChecks(unittest.TestCase):
    """Tests for LLM security gating."""

    def test_security_blocks_when_contains_secrets(self):
        """Test that contains_secrets=true blocks all LLM providers."""
        manifest = {"security": {"contains_secrets": True}}

        with self.assertRaises(QueryError) as ctx:
            _check_llm_security(manifest, "ollama")
        self.assertIn("contains_secrets", str(ctx.exception))

        with self.assertRaises(QueryError) as ctx:
            _check_llm_security(manifest, "openrouter")
        self.assertIn("contains_secrets", str(ctx.exception))

    def test_security_allows_local_ollama_when_remote_disabled(self):
        """Test that allow_remote_llm=false allows Ollama but blocks OpenRouter."""
        manifest = {"security": {"allow_remote_llm": False}}

        # Should NOT raise for Ollama
        _check_llm_security(manifest, "ollama")

        # Should raise for OpenRouter
        with self.assertRaises(QueryError) as ctx:
            _check_llm_security(manifest, "openrouter")
        self.assertIn("allow_remote_llm", str(ctx.exception))

    def test_security_allows_all_when_remote_enabled(self):
        """Test that allow_remote_llm=true allows all providers."""
        manifest = {"security": {"allow_remote_llm": True}}

        # Should NOT raise for either
        _check_llm_security(manifest, "ollama")
        _check_llm_security(manifest, "openrouter")

    def test_security_with_empty_manifest(self):
        """Test default security behavior with empty manifest."""
        manifest = {}

        # Ollama should work (local)
        _check_llm_security(manifest, "ollama")

        # OpenRouter should be blocked by default (allow_remote_llm defaults to False)
        with self.assertRaises(QueryError):
            _check_llm_security(manifest, "openrouter")


class TestHelperFunctions(unittest.TestCase):
    """Tests for helper functions."""

    def test_format_chunks_for_prompt(self):
        """Test chunk formatting for prompts."""
        chunks = [
            {"artifact_path": "src/main.py", "line_start": 1, "line_end": 5, "content": "code here"},
            {"artifact_path": "src/utils.py", "line_start": 10, "line_end": 20, "content": "more code"},
        ]

        result = _format_chunks_for_prompt(chunks)

        self.assertIn("src/main.py:1-5", result)
        self.assertIn("code here", result)
        self.assertIn("src/utils.py:10-20", result)
        self.assertIn("more code", result)

    def test_format_chunks_truncates_long_content(self):
        """Test that long content is truncated."""
        chunks = [{"artifact_path": "file.py", "line_start": 1, "line_end": 1, "content": "x" * 600}]

        result = _format_chunks_for_prompt(chunks)

        # Should be truncated to ~500 chars + "..."
        self.assertTrue(len(result) < 600)
        self.assertIn("...", result)

    def test_format_chunks_respects_max_chars(self):
        """Test that total output respects max_chars limit."""
        chunks = [
            {"artifact_path": f"file{i}.py", "line_start": 1, "line_end": 1, "content": "code " * 100}
            for i in range(20)
        ]

        result = _format_chunks_for_prompt(chunks, max_chars=1000)

        self.assertTrue(len(result) <= 1100)  # Some margin for truncation

    def test_build_dir_tree(self):
        """Test directory tree building."""
        chunks = [
            {"artifact_path": "src/main.py"},
            {"artifact_path": "src/utils/helpers.py"},
            {"artifact_path": "tests/test_main.py"},
        ]

        result = _build_dir_tree(chunks)

        self.assertIn("src/", result)
        self.assertIn("src/utils/", result)
        self.assertIn("tests/", result)

    def test_build_dir_tree_empty_chunks(self):
        """Test directory tree with empty chunks."""
        result = _build_dir_tree([])
        self.assertEqual(result, "(no files found)")


class TestGenerateSummaries(unittest.TestCase):
    """Tests for the main generate_summaries function."""

    def test_generate_overview_summary_with_mock_llm(self):
        """Test generating overview summary with mocked LLM."""
        with tempfile.TemporaryDirectory() as tmp:
            skill_root = _create_test_skill(Path(tmp))
            bundle = load_skill_bundle(skill_root)

            mock_llm_response = "# Repository Overview\n\nThis is a test repository.\n"

            with patch("ecp_reference.summary_generator.ollama_chat_completion", return_value=mock_llm_response):
                result = generate_summaries(
                    skill_root=skill_root,
                    bundle=bundle,
                    llm="ollama",
                    llm_model="llama3.2",
                    dry_run=False,
                )

            self.assertIn("repo-overview", result.generated)
            self.assertEqual(len(result.failed), 0)

            # Check that the file was created
            overview_path = skill_root / "expert" / "context" / "summaries" / "overview.md"
            self.assertTrue(overview_path.exists())
            content = overview_path.read_text(encoding="utf-8")
            self.assertIn("Repository Overview", content)

    def test_dry_run_no_writes(self):
        """Test that dry run doesn't write files."""
        with tempfile.TemporaryDirectory() as tmp:
            skill_root = _create_test_skill(Path(tmp))
            bundle = load_skill_bundle(skill_root)

            mock_llm_response = "# Summary\n\nTest content.\n"

            with patch("ecp_reference.summary_generator.ollama_chat_completion", return_value=mock_llm_response):
                result = generate_summaries(
                    skill_root=skill_root,
                    bundle=bundle,
                    llm="ollama",
                    dry_run=True,
                )

            self.assertIn("repo-overview", result.generated)

            # Check that the file was NOT created
            overview_path = skill_root / "expert" / "context" / "summaries" / "overview.md"
            self.assertFalse(overview_path.exists())

    def test_security_blocks_remote_llm(self):
        """Test that security blocks remote LLM when contains_secrets=true."""
        with tempfile.TemporaryDirectory() as tmp:
            skill_root = _create_test_skill(Path(tmp), with_secrets=True)
            bundle = load_skill_bundle(skill_root)

            result = generate_summaries(
                skill_root=skill_root,
                bundle=bundle,
                llm="ollama",
            )

            self.assertEqual(len(result.generated), 0)
            self.assertTrue(any("contains_secrets" in err for err in result.errors))

    def test_unknown_llm_provider(self):
        """Test handling of unknown LLM provider."""
        with tempfile.TemporaryDirectory() as tmp:
            skill_root = _create_test_skill(Path(tmp))
            bundle = load_skill_bundle(skill_root)

            result = generate_summaries(
                skill_root=skill_root,
                bundle=bundle,
                llm="unknown_provider",
            )

            self.assertEqual(len(result.generated), 0)
            self.assertTrue(any("Unknown LLM provider" in err for err in result.errors))

    def test_no_summaries_declared(self):
        """Test handling when no summaries are declared."""
        with tempfile.TemporaryDirectory() as tmp:
            skill_root = _create_test_skill(Path(tmp), with_summaries=False)
            bundle = load_skill_bundle(skill_root)

            result = generate_summaries(
                skill_root=skill_root,
                bundle=bundle,
                llm="ollama",
            )

            self.assertEqual(len(result.generated), 0)
            self.assertTrue(any("No summaries declared" in err for err in result.errors))

    def test_no_chunks_available(self):
        """Test handling when no chunks are available."""
        with tempfile.TemporaryDirectory() as tmp:
            skill_root = _create_test_skill(Path(tmp), with_chunks=False)
            bundle = load_skill_bundle(skill_root)

            result = generate_summaries(
                skill_root=skill_root,
                bundle=bundle,
                llm="ollama",
            )

            self.assertEqual(len(result.generated), 0)
            self.assertTrue(any("No chunks found" in err for err in result.errors))

    def test_specific_summary_ids(self):
        """Test generating only specific summary IDs."""
        with tempfile.TemporaryDirectory() as tmp:
            skill_root = _create_test_skill(Path(tmp))
            bundle = load_skill_bundle(skill_root)

            mock_llm_response = "# Summary\n\nTest content.\n"

            with patch("ecp_reference.summary_generator.ollama_chat_completion", return_value=mock_llm_response):
                result = generate_summaries(
                    skill_root=skill_root,
                    bundle=bundle,
                    llm="ollama",
                    summary_ids=["repo-overview"],  # Only generate this one
                    dry_run=True,
                )

            # Should only generate repo-overview, not architecture
            self.assertEqual(result.generated, ["repo-overview"])

    def test_llm_failure_handling(self):
        """Test handling of LLM failures during generation."""
        with tempfile.TemporaryDirectory() as tmp:
            skill_root = _create_test_skill(Path(tmp))
            bundle = load_skill_bundle(skill_root)

            with patch("ecp_reference.summary_generator.ollama_chat_completion",
                      side_effect=RuntimeError("LLM connection failed")):
                result = generate_summaries(
                    skill_root=skill_root,
                    bundle=bundle,
                    llm="ollama",
                )

            # All should fail
            self.assertEqual(len(result.generated), 0)
            self.assertTrue(len(result.failed) > 0)
            self.assertTrue(any("LLM connection failed" in err for err in result.errors))

    def test_duration_tracking(self):
        """Test that duration is tracked in the result."""
        with tempfile.TemporaryDirectory() as tmp:
            skill_root = _create_test_skill(Path(tmp))
            bundle = load_skill_bundle(skill_root)

            mock_llm_response = "# Summary\n\nTest content.\n"

            with patch("ecp_reference.summary_generator.ollama_chat_completion", return_value=mock_llm_response):
                result = generate_summaries(
                    skill_root=skill_root,
                    bundle=bundle,
                    llm="ollama",
                    dry_run=True,
                )

            self.assertIsInstance(result.duration_seconds, float)
            self.assertGreaterEqual(result.duration_seconds, 0)


class TestSummaryGenerationResult(unittest.TestCase):
    """Tests for SummaryGenerationResult dataclass."""

    def test_dataclass_fields(self):
        """Test that all expected fields are present."""
        result = SummaryGenerationResult(
            generated=["a", "b"],
            skipped=["c"],
            failed=["d"],
            errors=["error message"],
            duration_seconds=1.5,
        )

        self.assertEqual(result.generated, ["a", "b"])
        self.assertEqual(result.skipped, ["c"])
        self.assertEqual(result.failed, ["d"])
        self.assertEqual(result.errors, ["error message"])
        self.assertEqual(result.duration_seconds, 1.5)


if __name__ == "__main__":
    unittest.main()
