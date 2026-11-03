"""Shared fixtures for the wheel tests: the requests ATM sends a hook, and the crate paths."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CRATE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CRATE))  # gen_stubs

SHA = "0123456789abcdef0123456789abcdef01234567"


def request_json(hook: str, report: str = "", op: dict[str, str] | None = None, to: str | None = None) -> str:
    """ATM's hook stdin for `hook`, shaped like the Rust tests' `close_request` fixture."""
    return json.dumps({
        "schema_version": "1.0.0", "hook": hook, "team": "t", "phase": "bo",
        "caller": {"identity": "qa", "team": "t", "host": None}, "custom": {},
        "request": {"home_dir": "/h", "current_dir": "/r", "caller_identity": "qa", "caller_team": "t",
                    "to": None if to is None else {"agent": to}, "message_source": {"Inline": report},
                    "requires_ack": False, "task_id": "bo-3", "task_op": op, "dry_run": False},
    })


def pass_report() -> str:
    return f'done\n```json\n{{"verdict": "PASS", "sha": "{SHA}"}}\n```\n'
