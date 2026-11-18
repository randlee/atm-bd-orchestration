"""A split sprint: one sanity and one QA assignment name every child bead and its commit."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from rendering import render

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

    def test_split_manifest_carries_each_child_deliverables_at_its_commit(self):
        done = self.split("--child", f"t-x-1.sub-1={'1' * 40}", "--child", f"t-x-1.sub-2={'2' * 40}")
        self.assertEqual(done.returncode, 0, done.stderr)
        manifest = json.loads(done.stdout)
        self.assertEqual([(c["id"], c["commit"], c["deliverables_total"]) for c in manifest["children"]],
                         [("t-x-1.sub-1", "1" * 40, 2), ("t-x-1.sub-2", "2" * 40, 1)])
        first = manifest["children"][0]["assignments"][1]["assignment"]
        self.assertEqual((first["dev_bead"]["id"], first["commit"], first["deliverable"]["number"]),
                         ("t-x-1.sub-1", "1" * 40, 2))
        self.assertEqual([a["number"] for a in manifest["assignments"]], [1])
        self.assertEqual(manifest["assignments"][0]["assignment"]["commit"], "a" * 40)

    def test_split_without_child_has_no_children_key(self):
        done = self.split()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn("children", json.loads(done.stdout))

    def test_split_refuses_a_malformed_child(self):
        done = self.split("--child", "t-x-1.sub-1")
        self.assertEqual(done.returncode, 1)
        self.assertIn("<bead>=<commit>", done.stderr)


if __name__ == "__main__":
    unittest.main()
