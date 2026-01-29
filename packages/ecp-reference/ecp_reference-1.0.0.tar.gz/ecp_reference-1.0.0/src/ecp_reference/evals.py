from __future__ import annotations

import dataclasses
import re
import subprocess
from pathlib import Path
from typing import Any

from .errors import EvalValidationError
from .maintenance import parse_file_uri
from .runtime import query_expert
from .skill_loader import SkillBundle
from .utils import (
    normalize_newlines,
    read_text_file,
    resolve_under_root,
    sha256_bytes,
    within_scope,
)

_GIT_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")

@dataclasses.dataclass
class CaseResult:
    case_id: str
    passed: bool
    failures: list[str]
    response: dict | None = None

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "failures": self.failures,
        }

def _assert_contains(haystack: str, needles: list[str], *, label: str) -> list[str]:
    failures: list[str] = []
    for n in needles:
        if n not in haystack:
            failures.append(f"{label} must include '{n}'")
    return failures

def _assert_not_contains(haystack: str, needles: list[str], *, label: str) -> list[str]:
    failures: list[str] = []
    for n in needles:
        if n in haystack:
            failures.append(f"{label} must NOT include '{n}'")
    return failures

def _assert_must_cite(citations: list[dict], must_cite: list[str]) -> list[str]:
    failures: list[str] = []
    cited_paths = [c.get("artifact_path", "") for c in citations]
    for m in must_cite:
        if not any(m in p for p in cited_paths):
            failures.append(f"must cite a source containing '{m}' (cited: {cited_paths})")
    return failures

def _assert_must_not_cite(citations: list[dict], must_not_cite: list[str]) -> list[str]:
    failures: list[str] = []
    cited_paths = [c.get("artifact_path", "") for c in citations]
    for m in must_not_cite:
        if any(m in p for p in cited_paths):
            failures.append(f"must NOT cite a source containing '{m}' (cited: {cited_paths})")
    return failures

def _assert_must_cite_source_ids(
    citations: list[dict], must_cite_source_ids: list[str]
) -> list[str]:
    failures: list[str] = []
    cited_source_ids = [c.get("source_id", "") for c in citations]
    for sid in must_cite_source_ids:
        if not any(str(sid) == str(x) for x in cited_source_ids):
            failures.append(f"must cite source_id '{sid}' (cited source_ids: {cited_source_ids})")
    return failures

def _assert_citation_count(
    citations: list[dict], *, min_citations: int | None, max_citations: int | None
) -> list[str]:
    failures: list[str] = []
    n = len(citations)
    if min_citations is not None and n < int(min_citations):
        failures.append(f"expected at least {int(min_citations)} citations (got {n})")
    if max_citations is not None and n > int(max_citations):
        failures.append(f"expected at most {int(max_citations)} citations (got {n})")
    return failures

def _assert_regex_matches(answer: str, patterns: list[str]) -> list[str]:
    failures: list[str] = []
    for raw in patterns:
        try:
            rx = re.compile(str(raw))
        except re.error as e:
            failures.append(f"invalid regex '{raw}': {e}")
            continue
        if not rx.search(answer):
            failures.append(f"answer must match /{raw}/")
    return failures

def _as_str_list(v: Any) -> list[str] | None:
    if v is None:
        return None
    if isinstance(v, str):
        return [v]
    if isinstance(v, list):
        out: list[str] = []
        for x in v:
            if x is None:
                continue
            out.append(str(x))
        return out
    return [str(v)]

def _assert_response_fields(resp: dict, fields: list[str]) -> list[str]:
    failures: list[str] = []
    for f in fields:
        key = str(f)
        if key not in resp:
            failures.append(f"response missing field '{key}'")
    return failures

def _as_of_source_ids(resp: dict) -> set[str]:
    as_of = resp.get("as_of")
    if not isinstance(as_of, dict):
        return set()

    out: set[str] = set()
    if as_of.get("source_id"):
        out.add(str(as_of.get("source_id")))

    sources = as_of.get("sources")
    if isinstance(sources, list):
        for e in sources:
            if isinstance(e, dict) and e.get("source_id"):
                out.add(str(e.get("source_id")))
    return out

