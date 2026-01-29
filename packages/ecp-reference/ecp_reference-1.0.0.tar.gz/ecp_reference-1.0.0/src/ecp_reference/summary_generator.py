from __future__ import annotations

import dataclasses
import json
import os
import time
from pathlib import Path
from typing import Any, Callable

from .errors import QueryError
from .llm_ollama import DEFAULT_OLLAMA_MODEL, ollama_chat_completion
from .llm_openrouter import DEFAULT_OPENROUTER_MODEL, openrouter_chat_completion
from .skill_loader import SkillBundle
from .utils import rfc3339_now, write_yaml


@dataclasses.dataclass
class SummaryGenerationResult:
    """Result of summary generation operation."""
    generated: list[str]      # Summary IDs that were generated
    skipped: list[str]        # Summary IDs skipped (no LLM configured)
    failed: list[str]         # Summary IDs that failed
    errors: list[str]         # Error messages for failures
    duration_seconds: float


# Type alias for LLM callable
LLMFunc = Callable[[list[dict[str, str]], int], str]


def _check_llm_security(manifest: dict, llm: str) -> None:
    """Validate that LLM usage is allowed by security settings.

    Security gating:
    - contains_secrets: true => BLOCK all LLM providers
    - allow_remote_llm: false => BLOCK remote providers (openrouter), ALLOW local (ollama)
    - allow_remote_llm: true => Check allowlist (if any)
    """
    security = manifest.get("security") or {}

    # Block all LLM if contains_secrets
    if security.get("contains_secrets"):
        raise QueryError(
            "LLM summary generation disabled: security.contains_secrets=true. "
            "Remove secrets from source or use pre-generated summaries."
        )

    # Block remote LLM if not allowed
    if llm == "openrouter":
        if not security.get("allow_remote_llm", False):
            raise QueryError(
                "Remote LLM summary generation disabled: security.allow_remote_llm=false. "
                "Use --llm ollama for local processing, or enable allow_remote_llm in EXPERT.yaml."
            )


def _load_chunks_from_index(index_dir: Path, max_chunks: int = 500) -> list[dict]:
    """Load chunk records from an index's chunks.jsonl file."""
    chunks_path = index_dir / "chunks.jsonl"
    if not chunks_path.exists():
        return []

    chunks: list[dict] = []
    with chunks_path.open("r", encoding="utf-8") as f:
        for line in f:
            if max_chunks and len(chunks) >= max_chunks:
                break
            s = line.strip()
            if not s:
                continue
            try:
                chunks.append(json.loads(s))
            except json.JSONDecodeError:
                continue
    return chunks


def _get_index_dirs(bundle: SkillBundle) -> list[Path]:
    """Get all index directories from the manifest."""
    artifacts = (bundle.manifest.get("context") or {}).get("artifacts") or {}
    indexes = artifacts.get("indexes") or []
    dirs: list[Path] = []
    for idx in indexes:
        if not isinstance(idx, dict):
            continue
        idx_path = idx.get("path")
        if idx_path:
            idx_dir = bundle.skill_root / idx_path
            if idx_dir.exists():
                dirs.append(idx_dir)
    return dirs


def _get_summary_declarations(manifest: dict) -> list[dict]:
    """Get summary declarations from manifest."""
    artifacts = (manifest.get("context") or {}).get("artifacts") or {}
    return artifacts.get("summaries") or []


