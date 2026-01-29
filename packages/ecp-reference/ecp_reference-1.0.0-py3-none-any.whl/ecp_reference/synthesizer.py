from __future__ import annotations

import os
from typing import Any, Sequence

from .errors import QueryError
from .llm_ollama import DEFAULT_OLLAMA_MODEL, ollama_chat_completion
from .llm_openrouter import DEFAULT_OPENROUTER_MODEL, openrouter_chat_completion
from .retriever import RetrievedChunk
from .utils import tokenize

def synthesize_answer(
    *,
    question: str,
    chunks: Sequence[RetrievedChunk],
    as_of: dict,
    mode: str = "ephemeral",
    max_chunks: int = 5,
    llm: str | None = None,
    llm_model: str | None = None,
    llm_timeout_seconds: int = 60,
) -> tuple[str, dict[str, Any]]:
    llm = (llm or "").strip().lower()
    if llm in ("", "none"):
        llm = ""
    if llm and llm not in ("openrouter", "ollama"):
        raise QueryError(f"Unknown LLM provider: {llm}")

    synthesis: dict[str, Any] = {
        "provider": "local",
        "method": "heuristic",
        "max_evidence_chunks": int(max(1, max_chunks)),
    }

    if not chunks:
        return (
            "I could not find any high-confidence matches in the current keyword index for the question:\n"
            f"- {question}\n\n"
            "Suggestions:\n"
            "- Use more concrete identifiers (module names, classes, function names).\n"
            "- Ask for a specific subsystem and timeframe (e.g., 'as of last release').\n"
        ), synthesis

    if llm == "openrouter":
        answer, model = _synthesize_with_openrouter(
            question=question,
            chunks=chunks,
            mode=mode,
            max_chunks=max_chunks,
            llm_model=llm_model,
            llm_timeout_seconds=llm_timeout_seconds,
        )
        return (
            answer,
            {
                "provider": "openrouter",
                "model": model,
                "method": "llm",
                "max_evidence_chunks": int(max(1, max_chunks)),
            },
        )

    if llm == "ollama":
        answer, model = _synthesize_with_ollama(
            question=question,
            chunks=chunks,
            mode=mode,
            max_chunks=max_chunks,
            llm_model=llm_model,
            llm_timeout_seconds=llm_timeout_seconds,
        )
        return (
            answer,
            {
                "provider": "ollama",
                "model": model,
                "method": "llm",
                "max_evidence_chunks": int(max(1, max_chunks)),
            },
        )

    def _first_nonempty_line(text: str) -> str:
        for ln in text.splitlines():
            s = ln.strip()
            if s:
                return s
        return ""

    qset = set(tokenize(question))

    def _preview_for(snippet: str) -> str:
        if qset:
            best_line = ""
            best_score = 0
            for ln in snippet.splitlines():
                s = ln.strip()
                if not s:
                    continue
                score = len(set(tokenize(s)) & qset)
                if score > best_score:
                    best_score = score
                    best_line = s
                    if best_score >= len(qset):
                        break
            if best_score > 0:
                return best_line
        return _first_nonempty_line(snippet)

    # Keep the answer concise; expose raw snippets separately via response.chunks[].
    items: list[tuple[str, str, int, int, str]] = []
    seen: set[tuple[str, str, int, int]] = set()
    for ch in list(chunks):
        src = getattr(ch.citation, "source_id", "") or ""
        key = (src, ch.path, int(ch.line_start), int(ch.line_end))
        if key in seen:
            continue
        seen.add(key)
        preview = _preview_for(ch.snippet)
        if len(preview) > 180:
            preview = preview[:177] + "..."
        items.append((src, ch.path, int(ch.line_start), int(ch.line_end), preview))
        if len(items) >= max_chunks:
            break

    lines: list[str] = []
    lines.append("Most relevant locations:")
    for src, path, line_start, line_end, preview in items:
        src_prefix = f"[{src}] " if src else ""
        lines.append(f"- {src_prefix}{path} (lines {line_start}-{line_end})")
        if preview:
            lines.append(f"  - {preview}")

    if mode == "summarized":
        lines.append("")
        lines.append("Mode: summarized (prefers declared summaries when available).")

    return ("\n".join(lines).rstrip() + "\n"), synthesis


