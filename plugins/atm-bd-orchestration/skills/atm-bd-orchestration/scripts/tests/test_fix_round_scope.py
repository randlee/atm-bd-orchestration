from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).parents[1] / "fix-round-scope"
LOADER = importlib.machinery.SourceFileLoader("fix_round_scope", str(Path(__file__).parents[1] / "fix-round-scope"))
scope = importlib.util.module_from_spec(importlib.util.spec_from_loader("fix_round_scope", LOADER))
LOADER.exec_module(scope)

# The scope-locked set comes from the repository configuration; the tests pass it explicitly.
LOCKED = ("ruthless-boundary-qa", "rust-best-practices-agent", "rust-service-hardening-agent")
CARRIED = [
    {"id": "x-d-4-qa1-f1", "metadata": {"reviewer": "ruthless-boundary-qa", "finding_ref": "RBQA-F001"}},
    {"id": "x-d-4-qa1-f2", "metadata": {"reviewer": "arch-qa", "finding_ref": "ARCH-F002"}},
]


class FixRoundScopeTests(unittest.TestCase):
    def test_only_owning_adversarial_reviewers_are_dispatched(self):
        self.assertEqual(scope.owned(CARRIED, LOCKED), {"ruthless-boundary-qa": ["RBQA-F001"]})
        self.assertEqual(scope.owned([CARRIED[1]], LOCKED), {})  # no RBP/RBQA/RSH carried -> none of them runs

    def test_out_of_scope_findings_never_survive(self):
        result = {"data": {"findings": [
            {"id": "RBQA-F001", "evidence": "still leaks"},
            {"id": "RBQA-F002", "evidence": "brand new"},
            {"id": "RBQA-F001", "evidence": "id collision, second copy"}]}}
        out = scope.filter_result("ruthless-boundary-qa", CARRIED, result)
        self.assertEqual(out["new_findings"], [])
        self.assertEqual([d["bead"] for d in out["dispositions"]], ["x-d-4-qa1-f1"])
        self.assertEqual(out["dispositions"][0]["disposition"], "open")
        self.assertEqual(len(out["dropped_out_of_scope"]), 2)

    def test_unreported_carried_finding_is_fixed(self):
        out = scope.filter_result("ruthless-boundary-qa", CARRIED, {"data": {"findings": []}})
        self.assertEqual(out["dispositions"][0]["disposition"], "fixed")

    def test_another_reviewers_ids_are_not_in_scope(self):
        out = scope.filter_result("rust-best-practices-agent", CARRIED, {"data": {"findings": [{"id": "RBQA-F001"}]}})
        self.assertEqual(out["dispositions"], [])
        self.assertEqual(len(out["dropped_out_of_scope"]), 1)


    def test_check_rejects_an_adversarial_finding_in_a_fix_round_import(self):
        rows = [{"id": "q-f1", "metadata": {"reviewer": "rust-qa-agent"}},
                {"id": "q-f2", "metadata": {"reviewer": "rust-service-hardening-agent"}}]
        self.assertEqual(scope.check(rows, LOCKED), ["q-f2"])
        self.assertEqual(scope.check(rows[:1], LOCKED), [])


class ConfiguredScopeTests(unittest.TestCase):
    """The CLI takes the scope-locked set from `reviewers_scope_locked`, and refuses to run without it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        (self.repo / "carried.json").write_text(json.dumps(CARRIED))

    def tearDown(self):
        self.tmp.cleanup()

    def configure(self, text: str) -> None:
        path = self.repo / ".claude/project/atm-bd-orchestration.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.repo, capture_output=True, text=True)

    def test_configured_set_decides_who_is_scope_locked(self):
        self.configure("reviewers_scope_locked: [arch-qa]\n")
        out = self.run_cli("owned", "--carried", "carried.json")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout), {"arch-qa": ["ARCH-F002"]})
        (self.repo / "f.jsonl").write_text(json.dumps({"id": "q-f1", "metadata": {"reviewer": "arch-qa"}}) + "\n"
                                           + json.dumps({"id": "q-f2", "metadata": {"reviewer": "ruthless-boundary-qa"}}) + "\n")
        check = self.run_cli("check", "--findings", "f.jsonl")
        self.assertEqual(check.returncode, 5)
        self.assertIn("q-f1", check.stderr)
        self.assertNotIn("q-f2", check.stderr)

    def test_missing_key_is_a_named_error_not_an_empty_set(self):
        self.configure("lead: someone\n")
        out = self.run_cli("check", "--findings", "")
        self.assertEqual(out.returncode, 2)
        self.assertIn("reviewers_scope_locked", out.stderr)

    def test_missing_config_file_is_an_error(self):
        out = self.run_cli("owned", "--carried", "carried.json")
        self.assertEqual(out.returncode, 2)
        self.assertIn("atm-bd-orchestration.yaml", out.stderr)


if __name__ == "__main__":
    unittest.main()