def _assert_as_of_must_include_source_ids(resp: dict, expected: list[str]) -> list[str]:
    failures: list[str] = []
    got = _as_of_source_ids(resp)
    for sid in expected:
        if str(sid) not in got:
            failures.append(f"as_of missing source_id '{sid}' (got: {sorted(got)})")
    return failures

def _git_show_text(
    repo: Path,
    *,
    commit: str,
    rel_path: str,
    timeout_seconds: int = 20,
) -> str | None:
    try:
        p = subprocess.run(
            ["git", "-C", str(repo), "show", f"{commit}:{rel_path}"],
            capture_output=True,
            timeout=timeout_seconds,
        )
    except Exception:
        return None
    if p.returncode != 0:
        return None
    try:
        text = p.stdout.decode("utf-8")
    except Exception:
        text = p.stdout.decode("utf-8", errors="replace")
    return normalize_newlines(text)

def _git_commit_exists(repo: Path, *, commit: str, timeout_seconds: int = 20) -> bool:
    try:
        p = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", f"{commit}^{{commit}}"],
            capture_output=True,
            timeout=timeout_seconds,
        )
    except Exception:
        return False
    return p.returncode == 0

def _source_entry(bundle: SkillBundle, source_id: str) -> dict | None:
    sources = bundle.manifest.get("sources") or []
    if not isinstance(sources, list):
        return None
    for s in sources:
        if isinstance(s, dict) and str(s.get("source_id")) == str(source_id):
            return s
    return None

def _source_root(bundle: SkillBundle, *, source_id: str, fallback_uri: str | None = None) -> Path | None:
    if str(source_id) == "ecp_artifacts":
        return bundle.skill_root

    entry = _source_entry(bundle, source_id)
    uri = (entry or {}).get("uri") if isinstance(entry, dict) else None
    if not uri:
        uri = fallback_uri
    if not uri:
        return None
    try:
        return parse_file_uri(str(uri), base_dir=bundle.skill_root)
    except Exception:
        return None

def _source_scope(bundle: SkillBundle, source_id: str) -> tuple[list[str], list[str]] | None:
    entry = _source_entry(bundle, source_id)
    if not isinstance(entry, dict):
        return None
    scope = entry.get("scope") or {}
    if not isinstance(scope, dict):
        return None
    include = scope.get("include") or ["**/*"]
    exclude = scope.get("exclude") or []
    if not isinstance(include, list):
        include = [str(include)]
    if not isinstance(exclude, list):
        exclude = [str(exclude)]
    return ([str(x) for x in include if x is not None], [str(x) for x in exclude if x is not None])

def _hash_checkable_chunk_id(chunk_id: str) -> bool:
    if chunk_id.startswith("summary:"):
        return True
    return ("::" in chunk_id) and ("#L" in chunk_id)

