"""Sprints split into subtask beads: the dev close and the sanity hook (atm-bd-orchestration phase bs, sprint bs-5)."""
from __future__ import annotations

import json

import pytest

from task_close_world import World, bd_row


@pytest.fixture
def world(tmp_path, monkeypatch):
    return World(tmp_path, monkeypatch)


def add_children(world, count=2, *, closed=True):
    """`count` stage:subtask children of the sprint, each with its poured sanity bead and (unassigned) sanity task."""
    sprint = "atm-bj-1"
    world.beads[world.values["checked_bead"]]["metadata"]["sprint_bead"] = sprint
    pairs = []
    for n in range(1, count + 1):
        child, sanity = f"{sprint}.sub-{n}", f"{sprint}.group-sub-{n}-sanity"
        world.beads[child] = bd_row(child, status="closed" if closed else "open", labels=["stage:subtask"], parent=sprint,
                                    description=f"deliverables of {n}", metadata={"model_class": "luna", "sprint_bead": sprint})
        world.beads[sanity] = bd_row(sanity, labels=["stage:dev-sanity"], parent=sprint,
                                     metadata={"checked_bead": child, "dev_bead": world.values["checked_bead"], "sanity_bead": sanity})
        world.tasks[sanity] = []
        pairs.append((child, sanity))
    return pairs


def test_dev_close_with_children_assigns_each_child_sanity_not_the_sprint_sanity(world):
    pairs = add_children(world)
    result = world.run("dev", skip_checks=True)
    assert "ok" in result, result
    assigned = [m for m in world.messages if m["type"] == "dev-sanity-task"]
    assert [m["values"]["checked_bead"] for m in assigned] == [child for child, _ in pairs]
    assert [m["values"]["sanity_task_id"] for m in assigned] == [sanity for _, sanity in pairs]
    assert world.tasks[world.values["sanity_task_id"]] == []  # the sprint's own sanity waits for its children
    assert world.beads[world.values["checked_bead"]]["status"] == "closed"
    assert world.beads[world.values["checked_bead"]]["metadata"]["sanity_base"] == "b" * 40


def test_dev_close_refuses_while_a_child_is_open_and_closes_nothing(world):
    add_children(world, closed=False)
    result = world.run("dev", skip_checks=True)
    assert result["err"]["code"] == "CLOSE.OPEN_SUBTASKS", result
    assert "atm-bj-1.sub-1" in result["err"]["message"] and "bd close" in result["err"]["fix"]
    assert world.beads[world.values["checked_bead"]]["status"] != "closed"
    assert not world.messages


def test_dev_close_replay_does_not_assign_the_child_sanity_twice(world):
    add_children(world)
    assert "ok" in world.run("dev", skip_checks=True)
    before = len(world.messages)
    assert "ok" in world.run("dev", skip_checks=True)
    assert len(world.messages) == before


def test_dev_close_without_children_is_unchanged(world):
    world.beads[world.values["checked_bead"]]["metadata"]["sprint_bead"] = "atm-bj-1"
    result = world.run("dev", skip_checks=True)
    assert "ok" in result, result
    assert world.tasks[world.values["sanity_task_id"]]


CHILDREN = [{"id": "atm-bj-1.sub-1", "title": "types", "model_class": "luna", "deliverables": "1. add the type"},
            {"id": "atm-bj-1.sub-2", "title": "wiring", "model_class": None, "deliverables": "1. wire it"}]


def test_dev_template_lists_children_and_the_open_subtask_refusal(world):
    from task_close_world import EXAMPLES, SCRIPTS, hook
    values = json.loads((EXAMPLES / "dev-template-vars.json").read_text())
    values.update(primary_checkout=str(world.root), worktree_path=str(world.root), phase_root="atm-phase-bj")
    path = SCRIPTS.parent / "templates/dev-template.xml.j2"
    plain = hook.sc_render.render(path, {**values, "children": []})
    split = hook.sc_render.render(path, {**values, "children": CHILDREN})
    assert 'id="d0"' not in plain
    assert 'id="d0"' in split and "`atm-bj-1.sub-1` (types; model class `luna`)" in split
    assert "`atm-bj-1.sub-2` (wiring; model class `the sprint's`)" in split and "CLOSE.OPEN_SUBTASKS" in split


def test_qa_template_carries_each_childs_deliverables(world):
    from task_close_world import SCRIPTS, hook
    values = json.loads((SCRIPTS.parent / "examples/qa-template-vars.json").read_text())
    path = SCRIPTS.parent / "templates/qa-template.xml.j2"
    assert "<subtasks>" not in hook.sc_render.render(path, values)
    split = hook.sc_render.render(path, {**values, "children": CHILDREN})
    assert "<subtasks>" in split and "atm-bj-1.sub-2: wiring\n1. wire it" in split
