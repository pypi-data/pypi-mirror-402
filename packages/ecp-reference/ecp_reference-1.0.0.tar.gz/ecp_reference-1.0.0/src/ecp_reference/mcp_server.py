from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .errors import ECPError
from .evals import run_eval_suites
from .maintenance import build_or_refresh
from .runtime import query_expert, status
from .skill_loader import load_skill_bundle


def _send_message(obj: dict) -> None:
    body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def _read_message() -> dict | None:
    first = sys.stdin.buffer.readline()
    if not first:
        return None

    if first.lstrip().startswith(b"{"):
        try:
            return json.loads(first.decode("utf-8"))
        except Exception:
            return None

    headers: dict[str, str] = {}
    line = first
    while True:
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        if b":" in line:
            name, value = line.split(b":", 1)
            headers[name.decode("ascii", errors="replace").strip().lower()] = (
                value.decode("ascii", errors="replace").strip()
            )
        line = sys.stdin.buffer.readline()

    content_length = headers.get("content-length")
    if not content_length:
        return None
    try:
        n = int(content_length)
    except Exception:
        return None
    if n <= 0:
        return None
    body = sys.stdin.buffer.read(n)
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


def _rpc_error(*, req_id: Any, code: int, message: str, data: Any | None = None) -> dict:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}


def _rpc_result(*, req_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "expert.query",
            "description": "Answer an expert question with citations from persistent context artifacts.",
            "inputSchema": {
                "type": "object",
                "required": ["question"],
                "properties": {
                    "question": {"type": "string"},
                    "mode": {
                        "type": "string",
                        "enum": ["ephemeral", "persistent", "summarized"],
                        "default": "ephemeral",
                    },
                    "top_k": {"type": "integer", "minimum": 1, "default": 5},
                    "llm": {
                        "type": "string",
                        "enum": ["none", "openrouter"],
                        "default": "none",
                    },
                    "llm_model": {"type": "string"},
                    "llm_timeout_seconds": {"type": "integer", "minimum": 1, "default": 60},
                    "filters": {
                        "type": "object",
                        "properties": {
                            "source_id": {
                                "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]
                            },
                            "path_prefix": {
                                "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]
                            },
                        },
                        "additionalProperties": True,
                    },
                    "query_vector": {
                        "description": "Optional dense [float,...] or sparse [[i,value],...] query embedding for vector indexes.",
                        "type": "array",
                    },
                    "query_embedding": {"type": "object", "additionalProperties": True},
                },
                "additionalProperties": True,
            },
        },
        {
            "name": "expert.refresh",
            "description": "Refresh context artifacts (incremental if possible), optionally eval-gated.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "dry_run": {"type": "boolean", "default": False},
                    "no_evals": {"type": "boolean", "default": False},
                    "rebuild": {"type": "boolean", "default": False},
                },
                "additionalProperties": True,
            },
        },
        {
            "name": "expert.run_evals",
            "description": "Run evaluation suites declared in EXPERT.yaml.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "suite_id": {"type": "array", "items": {"type": "string"}},
                },
                "additionalProperties": True,
            },
        },
        {
            "name": "expert.status",
            "description": "Return basic status for the expert and its configured artifacts.",
            "inputSchema": {"type": "object", "additionalProperties": True},
        },
    ]


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


