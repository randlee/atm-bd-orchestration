"""bo-12 acceptance: one tick with the contract's lite cron script against fake PhaseFacts."""
import json
from collections import deque
from pathlib import Path

import pytest

from atm_bd_core.execute import RETRY_LIMIT
from atm_bd_core.tick import tick
from atm_bd_types import Assign, CollectError, ErrorId, FactKind, PhaseFacts, Refusal, TaskFact, TaskState
from atm_bd_types._core import OutcomeKind, Ports, TickResult

from .helpers import LEAD, QA, Collector, Runner, make_primary, make_profile, ports, qa_bead

NOW = 1_700_000_000


def run(tmp: Path, runner: Runner, collector: Collector, dry_run: bool = False) -> TickResult:
    result = tick(tmp / "skill" / "profile.toml", "bo", tmp / "primary", ports=ports(runner), now=NOW,
                  dry_run=dry_run, collector=collector)
    assert isinstance(result, TickResult), result
    return result


def state(tmp: Path) -> dict:
    return json.loads((tmp / "primary/.atm-bd/state/phase-bo/executed.json").read_text(encoding="utf-8"))


def test_released_qa_bead_is_assigned_once_and_deduped_next_tick(tmp_path):
    make_profile(tmp_path)
    make_primary(tmp_path)
    runner, collector = Runner(), Collector([qa_bead()])
    first = run(tmp_path, runner, collector)
    assert [o.kind for o in first.outcomes] == [OutcomeKind.SENT]
    assert len(runner.calls) == 1
    argv, stdin = runner.calls[0]
    assert stdin is not None
    template = str((tmp_path / "skill/templates/qa.xml.j2").resolve())
    assert argv == ["env", f"ATM_IDENTITY={LEAD}", "atm", "task", "assign", QA, "--as", LEAD, "--task-id",
                    "tst-1.qa", "--template", template, "--vars", "-"]
    assert json.loads(stdin) == {"task_id": "tst-1.qa", "phase": "bo", "profile": "lite", "repo": "owner/repo",
                                 "pr_number": 42, "branch": "branch-tst-1.qa", "commit": "a" * 40}
    assert first.view.actions[0].outcome == OutcomeKind.SENT

    second = run(tmp_path, runner, collector)
    assert len(runner.calls) == 1, "second tick executed a command"
    assert second.decision.actions == [] and second.outcomes == []
    assert state(tmp_path)["sent"] == ["assign:tst-1.qa"]


def test_completed_assign_is_persisted_before_a_later_command_raises(tmp_path):
    class InterruptedRunner(Runner):
        def run(self, argv, stdin):
            if len(self.calls) == 1:
                raise RuntimeError("interrupted second command")
            return super().run(argv, stdin)

    make_profile(tmp_path)
    make_primary(tmp_path)
    runner = InterruptedRunner()
    collector = Collector([qa_bead("tst-1.qa"), qa_bead("tst-2.qa")])
    with pytest.raises(RuntimeError, match="interrupted second command"):
        run(tmp_path, runner, collector)
    assert state(tmp_path)["sent"] == ["assign:tst-1.qa"]

    resumed = Runner()
    result = run(tmp_path, resumed, collector)
    assert [action.bead_id for action in result.decision.actions] == ["tst-2.qa"]
    assert [argv[argv.index("--task-id") + 1] for argv, _ in resumed.calls] == ["tst-2.qa"]


def test_a_key_decide_stops_returning_is_forgotten_and_assigned_again_when_re_released(tmp_path):
    make_profile(tmp_path)
    make_primary(tmp_path)
    runner, collector = Runner(), Collector([qa_bead()])
    run(tmp_path, runner, collector)
    collector.ready = [qa_bead(assignee=QA)]  # the assign landed: decide returns nothing
    collector.tasks = [TaskFact("tst-1.qa", QA, TaskState.ASSIGNED, "tst-1.qa")]
    run(tmp_path, runner, collector)
    assert state(tmp_path)["sent"] == []
    collector.ready = [qa_bead()]  # released again (reopened)
    collector.tasks = []
    run(tmp_path, runner, collector)
    assert len(runner.calls) == 2


