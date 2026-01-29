from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


class TestDemoIntegration(unittest.TestCase):
    def _run_cli(self, *args: str, cwd: Path, env: dict[str, str]) -> str:
        p = subprocess.run(
            [sys.executable, "-m", "ecp_reference.cli", *args],
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
        )
        if p.returncode != 0:
            msg = (
                f"ecpctl failed: {' '.join(args)}\n"
                f"returncode={p.returncode}\n"
                f"stdout:\n{p.stdout}\n"
                f"stderr:\n{p.stderr}\n"
            )
            self.fail(msg)
        return p.stdout

    def test_conformance_pack_demo_script_flow(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        skill_dir = repo_root / "examples" / "ecp-conformance-pack"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root / "src") + os.pathsep + env.get("PYTHONPATH", "")

        self._run_cli("validate", "--strict", "--with-artifacts", "--skill", str(skill_dir), cwd=repo_root, env=env)

        out = self._run_cli(
            "query",
            "--json",
            "--skill",
            str(skill_dir),
            "Which modules handle authentication?",
            cwd=repo_root,
            env=env,
        )
        data = json.loads(out)
        self.assertIsInstance(data.get("answer"), str)
        self.assertIsInstance(data.get("citations"), list)
        self.assertTrue(data.get("citations"), "expected query to return citations")

        self._run_cli("run-evals", "--skill", str(skill_dir), "--suite-id", "conformance", cwd=repo_root, env=env)

        with tempfile.TemporaryDirectory(prefix="ecp_demo_") as td:
            zip_path = Path(td) / "ecp-conformance-pack.zip"
            unpack_dir = Path(td) / "unpacked"
            unpack_dir.mkdir(parents=True, exist_ok=True)

            self._run_cli("pack", "--skill", str(skill_dir), "--out", str(zip_path), cwd=repo_root, env=env)
            self._run_cli("verify-pack", "--package", str(zip_path), cwd=repo_root, env=env)

            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(unpack_dir)

            pkg_candidates = list(unpack_dir.rglob("expert/package.json"))
            self.assertEqual(len(pkg_candidates), 1, f"expected 1 expert/package.json, got {len(pkg_candidates)}")
            unpacked_skill_dir = pkg_candidates[0].parent.parent

            self._run_cli(
                "validate",
                "--strict",
                "--with-artifacts",
                "--skill",
                str(unpacked_skill_dir),
                cwd=repo_root,
                env=env,
            )
            self._run_cli(
                "query",
                "--json",
                "--skill",
                str(unpacked_skill_dir),
                "Which modules handle authentication?",
                cwd=repo_root,
                env=env,
            )
            self._run_cli(
                "run-evals",
                "--skill",
                str(unpacked_skill_dir),
                "--suite-id",
                "conformance",
                cwd=repo_root,
                env=env,
            )