def _call_tool(skill_root: Path, *, name: str, arguments: dict[str, Any]) -> Any:
    if name == "expert.query":
        question = arguments.get("question")
        if not isinstance(question, str) or not question.strip():
            raise ECPError("expert.query requires non-empty 'question' (string).")
        mode = str(arguments.get("mode") or "ephemeral")
        try:
            top_k = int(arguments.get("top_k") or 5)
        except Exception:
            top_k = 5
        top_k = max(1, min(top_k, 50))
        llm = str(arguments.get("llm") or "none")
        llm_model = arguments.get("llm_model")
        try:
            llm_timeout_seconds = int(arguments.get("llm_timeout_seconds") or 60)
        except Exception:
            llm_timeout_seconds = 60

        filters = arguments.get("filters")
        if not isinstance(filters, dict):
            filters = {}
        source_ids = _as_str_list(filters.get("source_id") or filters.get("source_ids"))
        path_prefixes = _as_str_list(filters.get("path_prefix") or filters.get("path_prefixes"))
        query_vector = arguments.get("query_vector")

        return query_expert(
            skill_root,
            question=question,
            mode=mode,
            top_k=top_k,
            source_ids=source_ids,
            path_prefixes=path_prefixes,
            llm=llm,
            llm_model=str(llm_model) if llm_model is not None else None,
            llm_timeout_seconds=llm_timeout_seconds,
            query_vector=query_vector,
        )

    if name == "expert.refresh":
        dry_run = bool(arguments.get("dry_run", False))
        no_evals = bool(arguments.get("no_evals", False))
        rebuild = bool(arguments.get("rebuild", False))
        res = build_or_refresh(
            skill_root,
            run_evals=not no_evals,
            dry_run=dry_run,
            force_rebuild=rebuild,
        )
        return dataclasses.asdict(res) if dataclasses.is_dataclass(res) else res

    if name == "expert.run_evals":
        suite_ids = arguments.get("suite_id")
        suite_ids_list = _as_str_list(suite_ids)
        bundle = load_skill_bundle(skill_root)
        return run_eval_suites(bundle, suite_ids=suite_ids_list)

    if name == "expert.status":
        return status(skill_root)

    raise ECPError(f"Unknown tool: {name}")


def run_stdio_mcp_server(skill_root: Path) -> None:
    """Run a minimal MCP-compatible JSON-RPC server over stdio.

    Implements:
    - initialize
    - tools/list
    - tools/call
    - shutdown / exit
    """
    skill_root = skill_root.resolve()
    tools = _tool_definitions()

    should_exit = False
    while not should_exit:
        msg = _read_message()
        if msg is None:
            break

        if not isinstance(msg, dict):
            continue

        method = msg.get("method")
        params = msg.get("params")
        req_id = msg.get("id", None)

        is_notification = "id" not in msg

        try:
            if method == "initialize":
                if is_notification:
                    continue
                pv = None
                if isinstance(params, dict):
                    pv = params.get("protocolVersion")
                pv = str(pv or "2025-11-25")
                _send_message(
                    _rpc_result(
                        req_id=req_id,
                        result={
                            "protocolVersion": pv,
                            "serverInfo": {"name": "ecpctl", "version": __version__},
                            "capabilities": {"tools": {"listChanged": False}},
                        },
                    )
                )
                continue

            if method == "notifications/initialized":
                continue

            if method == "tools/list":
                if is_notification:
                    continue
                _send_message(_rpc_result(req_id=req_id, result={"tools": tools}))
                continue

            if method == "tools/call":
                if is_notification:
                    continue
                if not isinstance(params, dict):
                    raise ECPError("tools/call requires params object.")
                name = params.get("name")
                arguments = params.get("arguments") or {}
                if not isinstance(name, str) or not name:
                    raise ECPError("tools/call requires non-empty params.name.")
                if not isinstance(arguments, dict):
                    raise ECPError("tools/call requires params.arguments object.")
                result_obj = _call_tool(skill_root, name=name, arguments=arguments)
                _send_message(
                    _rpc_result(
                        req_id=req_id,
                        result={
                            "content": [
                                {"type": "text", "text": json.dumps(result_obj, ensure_ascii=False)}
                            ],
                            "isError": False,
                        },
                    )
                )
                continue

            if method == "shutdown":
                if is_notification:
                    continue
                _send_message(_rpc_result(req_id=req_id, result=None))
                continue

            if method == "exit":
                should_exit = True
                continue

            if is_notification:
                continue
            _send_message(_rpc_error(req_id=req_id, code=-32601, message=f"Method not found: {method}"))

        except ECPError as e:
            if is_notification:
                continue
            _send_message(_rpc_error(req_id=req_id, code=-32000, message=str(e)))
        except Exception as e:
            if is_notification:
                continue
            _send_message(_rpc_error(req_id=req_id, code=-32603, message="Internal error", data=str(e)))
