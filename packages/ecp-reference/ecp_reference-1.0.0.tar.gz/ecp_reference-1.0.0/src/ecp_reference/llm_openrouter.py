from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "xiaomi/mimo-v2-flash:free"


def openrouter_chat_completion(
    *,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    timeout_seconds: int = 60,
    max_tokens: int | None = None,
    temperature: float | None = None,
    base_url: str | None = None,
    referer: str | None = None,
    title: str | None = None,
) -> str:
    """Call OpenRouter's Chat Completions API and return the assistant content."""
    base_url = base_url or os.environ.get("OPENROUTER_BASE_URL") or DEFAULT_OPENROUTER_BASE_URL
    referer = referer or os.environ.get("OPENROUTER_HTTP_REFERER")
    title = title or os.environ.get("OPENROUTER_TITLE")

    payload: dict[str, Any] = {
        "model": model or (os.environ.get("OPENROUTER_MODEL") or DEFAULT_OPENROUTER_MODEL),
        "messages": messages,
    }
    if max_tokens is not None:
        payload["max_tokens"] = int(max_tokens)
    if temperature is not None:
        payload["temperature"] = float(temperature)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if referer:
        headers["HTTP-Referer"] = str(referer)
    if title:
        headers["X-Title"] = str(title)

    req = urllib.request.Request(
        base_url,
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
        raise RuntimeError(f"OpenRouter request failed (HTTP {e.code}): {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"OpenRouter request failed: {e}") from e

    try:
        data = json.loads(body)
    except Exception as e:
        raise RuntimeError(f"OpenRouter returned non-JSON response: {body[:500]!r}") from e

    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(f"OpenRouter response missing choices[]: {data}")

    msg = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(msg, dict):
        raise RuntimeError(f"OpenRouter response missing choices[0].message: {data}")

    content = msg.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        # Best-effort support for multimodal content formats.
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts).strip()

    raise RuntimeError(f"OpenRouter response message content was not text: {type(content)}")