def _validate_response_citations(
    bundle: SkillBundle,
    resp: dict,
    *,
    must_resolve: bool,
    must_match_snippets: bool,
    must_match_hashes: bool,
) -> list[str]:
    failures: list[str] = []
    chunks = resp.get("chunks") or []
    if not isinstance(chunks, list):
        return ["response.chunks must be an array when citation integrity checks are enabled"]

    for i, ch in enumerate(chunks):
        if not isinstance(ch, dict):
            continue
        snippet = normalize_newlines(str(ch.get("snippet") or ""))
        citation = ch.get("citation") or {}
        if not isinstance(citation, dict):
            failures.append(f"chunk[{i}].citation must be an object")
            continue

        source_id = str(citation.get("source_id") or "")
        source_type = str(citation.get("source_type") or "")
        artifact_path = citation.get("artifact_path")
        if not isinstance(artifact_path, str) or not artifact_path:
            failures.append(f"chunk[{i}] citation missing artifact_path")
            continue
        artifact_path = artifact_path.replace("\\", "/").lstrip("/")

        loc = citation.get("loc") if isinstance(citation.get("loc"), dict) else {}
        start_line = loc.get("start_line") or citation.get("line_start") or ch.get("line_start")
        end_line = loc.get("end_line") or citation.get("line_end") or ch.get("line_end")
        try:
            start_line_i = int(start_line)
            end_line_i = int(end_line)
        except Exception:
            failures.append(f"chunk[{i}] citation loc must include integer start_line/end_line")
            continue
        if start_line_i < 1 or end_line_i < start_line_i:
            failures.append(f"chunk[{i}] invalid loc range: {start_line_i}-{end_line_i}")
            continue

        scope = _source_scope(bundle, source_id)
        if scope is not None:
            inc, exc = scope
            if not within_scope(artifact_path, inc or ["**/*"], exc or []):
                failures.append(f"chunk[{i}] cited path out of scope for source_id={source_id}: {artifact_path}")

        root = _source_root(
            bundle,
            source_id=source_id,
            fallback_uri=str(citation.get("uri") or "") or None,
        )
        if root is None:
            failures.append(f"chunk[{i}] could not resolve source root for source_id={source_id}")
            continue

        revision = citation.get("revision") if isinstance(citation.get("revision"), dict) else {}
        commit = str(revision.get("commit") or "").strip()

        lines: list[str] | None = None
        if source_type == "git":
            if not commit:
                failures.append(
                    f"chunk[{i}] git citation missing revision.commit for {source_id}:{artifact_path}"
                )
                continue
            if commit.lower() == "head":
                failures.append(
                    f"chunk[{i}] git citation revision.commit must be a concrete commit hash (not 'HEAD') for {source_id}:{artifact_path}"
                )
                continue
            if not _GIT_COMMIT_RE.match(commit):
                failures.append(
                    f"chunk[{i}] git citation revision.commit must be a git commit hash (7-40 hex chars); got {commit!r} for {source_id}:{artifact_path}"
                )
                continue
            if not _git_commit_exists(root, commit=commit):
                failures.append(
                    f"chunk[{i}] git commit not found for {source_id}:{artifact_path}: {commit!r}"
                )
                continue
            text = _git_show_text(root, commit=commit, rel_path=artifact_path)
            if text is None:
                failures.append(
                    f"chunk[{i}] could not read cited file at git commit for {source_id}:{artifact_path}@{commit}"
                )
                continue
            lines = text.splitlines(keepends=True)

        if lines is None:
            try:
                abs_path = resolve_under_root(root, artifact_path)
            except Exception:
                failures.append(f"chunk[{i}] cited path escapes root: {artifact_path}")
                continue
            if not abs_path.exists():
                failures.append(f"chunk[{i}] cited file not found: {source_id}:{artifact_path}")
                continue
            try:
                text = read_text_file(abs_path)
                lines = text.splitlines(keepends=True)
            except Exception as e:
                failures.append(f"chunk[{i}] failed to read cited file: {source_id}:{artifact_path}: {e}")
                continue

        if not lines:
            failures.append(f"chunk[{i}] cited file is empty or unreadable: {source_id}:{artifact_path}")
            continue

        if end_line_i > len(lines):
            failures.append(
                f"chunk[{i}] loc end_line out of range for {source_id}:{artifact_path}: {end_line_i} > {len(lines)}"
            )
            continue

        expected = normalize_newlines("".join(lines[start_line_i - 1 : end_line_i]))

        if must_match_snippets and expected != snippet:
            expected_sha = sha256_bytes(expected.encode("utf-8"))
            got_sha = sha256_bytes(snippet.encode("utf-8"))
            where = f"{source_id}:{artifact_path}#L{start_line_i}-L{end_line_i}"
            where = f"{where}@{commit}" if source_type == "git" else where
            failures.append(
                f"chunk[{i}] snippet mismatch for {where} (expected_sha256 {expected_sha}, got_sha256 {got_sha})"
            )

        if must_match_hashes:
            chunk_id = str(citation.get("chunk_id") or "")
            chunk_hash = citation.get("chunk_hash")
            if isinstance(chunk_hash, str) and chunk_hash and _hash_checkable_chunk_id(chunk_id):
                got = sha256_bytes(snippet.encode("utf-8"))
                if got != chunk_hash:
                    where = f"{source_id}:{artifact_path}#L{start_line_i}-L{end_line_i}"
                    where = f"{where}@{commit}" if source_type == "git" else where
                    failures.append(
                        f"chunk[{i}] chunk_hash mismatch for {where} (expected {chunk_hash}, got {got})"
                    )

        if must_resolve and (start_line_i < 1 or end_line_i < 1):
            failures.append(f"chunk[{i}] invalid loc for {source_id}:{artifact_path}")

    return failures

