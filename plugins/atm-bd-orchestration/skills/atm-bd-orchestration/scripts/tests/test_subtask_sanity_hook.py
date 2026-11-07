"""The sanity close hook on a subtask's sanity task (atm-bd-orchestration phase bs, sprint bs-5)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import sanity_task_close_hook as hook
from test_sanity_task_close_hook import SCRIPTS, World as SanityWorld

SPRINT = "atm-test-1"


class World(SanityWorld):
    """The sanity World re-pointed at subtask 1 of a sprint with two subtasks; subtask 2's sanity is open or closed."""

    def __init__(self, tmp_path, monkeypatch, *, sibling_closed):
        super().__init__(tmp_path, monkeypatch)
        self.sprint_sanity, self.qa = f"{SPRINT}.group-sanity", f"{SPRINT}.group-qa"
        self.child, self.sibling = f"{SPRINT}.sub-1", f"{SPRINT}.sub-2"
        self.sibling_sanity = f"{SPRINT}.group-sub-2-sanity"
        self.dev = f"{SPRINT}.group-dev"
        self.task = f"{SPRINT}.group-sub-1-sanity"
        self.bd.rows.clear()
        self.bd.add(self.dev, status="closed", assignee="test-dev", labels=["phase-test", "stage:dev"],
                    metadata={"commit": self.sha, "sprint": "test-1", "stack": "phase-test", "pr_target": "main", "branch": "sprint/test",
                              "worktree": str(tmp_path), "sprint_bead": SPRINT, "sanity_bead": self.sprint_sanity, "sanity_base": "b" * 40,
                              "pr_number": 12, "pr_url": "https://example.test/pull/12"})
        for child in (self.child, self.sibling):
            self.bd.add(child, labels=["phase-test", "stage:subtask"], status="closed", metadata={"sprint_bead": SPRINT})
        self.bd.add(self.task, status="in_progress", assignee="test-sanity", labels=["phase-test", "stage:dev-sanity"],
                    metadata={"dev_bead": self.dev, "checked_bead": self.child, "commit": self.sha})
        self.bd.edge(self.task, self.dev, "blocks")
        self.bd.add(self.sibling_sanity, status="closed" if sibling_closed else "open", labels=["phase-test", "stage:dev-sanity"],
                    metadata={"dev_bead": self.dev, "checked_bead": self.sibling})
        self.bd.add(self.qa, labels=["phase-test", "stage:qa"], metadata={"layer": 1, "reviewers_round1": ["req-qa"]})
        self.bd.add(self.sprint_sanity, labels=["phase-test", "stage:dev-sanity"],
                    metadata={"dev_bead": self.dev, "checked_bead": self.dev, "qa_bead": self.qa, "phase": "test", "sprint": "test-1",
                              "sprint_bead": SPRINT, "stack": "phase-test", "stack_bead": "atm-phase-test.stack", "checked_title": "t",
                              "phase_feature": "f", "lint_command": "just lint", "policy_path": "policy.md", "max_sanity_rounds": 5})
        for blocker in (self.dev, self.task, self.sibling_sanity):
            self.bd.edge(self.sprint_sanity, blocker, "blocks")
        self.histories = {self.task: [{"event": "assigned", "assignee": "test-sanity", "message_id": "assign-s", "to_state": "assigned"}],
                          self.dev: [{"event": "assigned", "assignee": "test-dev", "message_id": "assign-d", "to_state": "assigned"},
                                     {"event": "completed", "to_state": "complete"}]}
        self.values.update(task_id=self.task, checked_bead=self.child)
        self.request["request"]["task_id"] = self.task

    def run(self, command, **kwargs):
        if command[:3] == ["bd", "children", SPRINT]:
            return self.bd.done(command, out=json.dumps([row for row in self.bd.rows.values() if "stage:subtask" in row["labels"]]))
        return super().run(command, **kwargs)


@pytest.fixture
def last_world(tmp_path, monkeypatch):
    return World(tmp_path, monkeypatch, sibling_closed=True)


@pytest.fixture
def middle_world(tmp_path, monkeypatch):
    return World(tmp_path, monkeypatch, sibling_closed=False)


def test_child_pass_closes_only_the_child_sanity_while_a_sibling_is_open(middle_world):
    result = middle_world.invoke()
    assert [(a["command"], a["request"]["task_id"]) for a in result["atm-action"]] == [("task.close", middle_world.task)]
    assert middle_world.journal() == [(middle_world.task, "close", {"reason": f"PASS at {middle_world.sha}"}, "pending")]


def test_last_child_pass_releases_the_sprint_sanity_with_renderable_vars(last_world):
    result = last_world.invoke()
    assert [(a["command"], a["request"]["task_id"]) for a in result["atm-action"]] == [
        ("task.close", last_world.task), ("task.assign", last_world.sprint_sanity)]
    assign = result["atm-action"][1]
    assert assign["as"] == "test-lead" and assign["request"]["to"] == {"agent": "test-sanity", "team": "test-team"}
    source = assign["request"]["message_source"]["Template"]
    values = source["var_file_values"]
    assert (values["task_id"], values["checked_bead"], values["base"]) == (last_world.sprint_sanity, last_world.dev, "b" * 40)
    assert values["close_context"]["qa_bead"] == last_world.qa and values["close_context"]["reviewers_round1"] == ["req-qa"]
    import sc_render
    body = sc_render.render(Path(source["canonical_template_path"]), values)
    assert last_world.sprint_sanity in body


def test_child_pass_before_the_dev_task_completes_is_refused(middle_world):
    middle_world.histories[middle_world.dev].pop()
    result = middle_world.invoke()
    assert result["result"] == "refused" and "subtask sanity needs the sprint's dev task" in result["message"]
    assert not middle_world.journal()


def test_child_must_be_a_subtask_bead(middle_world):
    middle_world.beads[middle_world.child]["labels"] = ["phase-test", "stage:dev"]
    result = middle_world.invoke()
    assert result["result"] == "refused" and "must be a stage:subtask bead" in result["message"]


def test_child_fail_reopens_dev_and_reassigns_with_the_children_listed(middle_world):
    middle_world.values.update(verdict="FAIL", findings=[{"deliverable": 2, "issue": "missing"}])
    result = middle_world.invoke()
    assert result["result"] == "handled"
    journal = middle_world.journal()
    assert any(op == "update" and "sub-1" in args.get("append_notes", "") for _, op, args, _ in journal)
    assign = next(a for a in result["atm-action"] if a["command"] == "task.assign")
    values = assign["request"]["message_source"]["Template"]["var_file_values"]
    assert [child["id"] for child in values["children"]] == [middle_world.child, middle_world.sibling]
    assert not any(a["request"]["task_id"] == middle_world.sprint_sanity for a in result["atm-action"])
