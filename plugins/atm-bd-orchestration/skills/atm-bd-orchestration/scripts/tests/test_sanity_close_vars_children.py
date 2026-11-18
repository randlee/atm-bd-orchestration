"""sanity-close-vars on a split sprint's manifest: the numbers cover the checked bead's and every child's deliverables."""
from __future__ import annotations

import json

import pytest

from test_sanity_close_vars import CLOSE, inputs, task_events  # noqa: F401  (fixtures)

CHILDREN = [("t-x-1.sub-1", "1" * 40), ("t-x-1.sub-2", "2" * 40)]


@pytest.fixture
def split(inputs):  # noqa: F811
    manifest, selected = inputs
    manifest["deliverables_total"] = 4
    manifest["assignments"] = [{"number": 1}, {"number": 2, "bead": CHILDREN[0][0], "commit": CHILDREN[0][1]},
                               {"number": 3, "bead": CHILDREN[0][0], "commit": CHILDREN[0][1]},
                               {"number": 4, "bead": CHILDREN[1][0], "commit": CHILDREN[1][1]}]
    manifest["children"] = [{"id": c, "commit": s, "deliverables_total": n} for (c, s), n in zip(CHILDREN, (2, 1))]
    return manifest, selected


def test_a_pass_counts_every_child_deliverable(split):
    manifest, selected = split
    result = CLOSE.build(manifest, selected)
    assert (result["deliverables_total"], result["deliverables_complete"], result["undone"]) == (4, 4, [])
    assert result["commit"] == manifest["sha"] and result["checked_bead"] == manifest["dev_bead"]


def test_an_undone_child_deliverable_is_counted_and_named(split):
    manifest, selected = split
    selected.update(verdict="FAIL", findings_count=1, findings=[{"deliverable": 3, "issue": "sub-1 not done"}])
    result = CLOSE.build(manifest, selected)
    assert result["undone"] == [{"number": 3, "reason": "sub-1 not done"}]
    assert (result["deliverables_total"], result["deliverables_complete"]) == (4, 3)


def test_a_lint_failure_marks_every_numbered_deliverable_undone(split):
    manifest, selected = split
    selected.update(verdict="FAIL", findings_count=1, lint_md="lint exited 1")
    assert [item["number"] for item in CLOSE.build(manifest, selected)["undone"]] == [1, 2, 3, 4]
