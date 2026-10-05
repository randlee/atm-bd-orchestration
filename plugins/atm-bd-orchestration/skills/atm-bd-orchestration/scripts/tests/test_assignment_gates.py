from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

MODULE = Path(__file__).parents[1] / "assignment-gates.py"
FIXTURES = Path(__file__).parent / "fixtures"
SPEC = importlib.util.spec_from_file_location("assignment_gates", MODULE)
assert SPEC and SPEC.loader
gates = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gates)
LOCATE = gates.stack_view_script


class FakeRunner:
    """Answers by (cwd, argv) first, then argv; records every call's cwd."""
    def __init__(self, responses): self.responses, self.calls = responses, []
    @property
    def cwds(self): return [cwd for cwd, _ in self.calls]
    def __call__(self, args, **kwargs):
        self.calls.append((kwargs.get("cwd"), tuple(args)))
        code, stdout, *stderr = self.responses.get((kwargs.get("cwd"), tuple(args)), self.responses.get(tuple(args), (0, "")))
        return subprocess.CompletedProcess(args, code, stdout, "".join(stderr))


VIEW = "/scripts/gh_stack_view.py"
STACK_VIEW = (sys.executable, VIEW, "--json")


def ns(kind, **overrides):
    values = dict(kind=kind, root="{{ bead_prefix }}-phase-d", bead="bead", pr_target="target", identity="terra",
                  pr_number="7", commit="head", checked_bead="checked")
    values.update(overrides)
    return SimpleNamespace(**values)


def dumped(value): return json.dumps(value)


def dev_runner(overrides=None):
    data = {
        (gates.VALIDATE_PLAN, "--root", "{{ bead_prefix }}-phase-d"): (0, ""),
        ("bd", "ready", "-n", "0", "--json"): (0, dumped([{"id": "bead"}])),
        ("bd", "show", "bead", "--json"): (0, dumped([{"status": "open", "assignee": "", "metadata": {"difficulty": "normal", "pr_target": "target"}}])),
        ("atm", "members", "--json"): (0, dumped([{"identity": "terra", "model": "gpt-6-terra"}])),
        ("git", "merge-base", "--is-ancestor", "origin/target", "HEAD"): (0, ""),
    }; data.update(overrides or {}); return FakeRunner(data)


def sanity_runner(overrides=None):
    data = {
        ("bd", "show", "bead", "--json"): (0, dumped([{"metadata": {}}])),
        ("gh", "pr", "view", "7", "--json", "baseRefName,headRefName,headRefOid"): (0, dumped({"baseRefName": "target", "headRefName": "branch", "headRefOid": "head"})),
        (str(gates.PRIMARY), STACK_VIEW): (0, dumped({"stacks": [{"trunk": "integrate", "rows": [
            {"branch": "merged", "pr": 5, "pr_base": "integrate", "merged": True}, {"branch": "target", "pr": 6, "pr_base": "integrate", "merged": False},
            {"branch": "branch", "pr": 7, "pr_base": "target", "merged": False}]}]})),
        ("git", "fetch", "origin"): (0, ""),
        ("git", "rev-parse", "target"): (0, "base"),
        ("git", "rev-parse", "origin/target"): (0, "base"),
        ("git", "log", "--format=%H", "origin/target..head"): (0, "delta"),
        ("git", "status", "--porcelain", "--untracked-files=no"): (0, "?? .beads.gate.lock"),
        ("bd", "history", "bead", "--json"): (0, dumped({"events": []})),
    }; data.update(overrides or {}); return FakeRunner(data)


def qa_runner(overrides=None):
    data = {
        ("bd", "show", "bead", "--json"): (0, dumped([{"metadata": {"checked_bead": "checked", "pr_target": "target"}}])),
        ("bd", "list", "-l", "stage:dev-sanity", "--status", "closed", "-n", "0", "--json"): (0, dumped([
            {"id": "checked-sanity-old", "close_reason": "PASS at 0ld0ld0", "closed_at": "2026-10-01T00:00:00Z",
             "metadata": {"dev_bead": "checked"}},
            {"id": "checked-sanity", "close_reason": "PASS at abc1234", "closed_at": "2026-10-02T00:00:00Z",
             "metadata": {"dev_bead": "checked"}},
            {"id": "other-sanity", "close_reason": "PASS at fff9999", "closed_at": "2026-10-03T00:00:00Z",
             "metadata": {"dev_bead": "other"}}])),
        ("gh", "pr", "view", "7", "--json", "baseRefName,headRefOid"): (0, dumped({"baseRefName": "target", "headRefOid": "abc1234def"})),
        ("git", "rev-parse", "HEAD"): (0, "abc1234def"),
    }; data.update(overrides or {}); return FakeRunner(data)


