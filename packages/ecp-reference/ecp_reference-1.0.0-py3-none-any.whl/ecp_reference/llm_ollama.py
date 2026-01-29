from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2"


def ollama_chat_completion(
    *,
    model: str | None = None,
    messages: list[dict[str, str]],
    timeout_seconds: int = 60,
    max_tokens: int | None = None,
    temperature: float | None = None,
    host: str | None = None,
) -> str:
    """Call Ollama /api/chat endpoint and return the assistant content.

    Environment variables:
    - OLLAMA_HOST: Base URL for Ollama (default: http://localhost:11434)
    - OLLAMA_MODEL: Model to use (default: llama3.2)
    """
    host = host or os.environ.get("OLLAMA_HOST") or DEFAULT_OLLAMA_HOST
    model = model or os.environ.get("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL

    # Normalize host URL (strip trailing slash)
    host = host.rstrip("/")
    url = f"{host}/api/chat"

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,  # Get complete response in one request
    }

    # Ollama uses "options" for parameters like num_predict (max_tokens) and temperature
    options: dict[str, Any] = {}
    if max_tokens is not None:
        options["num_predict"] = int(max_tokens)
    if temperature is not None:
        options["temperature"] = float(temperature)
    if options:
        payload["options"] = options

    headers = {
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        detail = err_body.strip() or str(getattr(e, "reason", "")) or "HTTP error"
        raise RuntimeError(f"Ollama request failed (HTTP {e.code}): {detail}") from e
    except urllib.error.URLError as e:
        # Connection refused, timeout, etc.
        reason = str(getattr(e, "reason", e))
        raise RuntimeError(
            f"Ollama request failed: {reason}. "
            f"Is Ollama running at {host}? Try: ollama serve"
        ) from e

    try:
        data = json.loads(body)
    except Exception as e:
        raise RuntimeError(f"Ollama returned non-JSON response: {body[:500]!r}") from e

    # Ollama response format: {"message": {"role": "assistant", "content": "..."}}
    msg = data.get("message")
    if not isinstance(msg, dict):
        raise RuntimeError(f"Ollama response missing message: {data}")

    content = msg.get("content")
    if isinstance(content, str):
        return content.strip()

    raise RuntimeError(f"Ollama response message content was not text: {type(content)}")