def _synthesize_with_openrouter(
    *,
    question: str,
    chunks: Sequence[RetrievedChunk],
    mode: str,
    max_chunks: int,
    llm_model: str | None,
    llm_timeout_seconds: int,
) -> tuple[str, str]:
    api_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if not api_key:
        raise QueryError(
            "OPENROUTER_API_KEY is not set; required for --llm openrouter. "
            "Set OPENROUTER_API_KEY or omit --llm to use the local synthesizer."
        )

    model = (llm_model or os.environ.get("OPENROUTER_MODEL") or DEFAULT_OPENROUTER_MODEL).strip()

    used = list(chunks)[: max(1, max_chunks)]
    evidence: list[str] = []
    for i, ch in enumerate(used, start=1):
        sid = getattr(ch.citation, "source_id", "") or ""
        src_prefix = f"{sid}:" if sid else ""
        loc = f"{src_prefix}{ch.path}#L{int(ch.line_start)}-L{int(ch.line_end)}"
        snippet = ch.snippet.strip()
        if len(snippet) > 1800:
            snippet = snippet[:1797] + "..."
        evidence.append(f"[E{i}] {loc}\n{snippet}")

    system = (
        "You are a careful technical assistant.\n"
        "Answer the user's question using ONLY the provided evidence excerpts.\n"
        "If the evidence is insufficient, say so and suggest what to look for next.\n"
        "Cite evidence by referencing the excerpt IDs like [E1], [E2] in your answer.\n"
        "Do not invent file paths, symbols, or behavior not supported by the evidence."
    )
    user = (
        f"Question:\n{question}\n\n"
        f"Mode: {mode}\n\n"
        "Evidence excerpts:\n\n"
        + "\n\n".join(evidence)
        + "\n\n"
        "Write a concise answer in Markdown with:\n"
        "- A short explanation (3-8 bullets).\n"
        "- A 'Key Files' section listing file paths you relied on.\n"
        "- Inline citations like [E1] at the end of sentences.\n"
    )

    try:
        answer = openrouter_chat_completion(
            api_key=api_key,
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            timeout_seconds=max(1, int(llm_timeout_seconds)),
        )
    except Exception as e:
        raise QueryError(f"OpenRouter LLM synthesis failed: {e}") from e

    return answer, model


def _synthesize_with_ollama(
    *,
    question: str,
    chunks: Sequence[RetrievedChunk],
    mode: str,
    max_chunks: int,
    llm_model: str | None,
    llm_timeout_seconds: int,
) -> tuple[str, str]:
    model = (llm_model or os.environ.get("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL).strip()

    used = list(chunks)[: max(1, max_chunks)]
    evidence: list[str] = []
    for i, ch in enumerate(used, start=1):
        sid = getattr(ch.citation, "source_id", "") or ""
        src_prefix = f"{sid}:" if sid else ""
        loc = f"{src_prefix}{ch.path}#L{int(ch.line_start)}-L{int(ch.line_end)}"
        snippet = ch.snippet.strip()
        if len(snippet) > 1800:
            snippet = snippet[:1797] + "..."
        evidence.append(f"[E{i}] {loc}\n{snippet}")

    system = (
        "You are a careful technical assistant.\n"
        "Answer the user's question using ONLY the provided evidence excerpts.\n"
        "If the evidence is insufficient, say so and suggest what to look for next.\n"
        "Cite evidence by referencing the excerpt IDs like [E1], [E2] in your answer.\n"
        "Do not invent file paths, symbols, or behavior not supported by the evidence."
    )
    user = (
        f"Question:\n{question}\n\n"
        f"Mode: {mode}\n\n"
        "Evidence excerpts:\n\n"
        + "\n\n".join(evidence)
        + "\n\n"
        "Write a concise answer in Markdown with:\n"
        "- A short explanation (3-8 bullets).\n"
        "- A 'Key Files' section listing file paths you relied on.\n"
        "- Inline citations like [E1] at the end of sentences.\n"
    )

    try:
        answer = ollama_chat_completion(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            timeout_seconds=max(1, int(llm_timeout_seconds)),
        )
    except Exception as e:
        raise QueryError(f"Ollama LLM synthesis failed: {e}") from e

    return answer, model