def view(*rows, trunk="integrate"):
    return {(str(gates.PRIMARY), STACK_VIEW): (0, dumped({"stacks": [{"trunk": trunk, "rows": list(rows)}]}))}


class AssignmentGateTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(gates, "stack_view_script", return_value=VIEW)
        patcher.start(); self.addCleanup(patcher.stop)

    def expected(self, name): return json.loads((FIXTURES / name).read_text())["expected"]

    def assert_fixture(self, name, gate_args, runner):
        code = gates.evaluate(gate_args, runner)
        self.assertEqual(code, self.expected(name))
        output = io.StringIO()
        argv = [gate_args.kind, "--root", gate_args.root, "--bead", gate_args.bead, "--pr-target", gate_args.pr_target,
                "--identity", gate_args.identity, "--pr-number", gate_args.pr_number, "--commit", gate_args.commit,
                "--checked-bead", gate_args.checked_bead]
        with redirect_stdout(output): exit_code = gates.main(argv, runner)
        self.assertEqual(output.getvalue().strip(), code)
        self.assertEqual(exit_code, 0 if code == "READY" else 5)

    def test_dev_refusals_and_ready(self):
        cases = [
            ("plan-invalid.json", dev_runner({(gates.VALIDATE_PLAN, "--root", "{{ bead_prefix }}-phase-d"): (5, "bad")})),
            ("not-ready.json", dev_runner({("bd", "ready", "-n", "0", "--json"): (0, "[]")})),
            ("unclaimable.json", dev_runner({("bd", "show", "bead", "--json"): (0, dumped([{"status": "open", "assignee": "other", "metadata": {"difficulty": "normal"}}]))})),
            ("wrong-base.json", dev_runner({("git", "merge-base", "--is-ancestor", "origin/target", "HEAD"): (1, "")})),
            ("difficulty-mismatch.json", dev_runner({("bd", "show", "bead", "--json"): (0, dumped([{"status": "open", "assignee": "", "metadata": {"difficulty": "hard"}}]))})),
            ("dev-ready.json", dev_runner()),
        ]
        for fixture, runner in cases:
            with self.subTest(fixture=fixture): self.assert_fixture(fixture, ns("dev"), runner)

    def test_a_poured_dev_bead_takes_its_sprint_containers_pr_target(self):
        poured = {("bd", "show", "bead", "--json"): (0, dumped([{"status": "open", "assignee": "", "labels": ["stage:dev"],
                  "metadata": {"difficulty": "normal", "sprint_bead": "container"}}]))}
        for target, ancestor, expected in (("target", 1, "READY"), ("lower", 0, "READY"), ("other", 1, "PR_TARGET_MISMATCH"), ("other", 128, "GATE_CANNOT_RUN")):
            runner = dev_runner({**poured, ("bd", "show", "container", "--json"): (0, dumped([{"metadata": {"pr_target": target}}])),
                                 ("git", "merge-base", "--is-ancestor", f"origin/{target}", "origin/target"): (ancestor, "")})
            with self.subTest(container_target=target, ancestor=ancestor):
                self.assertEqual(gates.evaluate(ns("dev"), runner), expected)
        fix = {("bd", "show", "bead", "--json"): (0, dumped([{"status": "open", "assignee": "", "labels": ["stage:fix"],
               "metadata": {"difficulty": "normal", "sprint_bead": "container"}}])),
               ("bd", "show", "container", "--json"): (0, dumped([{"metadata": {"pr_target": "other"}}]))}
        self.assertEqual(gates.evaluate(ns("dev"), dev_runner(fix)), "READY")  # a fix layer's target is set at dispatch

    def test_dev_gate_runs_validate_plan_in_primary_and_git_in_worktree(self):
        runner = dev_runner({("git", "-C", "/wt", "merge-base", "--is-ancestor", "origin/target", "HEAD"): (0, "")})
        self.assertEqual(gates.evaluate(ns("dev", worktree="/wt"), runner), "READY")
        self.assertEqual(runner.cwds[0], str(gates.PRIMARY))
        behind = dev_runner({("git", "-C", "/other", "merge-base", "--is-ancestor", "origin/target", "HEAD"): (1, "")})
        self.assertEqual(gates.evaluate(ns("dev", worktree="/other"), behind), "WRONG_BASE")

    def test_sanity_refusals_and_ready(self):
        cases = [
            ("pr-required.json", ns("sanity", pr_number=""), sanity_runner()),
            ("not-stacked.json", ns("sanity"), sanity_runner({("gh", "pr", "view", "7", "--json", "baseRefName,headRefName,headRefOid"): (0, dumped({"baseRefName": "wrong", "headRefName": "branch", "headRefOid": "head"}))})),
            ("not-stacked.json", ns("sanity"), sanity_runner({("gh", "pr", "view", "7", "--json", "baseRefName,headRefName,headRefOid"): (0, dumped({"baseRefName": "target", "headRefName": "branch", "headRefOid": "moved"}))})),
            ("not-stacked.json", ns("sanity"), sanity_runner({(str(gates.PRIMARY), STACK_VIEW): (2, "", "gh-stack-view: no open gh stack found.")})),
            ("not-stacked.json", ns("sanity"), sanity_runner(view({"branch": "target", "pr": 6, "pr_base": "integrate", "merged": False}))),
            ("not-stacked.json", ns("sanity"), sanity_runner(view({"branch": "target", "pr": 6, "pr_base": "integrate", "merged": False},
                                                                   {"branch": "branch", "pr": 7, "pr_base": "integrate", "merged": False}))),
            ("not-stacked.json", ns("sanity", pr_target="planned"), sanity_runner({("git", "merge-base", "--is-ancestor", "origin/planned", "origin/target"): (1, "")})),
            ("sanity-ready.json", ns("sanity", pr_target="planned"), sanity_runner({("git", "merge-base", "--is-ancestor", "origin/planned", "origin/target"): (0, "")})),
            ("not-rebased.json", ns("sanity"), sanity_runner({("git", "merge-base", "--is-ancestor", "origin/target", "head"): (1, "")})),
            ("zero-delta.json", ns("sanity"), sanity_runner({("git", "log", "--format=%H", "origin/target..head"): (0, "")})),
            ("dirty-tree.json", ns("sanity"), sanity_runner({("git", "status", "--porcelain", "--untracked-files=no"): (0, " M tracked.py")})),
            ("sanity-frozen.json", ns("sanity"), sanity_runner({("bd", "history", "bead", "--json"): (0, dumped({"verdict": "PASS"}))})),
            ("sanity-ready.json", ns("sanity"), sanity_runner()),
        ]
        for fixture, gate_args, runner in cases:
            with self.subTest(fixture=fixture): self.assert_fixture(fixture, gate_args, runner)

    def test_sanity_rebase_check_that_cannot_run_is_not_a_refusal(self):
        runner = sanity_runner({("git", "merge-base", "--is-ancestor", "origin/target", "head"): (128, "")})
        self.assertEqual(gates.evaluate(ns("sanity"), runner), "GATE_CANNOT_RUN")

    def test_sanity_stack_checks_that_cannot_run_are_not_refusals(self):
        for override in ({(str(gates.PRIMARY), STACK_VIEW): (2, "", "gh-stack-view: gh repo view failed")},
                         {(str(gates.PRIMARY), STACK_VIEW): (0, "not json")},
                         {("git", "merge-base", "--is-ancestor", "origin/planned", "origin/target"): (128, "")}):
            with self.subTest(override=override):
                self.assertEqual(gates.evaluate(ns("sanity", pr_target="planned"), sanity_runner(override)), "GATE_CANNOT_RUN")

    def test_the_first_open_layer_is_based_on_the_trunk(self):
        runner = sanity_runner({**view({"branch": "merged", "pr": 5, "pr_base": "integrate", "merged": True},
                                       {"branch": "target", "pr": 7, "pr_base": "integrate", "merged": False}),("gh", "pr", "view", "7", "--json", "baseRefName,headRefName,headRefOid"): (0, dumped({"baseRefName": "integrate", "headRefName": "target", "headRefOid": "head"})),
                                ("git", "merge-base", "--is-ancestor", "origin/target", "origin/integrate"): (1, ""),
                                ("git", "log", "--format=%H", "origin/integrate..head"): (0, "delta")})
        self.assertEqual(gates.evaluate(ns("sanity", pr_target="integrate"), runner), "READY")
        self.assertEqual(gates.evaluate(ns("sanity"), runner), "NOT_STACKED")  # the trunk does not descend from a planned layer above it

    def test_sanity_reads_the_stack_from_the_cross_worktree_view_not_the_checked_worktrees_tracking(self):
        # The dev's worktree has no gh-stack tracking (the dev never runs gh stack), so `gh stack view` exits 2 there.
        runner = sanity_runner({("/wt", ("gh", "stack", "view", "--json")): (2, "")})
        self.assertEqual(gates.evaluate(ns("sanity", worktree="/wt"), runner), "READY")
        self.assertIn((str(gates.PRIMARY), STACK_VIEW), runner.calls)
        self.assertFalse([call for call in runner.calls if call[1][:3] == ("gh", "stack", "view")])

    def test_stack_view_script_is_located_as_sc_gh_stack_does(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, plugin, home = (Path(tmp) / name for name in ("repo", "plugin", "home"))
            older, newer = home / ".claude/a/gh_stack_view.py", home / ".claude/b/gh_stack_view.py"
            for path in (older, newer):
                path.parent.mkdir(parents=True); path.write_text("")
            os.utime(older, (1, 1))
            with mock.patch.object(gates, "PRIMARY", root):
                self.assertEqual(LOCATE({}, home), str(newer))
                (plugin / "scripts").mkdir(parents=True); (plugin / "scripts/gh_stack_view.py").write_text("")
                self.assertEqual(LOCATE({"CLAUDE_PLUGIN_ROOT": str(plugin)}, home), str(plugin / "scripts/gh_stack_view.py"))
                (root / ".claude/scripts").mkdir(parents=True); (root / ".claude/scripts/gh_stack_view.py").write_text("")
                self.assertEqual(LOCATE({"CLAUDE_PLUGIN_ROOT": str(plugin)}, home), str(root / ".claude/scripts/gh_stack_view.py"))
                (root / ".claude/scripts/gh_stack_view.py").unlink()
                with self.assertRaises(RuntimeError):
                    LOCATE({}, Path(tmp) / "nobody")
        with mock.patch.object(gates, "stack_view_script", side_effect=RuntimeError("gh_stack_view.py not found")):
            self.assertEqual(gates.evaluate(ns("sanity"), sanity_runner()), "GATE_CANNOT_RUN")

    def test_a_lower_bound_whose_branch_is_gone_holds_only_when_its_pr_merged(self):
        gone = {("git", "merge-base", "--is-ancestor", "origin/planned", "origin/target"): (128, ""),
                ("git", "rev-parse", "--verify", "--quiet", "refs/remotes/origin/planned"): (1, "")}
        merged = ("gh", "pr", "list", "--head", "planned", "--state", "merged", "--json", "number")
        self.assertEqual(gates.evaluate(ns("sanity", pr_target="planned"), sanity_runner({**gone, merged: (0, dumped([{"number": 3}]))})), "READY")
        self.assertEqual(gates.evaluate(ns("sanity", pr_target="planned"), sanity_runner({**gone, merged: (0, "[]")})), "GATE_CANNOT_RUN")

    def test_qa_refusals_and_ready(self):
        cases = [
            ("stale-sanity.json", qa_runner({("gh", "pr", "view", "7", "--json", "baseRefName,headRefOid"): (0, dumped({"baseRefName": "target", "headRefOid": "0ld0ld0aaa"}))})),
            ("stale-sanity.json", qa_runner({("bd", "list", "-l", "stage:dev-sanity", "--status", "closed", "-n", "0", "--json"): (0, dumped([
                {"id": "checked-sanity", "close_reason": "FAIL at abc1234", "closed_at": "2026-10-02T00:00:00Z", "metadata": {"dev_bead": "checked"}}]))})),
            ("qa-head-mismatch.json", qa_runner({("git", "rev-parse", "HEAD"): (0, "other")})),
            ("pr-target-mismatch.json", qa_runner({("git", "merge-base", "--is-ancestor", "origin/target", "origin/top"): (1, ""),
                                                   ("gh", "pr", "view", "7", "--json", "baseRefName,headRefOid"): (0, dumped({"baseRefName": "top", "headRefOid": "abc1234def"}))})),
            ("qa-ready.json", qa_runner({("git", "merge-base", "--is-ancestor", "origin/target", "origin/top"): (0, ""),
                                         ("gh", "pr", "view", "7", "--json", "baseRefName,headRefOid"): (0, dumped({"baseRefName": "top", "headRefOid": "abc1234def"}))})),
            ("qa-ready.json", qa_runner()),
        ]
        for fixture, runner in cases:
            with self.subTest(fixture=fixture): self.assert_fixture(fixture, ns("qa"), runner)


    def test_qa_base_check_that_cannot_run_is_not_a_refusal(self):
        runner = qa_runner({("git", "merge-base", "--is-ancestor", "origin/target", "origin/top"): (128, ""),
                            ("gh", "pr", "view", "7", "--json", "baseRefName,headRefOid"): (0, dumped({"baseRefName": "top", "headRefOid": "abc1234def"}))})
        self.assertEqual(gates.evaluate(ns("qa"), runner), "GATE_CANNOT_RUN")


if __name__ == "__main__": unittest.main()