def run_eval_suites(bundle: SkillBundle, *, suite_ids: list[str] | None = None) -> dict:
    suites = bundle.eval_suites
    if suite_ids:
        suites = [s for s in suites if s.suite_id in set(suite_ids)]
        if not suites:
            raise EvalValidationError(f"No eval suites matched requested ids: {suite_ids}")

    suite_reports: list[dict] = []
    all_passed = True

    for suite in suites:
        suite_data = suite.data
        cases = suite_data.get("cases") or []
        case_results: list[CaseResult] = []
        suite_passed = True

        for case in cases:
            case_id = case.get("case_id")
            mode = case.get("mode", "ephemeral")
            question = case.get("question")
            assertions = case.get("assertions") or {}
            filters = case.get("filters") or {}
            if not isinstance(filters, dict):
                filters = {}

            top_k = None
            if "top_k" in case:
                try:
                    top_k = int(case.get("top_k"))
                except Exception:
                    top_k = None
            if top_k is not None:
                top_k = max(1, min(top_k, 50))

            failures: list[str] = []
            try:
                resp = query_expert(
                    bundle.skill_root,
                    question=question,
                    mode=mode,
                    top_k=top_k if top_k is not None else 5,
                    source_ids=_as_str_list(filters.get("source_id") or filters.get("source_ids")),
                    path_prefixes=_as_str_list(filters.get("path_prefix") or filters.get("path_prefixes")),
                )
            except Exception as e:
                failures.append(f"query failed: {e}")
                resp = None

            if resp is not None:
                answer = resp.get("answer", "")
                citations = resp.get("citations", []) or []

                must_cite = list(assertions.get("must_cite") or [])
                failures += _assert_must_cite(citations, must_cite)

                failures += _assert_must_not_cite(
                    citations, list(assertions.get("must_not_cite") or [])
                )
                failures += _assert_must_cite_source_ids(
                    citations, list(assertions.get("must_cite_source_ids") or [])
                )
                min_citations = assertions.get("min_citations")
                max_citations = assertions.get("max_citations")
                failures += _assert_citation_count(
                    citations,
                    min_citations=int(min_citations) if min_citations is not None else None,
                    max_citations=int(max_citations) if max_citations is not None else None,
                )

                failures += _assert_contains(answer, list(assertions.get("answer_must_include") or []), label="answer")
                failures += _assert_not_contains(answer, list(assertions.get("answer_must_not_include") or []), label="answer")
                failures += _assert_regex_matches(
                    answer, list(assertions.get("answer_must_match") or [])
                )

                response_fields = _as_str_list(assertions.get("response_must_include_fields"))
                if response_fields:
                    failures += _assert_response_fields(resp, response_fields)

                as_of_expected = _as_str_list(assertions.get("as_of_must_include_source_ids"))
                if as_of_expected:
                    failures += _assert_as_of_must_include_source_ids(resp, as_of_expected)

                must_resolve = bool(assertions.get("citations_must_resolve", False))
                must_match_snippets = bool(assertions.get("citations_must_match_snippets", False))
                must_match_hashes = bool(assertions.get("citations_must_match_hashes", False))
                if must_resolve or must_match_snippets or must_match_hashes:
                    failures += _validate_response_citations(
                        bundle,
                        resp,
                        must_resolve=must_resolve,
                        must_match_snippets=must_match_snippets,
                        must_match_hashes=must_match_hashes,
                    )

                # Minimal citation coverage rule: if any must_cite is defined OR question length suggests non-trivial,
                # require at least 1 citation.
                if (must_cite or len((question or "").split()) >= 3) and len(citations) < 1:
                    failures.append("expected at least 1 citation for a non-trivial question")

            passed = len(failures) == 0
            suite_passed = suite_passed and passed
            all_passed = all_passed and passed
            case_results.append(CaseResult(case_id=case_id, passed=passed, failures=failures))

        suite_reports.append({
            "suite_id": suite.suite_id,
            "passed": suite_passed,
            "cases": [cr.to_dict() for cr in case_results],
        })

    return {"passed": all_passed, "suites": suite_reports}