def _make_llm_func(llm: str, llm_model: str | None, llm_timeout_seconds: int) -> LLMFunc:
    """Create an LLM function based on provider."""

    def call_llm(messages: list[dict[str, str]], timeout: int) -> str:
        if llm == "ollama":
            model = llm_model or os.environ.get("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL
            return ollama_chat_completion(
                model=model,
                messages=messages,
                timeout_seconds=timeout,
            )
        elif llm == "openrouter":
            api_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
            if not api_key:
                raise QueryError(
                    "OPENROUTER_API_KEY not set; required for --llm openrouter."
                )
            model = llm_model or os.environ.get("OPENROUTER_MODEL") or DEFAULT_OPENROUTER_MODEL
            return openrouter_chat_completion(
                api_key=api_key,
                model=model,
                messages=messages,
                timeout_seconds=timeout,
            )
        else:
            raise QueryError(f"Unknown LLM provider: {llm}")

    return call_llm


# ============================================================================
# Prompt Templates
# ============================================================================

OVERVIEW_SYSTEM_PROMPT = """You are a technical documentation expert.
Generate a concise repository overview based on the provided code chunks.
Focus on: purpose, architecture, key components, and technologies used.
Be accurate and grounded in the evidence provided."""

OVERVIEW_USER_PROMPT = """Based on the following code excerpts from a repository, generate a comprehensive overview summary.

Code excerpts:
{chunks}

Generate a Markdown summary with these sections:
1. **Purpose**: What does this codebase do? (2-3 sentences)
2. **Architecture**: High-level structure and design patterns
3. **Key Components**: Main modules/packages and their responsibilities
4. **Technologies**: Languages, frameworks, and key dependencies
5. **Getting Started**: Entry points for developers new to the codebase

Keep the summary concise (300-500 words) and grounded in the code evidence."""


HIERARCHICAL_SYSTEM_PROMPT = """You are a technical documentation expert.
Generate a hierarchical summary of a codebase based on its directory structure and code samples.
Focus on explaining the purpose and contents of each major directory."""

HIERARCHICAL_USER_PROMPT = """Based on the directory structure and code excerpts below, generate a hierarchical summary.

Directory tree:
{dir_tree}

Code excerpts:
{chunks}

Generate a Markdown summary that:
1. Describes each major directory's purpose
2. Lists key files and their roles
3. Explains relationships between components
4. Uses proper indentation to show hierarchy

Format as a hierarchical outline with bullet points."""


CHANGELOG_SYSTEM_PROMPT = """You are a technical writer specializing in release notes.
Generate a changelog summary based on git history and code changes.
Focus on user-facing changes, bug fixes, and new features."""

CHANGELOG_USER_PROMPT = """Based on the following git log and code changes, generate a changelog summary.

Recent commits:
{git_log}

Changed code excerpts:
{chunks}

Generate a Markdown changelog with:
1. **New Features**: Significant new functionality
2. **Improvements**: Enhancements to existing features
3. **Bug Fixes**: Issues that were resolved
4. **Breaking Changes**: Changes that affect backward compatibility

Group by type and include brief descriptions. Reference commits where relevant."""


TOPIC_SYSTEM_PROMPT = """You are a technical documentation expert.
Generate a focused summary on a specific topic or subsystem.
Be precise and cite specific code locations."""

TOPIC_USER_PROMPT = """Generate a summary focused on the topic: "{topic_id}"

Relevant code excerpts:
{chunks}

Generate a Markdown summary that:
1. Explains what this component/feature does
2. Describes key classes, functions, or modules involved
3. Shows example usage patterns if visible in the code
4. Notes any dependencies or interactions with other parts

Keep it concise (200-400 words) and cite specific files."""


# ============================================================================
# Summary Generation Functions
# ============================================================================

def _format_chunks_for_prompt(chunks: list[dict], max_chars: int = 8000) -> str:
    """Format chunks into a string for LLM prompts."""
    lines: list[str] = []
    total_chars = 0

    for chunk in chunks:
        path = chunk.get("artifact_path") or chunk.get("uri") or "unknown"
        line_start = chunk.get("line_start", 1)
        line_end = chunk.get("line_end", line_start)
        content = chunk.get("content") or ""

        # Truncate long content
        if len(content) > 500:
            content = content[:497] + "..."

        entry = f"--- {path}:{line_start}-{line_end} ---\n{content}"

        if total_chars + len(entry) > max_chars:
            break

        lines.append(entry)
        total_chars += len(entry)

    return "\n\n".join(lines)


def _build_dir_tree(chunks: list[dict]) -> str:
    """Build a directory tree string from chunk paths."""
    paths: set[str] = set()
    for chunk in chunks:
        path = chunk.get("artifact_path") or ""
        if path:
            paths.add(path)

    if not paths:
        return "(no files found)"

    # Sort and deduplicate directories
    dirs: set[str] = set()
    for p in sorted(paths):
        parts = p.split("/")
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]) + "/")
        dirs.add(p)

    # Format as tree
    return "\n".join(sorted(dirs))