def test_degraded_ready_facts_preserve_sent_keys_and_failure_counts(tmp_path):
    make_profile(tmp_path)
    make_primary(tmp_path)
    runner = Runner(deque([(0, ""), (1, "BEAD_NOT_READY")]))
    collector = Collector([qa_bead("tst-1.qa"), qa_bead("tst-2.qa")])
    run(tmp_path, runner, collector)
    before = state(tmp_path)
    assert before["sent"] == ["assign:tst-1.qa"]
    assert before["failures"]["assign:tst-2.qa"]["attempts"] == 1

    def degraded(phase, phase_file, ports, now, state_dir):
        error = CollectError(FactKind.READY, [], "read failed", "retry")
        return PhaseFacts(phase, now, phase_file, reported_keys=[], ready=None, errors=[error])

    result = tick(tmp_path / "skill/profile.toml", "bo", tmp_path / "primary", ports=ports(runner), now=NOW,
                  collector=degraded)
    assert isinstance(result, TickResult)
    assert state(tmp_path) == before
    run(tmp_path, runner, collector)
    assert [argv[argv.index("--task-id") + 1] for argv, _ in runner.calls] == ["tst-1.qa", "tst-2.qa", "tst-2.qa"]


def test_tick_drains_before_collection_and_reports_escalated_race(tmp_path, monkeypatch):
    monkeypatch.setenv("ATM_TEAM", "test-team")
    make_profile(tmp_path)
    make_primary(tmp_path)
    events = []

    class Cache:
        def drain(self):
            events.append("drain")
            return [{"seq": 7, "bead": "tst-1", "last_error": "BD_CACHE.PRECONDITION: stale"}]

        def mark_announced(self, seq):
            events.append(("announced", seq))

    collector = Collector()

    def collect_after_drain(*args):
        assert events == ["drain"]
        events.append("collect")
        return collector(*args)

    runner = Runner()
    result = tick(tmp_path / "skill/profile.toml", "bo", tmp_path / "primary", ports=Ports(runner, Cache()),
                  now=NOW, collector=collect_after_drain)
    assert isinstance(result, TickResult)
    assert events == ["drain", "collect", ("announced", 7)]
    assert len(runner.calls) == 1 and "BEAD_RACED" in (runner.calls[0][1] or "")


def test_failed_assign_is_retried_next_tick_then_reported_with_its_error_id(tmp_path):
    make_profile(tmp_path)
    make_primary(tmp_path)
    refused = (1, "hook refused: BEAD_NOT_READY bead=tst-1.qa")
    runner, collector = Runner(deque([refused] * RETRY_LIMIT)), Collector([qa_bead()])
    for attempt in range(1, RETRY_LIMIT + 1):
        result = run(tmp_path, runner, collector)
        assert len(runner.calls) == attempt, "a failed assign was not retried on the next tick"
        [outcome] = result.outcomes
        assert outcome.kind == OutcomeKind.FAILED and outcome.failure.id == ErrorId.BEAD_NOT_READY
    assert state(tmp_path)["failures"]["assign:tst-1.qa"]["attempts"] == RETRY_LIMIT

    exhausted = run(tmp_path, runner, collector)
    assert len(runner.calls) == RETRY_LIMIT, "ran past the retry limit"
    [outcome] = exhausted.outcomes
    assert outcome.kind == OutcomeKind.FAILED and outcome.failure.id == ErrorId.BEAD_NOT_READY
    assert "retry limit" in repr(outcome.failure)


