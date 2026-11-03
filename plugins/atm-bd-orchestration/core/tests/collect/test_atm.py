import json

from atm_bd_core.collect.atm import task_events, tasks
from atm_bd_types import FactKind, TaskState


def test_tasks_success_and_failure(recorded_runner):
    argv = ["atm", "task", "list", "--all", "--json"]
    runner = recorded_runner({"stdout": json.dumps([{"task_id": "a", "assignee": "sam", "state": "active"}])})
    result, error = tasks(runner)
    assert result is not None and error is None and result[0].state == TaskState.ACTIVE
    assert runner.calls == [(argv, None)]
    runner = recorded_runner({"code": 1, "stderr": "failed"})
    result, error = tasks(runner)
    assert result is None and error is not None and error.kind == FactKind.TASKS
    assert runner.calls == [(argv, None)]


def test_events_success_and_failure(recorded_runner):
    argv = ["atm", "task", "events", "a", "--all", "--json"]
    runner = recorded_runner({"stdout": json.dumps({"events": [
        {"event": "started", "at": "2026-01-01T00:00:00Z"},
        {"event": "reminded", "outcome": "emitted"},
    ]})})
    result, error = task_events(runner, ["a"])
    assert result is not None and error is None and result[0].reminders_since_start == 1
    assert result[0].last_start == 1767225600
    assert runner.calls == [(argv, None)]
    runner = recorded_runner({"code": 1, "stderr": "failed"})
    result, error = task_events(runner, ["a"])
    assert result is None and error is not None and error.kind == FactKind.TASK_EVENTS
    assert runner.calls == [(argv, None)]
