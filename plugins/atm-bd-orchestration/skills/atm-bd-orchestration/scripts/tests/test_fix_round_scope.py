from __future__ import annotations

import importlib.machinery
import importlib.util
from pathlib import Path
import unittest

LOADER = importlib.machinery.SourceFileLoader("fix_round_scope", str(Path(__file__).parents[1] / "fix-round-scope"))
scope = importlib.util.module_from_spec(importlib.util.spec_from_loader("fix_round_scope", LOADER))
LOADER.exec_module(scope)

CARRIED = [
    {"id": "x-d-4-qa1-f1", "metadata": {"reviewer": "ruthless-boundary-qa", "finding_ref": "RBQA-F001"}},
    {"id": "x-d-4-qa1-f2", "metadata": {"reviewer": "arch-qa", "finding_ref": "ARCH-F002"}},
]


class FixRoundScopeTests(unittest.TestCase):
    def test_only_owning_adversarial_reviewers_are_dispatched(self):
        self.assertEqual(scope.owned(CARRIED), {"ruthless-boundary-qa": ["RBQA-F001"]})
        self.assertEqual(scope.owned([CARRIED[1]]), {})  # no RBP/RBQA/RSH carried -> none of them runs

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
        self.assertEqual(scope.check(rows), ["q-f2"])
        self.assertEqual(scope.check(rows[:1]), [])


if __name__ == "__main__":
    unittest.main()
