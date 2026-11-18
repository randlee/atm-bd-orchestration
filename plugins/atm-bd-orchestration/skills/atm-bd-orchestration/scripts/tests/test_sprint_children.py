"""A split sprint: one sanity and one QA assignment name every child bead and its commit."""
from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import json
import subprocess
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from typing import Any

import pytest

from rendering import render
from task_close_world import World, bd_row
import test_close_vars as vars_tests
import test_sanity_split as split_tests

SKILL = Path(__file__).parents[2]
SANITY = SKILL / "templates" / "dev-sanity-template.xml.j2"
QA = SKILL / "templates" / "qa-template.xml.j2"
SPLIT = SKILL / "scripts" / "sanity-split"
CHILDREN = [{"id": "t-x-1.sub-1", "commit": "1" * 40}, {"id": "t-x-1.sub-2", "commit": "2" * 40}]
SANITY_VARS = {
    "task_id": "t-x-1-sanity", "checked_bead": "t-x-1", "sprint": "x-1", "worktree_path": "/w/x-1",
    "branch": "sprint/x-1", "commit": "a" * 40, "base": "b" * 40, "pr_number": 7, "pr_url": "https://example.invalid/pull/7",
    "primary_checkout": "/primary", "lint_command": "just lint", "beads_dir": "/primary/.beads",
    "close_context": {}, "sanity_close_mode": "legacy",
}
QA_VARS = {
    "task_id": "t-x-1-qa1", "checked_bead": "t-x-1", "phase": "x", "phase_feature": "phase-x", "sprint": "x-1",
    "stack": "phase-x", "layer": 1, "round": 1, "branch": "sprint/x-1", "commit": "a" * 40, "base": "develop",
    "worktree_path": "/w/x-1", "pr_number": 7, "policy_path": "policy.md", "reviewers_round1": ["req-qa"],
}


def rendered(template: Path, variables: dict) -> str:
    done = render(template, variables)
    assert done.returncode == 0, done.stderr
    return done.stdout


def bead(bead_id: str, deliverables: str) -> dict:
    return {"id": bead_id, "title": f"{bead_id} title", "description": f"## Deliverables\n{deliverables}",
            "metadata": {"owned_paths": ["src/**"]}}


