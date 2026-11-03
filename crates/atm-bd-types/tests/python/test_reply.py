"""One test per HookReply shape, through the wheel: the same bytes as the Rust tests in src/wire.rs."""

from __future__ import annotations

import subprocess
import sys

from atm_bd_types import ErrorId, HookAction, HookReply, HookRequest, QaPass, Refusal, Template
from atm_bd_types._native import _phase_file
from conftest import SHA, pass_report, request_json

COMPLETED = {"op": "close", "outcome": "completed"}


def test_reply_pass_through() -> None:
    assert HookReply.pass_through().to_json() == '{"result":"pass-through"}'


def test_reply_not_applicable() -> None:
    assert HookReply.not_applicable().to_json() == '{"result":"not-applicable"}'


def test_reply_refused_before_any_request_parse() -> None:
    script = """
from atm_bd_types import ErrorId, HookReply, Refusal
refusal = Refusal(ErrorId.BEAD_NOT_READY, bead="bo-1", ids=["bo-2", "bo-3"])
print(HookReply.refused(refusal).to_json())
"""
    result = subprocess.run([sys.executable, "-c", script], check=True, capture_output=True, text=True)
    assert result.stdout == (
        '{"result":"refused","message":"BEAD_NOT_READY: bead=bo-1, ids=bo-2, bo-3"}\n'
    )


def test_reply_uses_most_recently_parsed_request() -> None:
    script = """
import sys
from atm_bd_types import ErrorId, HookReply, HookRequest, Refusal
assert isinstance(HookRequest.parse(sys.argv[1]), HookRequest)
assert isinstance(HookRequest.parse(sys.argv[2]), HookRequest)
refusal = Refusal(ErrorId.BEAD_NOT_READY, bead="bo-1", ids=["bo-2", "bo-3"])
print(HookReply.refused(refusal).to_json())
"""
    result = subprocess.run(
        [sys.executable, "-c", script, request_json("task.assign"), request_json("task.start")],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == (
        '{"result":"refused","message":"BEAD_NOT_READY: bo-1 is blocked by bo-2, bo-3. Wait for the lead."}\n'
    )


def test_reply_refused() -> None:
    assert isinstance(HookRequest.parse(request_json("task.start")), HookRequest)  # task.start selects the fix table
    refusal = Refusal(ErrorId.BEAD_NOT_READY, bead="bo-1", ids=["bo-2", "bo-3"])
    assert HookReply.refused(refusal).to_json() == (
        '{"result":"refused","message":"BEAD_NOT_READY: bo-1 is blocked by bo-2, bo-3. Wait for the lead."}')


def test_reply_handled() -> None:
    req = HookRequest.parse(request_json("task.close", pass_report(), COMPLETED))
    assert isinstance(req, HookRequest)
    verdict = req.qa_pass()
    assert isinstance(verdict, QaPass)
    templates = [(f"/r/t/{n}.md.j2", "/r/t", b"ok") for n in ("refuse", "dev-close", "qa-pass", "qa-findings", "land-close")]
    phase = _phase_file("lite", "lead", templates, [])
    reply = HookReply.handled([HookAction.close(phase.template(Template.QA_PASS), verdict)])
    assert reply.to_json() == (
        '{"result":"handled","atm-action":[{"command":"task.close","request":{"home_dir":"/h","current_dir":"/r",'
        '"caller_identity":"qa","caller_team":"t","message_source":{"Template":{"canonical_template_path":'
        '"/r/t/qa-pass.md.j2","canonical_template_root":"/r/t","raw_file_bytes":[111,107],"input_defaults":{},'
        f'"var_file_values":{{"sha":"{SHA}"}},"explicit_values":{{}},"environment_values":{{}}}}}},'
        '"requires_ack":false,"task_id":"bo-3","task_op":{"op":"close","outcome":"completed"},"dry_run":false}}]}')