def _generate_overview(
    chunks: list[dict],
    llm_func: LLMFunc,
    timeout: int,
) -> str:
    """Generate an overview summary."""
    chunks_text = _format_chunks_for_prompt(chunks)
    user_prompt = OVERVIEW_USER_PROMPT.format(chunks=chunks_text)

    return llm_func(
        [
            {"role": "system", "content": OVERVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        timeout,
    )


def _generate_hierarchical(
    chunks: list[dict],
    llm_func: LLMFunc,
    timeout: int,
) -> str:
    """Generate a hierarchical summary."""
    chunks_text = _format_chunks_for_prompt(chunks, max_chars=6000)
    dir_tree = _build_dir_tree(chunks)
    user_prompt = HIERARCHICAL_USER_PROMPT.format(dir_tree=dir_tree, chunks=chunks_text)

    return llm_func(
        [
            {"role": "system", "content": HIERARCHICAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        timeout,
    )


def _generate_changelog(
    chunks: list[dict],
    git_log: str,
    llm_func: LLMFunc,
    timeout: int,
) -> str:
    """Generate a changelog summary."""
    chunks_text = _format_chunks_for_prompt(chunks, max_chars=6000)
    user_prompt = CHANGELOG_USER_PROMPT.format(git_log=git_log, chunks=chunks_text)

    return llm_func(
        [
            {"role": "system", "content": CHANGELOG_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        timeout,
    )


def _generate_topic(
    chunks: list[dict],
    topic_id: str,
    llm_func: LLMFunc,
    timeout: int,
) -> str:
    """Generate a topic-focused summary."""
    chunks_text = _format_chunks_for_prompt(chunks)
    user_prompt = TOPIC_USER_PROMPT.format(topic_id=topic_id, chunks=chunks_text)

    return llm_func(
        [
            {"role": "system", "content": TOPIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        timeout,
    )


def _write_summary_file(
    skill_root: Path,
    summary_path: str,
    content: str,
    summary_id: str,
    llm: str,
    llm_model: str | None,
) -> None:
    """Write generated summary to file."""
    out_path = skill_root / summary_path

    # Ensure parent directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Detect format from path extension
    ext = out_path.suffix.lower()

    if ext in (".yaml", ".yml"):
        # Write as YAML with metadata
        data = {
            "summary_id": summary_id,
            "generated_at": rfc3339_now(),
            "generator": {
                "provider": llm,
                "model": llm_model or "(default)",
            },
            "content": content,
        }
        write_yaml(out_path, data)
    else:
        # Write as plain markdown/text
        header = f"<!-- Generated by ECP PoC using {llm} at {rfc3339_now()} -->\n\n"
        out_path.write_text(header + content, encoding="utf-8")


def generate_summaries(
    *,
    skill_root: Path,
    bundle: SkillBundle,
    llm: str,
    llm_model: str | None = None,
    llm_timeout_seconds: int = 120,
    summary_ids: list[str] | None = None,
    dry_run: bool = False,
) -> SummaryGenerationResult:
    """Generate LLM-powered summaries for an ECP skill.

    Args:
        skill_root: Path to the skill directory
        bundle: Loaded SkillBundle
        llm: LLM provider ("ollama" or "openrouter")
        llm_model: Optional model name override
        llm_timeout_seconds: Timeout for LLM requests
        summary_ids: Optional list of specific summary IDs to generate
        dry_run: If True, don't write files

    Returns:
        SummaryGenerationResult with generated/skipped/failed lists
    """
    start_time = time.monotonic()

    generated: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []
    errors: list[str] = []

    # Validate LLM provider
    llm = (llm or "").strip().lower()
    if llm not in ("ollama", "openrouter"):
        return SummaryGenerationResult(
            generated=[],
            skipped=[],
            failed=[],
            errors=[f"Unknown LLM provider: {llm}"],
            duration_seconds=time.monotonic() - start_time,
        )

    # Security check
    try:
        _check_llm_security(bundle.manifest, llm)
    except QueryError as e:
        return SummaryGenerationResult(
            generated=[],
            skipped=[],
            failed=[],
            errors=[str(e)],
            duration_seconds=time.monotonic() - start_time,
        )

    # Get summary declarations
    summaries = _get_summary_declarations(bundle.manifest)
    if not summaries:
        return SummaryGenerationResult(
            generated=[],
            skipped=[],
            failed=[],
            errors=["No summaries declared in context.artifacts.summaries"],
            duration_seconds=time.monotonic() - start_time,
        )

    # Filter to requested summary IDs if specified
    if summary_ids:
        summary_set = set(summary_ids)
        summaries = [s for s in summaries if s.get("id") in summary_set]

    # Load chunks from all indexes
    index_dirs = _get_index_dirs(bundle)
    all_chunks: list[dict] = []
    for idx_dir in index_dirs:
        all_chunks.extend(_load_chunks_from_index(idx_dir))

    if not all_chunks:
        return SummaryGenerationResult(
            generated=[],
            skipped=[],
            failed=[],
            errors=["No chunks found in indexes. Run 'ecpctl build' first."],
            duration_seconds=time.monotonic() - start_time,
        )

    # Create LLM function
    llm_func = _make_llm_func(llm, llm_model, llm_timeout_seconds)

    # Generate each summary
    for summary_decl in summaries:
        summary_id = summary_decl.get("id") or "unknown"
        summary_type = summary_decl.get("type") or "overview"
        summary_path = summary_decl.get("path") or f"expert/context/summaries/{summary_id}.md"

        try:
            # Generate based on type
            if summary_type == "overview" or summary_type == "repo-overview":
                content = _generate_overview(all_chunks, llm_func, llm_timeout_seconds)
            elif summary_type == "hierarchical":
                content = _generate_hierarchical(all_chunks, llm_func, llm_timeout_seconds)
            elif summary_type == "changelog":
                # For changelog, we'd ideally have git log - use placeholder
                git_log = "(Git log not available - using code structure)"
                content = _generate_changelog(all_chunks, git_log, llm_func, llm_timeout_seconds)
            elif summary_type == "topic":
                # Topic summaries use their ID as the topic
                content = _generate_topic(all_chunks, summary_id, llm_func, llm_timeout_seconds)
            else:
                # Default to overview for unknown types
                content = _generate_overview(all_chunks, llm_func, llm_timeout_seconds)

            if not dry_run:
                _write_summary_file(
                    skill_root=skill_root,
                    summary_path=summary_path,
                    content=content,
                    summary_id=summary_id,
                    llm=llm,
                    llm_model=llm_model,
                )

            generated.append(summary_id)

        except Exception as e:
            failed.append(summary_id)
            errors.append(f"{summary_id}: {e}")

    return SummaryGenerationResult(
        generated=generated,
        skipped=skipped,
        failed=failed,
        errors=errors,
        duration_seconds=time.monotonic() - start_time,
    )
