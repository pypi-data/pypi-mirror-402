from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from ecp_reference.evals import _validate_response_citations, run_eval_suites
from ecp_reference.errors import ECPError
from ecp_reference.indexer import SourceSpec, build_keyword_index_multi
from ecp_reference.packaging import create_skill_package
from ecp_reference.runtime import query_expert
from ecp_reference.skill_loader import load_skill_bundle


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _run(cmd: list[str], *, cwd: Path) -> str:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=True)
    return (p.stdout or "").strip()


def _init_git_repo(repo: Path) -> str:
    repo.mkdir(parents=True, exist_ok=True)
    _run(["git", "init"], cwd=repo)
    _run(["git", "config", "user.email", "test@example.com"], cwd=repo)
    _run(["git", "config", "user.name", "Test User"], cwd=repo)
    _run(["git", "config", "core.autocrlf", "false"], cwd=repo)
    _run(["git", "config", "core.eol", "lf"], cwd=repo)
    return repo.as_posix()


def _commit_all(repo: Path, message: str) -> str:
    _run(["git", "add", "-A"], cwd=repo)
    _run(["git", "commit", "-m", message], cwd=repo)
    return _run(["git", "rev-parse", "HEAD"], cwd=repo)


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


def _minimal_skill_md(*, name: str) -> str:
    return (
        "---\n"
        f"name: {name}\n"
        "description: test skill\n"
        "---\n\n"
        "# Test Skill\n"
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


def _conformance_eval_suite_yaml(*, source_id: str, must_cite: str) -> str:
    return (
        "suite_id: conformance\n"
        "suite_version: '1.0'\n"
        "cases:\n"
        "  - case_id: cite-auth\n"
        "    mode: ephemeral\n"
        "    question: Where is login implemented?\n"
        "    filters:\n"
        f"      source_id: {source_id}\n"
        "    assertions:\n"
        "      response_must_include_fields:\n"
        "        - answer\n"
        "        - as_of\n"
        "        - citations\n"
        "        - chunks\n"
        "        - synthesis\n"
        "      as_of_must_include_source_ids:\n"
        f"        - {source_id}\n"
        "      min_citations: 1\n"
        "      must_cite_source_ids:\n"
        f"        - {source_id}\n"
        "      must_cite:\n"
        f"        - {must_cite}\n"
        "      citations_must_resolve: true\n"
        "      citations_must_match_snippets: true\n"
        "      citations_must_match_hashes: true\n"
    )


class TestProvenanceAndCitations(unittest.TestCase):
    def test_pack_refuses_codebase_without_pinned_git_commit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "codebase-skill"
            _write(root / "SKILL.md", _minimal_skill_md(name=root.name))
            _write(
                root / "expert" / "maintenance" / "policy.json",
                _minimal_policy_json(suite_id="smoke"),
            )
            _write(
                root / "expert" / "evals" / "smoke.yaml",
                _minimal_eval_suite_yaml(suite_id="smoke"),
            )
            _write(root / "expert" / "context" / "summaries" / "overview.md", "# ok\n")

            # Git source is intentionally *not* commit-pinned.
            expert_yaml = (
                "ecp_version: '1.0'\n"
                f"id: {root.name}\n"
                "profile: codebase\n"
                "skill:\n"
                f"  name: {root.name}\n"
                "sources:\n"
                "  - source_id: repo\n"
                "    type: git\n"
                "    uri: expert/sources/repo\n"
                "    scope:\n"
                "      include: ['**/*']\n"
                "      exclude: ['**/.git/**']\n"
                "    revision:\n"
                "      commit: HEAD\n"
                "      timestamp: '2026-01-01T00:00:00Z'\n"
                "    refresh:\n"
                "      strategy: none\n"
                "context:\n"
                "  strategy: hybrid\n"
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
            )
            _write(root / "expert" / "EXPERT.yaml", expert_yaml)

            with self.assertRaises(ECPError) as ctx:
                create_skill_package(root, out_path=Path(td) / "out.zip")
            msg = str(ctx.exception)
            self.assertIn("Refusing to package", msg)
            self.assertIn("revision.commit", msg)
            self.assertIn("HEAD", msg)

    def test_conformance_fails_without_git_commit_pinning(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "git-skill"
            repo = root / "expert" / "sources" / "repo"
            _init_git_repo(repo)
            _write(repo / "auth.py", "def login():\n    return 'ok'\n")
            commit = _commit_all(repo, "init")

            # Build a keyword-index-v2 over the git repo.
            index_dir = root / "expert" / "context" / "indexes" / "kw-v2"
            src = SourceSpec(
                source_id="repo",
                source_type="git",
                source_uri="expert/sources/repo",
                source_root=repo,
                include=["**/*"],
                exclude=["**/.git/**"],
                revision={"commit": commit, "timestamp": "2026-01-01T00:00:00Z"},
            )
            build_keyword_index_multi(index_id="kw-v2", sources=[src], out_dir=index_dir)

            _write(root / "SKILL.md", _minimal_skill_md(name=root.name))
            _write(
                root / "expert" / "maintenance" / "policy.json",
                _minimal_policy_json(suite_id="conformance"),
            )
            _write(
                root / "expert" / "evals" / "conformance.yaml",
                _conformance_eval_suite_yaml(source_id="repo", must_cite="auth.py"),
            )

            # Missing revision.commit in the manifest means citations are not commit-pinned.
            expert_yaml = (
                "ecp_version: '1.0'\n"
                f"id: {root.name}\n"
                "profile: codebase\n"
                "skill:\n"
                f"  name: {root.name}\n"
                "security:\n"
                "  allow_remote_llm: false\n"
                "sources:\n"
                "  - source_id: repo\n"
                "    type: git\n"
                "    uri: expert/sources/repo\n"
                "    scope:\n"
                "      include: ['**/*']\n"
                "      exclude: ['**/.git/**']\n"
                "    revision:\n"
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
                "    - suite_id: conformance\n"
                "      path: expert/evals/conformance.yaml\n"
            )
            _write(root / "expert" / "EXPERT.yaml", expert_yaml)

            bundle = load_skill_bundle(root)
            report = run_eval_suites(bundle, suite_ids=["conformance"])
            self.assertFalse(report.get("passed"))

            failures = report["suites"][0]["cases"][0]["failures"]
            self.assertTrue(any("git citation missing revision.commit" in f for f in failures))

    def test_conformance_detects_tampered_filesystem_corpus(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "fs-skill"
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
                _minimal_policy_json(suite_id="conformance"),
            )
            _write(
                root / "expert" / "evals" / "conformance.yaml",
                _conformance_eval_suite_yaml(source_id="repo", must_cite="auth.py"),
            )

            expert_yaml = (
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
                "    - suite_id: conformance\n"
                "      path: expert/evals/conformance.yaml\n"
            )
            _write(root / "expert" / "EXPERT.yaml", expert_yaml)

            bundle = load_skill_bundle(root)
            report_ok = run_eval_suites(bundle, suite_ids=["conformance"])
            self.assertTrue(report_ok.get("passed"))

            # Tamper the corpus without rebuilding indexes: hash checks must fail deterministically.
            _write(repo / "auth.py", "def login():\n    return 'tampered'\n")

            report_bad = run_eval_suites(bundle, suite_ids=["conformance"])
            self.assertFalse(report_bad.get("passed"))
            failures = report_bad["suites"][0]["cases"][0]["failures"]
            self.assertTrue(any("chunk_hash mismatch" in f for f in failures))

    def test_snippet_mismatch_reports_expected_and_actual_hashes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ecp_test_") as td:
            root = Path(td) / "fs-skill-snippet"
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
                _minimal_policy_json(suite_id="conformance"),
            )
            _write(
                root / "expert" / "evals" / "conformance.yaml",
                _conformance_eval_suite_yaml(source_id="repo", must_cite="auth.py"),
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
                    "    - suite_id: conformance\n"
                    "      path: expert/evals/conformance.yaml\n"
                ),
            )

            bundle = load_skill_bundle(root)
            resp = query_expert(root, question="Where is login implemented?", mode="ephemeral", top_k=1)
            self.assertIsInstance(resp.get("chunks"), list)
            self.assertGreaterEqual(len(resp.get("chunks") or []), 1)
            resp["chunks"][0]["snippet"] = "tampered\n"

            failures = _validate_response_citations(
                bundle,
                resp,
                must_resolve=True,
                must_match_snippets=True,
                must_match_hashes=False,
            )
            self.assertTrue(any("expected_sha256" in f and "got_sha256" in f for f in failures))
