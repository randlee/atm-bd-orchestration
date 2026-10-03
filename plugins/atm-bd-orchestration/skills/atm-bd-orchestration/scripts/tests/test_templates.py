from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).parents[2]


class TemplateContractTests(unittest.TestCase):
    def test_dev_template_requires_pr_target_not_obsolete_top(self):
        text = (ROOT / "templates/dev-template.xml.j2").read_text()
        self.assertIn("- pr_target", text)
        self.assertNotIn("- top", text)
        self.assertNotIn("pushed" + " top", text)

    def test_finding_requires_difficulty_and_priority_map_is_current(self):
        text = (ROOT / "templates/finding-bead.json.j2").read_text()
        self.assertIn("- difficulty", text)
        import json, sys
        sys.path.insert(0, str(ROOT.parents[1] / "atm-beads" / "scripts"))
        from plan_contract import SEVERITY_PRIORITY
        self.assertIn(json.dumps(SEVERITY_PRIORITY).replace(", ", ", "), text)  # the literal mirrors plan_contract; Jinja cannot import it
        self.assertIn('"difficulty"', text)
        self.assertIn("## Deliverables\\n1.", text)

    def test_sanity_assignment_has_pr_and_exact_checks(self):
        text = (ROOT / "templates/dev-sanity-template.xml.j2").read_text()
        self.assertIn("- pr_number", text)
        self.assertIn("- pr_url", text)
        self.assertIn("gh pr view", text)
        self.assertIn("SANITY.ZERO_DELTA", text)

    def test_workflow_issue_template_exists(self):
        self.assertTrue((ROOT / "templates/workflow-issue-bead.json.j2").exists())

    def test_gate_commands_render_root_and_primary_checkout(self):
        for name in ("dev-template", "fix-assignment", "dev-fix", "dev-sanity-template"):
            text = (ROOT / f"templates/{name}.xml.j2").read_text()
            with self.subTest(template=name):
                self.assertNotIn("<phase>", text)
                self.assertNotIn("git worktree list", text)
                self.assertIn("{{ primary_checkout | string | cdata_escape }}/.claude/skills/", text)
                if name != "dev-sanity-template":
                    self.assertIn("--root {{ phase_root | string | cdata_escape }}", text)

    def test_sanity_template_has_no_stale_base_check(self):
        text = (ROOT / "templates/dev-sanity-template.xml.j2").read_text()
        self.assertNotIn("STALE_BASE", text)  # sanity-split pins origin/<base> itself (three-dot diff)
        self.assertIn("git fetch origin && git log --format=%H origin/", text)  # but the tracking ref must be fresh

    def test_finding_bead_deliverables_are_splittable(self):
        import importlib.machinery, importlib.util, json, subprocess
        loader = importlib.machinery.SourceFileLoader("sanity_split", str(ROOT / "scripts/sanity-split"))
        split = importlib.util.module_from_spec(importlib.util.spec_from_loader("sanity_split", loader))
        loader.exec_module(split)
        result = subprocess.run(["sc-compose", "render", "--file", str(ROOT / "templates/finding-bead.json.j2"),
                                 "--var-file", str(ROOT / "examples/finding-bead-vars.json"), "--strict"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        items = split.parse_deliverables(json.loads(result.stdout)["description"])
        self.assertEqual(len(items), 1)

    def test_dev_step_a_rebases_before_the_gate(self):
        for name in ("dev-template", "fix-assignment", "dev-fix"):
            text = (ROOT / f"templates/{name}.xml.j2").read_text()
            with self.subTest(template=name):
                self.assertIn("`git fetch origin && git rebase origin/{{ pr_target | string | cdata_escape }}` in the worktree", text)
                self.assertLess(text.index("git rebase origin/"), text.index("assignment-gates.py dev"))

    def test_integration_completion_requires_audit_evidence(self):
        import json
        import tempfile

        template = ROOT / "templates/review-complete.md.j2"
        original = json.loads((ROOT / "examples/review-complete-vars.json").read_text())
        passed = {**original, "findings_important": 0, "verdict": "PASS", "integration_review": "integration_review_passed",
                  "post_mortem_counts": {"total": 0, "verified_fixed": 0, "justified_nonfix": 0, "unresolved": 0},
                  "post_mortem_md": "Empty inventory verified; no_systemic_followup"}
        cases = [
            (passed, True),
            ({**passed, "findings_blocking": 1}, False),
            ({**passed, "findings_important": 1}, False),
            ({**passed, "findings_minor": -1}, False),
            (original, True),
            ({**original, "integration_review": "PASS"}, False),
            ({**original, "post_mortem_md": "  "}, False),
            ({k: v for k, v in original.items() if k != "integration_review"}, False),
            ({k: v for k, v in original.items() if k != "post_mortem_md"}, False),
            ({**passed, "post_mortem_counts": original["post_mortem_counts"]}, False),
            ({**passed, "integration_commit": "f" * 40}, False),
            ({**passed, "integration_commit": "short"}, False),
            ({**passed, "verdict": "FAIL"}, False),
            ({**passed, "post_mortem_counts": {"total": 2, "verified_fixed": 1, "justified_nonfix": 0, "unresolved": 0}}, False),
            ({**passed, "post_mortem_counts": {"total": 0, "verified_fixed": 1, "justified_nonfix": -1, "unresolved": 0}}, False),
        ]
        with tempfile.TemporaryDirectory() as directory:
            variables = Path(directory) / "vars.json"
            for values, valid in cases:
                with self.subTest(values=values, valid=valid):
                    variables.write_text(json.dumps(values))
                    import sys
                    checked = subprocess.run([
                        sys.executable, str(ROOT / "scripts/check-review-completion.py"),
                        str(variables)], capture_output=True, text=True)
                    self.assertEqual(checked.returncode == 0, valid, checked.stderr)
                    if not valid:
                        self.assertIn("review completion:", checked.stderr)
                        continue
                    result = subprocess.run([
                        "sc-compose", "render", "--file", str(template),
                        "--var-file", str(variables), "--strict"], capture_output=True, text=True)
                    self.assertEqual(result.returncode == 0, valid, result.stderr)
                    if valid:
                        machine = json.loads(result.stdout.split("```json\n", 1)[1].split("```", 1)[0])
                        self.assertEqual(machine["integration_review"], values["integration_review"])

    def test_review_completion_requires_jev_execution_receipt(self):
        import json
        import tempfile
        values = json.loads((ROOT / "examples/review-complete-vars.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vars.json"
            for include in (True, False):
                candidate = dict(values)
                if not include:
                    del candidate["post_mortem_jev"]
                path.write_text(json.dumps(candidate))
                result = subprocess.run([
                    "sc-compose", "render", "--file", str(ROOT / "templates/review-complete.md.j2"),
                    "--var-file", str(path), "--strict"], capture_output=True, text=True)
                self.assertEqual(result.returncode == 0, include, result.stderr)
                if include:
                    machine = json.loads(result.stdout.split("```json\n", 1)[1].split("```", 1)[0])
                    self.assertEqual(machine["post_mortem_jev"], candidate["post_mortem_jev"])

    def test_assignment_examples_render_strictly(self):
        examples = ROOT / "examples"
        templates = sorted((ROOT / "templates").glob("*.j2"))
        self.assertTrue(templates, "templates directory must not be empty")
        for template_path in templates:
            fixture_name = template_path.name.removesuffix(".j2").rsplit(".", 1)[0] + "-vars.json"
            variables = examples / fixture_name
            with self.subTest(template=template_path.name):
                self.assertTrue(variables.is_file(), f"missing strict-render fixture: {fixture_name}")
                result = subprocess.run([
                    "sc-compose", "render", "--file", str(template_path),
                    "--var-file", str(variables), "--strict"], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)


def _render(template: str, values: dict) -> subprocess.CompletedProcess:
    import json
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        variables = Path(directory) / "vars.json"
        variables.write_text(json.dumps(values))
        return subprocess.run(["sc-compose", "render", "--file", str(ROOT / "templates" / template),
                               "--var-file", str(variables), "--strict"], capture_output=True, text=True)


def _example(name: str) -> dict:
    import json
    return json.loads((ROOT / "examples" / name).read_text())


class FixRoundReviewerScopeTests(unittest.TestCase):
    """A fix round runs req-qa, arch-qa and rust-qa-agent; the adversarial reviewers only re-check their own ids."""

    RBQA = "ruthless-boundary-qa-assignment.json.j2"
    QA = "qa-template.xml.j2"

    def rbqa(self, **values) -> subprocess.CompletedProcess:
        base = {k: v for k, v in _example("ruthless-boundary-qa-assignment-vars.json").items()
                if k not in ("qa_round", "carry_forward_findings_json")}
        return _render(self.RBQA, {**base, **values})

    def test_round_one_is_unlocked(self):
        import json
        result = self.rbqa(qa_round=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIs(json.loads(result.stdout)["findings_scope_locked"], False)
        qa = _render(self.QA, _example("qa-template-vars.json"))
        self.assertEqual(qa.returncode, 0, qa.stderr)
        self.assertIn("This is round 1: run the full reviewer set", qa.stdout)
        self.assertIn("`qa_round` = 1", qa.stdout)
        self.assertNotIn("fix-round-scope", qa.stdout)

    def test_fix_round_with_ids_is_locked(self):
        import json
        result = self.rbqa(qa_round=2, carry_forward_findings_json='["RBQA-004"]')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIs(data["findings_scope_locked"], True)
        self.assertEqual(data["carry_forward_findings"], ["RBQA-004"])
        qa = _render(self.QA, _example("qa-template-fix-round-vars.json"))
        self.assertEqual(qa.returncode, 0, qa.stderr)
        self.assertIn("Reviewers, exactly: `req-qa`, `arch-qa` and `rust-qa-agent`", qa.stdout)
        self.assertIn("scripts/fix-round-scope owned --carried", qa.stdout)
        self.assertIn("`qa_round` = 2", qa.stdout)
        self.assertNotIn("full reviewer set", qa.stdout)
        self.assertLess(qa.stdout.index("scripts/fix-round-scope check --findings"), qa.stdout.index("&& bd import"))

    def test_fix_round_with_empty_scope_fails(self):
        for scope in (None, "[]", "[ ]", "", "  ", "null"):
            with self.subTest(scope=scope):
                values = {"qa_round": 2} if scope is None else {"qa_round": 2, "carry_forward_findings_json": scope}
                self.assertNotEqual(self.rbqa(**values).returncode, 0)
        values = {k: v for k, v in _example("qa-template-fix-round-vars.json").items() if k != "carry_forward"}
        self.assertNotEqual(_render(self.QA, values).returncode, 0)

    def test_missing_round_fails(self):
        result = self.rbqa(carry_forward_findings_json='["RBQA-004"]')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("qa_round", result.stderr)
        values = {k: v for k, v in _example("qa-template-vars.json").items() if k != "round"}
        self.assertNotEqual(_render(self.QA, values).returncode, 0)

    def test_fix_branch_at_round_one_is_a_fix_round(self):
        qa = _render(self.QA, {**_example("qa-template-vars.json"), "branch": "fix/d-4-qa1-f1-retry-jitter"})
        self.assertEqual(qa.returncode, 0, qa.stderr)
        self.assertIn("Reviewers, exactly: `req-qa`, `arch-qa` and `rust-qa-agent`", qa.stdout)
        self.assertIn("No finding is carried", qa.stdout)
        self.assertIn("scripts/fix-round-scope check --findings", qa.stdout)
        self.assertNotIn("full reviewer set", qa.stdout)


if __name__ == "__main__":
    unittest.main()