class SprintChildrenTests(unittest.TestCase):
    def test_sanity_assignment_lists_both_children_with_commits(self):
        text = rendered(SANITY, {**SANITY_VARS, "children": CHILDREN})
        self.assertEqual(text.count("<atm-task "), 1)
        for child in CHILDREN:
            self.assertIn(f'<child id="{child["id"]}" commit="{child["commit"]}"/>', text)
        self.assertIn("--child <id>=<commit>", text)

    def test_daemon_mode_sanity_verifies_each_child_at_its_commit(self):
        """qa1-f2: daemon close mode runs no sanity-split, so the assignment itself carries the child check."""
        sentence = ("Each `<children>` entry is a child bead of this sprint: read its numbered deliverables with "
                    "`bd show <id> --json` and verify each at that child's commit; number them after the checked "
                    "bead's, in `<children>` order, and name the child in each finding's issue.")
        daemon = {**SANITY_VARS, "sanity_close_mode": "daemon"}
        text = rendered(SANITY, {**daemon, "children": CHILDREN})
        for child in CHILDREN:
            self.assertIn(f'<child id="{child["id"]}" commit="{child["commit"]}"/>', text)
        self.assertNotIn("--child", text)                       # daemon mode never runs sanity-split
        step_b = text[text.index('<step id="b">'):text.index('<step id="e">')]
        self.assertIn(sentence, step_b)
        self.assertLess(step_b.index("Verify the numbered deliverables"), step_b.index(sentence))
        self.assertNotIn("child bead of this sprint", rendered(SANITY, daemon))
        legacy = rendered(SANITY, {**SANITY_VARS, "children": CHILDREN})
        self.assertNotIn("child bead of this sprint", legacy)   # the other mode checks children through sanity-split
        self.assertIn("--child <id>=<commit>", legacy)

    def test_qa_assignment_names_both_children(self):
        text = rendered(QA, {**QA_VARS, "children": CHILDREN})
        self.assertEqual(text.count("<repo-qa-task "), 1)
        for child in CHILDREN:
            self.assertIn(f'<child id="{child["id"]}" commit="{child["commit"]}"/>', text)

    def test_sprint_without_children_renders_no_child_text(self):
        for template, variables in ((SANITY, SANITY_VARS), (QA, QA_VARS)):
            text = rendered(template, variables)
            self.assertNotIn("<children>", text)
            self.assertNotIn("--child", text)

    def split(self, *extra: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as root:
            beads = Path(root) / "beads.json"
            beads.write_text(json.dumps([bead("t-x-1", "1. Parent.\n"), bead("t-x-1.sub-1", "1. One.\n2. Two.\n"),
                                         bead("t-x-1.sub-2", "1. Three.\n")]))
            return subprocess.run(
                [str(SPLIT), "--task", "t-x-1-sanity", "--bead", "t-x-1", "--worktree", root, "--branch", "sprint/x-1",
                 "--commit", "a" * 40, "--base", "b" * 40, "--lint-command", "true", "--scratch", root,
                 "--bead-json", str(beads), "--split-only", *extra], capture_output=True, text=True)

    def test_split_numbers_each_child_deliverable_after_the_checked_beads_at_its_commit(self):
        done = self.split("--child", f"t-x-1.sub-1={'1' * 40}", "--child", f"t-x-1.sub-2={'2' * 40}")
        self.assertEqual(done.returncode, 0, done.stderr)
        manifest = json.loads(done.stdout)
        self.assertEqual(manifest["deliverables_total"], 4)
        self.assertEqual([(c["id"], c["commit"], c["deliverables_total"]) for c in manifest["children"]],
                         [("t-x-1.sub-1", "1" * 40, 2), ("t-x-1.sub-2", "2" * 40, 1)])
        rows = [(a["number"], a.get("bead"), a.get("commit"), a["assignment"]["dev_bead"]["id"], a["assignment"]["commit"],
                 a["assignment"]["deliverables_total"]) for a in manifest["assignments"]]
        self.assertEqual(rows, [(1, None, None, "t-x-1", "a" * 40, 4),
                                (2, "t-x-1.sub-1", "1" * 40, "t-x-1.sub-1", "1" * 40, 4),
                                (3, "t-x-1.sub-1", "1" * 40, "t-x-1.sub-1", "1" * 40, 4),
                                (4, "t-x-1.sub-2", "2" * 40, "t-x-1.sub-2", "2" * 40, 4)])

    def test_split_without_child_has_no_children_key(self):
        done = self.split()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn("children", json.loads(done.stdout))

    def test_split_refuses_a_malformed_child(self):
        done = self.split("--child", "t-x-1.sub-1")
        self.assertEqual(done.returncode, 1)
        self.assertIn("<bead>=<commit>", done.stderr)


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                           "-c", "commit.gpgsign=false", *args], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def _commit(repo: Path, name: str, bead: str | None = None) -> str:
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / name).write_text(name)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", name + (f"\n\nBead: {bead}" if bead else ""))
    return _git(repo, "rev-parse", "HEAD")


