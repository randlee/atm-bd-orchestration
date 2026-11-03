"""Controlled fixtures for each deterministic gate and Jev outcome."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / "plugins/atm-bd-orchestration/core/gate/atm-bd-lite-gate.py"
SPEC_PATH = ROOT / "plugins/atm-bd-orchestration/skills/atm-bd-lite/hooks/task-start.md"
TASK_CLOSE_SPEC_PATH = ROOT / "plugins/atm-bd-orchestration/skills/atm-bd-lite/hooks/task-close.md"
FIXTURES = Path(__file__).parent
EXPECTED_CLOSE = FIXTURES / "expected.json"
spec = importlib.util.spec_from_file_location("hook_gate", GATE_PATH)
assert spec is not None and spec.loader is not None
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def failures(name: str) -> list[str]:
    source = (FIXTURES / name).read_text(encoding="utf-8")
    return gate.deterministic(source, gate.facts(source), gate.table(SPEC_PATH.read_text(), "Transitions"))


@pytest.mark.parametrize(("bad", "rule"), [
    ("fail-rows.py", "ANC-052"), ("fail-writes.py", "ANC-064"),
    ("fail-loop-write.py", "ANC-064"), ("fail-stack.py", "ANC-065"),
    ("fail-process.py", "ANC-066"), ("fail-lines.py", "ANC-070"),
])
def test_each_deterministic_rule_has_passing_and_failing_fixture(bad: str, rule: str) -> None:
    assert failures("start-clean.py") == []
    assert any(item.startswith(rule) for item in failures(bad))


@pytest.mark.parametrize(("script", "spec_name"), [
    ("atm-bd-task-assign-hook.py", "task-assign.md"),
    ("atm-bd-task-start-hook.py", "task-start.md"),
    ("atm-bd-task-hook.py", "task-close.md"),
])
def test_shipped_hooks_pass_deterministic_gate_offline(script: str, spec_name: str) -> None:
    skill = ROOT / "plugins/atm-bd-orchestration/skills/atm-bd-lite"
    source = (skill / "scripts" / script).read_text(encoding="utf-8")
    spec_text = (skill / "hooks" / spec_name).read_text(encoding="utf-8")
    assert gate.deterministic(source, gate.facts(source), gate.table(spec_text, "Transitions")) == []


def test_jev_no_answers_map_to_the_specific_row_and_site() -> None:
    facts = {"arms": [("Transition.START", 3)], "replies": [("HookReply.pass_through()", 4)]}
    answers = {"implemented:T-START-01": {"choice": "no"}, "listed:L4:1": {"choice": "no"}}
    assert gate.findings(answers, facts) == [
        "implement T-START-01", "add a row for L4:1 `HookReply.pass_through()`, or remove the branch"]
    assert gate.findings({key: {"choice": "yes"} for key in answers}, facts) == []


def test_one_jev_check_and_typed_outage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    hook = FIXTURES / "start-clean.py"
    out = tmp_path / "result.json"
    calls = []

    def accept(state, questions):
        calls.append((state, questions))
        class Reply:
            answers = {key: {"choice": "yes"} for key in questions}
            input_tokens = 1
        return Reply()

    monkeypatch.setattr(gate, "check", accept)
    assert gate.main([str(hook), str(SPEC_PATH), "--out", str(out)]) == 0
    assert len(calls) == 1
    assert json.loads(out.read_text())["pass"] is True

    def unavailable(_state, _questions):
        raise gate.JevError("SANITY.JEV_UNAVAILABLE", "test outage")

    monkeypatch.setattr(gate, "check", unavailable)
    assert gate.main([str(hook), str(SPEC_PATH), "--out", str(out)]) == 2
    assert json.loads(out.read_text())["jev_error"]["code"] == "SANITY.JEV_UNAVAILABLE"


def test_gate_uses_the_shared_jev_client(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = []

    def controlled_evaluate(request):
        seen.append(request)
        return {"answers": {"implemented:T-1": {"choice": "yes"}},
                "usage": {"input_tokens": 7}}

    monkeypatch.setattr(gate, "evaluate", controlled_evaluate)
    questions = {"implemented:T-1": {"type": "choice", "instructions": "check",
                                    "criteria": {"yes": "yes", "no": "no"}}}
    reply = gate.check({"hook": "source"}, questions)

    assert seen == [{"model": gate.MODEL, "state": {"hook": "source"}, "questions": questions}]
    assert reply.answers == {"implemented:T-1": {"choice": "yes"}}
    assert reply.input_tokens == 7


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_help_succeeds_without_running_gate(flag, capsys) -> None:
    assert gate.main([flag]) == 0
    output = capsys.readouterr()
    assert "usage:" in output.out and "--out run.json" in output.out
    assert output.err == ""


@pytest.mark.parametrize("extra", [[], ["--out"], ["--other", "result.json"], ["--out", ""]])
def test_output_path_is_required_before_reading_or_writing(tmp_path, capsys, extra) -> None:
    hook = tmp_path / "skill/scripts/hook.py"
    spec_path = tmp_path / "skill/hooks/spec.md"
    assert gate.main([str(hook), str(spec_path), *extra]) == 3
    assert "--out run.json" in capsys.readouterr().err
    assert not (tmp_path / "skill").exists()


def test_sites_on_same_line_are_not_dropped() -> None:
    facts = {"arms": [("Transition.START", 4)], "replies": [("HookReply.refused(error)", 4)]}
    assert len(gate.sites(facts)) == 2


def test_empty_spec_is_rejected() -> None:
    source = (FIXTURES / "start-clean.py").read_text(encoding="utf-8")
    assert any(item.startswith("ANC-052") for item in gate.deterministic(source, gate.facts(source), []))


def test_profile_runner_checks_each_hook_once_and_fails_missing_spec(monkeypatch, tmp_path, capsys):
    runner_path = GATE_PATH.with_name("run-plugin-gates.py")
    runner_spec = importlib.util.spec_from_file_location("gate_runner", runner_path)
    assert runner_spec is not None and runner_spec.loader is not None
    runner = importlib.util.module_from_spec(runner_spec)
    runner_spec.loader.exec_module(runner)
    plugin = tmp_path / "plugin"
    gate_file = plugin / "core/gate/run-plugin-gates.py"
    gate_file.parent.mkdir(parents=True)
    skill = plugin / "skills/sample"
    (skill / "hooks").mkdir(parents=True)
    (skill / "profile.toml").write_text('[hooks]\n"task.assign"="scripts/assign.py"\n'
                                          '"task.start"="scripts/start.py"\n')
    (skill / "hooks/task-assign.md").write_text("spec")
    (skill / "hooks/task-start.md").write_text("spec")
    monkeypatch.setattr(runner, "__file__", str(gate_file))
    calls = []

    def run(argv, *, check, timeout):
        assert check is False
        assert timeout == runner.GATE_TIMEOUT_SECONDS
        calls.append(argv)
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(runner.subprocess, "run", run)
    assert runner.main() == 0
    assert len(calls) == 2
    assert {Path(call[2]).name for call in calls} == {"assign.py", "start.py"}
    calls.clear()
    (skill / "hooks/task-start.md").unlink()
    assert runner.main() == 2
    assert len(calls) == 1

    def timed_out(argv, *, check, timeout):
        raise subprocess.TimeoutExpired(argv, timeout)

    monkeypatch.setattr(runner.subprocess, "run", timed_out)
    (skill / "hooks/task-start.md").write_text("spec")
    assert runner.main() == 2
    errors = capsys.readouterr().err
    assert "GATE.TIMEOUT: sample task.assign exceeded 180s" in errors
    assert "GATE.TIMEOUT: sample task.start exceeded 180s" in errors


def test_deterministic_failure_never_calls_jev(monkeypatch, tmp_path):
    def unexpected(*_args):
        raise AssertionError("Jev must not run after a deterministic failure")

    monkeypatch.setattr(gate, "check", unexpected)
    output = tmp_path / "result.json"
    assert gate.main([str(FIXTURES / "fail-rows.py"), str(SPEC_PATH), "--out", str(output)]) == 1
    result = json.loads(output.read_text())
    assert result["jev"] is None and result["deterministic_failures"]


def test_close_fixtures_match_controlled_jev_outcomes(monkeypatch, tmp_path):
    expected = json.loads(EXPECTED_CLOSE.read_text(encoding="utf-8"))
    spec_text = TASK_CLOSE_SPEC_PATH.read_text(encoding="utf-8")

    for name, contract in expected.items():
        hook = FIXTURES / f"{name}.py"
        output = tmp_path / f"{name}.json"
        expected_no = contract["expected_no"]
        calls = []

        def controlled_reply(state, questions):
            calls.append((state, questions))
            assert state["spec"] == spec_text
            assert set(expected_no) <= set(questions)

            class Reply:
                answers = {
                    key: {"choice": "no" if key in expected_no else "yes"}
                    for key in questions
                }
                input_tokens = 1

            return Reply()

        monkeypatch.setattr(gate, "check", controlled_reply)
        result = gate.main([str(hook), str(TASK_CLOSE_SPEC_PATH), "--out", str(output)])
        actual = json.loads(output.read_text(encoding="utf-8"))

        assert result == (1 if expected_no else 0)
        assert len(calls) == 1
        assert actual["deterministic_failures"] == []
        assert actual["jev"]["no"] == expected_no
        assert actual["pass"] is (not expected_no)
