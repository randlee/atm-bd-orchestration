"""Check shipped workflow contracts without creating real tasks or beads."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

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
    assert "template rendering failed: invalid operation: invalid float literal" in result.stderr
    assert not (tmp_path / "output.xml").exists()


@pytest.mark.parametrize(
    ("variable", "hostile_value"),
    [
        ("step", "atm-wisp-2ha; touch /tmp/atm-g8-injected"),
        ("root", "atm-phase-d; touch /tmp/atm-g8-injected"),
        ("planner", "fenix; touch /tmp/atm-g8-injected"),
        ("actor", "arch-ctm; touch /tmp/atm-g8-injected"),
    ],
)
def test_step_template_refuses_shell_metacharacters(tmp_path, variable, hostile_value):
    source = tmp_path / "step.j2"
    source.write_bytes((SKILL / "templates/plan-hardening-step.xml.j2").read_bytes())
    variables = json.loads((SKILL / "examples/plan-hardening-step-teammate-vars.json").read_text())
    variables[variable] = hostile_value
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


def test_skill_plan_gate_references_resolve_from_skill_root():
    text = skill_text()
    references = re.findall(r"\[[^\]]+\]\((\.\./atm-bd-orchestration/SKILL\.md#[^)]+)\)", text)
    assert references == ["../atm-bd-orchestration/SKILL.md#plan-gate"] * 2
    for reference in references:
        path, anchor = reference.split("#", maxsplit=1)
        assert (SKILL / path).is_file()
        assert anchor == "plan-gate"
        assert re.search(r"^#{1,6} Plan Gate$", (SKILL / path).read_text(), re.MULTILINE)


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
    text = " ".join(adversarial_text().split())
    for clause in (
        "List every integration with another repository or an external API (CLI, schema, service).",
        "Assign a researcher to each integration to find detail missing from the plan.",
        "`area` naming that integration and `task` giving its research instruction",
    ):
        assert clause in text


def test_adversarial_reference_req_adr_step():
    text = " ".join(adversarial_text().split())
    for clause in (
        "Review every existing and new requirement and ADR the plan relates to.",
        "Look for inconsistency, gaps and vague language.",
        "When the plan outgrows, contradicts or sharpens an existing requirement or ADR, file a planner fix bead proposing its revision",
        "through an adversary wisp with `area=req-adr`.",
    ):
        assert clause in text


def test_adversarial_reference_lead_findings_new_tasks_tiers():
    text = " ".join(adversarial_text().split())
    for clause in (
        "Review the plan yourself through an adversary wisp with `area=lead`",
        "In iteration 2, first verify open fix beads filed by the `lead` and `adversary:*` passes",
        "Select researcher tiers using the dev-dispatch `difficulty` rule",
        "fast agents can cover broad, shallow ground in parallel; difficult code and integrations use frontier models, preferably different foundries.",
        "Never give an adversary the same task in iteration 2 as in iteration 1.",
        "Target a weakness iteration 1 found or an area nobody has covered.",
        "Record every adversary's area per iteration in its wisp title.",
    ):
        assert clause in text
    assert "file your own findings as plan-fix beads" in text


def test_skill_is_bd_only():
    files = [SKILL / "SKILL.md", * (SKILL / "references").glob("*.md"), * (SKILL / "templates").glob("*.j2"), * (SKILL / "formulas").glob("*.j2")]
    for path in files:
        text = path.read_text()
        assert not re.search(r"\bbr (create|update|close|show|list|ready|import)\b", text), path
        assert not re.search(r"sprint-[a-z0-9-]+\.md|phase-[a-z0-9-]+-plan\.md", text), path


def test_reviewer_agents_bd_form():
    for name in ("plan-scope-reviewer", "critical-plan-reviewer"):
        text = (PACKAGE / "agents" / f"{name}.md").read_text()
        frontmatter = yaml.safe_load(text.split("---\n", 2)[1])
        assert frontmatter["tools"] == "Glob, Grep, LS, Read, BashOutput"
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


def test_step_template_return_envelope(rendered):
    runner, text = rendered
    returns = [json.loads(block) for block in re.findall(r"```json\n(.*?)\n```", text, re.S)]
    completed, failed = returns
    assert completed == {"success": True, "data": {"step": "atm-wisp-2ha", "verdict": "PASS|FAIL", "findings": ["<filed fix bead ids>"]}, "error": None}
    assert failed["success"] is False
    assert failed["data"] == {"step": "atm-wisp-2ha", "verdict": None, "findings": []}
    assert set(failed["error"]) == {"code", "message", "recoverable", "suggested_action"}
    assert failed["error"]["code"] == "EXECUTION.STEP_FAILED"
    assert isinstance(failed["error"]["recoverable"], bool)
    assert failed["error"]["message"] and failed["error"]["suggested_action"]
    assert "bd update atm-wisp-2ha --status open --actor" in text
    if runner == "teammate":
        assert "atm task close atm-wisp-2ha refused --stdin" in text


def test_reviewer_output_filing_adapter():
    text = skill_text().split("## Filing reviewer output")[1].split("## Planner with subagents")[0]
    assert "concatenate `findings` and `minor_wording`" in text
    assert "File both arrays" in text
    assert "do not drop `minor_wording`" in text
    for name in ("critical-plan-reviewer", "plan-scope-reviewer"):
        agent = (PACKAGE / "agents" / f"{name}.md").read_text()
        assert "Filing reviewer output" in agent
        blocks = [json.loads(block) for block in re.findall(r"```json\n(.*?)\n```", agent, re.S)]
        output = next(block["data"] for block in blocks if "findings" in block.get("data", {}))
        for entry in output["findings"] + output["minor_wording"]:
            assert {"title", "description", "severity", "plan_bead"} <= entry.keys()
        assert "## Error Handling" in agent and "## Constraints" in agent
        assert "VALIDATION.INPUT" in agent and "REVIEW.TARGET_UNREADABLE" in agent


@pytest.mark.parametrize("review", [
    {"success": False, "data": None, "error": {"code": "VALIDATION.INPUT", "message": "missing root"}},
    {"success": False, "data": None, "error": None},
    {"success": True, "data": {"findings": [], "minor_wording": [], "errors": ["unreadable sprint"]}},
    {"success": True, "data": {"findings": [], "minor_wording": [], "errors": []}, "errors": ["bad input"]},
])
def test_reviewer_errors_force_failed_step(tmp_path, review):
    command = next(line for line in skill_text().splitlines() if line.startswith("jq -c 'if (.success"))
    path = tmp_path / "review.json"
    path.write_text(json.dumps(review))
    result = run("bash", "-c", 'REVIEW="$1"; ' + command, "mapping", str(path), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    mapped = json.loads(result.stdout)
    assert mapped["verdict"] == "FAIL" and mapped["error"] and mapped["findings"] == []


def test_successful_reviewer_output_files_both_arrays(tmp_path):
    command = next(line for line in skill_text().splitlines() if line.startswith("jq -c 'if (.success"))
    finding = {"title": "Gap", "description": "Fix gap", "severity": "Important", "plan_bead": "p-1", "issue": "extra"}
    review = {"success": True, "data": {"findings": [finding], "minor_wording": [{**finding, "severity": "Minor"}], "errors": []}, "error": None}
    path = tmp_path / "review.json"
    path.write_text(json.dumps(review))
    result = run("bash", "-c", 'REVIEW="$1"; ' + command, "mapping", str(path), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    mapped = json.loads(result.stdout)
    assert mapped["verdict"] == "FINDINGS" and mapped["error"] is None
    assert mapped["findings"] == [{k: v for k, v in finding.items() if k != "issue"},
                                   {k: v for k, v in {**finding, "severity": "Minor"}.items() if k != "issue"}]


def adversary_guard_request(tmp_path, area, task):
    source = SKILL / "formulas/plan-hardening-adversary.formula.toml.j2"
    (tmp_path / "input.j2").write_bytes(source.read_bytes())
    request = {"schema": "sc-compose/beads/v1", "operation": "render", "working_directory": str(tmp_path), "template": "input.j2", "rendered_formula": "output.formula.toml", "bead_variables": {}, "compose_variables": {"root": "atm-phase-d", "phase": "d", "iteration": "1", "planner": "fenix", "area": area, "task": task}}
    path = tmp_path / "request.json"
    path.write_text(json.dumps(request))
    return path


def adversary_guard(tmp_path, request, prefix):
    # Execute the documented guard itself; no real bd/ATM command is run.
    command = next(line.strip() for line in adversarial_text().splitlines() if line.strip().startswith(prefix))
    return run("bash", "-c", 'request="$1"; rendered_formula="$2"; ' + command, "guard", str(request), str(tmp_path / "output.formula.toml"), cwd=tmp_path)


@pytest.mark.parametrize("task", ['Check """ broken', r"Check C:\invalid\q"])
def test_adversary_rejects_invalid_rendered_toml(tmp_path, task):
    request = adversary_guard_request(tmp_path, "lead", task)
    rendered = run("sc-compose", "bead", "render", "--request", str(request), "--json", cwd=tmp_path)
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    assert adversary_guard(tmp_path, request, "python3 -c").returncode != 0