def test_each_merged_childs_commit_is_derived_and_verified_through_a_rebase(tmp_path):
    """qa1-f1: two children, each merged separately, then a rebase onto an advanced stack top. The rebase rewrites
    every commit and drops the merges; each child's `Bead:` trailer still identifies its commit on the branch."""
    loader = importlib.machinery.SourceFileLoader("sanity_split_children", str(SPLIT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    split = importlib.util.module_from_spec(spec)
    loader.exec_module(split)
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "top")
    _commit(repo, "base.txt")
    _git(repo, "checkout", "-q", "-b", "sprint")
    before: dict[str, str] = {}
    for child, files in (("t-x-1.sub-1", ("one-a.txt", "one-b.txt")), ("t-x-1.sub-2", ("two-a.txt",))):
        _git(repo, "checkout", "-q", "-b", child, "top")        # each child works on its own branch
        for name in files:
            before[child] = _commit(repo, name, child)
        _git(repo, "checkout", "-q", "sprint")
        _git(repo, "merge", "-q", "--no-ff", "-m", f"merge {child}", child)
    _commit(repo, "glue.txt")                                    # the dev's own commit carries no child trailer
    _git(repo, "checkout", "-q", "top")
    top = _commit(repo, "top.txt")                               # the stack top advances
    _git(repo, "checkout", "-q", "sprint")
    _git(repo, "rebase", "-q", "top")
    head = _git(repo, "rev-parse", "HEAD")
    assert _git(repo, "rev-list", "--merges", f"{top}..{head}") == ""
    beads = tmp_path / "beads.json"
    beads.write_text(json.dumps([bead("t-x-1", "1. Parent.\n"), bead("t-x-1.sub-1", "1. One.\n"),
                                 bead("t-x-1.sub-2", "1. Two.\n")]))

    def load(**commits: str):
        args = argparse.Namespace(child=[f"{child}={commit}" for child, commit in commits.items()], worktree=str(repo),
                                  split_only=False, bead_json=str(beads), bead="t-x-1")
        return split.load_children(args, head, top, ["src/**"])

    after = {child: split.child_commit_on_branch(str(repo), top, head, child) for child in before}
    assert all(after.values()) and len({*after.values(), head, *before.values()}) == 5
    for child, commit in after.items():                          # the derived commit is that child's last rewritten one
        assert _git(repo, "show", "-s", "--format=%(trailers:key=Bead,valueonly)", commit) == child
        assert _git(repo, "show", "-s", "--format=%s", commit) == _git(repo, "show", "-s", "--format=%s", before[child])
    one, two = load(**{"t-x-1.sub-1": after["t-x-1.sub-1"], "t-x-1.sub-2": after["t-x-1.sub-2"]})
    assert (one.commit, one.files) == (after["t-x-1.sub-1"], ["src/one-a.txt", "src/one-b.txt"])
    assert (two.commit, sorted(two.files)) == (after["t-x-1.sub-2"], ["src/one-a.txt", "src/one-b.txt", "src/two-a.txt"])
    planted = {"a commit recorded before the rebase": (before["t-x-1.sub-1"], "is not in the history"),
               "another child's commit": (after["t-x-1.sub-2"], "does not carry the trailer `Bead: t-x-1.sub-1`"),
               "the dev's own head": (head, "does not carry the trailer `Bead: t-x-1.sub-1`")}
    for label, (commit, why) in planted.items():
        with pytest.raises(split.Fail) as refused:
            load(**{"t-x-1.sub-1": commit})
        assert refused.value.code == 4, label
        assert why in str(refused.value), label
        assert f"bd update t-x-1.sub-1 --set-metadata commit={after['t-x-1.sub-1']}" in str(refused.value), label
    assert split.child_commit_on_branch(str(repo), top, head, "t-x-1.sub-9") is None
    with pytest.raises(split.Fail) as untagged:
        load(**{"t-x-1.sub-9": head})
    assert "each commit of a child ends with that trailer" in str(untagged.value)


SPRINT = "t-d-1"
KIDS = [{"id": "t-d-1.sub-2", "labels": ["stage:subtask"], "metadata": {"commit": "2" * 40, "parent": SPRINT}},
        {"id": "t-d-1.sub-1", "labels": ["stage:subtask"], "metadata": {"commit": "1" * 40, "parent": SPRINT}},
        {"id": "t-d-1.dev", "labels": ["stage:dev"], "metadata": {"parent": SPRINT}}]
TWO = [{"id": "t-d-1.sub-1", "commit": "1" * 40}, {"id": "t-d-1.sub-2", "commit": "2" * 40}]


class VarsTests(unittest.TestCase):
    def dev_vars(self, kids):
        dev = vars_tests.row("t-d-1.f1-fix", "stage:dev", "dev")
        with unittest.mock.patch.object(vars_tests.close_vars_cli, "read", lambda repo, bead, fallback, **_: dev):
            return vars_tests.close_vars_cli.build(vars_tests.REPO, dev["id"], subtasks_of=lambda repo, sprint: kids)["vars"]

    def qa_vars(self, kids):
        rows = {vars_tests.QA["id"]: vars_tests.QA, vars_tests.FIX["id"]: vars_tests.FIX}
        with unittest.mock.patch.object(vars_tests.close_vars_cli, "read", lambda repo, bead, fallback, **_: rows[bead]):
            return vars_tests.close_vars_cli.build_qa_assignment(
                vars_tests.REPO, vars_tests.QA["id"], pr_reader=lambda repo, number: vars_tests.CURRENT_PR,
                subtasks_of=lambda repo, sprint: kids)["vars"]

    def test_dev_vars_list_the_sprints_subtask_children(self):
        self.assertEqual(self.dev_vars(KIDS)["child_beads"], ["t-d-1.sub-1", "t-d-1.sub-2"])
        self.assertEqual(self.dev_vars([])["child_beads"], [])

    def test_qa_vars_carry_the_children_with_commits(self):
        self.assertEqual(self.qa_vars(KIDS)["children"], TWO)
        self.assertNotIn("children", self.qa_vars([]))

    def test_qa_vars_refuse_a_child_without_a_commit(self):
        bare = [{**KIDS[0], "metadata": {}}]
        with self.assertRaises(vars_tests.close_fields.CloseFieldsError) as caught:
            self.qa_vars(bare)
        self.assertIn("bd update t-d-1.sub-2 --set-metadata commit=<sha>", caught.exception.fix)


@pytest.fixture
def world(tmp_path, monkeypatch):
    return World(tmp_path, monkeypatch)


def with_children(world, kids):
    world.values["sprint_bead"] = SPRINT
    world.children = [bd_row(kid["id"], labels=kid["labels"], metadata=kid["metadata"]) for kid in kids]
    world.beads[world.values["checked_bead"]]["metadata"]["commit"] = world.head


def test_sanity_dispatch_passes_each_child_with_its_commit(world):
    with_children(world, KIDS)
    assert "ok" in world.run("dev")
    dispatch = next(m for m in world.messages if m["type"] == "dev-sanity-task")
    assert dispatch["values"]["children"] == TWO
    for child in TWO:
        assert f'<child id="{child["id"]}" commit="{child["commit"]}"/>' in dispatch["body"]


def test_sanity_dispatch_without_children_adds_none(world):
    with_children(world, [])
    assert "ok" in world.run("dev")
    dispatch = next(m for m in world.messages if m["type"] == "dev-sanity-task")
    assert "children" not in dispatch["values"] and "<children>" not in dispatch["body"]


def test_sanity_dispatch_refuses_a_child_without_a_commit_before_any_write(world):
    with_children(world, [{**KIDS[0], "metadata": {"parent": SPRINT}}])
    result = world.run("dev")
    assert result["err"]["code"] == "ASSIGN_VARS.CHILD_COMMIT_MISSING"
    assert "t-d-1.sub-2" in result["err"]["message"]
    assert "bd update t-d-1.sub-2 --set-metadata commit=<sha>" in result["err"]["fix"]
    assert world.writes == []


class MergeTests(unittest.TestCase):
    """A split sprint's merge: the child deliverables are checked at each child's commit."""
    repo: Any
    setUp = split_tests.SanitySplit.setUp
    run_split = split_tests.SanitySplit.run_split
    merge = split_tests.SanitySplit.merge
    wait_lint = split_tests.SanitySplit.wait_lint
    close_event_writer = split_tests.SanitySplit.close_event_writer

    def manifest(self):
        repo = self.repo
        repo.commit("crates/types/src/a.rs", "pub fn a() {}\n", "child one\n\nBead: x-1.sub-1")
        first = split_tests.git(repo.wt, "rev-parse", "HEAD")
        repo.commit("crates/types/src/b.rs", "pub fn b() {}\n", "child two\n\nBead: x-1.sub-2")
        split_tests.git(repo.wt, "push", "-q", "origin", "sprint/x")
        head = split_tests.git(repo.wt, "rev-parse", "HEAD")
        beads = [*split_tests.bead(), *({"id": f"x-1.sub-{n}", "title": f"sub {n}", "description": f"## Deliverables\n1. Child {n}.\n",
                                         "metadata": {"owned_paths": ["crates/**"]}} for n in (1, 2))]
        out = self.run_split(beads, None, head, "sprint/x", "develop", "--child", f"x-1.sub-1={first}",
                             "--child", f"x-1.sub-2={head}", lint="true")
        self.assertEqual(out.returncode, 0, out.stderr)
        manifest = json.loads(out.stdout)
        self.assertEqual(self.wait_lint(manifest["lint"]["exit_file"]), "0")
        return manifest, head, first

    def results(self, head, first, undone=()):
        issue = [{"kind": "skipped", "file": "crates/types/src/a.rs", "line": 1, "issue": "not done"}]
        wanted = [(1, "{{ bead_prefix }}-x-1", head), (2, "{{ bead_prefix }}-x-1", head), (3, "x-1.sub-1", first), (4, "x-1.sub-2", head)]
        out = []
        for number, bead, commit in wanted:
            reply = split_tests.result(number, commit, issue if number in undone else ())
            reply["data"]["dev_bead"] = bead
            out.append(reply)
        return out

    def test_all_child_deliverables_done_passes(self):
        manifest, head, first = self.manifest()
        merged = self.merge(manifest, self.results(head, first))
        self.assertEqual(merged.returncode, 0, merged.stderr)
        self.assertEqual(json.loads(merged.stdout)["verdict"], "PASS")

    def test_an_undone_child_deliverable_fails(self):
        manifest, head, first = self.manifest()
        merged = self.merge(manifest, self.results(head, first, undone=(3,)))
        self.assertEqual(merged.returncode, 0, merged.stderr)
        self.assertEqual(json.loads(merged.stdout)["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
