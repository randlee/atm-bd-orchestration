import json
from types import SimpleNamespace

from atm_bd_types import FactKind, TaskState

from atm_bd_core.collect.atm import task_events, tasks


class Runner:
    def __init__(self, body, code=0):
        self.body, self.code = body, code

    def run(self, argv, stdin):
        return SimpleNamespace(code=self.code, stdout=json.dumps(self.body), stderr="failed")


def test_tasks_success_and_failure():
    result, error = tasks(Runner([{"task_id": "a", "assignee": "sam", "state": "active"}]))
    assert result is not None
    assert error is None and result[0].state == TaskState.ACTIVE
    result, error = tasks(Runner([], 1))
    assert error is not None
    assert result is None and error.kind == FactKind.TASKS


def test_events_success_and_failure():
    result, error = task_events(Runner({"events": [
        {"event": "started", "at": "2026-01-01T00:00:00Z"},
        {"event": "reminder"},
    ]}), ["a"])
    assert result is not None
    assert error is None and result[0].reminders_since_start == 1
    assert result[0].last_start == 1767225600
    result, error = task_events(Runner({}, 1), ["a"])
    assert error is not None
    assert result is None and error.kind == FactKind.TASK_EVENTS