def test_failure_without_an_error_id_is_request_invalid_and_success_clears_the_count(tmp_path):
    make_profile(tmp_path)
    make_primary(tmp_path)
    runner, collector = Runner(deque([(2, "daemon unreachable")])), Collector([qa_bead()])
    [outcome] = run(tmp_path, runner, collector).outcomes
    assert outcome.failure.id == ErrorId.REQUEST_INVALID
    [outcome] = run(tmp_path, runner, collector).outcomes
    assert outcome.kind == OutcomeKind.SENT
    assert state(tmp_path) == {"sent": ["assign:tst-1.qa"], "failures": {}}


@pytest.mark.parametrize("message", [
    "failed path=/tmp/xBEAD_NOT_READY.log",
    "failed path=/tmp/BEAD_NOT_READY_extra.log",
])
def test_error_id_substring_inside_larger_token_is_not_typed(tmp_path, message):
    make_profile(tmp_path)
    make_primary(tmp_path)
    runner, collector = Runner(deque([(1, message)])), Collector([qa_bead()])

    [outcome] = run(tmp_path, runner, collector).outcomes

    assert outcome.kind == OutcomeKind.FAILED
    assert outcome.failure.id == ErrorId.REQUEST_INVALID


def test_dry_run_executes_nothing_and_writes_no_state(tmp_path):
    make_profile(tmp_path)
    make_primary(tmp_path)
    runner = Runner()
    result = run(tmp_path, runner, Collector([qa_bead()]), dry_run=True)
    assert [o.kind for o in result.outcomes] == [OutcomeKind.DRY_RUN]
    assert runner.calls == []
    assert not (tmp_path / "primary/.atm-bd/state").exists()


def test_missing_params_report_goes_to_the_lead_once_then_stays_a_row(tmp_path, monkeypatch):
    monkeypatch.setenv("ATM_TEAM", "test-team")
    make_profile(tmp_path, policy='[params]\nqa_agent = "qa-agent"\n')
    make_primary(tmp_path)
    runner, collector = Runner(), Collector([qa_bead()])
    first = run(tmp_path, runner, collector)
    assert [o.kind for o in first.outcomes] == [OutcomeKind.SENT]
    assert runner.calls[0][0] == ["env", f"ATM_IDENTITY={LEAD}", "atm", "send", f"{LEAD}@test-team", "--as",
                                  "atm-bd", "--team", "tool", "--stdin"]
    assert "qa_template" in (runner.calls[0][1] or "")
    keys = tmp_path / "primary/.atm-bd/state/phase-bo/reported-keys.json"
    assert json.loads(keys.read_text(encoding="utf-8")) == ["cron:params:tst-1.qa"]

    second = run(tmp_path, runner, collector)
    assert len(runner.calls) == 1
    assert second.decision.actions == [] and [r.key for r in second.decision.rows] == ["cron:params:tst-1.qa"]
    assert [r.key for r in second.view.rows] == ["cron:params:tst-1.qa"]


def test_unreadable_reported_keys_hold_reports_instead_of_resending(tmp_path):
    make_profile(tmp_path, policy='[params]\nqa_agent = "qa-agent"\n')
    make_primary(tmp_path)
    keys = tmp_path / "primary/.atm-bd/state/phase-bo/reported-keys.json"
    keys.parent.mkdir(parents=True)
    keys.write_text("{not json", encoding="utf-8")
    runner = Runner()
    [outcome] = run(tmp_path, runner, Collector([qa_bead()])).outcomes
    assert outcome.kind == OutcomeKind.FAILED and outcome.failure.id == ErrorId.PHASE_UNREADABLE
    assert runner.calls == []
    assert keys.read_text(encoding="utf-8") == "{not json"


def test_duplicate_keys_in_one_decide_execute_once(tmp_path):
    make_profile(tmp_path)
    make_primary(tmp_path)
    runner = Runner()
    result = run(tmp_path, runner, Collector([qa_bead(), qa_bead()]))
    assert len(result.decision.actions) == 1 and isinstance(result.decision.actions[0], Assign)
    assert len(runner.calls) == 1


