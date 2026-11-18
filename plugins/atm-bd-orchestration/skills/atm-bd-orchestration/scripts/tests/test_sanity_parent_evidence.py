"""Parent evidence is complete or refused, using controlled commit inputs."""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import jev_client


def load_split():
    loader = importlib.machinery.SourceFileLoader("sanity_parent_evidence", str(SCRIPTS / "sanity-split"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class ParentEvidenceTests(unittest.TestCase):
    def test_parent_is_complete_or_refused_and_children_remain_bounded(self):
        split = load_split()
        base, parent, child_a, child_b = (c * 40 for c in "0123")
        commits = [parent, child_a, child_b]
        patches = {parent: "parent change\n", child_a: "A" * 2000 + "\n", child_b: "B" * 2000 + "\n"}
        labels = {parent: "", child_a: "child-a", child_b: "child-b"}
        bead = split.parse_bead({"id": "sprint", "title": "Sprint", "description":
                                 "## Deliverables\n1. Integrate both children.\n", "metadata": {"owned_paths": ["**"]}}, "sprint")
        plans = []
        for name, sha in (("child-a", child_a), ("child-b", child_b)):
            child = split.parse_bead({"id": name, "title": name, "description": "## Deliverables\n1. Implement.\n",
                                      "metadata": {"owned_paths": [name]}}, name)
            plans.append(split.ChildPlan(child, sha, split.parse_deliverables(child.description), [], [name], []))

        def split_git(worktree, *args, **kwargs):
            if args[:4] == ("rev-list", "--reverse", "--topo-order", "--parents"):
                return "\n".join(f"{sha} {prev}" for sha, prev in zip(commits, [base, parent, child_a]))
            if args[:2] == ("show", "-s"):
                return labels[args[-1]]
            raise AssertionError(args)

        def run(argv, **kwargs):
            if "--is-ancestor" in argv:
                return subprocess.CompletedProcess(argv, 0, "", "")
            if "rev-list" in argv:
                return subprocess.CompletedProcess(argv, 0, "\n".join(commits), "")
            if "show" in argv:
                sha = argv[-2]
                return subprocess.CompletedProcess(argv, 0, f"commit {sha}\n{patches[sha]}", "")
            raise AssertionError(argv)

        def files(worktree, selected):
            return [labels[sha] or "parent" for sha in selected]

        argv = ["sanity-split", "--task", "sanity", "--bead", "sprint", "--worktree", "/repo",
                "--branch", "sprint/x", "--commit", child_b, "--base", base, "--lint-command", "true",
                "--scratch", "/scratch", "--child", f"child-a={child_a}", "--child", f"child-b={child_b}"]
        stdout, stderr = io.StringIO(), io.StringIO()
        with (patch.object(sys, "argv", argv), patch.object(split, "load_bead", return_value=bead),
              patch.object(split, "pin", return_value=(child_b, base)),
              patch.object(split, "changed_files", return_value=["parent", "child-a", "child-b"]),
              patch.object(split, "load_children", return_value=plans), patch.object(split, "git", side_effect=split_git),
              patch.object(split, "commit_files", side_effect=files), patch.object(jev_client.subprocess, "run", side_effect=run),
              patch.object(split, "start_lint", return_value={}) as start_lint,
              contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr)):
            with patch.object(jev_client, "MAX_REQUEST_BYTES", 3500):
                self.assertEqual(split.main(), 2)
                self.assertIn("SANITY.JEV_REQUEST_TOO_LARGE", stderr.getvalue())
                self.assertRegex(stderr.getvalue(), r"\d+ bytes > 3500")
                self.assertEqual(stdout.getvalue(), "")
                start_lint.assert_not_called()
            stdout.seek(0)
            stdout.truncate()
            with patch.object(jev_client, "MAX_REQUEST_BYTES", 10000):
                self.assertEqual(split.main(), 0, stderr.getvalue())
                assignments = [entry["assignment"] for entry in json.loads(stdout.getvalue())["assignments"]]
                self.assertEqual(assignments[0]["evidence_commits"], commits)
                self.assertEqual(assignments[1]["evidence_commits"], [child_a])
                self.assertEqual(assignments[2]["evidence_commits"], [child_b])
                parent_request = json.dumps(jev_client.assignment_requests(assignments[0])[0])
                self.assertIn("parent change", parent_request)
                self.assertIn("A" * 2000, parent_request)
                self.assertIn("B" * 2000, parent_request)
                for assignment, expected, excluded in ((assignments[1], "A", "B"), (assignments[2], "B", "A")):
                    request = json.dumps(jev_client.assignment_requests(assignment)[0])
                    self.assertIn(expected * 2000, request)
                    self.assertNotIn(excluded * 100, request)
