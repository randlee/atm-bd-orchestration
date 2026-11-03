"""One test per HookReply shape, through the wheel: the same bytes as the Rust tests in src/wire.rs."""

from __future__ import annotations

import subprocess
import sys

from atm_bd_types import ErrorId, Hook, HookAction, HookReply, HookRequest, QaPass, Refusal, Template
from atm_bd_types._native import _phase_file
from conftest import SHA, pass_report, request_json

COMPLETED = {"op": "close", "outcome": "completed"}


def test_reply_pass_through() -> None:
    assert HookReply.pass_through().to_json(None) == '{"result":"pass-through"}'


def test_reply_not_applicable() -> None:
    assert HookReply.not_applicable().to_json(None) == '{"result":"not-applicable"}'


def test_reply_refused_before_any_request_parse() -> None:
    script = """
from atm_bd_types import ErrorId, HookReply, Refusal
refusal = Refusal(ErrorId.BEAD_NOT_READY, bead="bo-1", ids=["bo-2", "bo-3"])
print(HookReply.refused(refusal).to_json(None))
"""
    result = subprocess.run([sys.executable, "-c", script], check=True, capture_output=True, text=True)
    assert result.stdout == (
        '{"result":"refused","message":"BEAD_NOT_READY: bead=bo-1, ids=bo-2, bo-3"}\n'
    )


def test_interleaved_requests_and_phases_keep_their_own_context() -> None:
    import json

    one = request_json("task.close", "", {"op": "close", "outcome": "refused", "reason": "first"})
    two = one.replace("bo-3", "bo-4")
    req_a, req_b = HookRequest.parse(one), HookRequest.parse(two)
    assert isinstance(req_a, HookRequest) and isinstance(req_b, HookRequest)
    names = ("refuse", "dev-close", "qa-pass", "qa-findings", "land-close")
    phase_a = _phase_file("lite", "lead", [(f"/r/t/{n}.j2", "/r/t", b"A") for n in names], [])
    phase_b = _phase_file("lite", "lead", [(f"/r/t/{n}.j2", "/r/t", b"B") for n in names], [])
    path_a = phase_a.template(Template.REFUSE)
    path_b = phase_b.template(Template.REFUSE)
    a = HookAction.close(req_a, phase_a, path_a, "first")
    b = HookAction.close(req_b, phase_b, path_b, "second")
    for action, task, raw in ((a, "bo-3", [65]), (b, "bo-4", [66])):
        wire = json.loads(HookReply.handled([action]).to_json(Hook.TASK_CLOSE))
        request = wire["atm-action"][0]["request"]
        assert request["task_id"] == task
        assert request["message_source"]["Template"]["raw_file_bytes"] == raw
    refusal = HookReply.refused(Refusal(ErrorId.BEAD_NOT_READY, bead="bo-1", ids=["bo-2"]))
    assert "Close the blockers first" in refusal.to_json(Hook.TASK_ASSIGN)
    assert "Wait for the lead" in refusal.to_json(Hook.TASK_START)


def test_reply_refused() -> None:
    assert isinstance(HookRequest.parse(request_json("task.start")), HookRequest)  # task.start selects the fix table
    refusal = Refusal(ErrorId.BEAD_NOT_READY, bead="bo-1", ids=["bo-2", "bo-3"])
    assert HookReply.refused(refusal).to_json(Hook.TASK_START) == (
        '{"result":"refused","message":"BEAD_NOT_READY: bo-1 is blocked by bo-2, bo-3. Wait for the lead."}')


def test_reply_handled() -> None:
    req = HookRequest.parse(request_json("task.close", pass_report(), COMPLETED))
    assert isinstance(req, HookRequest)
    verdict = req.qa_pass()
    assert isinstance(verdict, QaPass)
    templates = [(f"/r/t/{n}.md.j2", "/r/t", b"ok") for n in ("refuse", "dev-close", "qa-pass", "qa-findings", "land-close")]
    phase = _phase_file("lite", "lead", templates, [])
    reply = HookReply.handled([HookAction.close(req, phase, phase.template(Template.QA_PASS), verdict)])
    assert reply.to_json(None) == (
        '{"result":"handled","atm-action":[{"command":"task.close","request":{"home_dir":"/h","current_dir":"/r",'
        '"caller_identity":"qa","caller_team":"t","message_source":{"Template":{"canonical_template_path":'
        '"/r/t/qa-pass.md.j2","canonical_template_root":"/r/t","raw_file_bytes":[111,107],"input_defaults":{},'
        f'"var_file_values":{{"sha":"{SHA}"}},"explicit_values":{{}},"environment_values":{{}}}}}},'
        '"requires_ack":false,"task_id":"bo-3","task_op":{"op":"close","outcome":"completed"},"dry_run":false}}]}')