@pytest.mark.parametrize("area", ['bad"slug', "bad/slug", "Bad Slug"])
def test_adversary_rejects_non_slug_area(tmp_path, area):
    request = adversary_guard_request(tmp_path, area, "Check boundaries.")
    assert adversary_guard(tmp_path, request, "jq -e").returncode != 0


def test_adversary_guards_accept_valid_request(tmp_path):
    request = adversary_guard_request(tmp_path, "repo-sc-compose", "Check boundaries.")
    assert adversary_guard(tmp_path, request, "jq -e").returncode == 0
    rendered = run("sc-compose", "bead", "render", "--request", str(request), "--json", cwd=tmp_path)
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    assert adversary_guard(tmp_path, request, "python3 -c").returncode == 0


@pytest.mark.parametrize("batch", ["invalid_later", "valid"])
def test_finding_batch_validates_before_creating(rendered, tmp_path, batch):
    _, text = rendered
    script = re.search(r"```bash\n(set -euo pipefail\nSTEP=.*?)```", text, re.S)
    assert script is not None
    valid = {"title": "Correct ownership", "description": "Name the owner", "severity": "Important", "plan_bead": "atm-d-1"}
    findings = [valid, {**valid, "title": "" if batch == "invalid_later" else "Correct scope"}]
    (tmp_path / "atm-wisp-2ha-findings.json").write_text(json.dumps(findings))
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bd = bin_dir / "bd"
    bd.write_text("#!/bin/sh\ncase \"$1\" in\nshow) printf '%s\\n' '[{\"metadata\":{\"pass\":\"scope\"}}]' ;;\ncreate) printf '%s\\n' \"$*\" >> \"$BD_WRITES\"; printf '%s\\n' '{\"id\":\"created-fix\"}' ;;\n*) exit 64 ;;\nesac\n")
    bd.chmod(0o755)
    writes = tmp_path / "writes.txt"
    env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "TMPDIR": str(tmp_path), "BD_WRITES": str(writes)}
    result = subprocess.run(["bash", "-c", script.group(1)], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30, check=False)
    if batch == "invalid_later":
        assert result.returncode != 0
        assert not writes.exists(), "An invalid batch must not create its valid prefix"
    else:
        assert result.returncode == 0, result.stderr
        assert len(writes.read_text().splitlines()) == 2


