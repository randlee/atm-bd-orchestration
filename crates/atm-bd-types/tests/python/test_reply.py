"""One test per HookReply shape, through the wheel: the same bytes as the Rust tests in src/wire.rs."""

from __future__ import annotations

from atm_bd_types import ErrorId, HookAction, HookReply, HookRequest, QaPass, Refusal, Template
from atm_bd_types._native import _phase_file
from conftest import SHA, pass_report, request_json

COMPLETED = {"op": "close", "outcome": "completed"}


def test_reply_pass_through() -> None:
    assert HookReply.pass_through().to_json() == '{"result":"pass-through"}'


def test_reply_not_applicable() -> None:
    assert HookReply.not_applicable().to_json() == '{"result":"not-applicable"}'


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
    templates = [(f"/r/t/{n}.md.j2", "/r/t", b"ok") for n in ("refuse", "dev-close", "qa-pass", "qa-findings")]
    phase = _phase_file("lite", "lead", templates, [])
    reply = HookReply.handled([HookAction.close(phase.template(Template.QA_PASS), verdict)])
    assert reply.to_json() == (
        '{"result":"handled","atm-action":[{"command":"task.close","request":{"home_dir":"/h","current_dir":"/r",'
        '"caller_identity":"qa","caller_team":"t","message_source":{"Template":{"canonical_template_path":'
        '"/r/t/qa-pass.md.j2","canonical_template_root":"/r/t","raw_file_bytes":[111,107],"input_defaults":{},'
        f'"var_file_values":{{"sha":"{SHA}"}},"explicit_values":{{}},"environment_values":{{}}}}}},'
        '"requires_ack":false,"task_id":"bo-3","task_op":{"op":"close","outcome":"completed"},"dry_run":false}}]}')
