"""The simplify child, the sanity-less fix group of a non-blocking finding, and the screen verdicts a finding carries."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT.parent / "atm-beads" / "scripts"))
from rendering import render  # noqa: E402


def groups_module():
    loader = importlib.machinery.SourceFileLoader("bead_groups_simplify", str(SCRIPTS / "bead-groups"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def runner(groups, phase_config):
    run = object.__new__(groups.Run)
    run.option = None
    run.repo = ROOT
    run.config = {"worktree_base": "/worktrees", "lint_command": "just lint", "policy_path": "policy.md", "max_sanity_rounds": 5}
    run.bd = Mock()
    run.bd.show.return_value = None
    run.sidecars = {}
    stack = {"id": "t-phase-d.stack", "metadata": {"trunk": "integrate/phase-d", "stack_number": None, "layers": []}}
    container = {"status": "open", "title": "d-1: the work", "metadata": {"phase": "d", "sprint": "d-1", "stack": "stack", "difficulty": "normal",
                                                                         "layer": 4, "requirements": ["REQ-1"], "adrs": ["NONE"]}}
    run.show = lambda bead: stack if bead == "t-phase-d.stack" else container
    run.features = {"d": {"stack_bead": "t-phase-d.stack", "phase_feature": "phase d"}}
    return run, phase_config


def bake(formula: str, compose: dict) -> list[dict]:
    """The steps of `formula` rendered by `sc-compose bead render` with `compose`."""
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        shutil.copyfile(ROOT / "formulas" / f"{formula}.formula.toml.j2", root / "formula.toml.j2")
        request = {"schema": "sc-compose/beads/v1", "operation": "render", "working_directory": directory,
                   "template": "formula.toml.j2", "rendered_formula": "rendered.formula.toml",
                   "bead_variables": {}, "compose_variables": compose}
        (root / "request.json").write_text(json.dumps(request))
        output = subprocess.run(["sc-compose", "bead", "render", "--request", "request.json", "--json"],
                                cwd=root, capture_output=True, text=True, timeout=30)
        assert output.returncode == 0, output.stdout + output.stderr
        return tomllib.loads((root / "rendered.formula.toml").read_text())["steps"]


@unittest.skipUnless(shutil.which("sc-compose"), "sc-compose is required to render bead formulas")
class FindingFixTests(unittest.TestCase):
    def targets(self, severity: str, phase_config: dict | None = None):
        groups = groups_module()
        run, config = runner(groups, phase_config or {"root": "t-phase-d"})
        row = {"ref": "qa1-f1", "severity": severity, "reviewer": "req-qa", "title": "issue", "remedy": "fix"}
        with tempfile.TemporaryDirectory() as directory:
            findings = Path(directory) / "findings.json"
            findings.write_text(json.dumps({"sprint": "d-1", "round": 1, "filed_by": "qa", "found_at_commit": "a" * 40, "findings": [row]}))
            with patch.object(groups.sprint_index_common, "load_phase_config", return_value=config):
                target = run.finding_targets(findings)[0]
                child = run.simplify_target(target, "d-1.qa1-f1-r1-fix") if not isinstance(target, Exception) else None
        return groups, run, target, child

    def poured(self, severity: str, phase_config: dict | None = None):
        groups, run, target, child = self.targets(severity, phase_config)
        assert not isinstance(target, Exception) and child is not None, target
        return groups, run, target, child

    def test_an_important_finding_pours_fix_and_qa_with_no_sanity_step(self):
        _, run, target, _ = self.poured("important")
        self.assertEqual(target["formula"], "finding-fix")
        self.assertEqual(run.steps(target), ["fix", "qa"])
        steps = bake("finding-fix", target["compose"])
        self.assertEqual([s["id"] for s in steps], ["fix", "qa"])
        fix, qa = steps
        self.assertEqual(qa["needs"], ["fix"])
        self.assertEqual(fix["metadata"]["severity"], "important")
        self.assertEqual(qa["metadata"]["reviewers_round1"], ["req-qa"])
        for step in steps:
            self.assertEqual(step["metadata"]["sanity_bead"], "")
            self.assertIs(step["metadata"]["quick_fix"], True)

    def test_a_blocking_finding_still_pours_the_sanity_group(self):
        _, run, target, _ = self.poured("blocking")
        self.assertEqual(target["formula"], "finding-group")
        self.assertEqual(run.steps(target), ["fix", "sanity", "qa"])

    def test_an_unknown_severity_is_refused(self):
        _, _, target, _ = self.targets("nit")
        self.assertEqual(getattr(target, "code"), "BEAD_GROUPS_FINDINGS_INVALID")

    def test_the_simplify_child_is_a_child_of_the_fix_and_uses_the_default_simplifier(self):
        _, _, target, child = self.poured("important")
        self.assertEqual(child["id"], "d-1.qa1-f1-r1-fix.group-simplify")
        self.assertEqual(child["compose"]["parent"], "d-1.qa1-f1-r1-fix")
        self.assertEqual(child["compose"]["simplifier"], "simplify-reviewer")
        (step,) = bake("simplify", child["compose"])
        self.assertEqual(step["labels"][-1], "stage:simplify")
        self.assertEqual(step["metadata"]["checked_bead"], "d-1.qa1-f1-r1-fix")
        self.assertEqual(step["metadata"]["max_passes"], 2)
        self.assertNotIn("needs", step)

    def test_the_phase_file_names_another_simplifier(self):
        _, _, _, child = self.poured("blocking", {"root": "t-phase-d", "simplifier": "house-simplifier"})
        self.assertEqual(child["compose"]["simplifier"], "house-simplifier")


class SchemaTests(unittest.TestCase):
    def test_a_simplify_bead_and_a_non_blocking_fix_bead_validate(self):
        import bead_schema
        family = {"branch": "fix/d-1-qa1-f1", "worktree": "/w", "pr_target": "integrate/phase-d", "difficulty": "normal"}
        simplify = {"id": "d-1.qa1-f1-r1-fix.group-simplify", "status": "open", "labels": ["phase-d", "stage:simplify"],
                    "metadata": {**family, "role": "simplify", "checked_bead": "d-1.qa1-f1-r1-fix", "simplifier": "simplify-reviewer", "max_passes": 2}}
        self.assertEqual(bead_schema.validate_phase([simplify]), [])
        too_many = {**simplify, "metadata": {**simplify["metadata"], "max_passes": 3}}
        self.assertTrue(bead_schema.validate_phase([too_many]))
        self.assertEqual(bead_schema.problems({"id": "x", "metadata": {"finding_ref": "f", "severity": "important", "reviewer": "req-qa",
                                                                       "found_at_commit": "a", **family}, "status": "closed"},
                                              bead_schema.FixBead), [])

    def test_the_phase_file_simplifier_must_be_an_agent_name(self):
        import sprint_index_common
        templates = {k: f".claude/skills/atm-bd-orchestration/templates/{k}.xml.j2" for k in sprint_index_common.DEFAULT_TEMPLATES}
        data = {"plan": "p.jsonl", "root": "t-phase-d", "integration_branch": "integrate/phase-d", "lead": "lead",
                "templates": templates, "simplifier": "Not A Name"}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "simplifier: optional agent name"):
                sprint_index_common.validate_phase_config(Path(directory), "d", data)


class FindingBeadScreenTests(unittest.TestCase):
    def vars(self, **change):
        values = json.loads((ROOT / "examples/finding-bead-vars.json").read_text())
        values = {k: (v.replace("{{ bead_prefix }}", "p") if isinstance(v, str) else v) for k, v in values.items()}
        return {**values, **change}

    def test_both_screens_verdicts_and_reasons_are_carried(self):
        result = render(ROOT / "templates/finding-bead.json.j2", self.vars())
        self.assertEqual(result.returncode, 0, result.stderr)
        metadata = json.loads(result.stdout)["metadata"]
        self.assertEqual(metadata["simplify_screen"], "keep")
        self.assertTrue(metadata["screen_reason"] and metadata["simplify_reason"])

    def test_a_finding_without_the_simplify_screen_does_not_render(self):
        for change in ({"simplify_screen": "maybe"}, {"simplify_reason": ""}, {"screen_reason": ""}):
            result = render(ROOT / "templates/finding-bead.json.j2", self.vars(**change))
            self.assertEqual(result.returncode, 1, change)
            self.assertIn("ERR_RENDER_JSON_MALFORMED", result.stderr, change)


if __name__ == "__main__":
    unittest.main()
