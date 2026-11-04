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
    assert "runner_must_be_teammate_or_subagent" in result.stderr
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


def test_finding_block_resumes_partial_batch_without_duplicates(rendered, tmp_path):
    _, text = rendered
    block = next(block for block in re.findall(r"```bash\n(.*?)\n```", text, re.S)
                 if "STEP='atm-wisp-2ha'" in block)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    bd = bindir / "bd"
    bd.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
path = Path(os.environ["BD_STATE"])
rows = json.loads(path.read_text()) if path.exists() else []
args = sys.argv[1:]
if args[0] == "show":
    print(json.dumps([{"metadata": {"pass": "scope"}}]))
elif args[0] == "list":
    assert "--all" in args
    print(json.dumps(rows))
elif args[0] == "create":
    value = lambda option: args[args.index(option) + 1]
    row = {"id": f"fix-{len(rows)+1}", "title": args[1], "description": value("--description"),
           "metadata": json.loads(value("--metadata"))}
    rows.append(row)
    path.write_text(json.dumps(rows))
    print(json.dumps(row))
else:
    raise SystemExit("unexpected bd command")
''')
    bd.chmod(0o755)
    env = {**os.environ, "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}",
           "TMPDIR": str(tmp_path), "BD_STATE": str(tmp_path / "state.json")}
    findings = [{"title": "First", "description": "Fix one", "severity": "Important", "plan_bead": "p-1"},
                {"title": "Second", "description": "Fix two", "severity": "Minor", "plan_bead": "p-2"}]
    input_path = tmp_path / "atm-wisp-2ha-findings.json"
    for batch in (findings[:1], findings, findings):
        input_path.write_text(json.dumps(batch))
        result = subprocess.run(["bash", "-c", block], cwd=tmp_path, env=env, capture_output=True, text=True,
                                timeout=30, check=False)
        assert result.returncode == 0, result.stderr
    assert [row["title"] for row in json.loads((tmp_path / "state.json").read_text())] == ["First", "Second"]
    assert (tmp_path / "atm-wisp-2ha-filed.txt").read_text().splitlines() == ["fix-1", "fix-2"]


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


def test_formula_reviewer_references_resolve(formulas):
    reviewers = set()
    for formula in formulas.values():
        for step in formula["steps"]:
            reviewers.update(re.findall(r"\.claude/agents/([a-z-]+\.md)", step["description"]))
    assert reviewers == {"plan-scope-reviewer.md", "critical-plan-reviewer.md", "ceremony-qa.md"}
    for reviewer in reviewers:
        assert (PACKAGE / "agents" / reviewer).is_file(), reviewer


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

    for document in (SKILL / "SKILL.md", SKILL / "references/adversarial-plan-hardening.md"):
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text())
        assert links, document
        for link in links:
            target = (document.parent / link.split("#", 1)[0]).resolve()
            assert target.is_relative_to(PACKAGE)
            assert target.is_file(), (document, link)


def test_skill_names_three_modes():
    headings = set(re.findall(r"^## (.+)$", skill_text(), re.MULTILINE))
    assert {"Planner with subagents", "Planner with teammates", "Lead adversarial"} <= headings


def adversarial_text():
    return (SKILL / "references/adversarial-plan-hardening.md").read_text()


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


def test_plan_scope_reviewer_keeps_one_input_contract():
    agent = (PACKAGE / "agents/plan-scope-reviewer.md").read_text()
    reference = (SKILL / "references/plan-gate-reviewer-input.md").read_text()
    normalized_reference = " ".join(reference.split())
    assert agent.count("## Input Contract") == 1
    assert "plan-gate-reviewer-input.md" in agent
    assert "phase_root_doc" not in agent
    assert "findings_scope_locked" not in agent
    for field in ("phase_root_doc", "plan_docs", "round_index", "carry_forward_findings", "findings_scope_locked"):
        assert f'"{field}"' in reference
    assert "verify only `carry_forward_findings`" in normalized_reference
    assert "Do not make a new plan-shape review or file new findings." in normalized_reference


def test_role_doc():
    roots = list(SKILL.parents)
    if source := os.environ.get("ATM_BD_CONSOLE_SRC"):
        roots.insert(0, Path(source).parents[2])
    root = next((root for root in roots if (root / "docs/requirements/plan-hardening.md").is_file()), None)
    if root is None:
        pytest.skip("Requirement documentation belongs to the source repository")
    text = (root / "docs/requirements/plan-hardening.md").read_text()
    assert re.search(r"^Sources:", text, re.MULTILINE)
    headings = set(re.findall(r"^## (.+)$", text, re.MULTILINE))
    assert {"Requirements", "Unresolved"} <= headings
    requirements = text.split("## Requirements\n", 1)[1].split("\n## Unresolved", 1)[0]
    numbers = [int(number) for number in re.findall(r"^(\d+)\. ", requirements, re.MULTILINE)]
    assert numbers and numbers == list(range(1, len(numbers) + 1))
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", (root / "docs/requirements/README.md").read_text())
    assert "plan-hardening.md" in links


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
    for name in ("critical-plan-reviewer", "plan-scope-reviewer"):
        agent = (PACKAGE / "agents" / f"{name}.md").read_text()
        blocks = [json.loads(block) for block in re.findall(r"```json\n(.*?)\n```", agent, re.S)]
        output = next(block["data"] for block in blocks if "findings" in block.get("data", {}))
        for entry in output["findings"] + output["minor_wording"]:
            assert {"title", "description", "severity", "plan_bead"} <= entry.keys()
        headings = set(re.findall(r"^## (.+)$", agent, re.MULTILINE))
        assert {"Error Handling", "Constraints"} <= headings
        codes = set(re.findall(r"`([A-Z][A-Z_.]+)`", agent))
        assert {"VALIDATION.INPUT", "REVIEW.TARGET_UNREADABLE"} <= codes


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
    assert mapped["verdict"] == "ERROR" and mapped["error"] and mapped["findings"] == []


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
    assert adversary_guard(tmp_path, request, "uv run --no-project --python '>=3.11' python -c").returncode != 0


@pytest.mark.parametrize("area", ['bad"slug', "bad/slug", "Bad Slug"])
def test_adversary_rejects_non_slug_area(tmp_path, area):
    request = adversary_guard_request(tmp_path, area, "Check boundaries.")
    assert adversary_guard(tmp_path, request, "jq -e").returncode != 0


def test_adversary_guards_accept_valid_request(tmp_path):
    request = adversary_guard_request(tmp_path, "repo-sc-compose", "Check boundaries.")
    assert adversary_guard(tmp_path, request, "jq -e").returncode == 0
    rendered = run("sc-compose", "bead", "render", "--request", str(request), "--json", cwd=tmp_path)
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    assert adversary_guard(tmp_path, request, "uv run --no-project --python '>=3.11' python -c").returncode == 0


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
    bd.write_text("#!/bin/sh\ncase \"$1\" in\nshow) printf '%s\\n' '[{\"metadata\":{\"pass\":\"scope\"}}]' ;;\nlist) printf '%s\\n' '[]' ;;\ncreate) printf '%s\\n' \"$*\" >> \"$BD_WRITES\"; printf '%s\\n' '{\"id\":\"created-fix\"}' ;;\n*) exit 64 ;;\nesac\n")
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
    bd.write_text('#!/usr/bin/env python3\nimport json, os, sys\nif sys.argv[1] == "show":\n    print(json.dumps([{"metadata":{"pass":"ceremony"}}]))\nelif sys.argv[1] == "list":\n    print("[]")\nelif sys.argv[1] == "create":\n    with open(os.environ["BD_WRITES"], "a") as log:\n        log.write(json.dumps(sys.argv[1:]) + "\\n")\n    print(json.dumps({"id":"created-fix"}))\nelse:\n    sys.exit(64)\n')
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
