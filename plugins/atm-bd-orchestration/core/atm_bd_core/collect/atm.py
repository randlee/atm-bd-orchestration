"""ATM task facts collected through the injected command runner."""

import json
from datetime import datetime

from atm_bd_types import CollectError, FactKind, TaskEvents, TaskFact, TaskState


def _read(runner, argv):
    result = runner.run(argv, None)
    if result.code:
        raise ValueError(result.stderr or f"exit {result.code}")
    return json.loads(result.stdout)


def tasks(runner):
    argv = ["atm", "task", "list", "--all", "--json"]
    try:
        raw = _read(runner, argv)
        if not isinstance(raw, list):
            raise ValueError("expected task list")
        states = {"assigned": TaskState.ASSIGNED, "active": TaskState.ACTIVE, "complete": TaskState.COMPLETE}
        return [TaskFact(item["task_id"], item["assignee"], states[item["state"]], item.get("bead_id")) for item in raw], None
    except (OSError, ValueError, KeyError, TypeError) as error:
        return None, CollectError(FactKind.TASKS, argv, str(error), "Check ATM connectivity and task output.")


def task_events(runner, task_ids):
    facts = []
    for task_id in task_ids:
        argv = ["atm", "task", "events", task_id, "--all", "--json"]
        try:
            events = _read(runner, argv)["events"]
            if not isinstance(events, list):
                raise ValueError("expected events list")
            last_start = None
            reminders = 0
            for event in events:
                if event["event"] == "started":
                    value = datetime.fromisoformat(event["at"].replace("Z", "+00:00"))
                    if value.tzinfo is None:
                        raise ValueError("start time lacks timezone")
                    last_start = int(value.timestamp())
                    reminders = 0
                elif event["event"] == "reminder" and last_start is not None:
                    reminders += 1
            facts.append(TaskEvents(task_id, reminders, last_start))
        except (OSError, ValueError, KeyError, TypeError) as error:
            return None, CollectError(FactKind.TASK_EVENTS, argv, str(error), "Check ATM task event output.")
    return facts, None
