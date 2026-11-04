"""Check shipped workflow contracts without creating real tasks or beads."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1]
PACKAGE = SKILL.parents[1]


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=30, check=False)


@pytest.fixture(params=["teammate", "subagent"])
def rendered(request: pytest.FixtureRequest, tmp_path: Path) -> tuple[str, str]:
    runner = request.param
    template = tmp_path / "step.xml.j2"
    template.write_bytes((SKILL / "templates/plan-hardening-step.xml.j2").read_bytes())
    variables = tmp_path / "vars.json"
    variables.write_bytes((SKILL / f"examples/plan-hardening-step-{runner}-vars.json").read_bytes())
    result = run("sc-compose", "render", "--strict", "--file", str(template), "--var-file", str(variables), "--output", "step.xml", cwd=tmp_path)
    assert result.returncode == 0, result.stderr + result.stdout
    return runner, (tmp_path / "step.xml").read_text()


@pytest.fixture(scope="module")
def formulas(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict]:
    directory = tmp_path_factory.mktemp("formulas")
    values = {"root": "atm-phase-d", "phase": "d", "iteration": "1", "iterations": "2", "planner": "fenix", "area": "lead", "task": "Check boundary ownership."}
    outputs = {}
    for name in ("iteration", "final", "adversary"):
        source = SKILL / f"formulas/plan-hardening-{name}.formula.toml.j2"
        (directory / "input.j2").write_bytes(source.read_bytes())
        required = {key: values[key] for key in values if "{{{ " + key + " }}}" in source.read_text()}
        request = {"schema": "sc-compose/beads/v1", "operation": "render", "working_directory": str(directory), "template": "input.j2", "rendered_formula": "output.formula.toml", "bead_variables": {}, "compose_variables": required}
        (directory / "request.json").write_text(json.dumps(request))
        result = run("sc-compose", "bead", "render", "--request", str(directory / "request.json"), "--json", cwd=directory)
        assert result.returncode == 0, result.stderr + result.stdout
        outputs[name] = tomllib.loads((directory / "output.formula.toml").read_text())
    return outputs


def test_step_template_renders_both_runners(rendered):
    runner, text = rendered
    assert f'runner="{runner}"' in text
    assert '<plan-hardening-step id="atm-wisp-2ha"' in text


def test_step_template_refuses_other_runner(tmp_path):
    source = tmp_path / "step.j2"
    source.write_bytes((SKILL / "templates/plan-hardening-step.xml.j2").read_bytes())
    variables = json.loads((SKILL / "examples/plan-hardening-step-subagent-vars.json").read_text())
    variables["runner"] = "invalid"
    (tmp_path / "vars.json").write_text(json.dumps(variables))
    result = run("sc-compose", "render", "--strict", "--file", str(source), "--var-file", str(tmp_path / "vars.json"), "--output", "output.xml", cwd=tmp_path)
    assert result.returncode != 0
    assert not (tmp_path / "output.xml").exists()


def test_step_template_start_and_close_by_runner(rendered):
    runner, text = rendered
    assert "bd update atm-wisp-2ha --claim --actor" in text
    assert "bd close atm-wisp-2ha --actor" in text
    if runner == "teammate":
        assert "atm task start atm-wisp-2ha" in text
        assert "atm task close atm-wisp-2ha completed" in text
    else:
        assert not re.search(r"\batm ", text)


def test_step_template_reads_bead_description(rendered):
    _, text = rendered
    assert "bd show atm-wisp-2ha --json | jq -er '.[0].description'" in text
    assert "bd show atm-phase-d --json" in text
    assert "bd list --parent atm-phase-d -l stage:sprint" in text


def test_finding_block_files_planner_fix_beads(rendered):
    _, text = rendered
    assert "--parent 'atm-phase-d' --type task --assignee 'fenix'" in text
    assert "phase-d,stage:plan-fix" in text
    for field in ("title", "description", "severity", "plan_bead", "filed_by_step", "verified="):
        assert field in text


def test_formulas_are_vapor(formulas):
    assert all(formula["phase"] == "vapor" for formula in formulas.values())


def test_iteration_review_steps_are_parallel(formulas):
    steps = {step["id"]: step for step in formulas["iteration"]["steps"]}
    assert not steps["scope"].get("needs")
    assert not steps["critical"].get("needs")
    assert set(steps["fix"]["needs"]) == {"scope", "critical"}
    assert steps["fix"]["assignee"] == "fenix"


def test_final_formula_starts_with_ceremony(formulas):
    steps = formulas["final"]["steps"]
    assert [step["id"] for step in steps] == ["ceremony", "fix", "verify"]
    assert not steps[0].get("needs")
    assert steps[1]["needs"] == ["ceremony"]
    assert steps[2]["needs"] == ["fix"]


def skill_text():
    return (SKILL / "SKILL.md").read_text()


def test_skill_names_three_modes():
    text = skill_text().lower()
    for mode in ("planner with subagents", "planner with teammates", "lead adversarial"):
        assert mode in text


def test_skill_mode_selection():
    text = skill_text()
    for clause in ("team is idle", "no assigned work", "interrupting", "frontier model", "mid-phase replan"):
        assert clause in text


def test_skill_foundry_rule():
    text = skill_text()
    for clause in ("Anthropic, OpenAI, xAI", "iteration 2", "different foundry", "wherever possible", "Scope and critical passes run at frontier"):
        assert clause in text


def test_skill_default_two_iterations_and_final_fail_normal():
    text = skill_text()
    for clause in ("**2 iterations**", "lead or planner may set another number", "final critical pass is normal", "never add an iteration", "only after the last iteration"):
        assert clause in text


def test_skill_planner_mode_needs_no_lead():
    text = skill_text().split("## Planner with subagents")[1].split("## Planner with teammates")[0]
    for clause in ("every iteration", "final wisp", "No step waits on the phase lead", "only when handing", "Plan Gate"):
        assert clause in text


def adversarial_text():
    return (SKILL / "references/adversarial-plan-hardening.md").read_text()


def test_adversarial_reference_integration_step():
    text = adversarial_text()
    for clause in ("CLI", "schema", "service", "repository", "adversary", "source"):
        assert clause in text


def test_adversarial_reference_req_adr_step():
    text = adversarial_text()
    for clause in ("req-adr", "requirement", "ADR", "existing", "new"):
        assert clause in text


def test_adversarial_reference_lead_findings_new_tasks_tiers():
    text = adversarial_text()
    for clause in ("lead", "iteration 2", "fast", "frontier", "parallel", "weak", "area", "title"):
        assert clause in text
    assert "file your own findings as plan-fix beads" in text
    assert "same" in text and "task" in text


def test_skill_is_bd_only():
    files = [SKILL / "SKILL.md", * (SKILL / "references").glob("*.md"), * (SKILL / "templates").glob("*.j2"), * (SKILL / "formulas").glob("*.j2")]
    for path in files:
        text = path.read_text()
        assert not re.search(r"\bbr (create|update|close|show|list|ready|import)\b", text), path
        assert not re.search(r"sprint-[a-z0-9-]+\.md|phase-[a-z0-9-]+-plan\.md", text), path


def test_reviewer_agents_bd_form():
    for name in ("plan-scope-reviewer", "critical-plan-reviewer"):
        text = (PACKAGE / "agents" / f"{name}.md").read_text()
        assert "tools: Glob, Grep, LS, Read, BashOutput" in text
        assert "atm-beads-plan-guidelines.md" in text
        assert "sprint-planning-guidelines.md" not in text
        assert "sprint-scope-hardening fenced JSON handoff" not in text
        assert "scope and\ncritical reviews run in parallel" in text
        for field in ("title", "description", "severity", "plan_bead"):
            assert f'"{field}"' in text


def test_role_doc():
    roots = list(SKILL.parents)
    if source := os.environ.get("ATM_BD_CONSOLE_SRC"):
        roots.insert(0, Path(source).parents[2])
    root = next((root for root in roots if (root / "docs/requirements/plan-hardening.md").is_file()), None)
    if root is None:
        pytest.skip("Requirement documentation belongs to the source repository")
    text = (root / "docs/requirements/plan-hardening.md").read_text()
    assert "Sources" in text and "Requirements" in text and "Unresolved" in text
    assert re.search(r"^1\. ", text, re.MULTILINE)
    assert "plan-hardening.md" in (root / "docs/requirements/README.md").read_text()


def test_reviewer_output_filing_adapter():
    text = skill_text().split("## Filing reviewer output")[1].split("## Planner with subagents")[0]
    assert "concatenate `findings` and `minor_wording`" in text
    assert "File both arrays" in text
    assert "do not drop `minor_wording`" in text
    for name in ("critical-plan-reviewer", "plan-scope-reviewer"):
        agent = (PACKAGE / "agents" / f"{name}.md").read_text()
        assert "Filing reviewer output" in agent
        blocks = [json.loads(block) for block in re.findall(r"```json\n(.*?)\n```", agent, re.S)]
        output = next(block for block in blocks if "findings" in block)
        for entry in output["findings"] + output["minor_wording"]:
            assert {"title", "description", "severity", "plan_bead"} <= entry.keys()