@pytest.mark.parametrize("severity,verdict", [("important", "FAIL"), ("minor", "PASS")])
def test_ceremony_output_files_through_step(rendered, tmp_path, severity, verdict):
    _, text = rendered
    adapter = re.search(r"```bash\n(# Ceremony filing adapter.*?)```", skill_text(), re.S)
    filing = re.search(r"```bash\n(set -euo pipefail\nSTEP=.*?)```", text, re.S)
    assert adapter is not None and filing is not None
    capture = tmp_path / "plan.json"
    capture.write_text(json.dumps([{"id": "atm-d-1", "description": "Plan text"}]))
    issue, recommendation = "Redundant checklist", "Remove the duplicate checklist."
    review = {"success": True, "data": {"status": "findings", "findings": [{"id": "CQA-F001", "severity": severity, "class": "redundant_enforcement", "file": str(capture), "line": 1, "issue": issue, "recommendation": recommendation, "evidence": "Already enforced"}]}, "error": None}
    output = tmp_path / "ceremony.json"
    output.write_text(json.dumps(review))
    findings = tmp_path / "atm-wisp-2ha-findings.json"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bd = bin_dir / "bd"
    bd.write_text('#!/usr/bin/env python3\nimport json, os, sys\nif sys.argv[1] == "show":\n    print(json.dumps([{"metadata":{"pass":"ceremony"}}]))\nelif sys.argv[1] == "create":\n    with open(os.environ["BD_WRITES"], "a") as log:\n        log.write(json.dumps(sys.argv[1:]) + "\\n")\n    print(json.dumps({"id":"created-fix"}))\nelse:\n    sys.exit(64)\n')
    bd.chmod(0o755)
    writes = tmp_path / "writes.jsonl"
    env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "TMPDIR": str(tmp_path), "BD_WRITES": str(writes)}
    script = 'review_output="$1"; findings_file="$2";\n' + adapter.group(1) + filing.group(1)
    result = subprocess.run(["bash", "-c", script, "ceremony", str(output), str(findings)], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[0] == verdict
    canonical = {"title": issue, "description": issue + " " + recommendation, "severity": severity.capitalize(), "plan_bead": "atm-d-1"}
    assert json.loads(findings.read_text()) == [canonical]
    args, = [json.loads(line) for line in writes.read_text().splitlines()]
    assert args[:2] == ["create", issue]
    assert args[args.index("--description") + 1] == canonical["description"]
    metadata = json.loads(args[args.index("--metadata") + 1])
    assert metadata["pass"] == "ceremony"
    assert metadata["severity"] == canonical["severity"]
    assert metadata["plan_bead"] == "atm-d-1"
