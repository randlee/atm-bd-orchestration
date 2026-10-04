from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest

MODULE = Path(__file__).parents[1] / "assignment-gates.py"
FIXTURES = Path(__file__).parent / "fixtures"
SPEC = importlib.util.spec_from_file_location("assignment_gates", MODULE)
assert SPEC and SPEC.loader
gates = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gates)


class FakeRunner:
    def __init__(self, responses): self.responses = responses
    cwds: list = []
    def __call__(self, args, **kwargs):
        self.cwds.append(kwargs.get("cwd"))
        code, stdout = self.responses.get(tuple(args), (0, ""))
        return subprocess.CompletedProcess(args, code, stdout, "")


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
        ("gh", "pr", "view", "7", "--json", "baseRefName,headRefOid"): (0, dumped({"baseRefName": "target", "headRefOid": "head"})),
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


class AssignmentGateTests(unittest.TestCase):
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
        for target, expected in (("target", "READY"), ("other", "PR_TARGET_MISMATCH")):
            runner = dev_runner({**poured, ("bd", "show", "container", "--json"): (0, dumped([{"metadata": {"pr_target": target}}]))})
            with self.subTest(container_target=target):
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
            ("stale-base.json", ns("sanity"), sanity_runner({("gh", "pr", "view", "7", "--json", "baseRefName,headRefOid"): (0, dumped({"baseRefName": "wrong", "headRefOid": "head"}))})),
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

    def test_qa_refusals_and_ready(self):
        cases = [
            ("stale-sanity.json", qa_runner({("gh", "pr", "view", "7", "--json", "baseRefName,headRefOid"): (0, dumped({"baseRefName": "target", "headRefOid": "0ld0ld0aaa"}))})),
            ("stale-sanity.json", qa_runner({("bd", "list", "-l", "stage:dev-sanity", "--status", "closed", "-n", "0", "--json"): (0, dumped([
                {"id": "checked-sanity", "close_reason": "FAIL at abc1234", "closed_at": "2026-10-02T00:00:00Z", "metadata": {"dev_bead": "checked"}}]))})),
            ("qa-head-mismatch.json", qa_runner({("git", "rev-parse", "HEAD"): (0, "other")})),
            ("qa-ready.json", qa_runner()),
        ]
        for fixture, runner in cases:
            with self.subTest(fixture=fixture): self.assert_fixture(fixture, ns("qa"), runner)


if __name__ == "__main__": unittest.main()
