#!/usr/bin/env python3
"""Stdio MCP adapter for RunSpecimen — no approve / settle tools.

Exposes only the same narrow lifecycle surface as ``runspecimen_adapter.py``.
Requires ``runspecimen`` on PATH. Local-only; no network phone-home.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from typing import Any


PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "runspecimen"
SERVER_VERSION = "0.2.0-rc.12"

ALLOWED = frozenset({
    "about",
    "dashboard",
    "doctor",
    "validate",
    "status",
    "preflight",
    "run",
    "postflight",
    "verify",
})

TOOLS: list[dict[str, Any]] = [
    {
        "name": "about",
        "description": "Print RunSpecimen product summary (no workspace required).",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "doctor",
        "description": "Check local RunSpecimen installation and workspace readiness.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": {"type": "string", "description": "Workspace path"},
            },
            "required": ["workspace"],
            "additionalProperties": False,
        },
    },
    {
        "name": "validate",
        "description": "Validate a RunSpecimen contract against the workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": {"type": "string"},
                "contract": {"type": "string"},
            },
            "required": ["workspace", "contract"],
            "additionalProperties": False,
        },
    },
    {
        "name": "status",
        "description": "Read-only campaign/run status diagnosis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": {"type": "string"},
                "campaign_id": {"type": "string"},
                "run_id": {"type": "string"},
            },
            "required": ["workspace", "campaign_id", "run_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "preflight",
        "description": "Run preflight after the human has approved on a real TTY.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": {"type": "string"},
                "contract": {"type": "string"},
            },
            "required": ["workspace", "contract"],
            "additionalProperties": False,
        },
    },
    {
        "name": "run",
        "description": "Execute one bounded run after preflight (never approves).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": {"type": "string"},
                "contract": {"type": "string"},
            },
            "required": ["workspace", "contract"],
            "additionalProperties": False,
        },
    },
    {
        "name": "postflight",
        "description": "Assert outcomes and issue a receipt after run.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": {"type": "string"},
                "contract": {"type": "string"},
            },
            "required": ["workspace", "contract"],
            "additionalProperties": False,
        },
    },
    {
        "name": "verify",
        "description": "Verify receipts with campaign-id and run-id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": {"type": "string"},
                "contract": {"type": "string"},
                "campaign_id": {"type": "string"},
                "run_id": {"type": "string"},
            },
            "required": ["workspace", "contract", "campaign_id", "run_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "dashboard",
        "description": (
            "Start the loopback read-only dashboard (blocking). Prefer a "
            "detached terminal; cannot approve."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace": {"type": "string"},
                "contract": {"type": "string"},
                "open": {"type": "boolean", "default": False},
            },
            "required": ["workspace", "contract"],
            "additionalProperties": False,
        },
    },
]


def _message(msg_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _run_cli(action: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if action not in ALLOWED:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Action '{action}' is not allowed via MCP"}],
        }
    executable = shutil.which("runspecimen")
    if executable is None:
        return {
            "isError": True,
            "content": [{
                "type": "text",
                "text": "runspecimen is not installed on PATH. Install the CLI first.",
            }],
        }
    if action == "about":
        completed = subprocess.run(
            [executable, "about"],
            check=False,
            capture_output=True,
            text=True,
        )
    else:
        workspace = arguments.get("workspace")
        if not workspace:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "--workspace is required"}],
            }
        command = [executable, action, "--workspace", str(workspace)]
        contract = arguments.get("contract")
        if contract is not None:
            command.extend(["--contract", str(contract)])
        campaign_id = arguments.get("campaign_id")
        if campaign_id is not None:
            command.extend(["--campaign-id", str(campaign_id)])
        run_id = arguments.get("run_id")
        if run_id is not None:
            command.extend(["--run-id", str(run_id)])
        if arguments.get("open") and action == "dashboard":
            command.append("--open")
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
    text = (completed.stdout or "") + (completed.stderr or "")
    if not text.strip():
        text = f"exit_code={completed.returncode}"
    return {
        "isError": completed.returncode != 0,
        "content": [{"type": "text", "text": text}],
    }


def _handle(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    msg_id = request.get("id")
    params = request.get("params") or {}

    if method == "initialize":
        return _message(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "instructions": (
                "RunSpecimen MCP never approves. A human must run "
                "`runspecimen approve` on a real TTY before preflight/run."
            ),
        })
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _message(msg_id, {})
    if method == "tools/list":
        return _message(msg_id, {"tools": TOOLS})
    if method == "tools/call":
        name = str(params.get("name") or "")
        if name not in ALLOWED:
            return _message(msg_id, {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": (
                        f"Tool '{name}' is not available. Approve and remote-confirm "
                        "settle are intentionally excluded from this MCP adapter."
                    ),
                }],
            })
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            arguments = {}
        return _message(msg_id, _run_cli(name, arguments))
    if msg_id is None:
        return None
    return _error(msg_id, -32601, f"Method not found: {method}")


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(request, dict):
            continue
        response = _handle(request)
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