def test_profile_without_cron_decides_nothing(tmp_path):
    profile = make_profile(tmp_path)
    profile.write_text(profile.read_text(encoding="utf-8").replace('cron = "scripts/atm-bd-cron.py"\n', ""),
                       encoding="utf-8")
    make_primary(tmp_path)
    runner = Runner()
    result = run(tmp_path, runner, Collector([qa_bead()]))
    assert result.decision.actions == [] and runner.calls == []


def test_view_reports_sprint_steps_and_planned_actions(tmp_path):
    make_profile(tmp_path)
    make_primary(tmp_path)
    result = run(tmp_path, Runner(), Collector([qa_bead()]))
    assert result.view.lead == LEAD and result.view.root_id == "atm-phase-bo" and result.view.generated_at == NOW
    [sprint] = result.view.sprints
    assert sprint.id == "tst-1" and [s.bead_id for s in sprint.steps] == ["tst-1.qa"] and sprint.steps[0].ready


def test_phase_file_for_another_profile_refuses_before_any_read(tmp_path):
    make_profile(tmp_path)
    make_primary(tmp_path, profile="other")
    collector = Collector()
    result = tick(tmp_path / "skill/profile.toml", "bo", tmp_path / "primary", ports=ports(Runner()), now=NOW,
                  collector=collector)
    assert isinstance(result, Refusal) and result.id == ErrorId.PROFILE_MISMATCH
    assert collector.calls == 0


def test_corrupt_executed_state_refuses_before_any_read(tmp_path):
    make_profile(tmp_path)
    make_primary(tmp_path)
    path = tmp_path / "primary/.atm-bd/state/phase-bo/executed.json"
    path.parent.mkdir(parents=True)
    path.write_text("[]", encoding="utf-8")
    collector = Collector()
    result = tick(tmp_path / "skill/profile.toml", "bo", tmp_path / "primary", ports=ports(Runner()), now=NOW,
                  collector=collector)
    assert isinstance(result, Refusal) and result.id == ErrorId.PHASE_UNREADABLE and collector.calls == 0


@pytest.mark.parametrize(("body", "error"), [
    ('raise ValueError("bad decision")', "ValueError: bad decision"),
    ('return "not actions"', "TypeError:"),
    ('return [42]', "TypeError:"),
])
def test_decide_failure_refuses_before_executing_or_writing_state(tmp_path, body, error):
    make_profile(tmp_path)
    make_primary(tmp_path)
    script = tmp_path / "skill/scripts/atm-bd-cron.py"
    script.write_text(f"def decide(facts, params):\n    {body}\n", encoding="utf-8")
    runner = Runner()
    result = tick(tmp_path / "skill/profile.toml", "bo", tmp_path / "primary", ports=ports(runner), now=NOW,
                  collector=Collector([qa_bead()]))
    assert isinstance(result, Refusal) and result.id == ErrorId.PROFILE_MISMATCH
    assert str(script) in repr(result) and error in repr(result)
    assert runner.calls == []
    assert not (tmp_path / "primary/.atm-bd/state").exists()


def test_report_deduplication_uses_same_ledger_when_filename_changes(tmp_path, monkeypatch):
    from atm_bd_core import reported

    monkeypatch.setenv("ATM_TEAM", "test-team")

    monkeypatch.setattr(reported, "REPORTED_KEYS", "renamed-reports.json")
    make_profile(tmp_path, policy='[params]\nqa_agent = "qa-agent"\n')
    make_primary(tmp_path)
    runner, collector = Runner(), Collector([qa_bead()])
    first = run(tmp_path, runner, collector)
    assert [outcome.kind for outcome in first.outcomes] == [OutcomeKind.SENT]
    ledger = tmp_path / "primary/.atm-bd/state/phase-bo/renamed-reports.json"
    assert json.loads(ledger.read_text(encoding="utf-8")) == ["cron:params:tst-1.qa"]
    second = run(tmp_path, runner, collector)
    assert len(runner.calls) == 1
    assert second.decision.actions == [] and [row.key for row in second.decision.rows] == ["cron:params:tst-1.qa"]
