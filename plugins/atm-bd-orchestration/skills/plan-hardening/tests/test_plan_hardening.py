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
EVALS = PACKAGE / "evals/plan-hardening"


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


@pytest.mark.parametrize("evidence", ["", "/tmp/attached.json"])
def test_dispatch_carrier_delivers_paths(tmp_path: Path, evidence: str):
    template = tmp_path / "dispatch.xml.j2"
    template.write_bytes((SKILL / "templates/plan-hardening-dispatch.xml.j2").read_bytes())
    variables = tmp_path / "vars.json"
    variables.write_text(json.dumps({"step_path": "/tmp/step.xml", "evidence_path": evidence}))
    result = run("sc-compose", "render", "--strict", "--file", str(template), "--var-file", str(variables), "--output", "dispatch.xml", cwd=tmp_path)
    assert result.returncode == 0, result.stderr + result.stdout
    body = (tmp_path / "dispatch.xml").read_text()
    assert "Read /tmp/step.xml, follow it exactly" in body
    assert ("Attached evidence: /tmp/attached.json" in body) == bool(evidence)
    assert "If the step file is missing, stop" in body


def test_filing_reuses_existing_findings_with_stderr_warning(rendered, tmp_path: Path):
    _, prompt = rendered
    block = prompt.split('STEP=\'atm-wisp-2ha\'', 1)[1].split("\nATM_STEP", 1)[0]
    block = "set -euo pipefail\nSTEP='atm-wisp-2ha'" + block
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    bd = bin_dir / "bd"
    bd.write_text("""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
state = Path(os.environ['STATE'])
print('beads warning', file=sys.stderr)
if sys.argv[1] == 'show':
    print(json.dumps([{'metadata': {'pass': 'scope'}}]))
elif sys.argv[1] == 'list':
    print(state.read_text() if state.exists() else '[]')
else:
    args = sys.argv
    row = {'id': 'finding-1', 'title': args[2], 'description': args[args.index('--description') + 1], 'metadata': json.loads(args[args.index('--metadata') + 1])}
    state.write_text(json.dumps([row]))
    print(json.dumps({'id': row['id']}))
""")
    bd.chmod(0o755)
    (tmp_path / "atm-wisp-2ha-findings.json").write_text(json.dumps([{'title': 'Issue', 'description': 'Correction', 'severity': 'Important', 'plan_bead': 'sprint-1'}]))
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ['PATH'], TMPDIR=str(tmp_path), STATE=str(tmp_path / 'state.json'))
    for _ in range(2):
        result = subprocess.run(['bash', '-c', block], env=env, capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == 'finding-1'
    assert len(json.loads((tmp_path / 'state.json').read_text())) == 1
    assert len(list(tmp_path.glob('filing.*/create.json'))) == 1
    assert all('beads warning' in p.read_text() for p in tmp_path.glob('filing.*/list.stderr'))


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


def test_step_template_carries_isolated_context(rendered):
    _, text = rendered
    assert "cd '/tmp/worktree'" in text
    assert "export BEADS_DIR='/tmp/beads'" in text
    assert "--index '/tmp/phase-d.jsonl'" in text
    assert "TMPDIR=/tmp/eval-scratch" in text
    assert "export TMPDIR='/tmp/eval-scratch/atm-wisp-2ha'" in text
    assert "never push or commit the DAG" in text
    assert "/tmp/worktree/.atm-bd/atm.bd-cache.sqlite3" not in text
    assert text.count("`sprint-review`") == 1
    assert "No hardening step (including review, fix, and verify) runs" in text
    assert 'filed=' in text and 'stage:plan-hardening --include-ephemeral --all' in text


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_plan_snapshot_uses_isolated_context_and_includes_dependencies(rendered, tmp_path, shell):
    _, text = rendered
    command = text.split("create the plan snapshot below", 1)[1].split("```bash", 1)[1].split("```", 1)[0]
    command = command.replace("cd '/tmp/worktree'", f"cd '{tmp_path}'").replace("/tmp/eval-scratch/atm-wisp-2ha", str(tmp_path))
    bd = tmp_path / "bd"
    bd.write_text('''#!/usr/bin/env python3
import json, os, sys
assert os.environ['BEADS_DIR'] == '/tmp/beads'
args = sys.argv[1:]
if args[0] == 'show': result = [{'id': 'atm-phase-d'}]
elif args[0] == 'dep':
    assert args[1:3] == ['list', 'sprint-1']
    result = [{'id': 'prerequisite'}]
elif 'stage:sprint' in args: result = [{'id': 'sprint-1'}]
else:
    assert 'stage:plan-fix' in args and '--status' in args and 'open' in args
    result = [{'id': 'finding-1'}]
print(json.dumps(result))
''')
    bd.chmod(0o755)
    result = subprocess.run([shell, "-c", f"export PATH='{tmp_path}:'$PATH\n" + command], cwd=tmp_path,
                            env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"]},
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    snapshot = json.loads((tmp_path / "plan-snapshot.json").read_text())
    assert snapshot == {"root": [{"id": "atm-phase-d"}], "sprints": [{"id": "sprint-1"}],
                        "dependencies": [{"id": "sprint-1", "dependencies": [{"id": "prerequisite"}]}],
                        "open_plan_fixes": [{"id": "finding-1"}]}


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_step_filing_enumeration_executes(rendered, tmp_path, shell):
    _, text = rendered
    command = text.split("filing reported by earlier steps", 1)[1].split("```bash", 1)[1].split("```", 1)[0]
    command = command.replace("cd '/tmp/worktree'", f"cd '{tmp_path}'").replace("/tmp/eval-scratch/atm-wisp-2ha", str(tmp_path))
    bd = tmp_path / "bd"
    rows = [
        {"metadata": {"root": "atm-phase-d"}, "close_reason": "VERDICT=FAIL filed=one,two verified=none"},
        {"metadata": {"root": "other"}, "close_reason": "filed=wrong"},
        {"metadata": {"root": "atm-phase-d"}, "close_reason": "VERDICT=PASS filed=none"},
    ]
    bd.write_text("#!/bin/sh\ncase \"$*\" in *stage:plan-fix*) printf '%s\\n' '[{\"id\":\"one\"},{\"id\":\"two\"}]' ;; *) printf '%s\\n' " + "'" + json.dumps(rows) + "' ;; esac\n")
    bd.chmod(0o755)
    result = subprocess.run([shell, "-c", f"export PATH='{tmp_path}:'$PATH\n" + command], cwd=tmp_path,
                            env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"]},
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["one", "two"]
    bd.write_text(bd.read_text().replace('{"id":"two"}', '{"id":"different"}'))
    missing = subprocess.run([shell, "-c", f"export PATH='{tmp_path}:'$PATH\n" + command], cwd=tmp_path,
                             env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"]},
                             capture_output=True, text=True, check=False)
    assert missing.returncode != 0 and "two" in missing.stderr


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_sprint_render_uses_expanded_absolute_vars_path(rendered, tmp_path: Path, shell: str):
    _, text = rendered
    block = next(block for block in re.findall(r"```bash\n(.*?)\n```", text, re.S) if "SPRINT_VARS=\"$TMPDIR/sprint-vars.json\"" in block)
    block = block.replace("cd '/tmp/worktree'", f"cd '{tmp_path}'").replace("/tmp/eval-scratch/atm-wisp-2ha", str(tmp_path)).replace("/tmp/phase-d.jsonl", str(tmp_path / "index.jsonl"))
    (tmp_path / "sprint-vars.json").write_text('{}')
    sc = tmp_path / "sc-compose"
    sc.write_text('#!/bin/sh\nwhile [ "$#" -gt 0 ]; do case "$1" in --var-file) test -f "$2" || exit 9; shift 2 ;; --output) printf "{}\\n" > "$2"; shift 2 ;; *) shift ;; esac; done\n')
    sc.chmod(0o755)
    bd = tmp_path / "bd"
    bd.write_text('#!/bin/sh\nexit 0\n')
    bd.chmod(0o755)
    env = {**os.environ, "SPRINT_NAME": "qx-5", "DEPS_JSON": "[]"}
    result = subprocess.run([shell, "-c", f"export PATH='{tmp_path}:'$PATH\n" + block], cwd=tmp_path, env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / "index.jsonl").read_text()) == {"sprint": "qx-5", "depends_on": []}


@pytest.mark.parametrize("field", ["workdir", "beads_dir", "plan_index", "scratch_dir", "cache_path", "policy_path"])
def test_step_template_rejects_unsafe_path(tmp_path, field):
    source = tmp_path / "step.j2"
    source.write_bytes((SKILL / "templates/plan-hardening-step.xml.j2").read_bytes())
    variables = json.loads((SKILL / "examples/plan-hardening-step-subagent-vars.json").read_text())
    variables[field] = "/tmp/unsafe'path"
    (tmp_path / "vars.json").write_text(json.dumps(variables))
    result = run("sc-compose", "render", "--strict", "--file", str(source), "--var-file", str(tmp_path / "vars.json"), "--output", "output.xml", cwd=tmp_path)
    assert result.returncode != 0
    assert not (tmp_path / "output.xml").exists()


def test_step_template_requires_plan_index(tmp_path):
    source = tmp_path / "step.j2"
    source.write_bytes((SKILL / "templates/plan-hardening-step.xml.j2").read_bytes())
    variables = json.loads((SKILL / "examples/plan-hardening-step-subagent-vars.json").read_text())
    del variables["plan_index"]
    (tmp_path / "vars.json").write_text(json.dumps(variables))
    result = run("sc-compose", "render", "--strict", "--file", str(source), "--var-file", str(tmp_path / "vars.json"), "--output", "output.xml", cwd=tmp_path)
    assert result.returncode != 0


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
    assert "bd show 'atm-phase-d' --json" in text
    assert "bd list --parent 'atm-phase-d' -l stage:sprint" in text


def test_finding_block_files_planner_fix_beads(rendered):
    _, text = rendered
    assert "--parent 'atm-phase-d' --type task --assignee 'fenix'" in text
    assert "--no-inherit-labels --labels 'stage:plan-fix'" in text
    assert "phase-d,stage:plan-fix" not in text  # Temporary until schema issue #788 is fixed.
    for field in ("title", "description", "severity", "plan_bead", "filed_by_step", "verified="):
        assert field in text


def test_finding_block_resumes_partial_batch_without_duplicates(rendered, tmp_path):
    _, text = rendered
    block = next(block for block in re.findall(r"```bash\n(.*?)\n```", text, re.S)
                 if "STEP='atm-wisp-2ha'" in block)
    block = block.replace("cd '/tmp/worktree'", f"cd '{tmp_path}'").replace("/tmp/eval-scratch/atm-wisp-2ha", str(tmp_path))
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


def test_missing_governing_document_is_planned_not_parked(rendered, formulas):
    _, step = rendered
    phrase = "A missing governing document or section (ADR, REQ, architecture, or design document) is never an open decision."
    assert phrase in step
    assert phrase in skill_text()
    for name in ("iteration", "final"):
        fix = next(item for item in formulas[name]["steps"] if item["id"] == "fix")
        assert phrase in fix["description"]


def test_dispatcher_bd_examples_always_bind_database_and_workdir():
    docs = [SKILL / "SKILL.md"]
    if EVALS.is_dir():
        docs.extend([EVALS / "subagent.md", EVALS / "teammate.md"])
    command = re.compile(r"\bbd (?:version|mol|ready|dep|list|show|update|import|info)\b")
    for doc in docs:
        for line_number, line in enumerate(doc.read_text().splitlines(), 1):
            if command.search(line):
                assert "BEADS_DIR=" in line and "cd " in line, (doc, line_number, line)


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


def test_skill_declares_and_verifies_cli_dependencies_first(tmp_path):
    text = skill_text()
    frontmatter = yaml.safe_load(text.split("---\n", 2)[1])
    requirements = {item["name"]: item.get("minimum_version") for item in frontmatter["requires"]["cli"]}
    assert requirements == {"bd": "1.3.0", "atm": None, "sc-compose": "1.7.0", "jq": None, "uv": None}
    headings = re.findall(r"^## (.+)$", text, re.MULTILINE)
    assert headings[0] == "Step 1 — Verify CLI Installation"
    first_block = re.search(r"```bash\n(.*?)```", text, re.S)
    assert first_block is not None
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls.txt"
    for name in requirements:
        tool = bin_dir / name
        version = requirements[name] or "1.0.0"
        tool.write_text(f'#!/bin/sh\nprintf "%s\\n" "{name} $*" >> "$CLI_CALLS"\nprintf "%s\\n" "{name} {version}"\n')
        tool.chmod(0o755)
    env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "CLI_CALLS": str(calls), "workdir": str(tmp_path), "beads_dir": str(tmp_path / "beads")}
    result = subprocess.run(["bash", "-c", first_block.group(1)], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr
    assert {line for line in result.stdout.splitlines() if line.startswith("ok ")} == {"ok " + name for name in requirements}
    assert calls.read_text().splitlines() == ["bd version", "sc-compose --version", "uv --version"]
    reference = "../atm-beads/references/installation-and-troubleshooting.md"
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    assert reference in links
    assert (SKILL / reference).is_file()


def test_skill_names_three_modes():
    headings = set(re.findall(r"^## (.+)$", skill_text(), re.MULTILINE))
    assert {"Planner with subagents", "Planner with teammates", "Lead adversarial"} <= headings
    text = skill_text().lower()
    for mode in ("planner with subagents", "planner with teammates", "lead adversarial"):
        assert mode in text


def test_skill_limits_runner_writes_to_template_commands():
    text = skill_text().split("The runner's `bd` writes are limited", 1)[1].split("## Iterations", 1)[0]
    for clause in (
        "claim\nand close the step",
        "create `stage:plan-fix` beads under the root",
        "close\nverified fix beads or update their notes",
        "may also update plan beads and, only through the add-sprint path below",
        "corresponding container-to-container `blocks` edges",
        "modify sprint groups during hardening",
        "`bd create` of a sprint or any other `bd` write fails the step",
        "only permitted `git` write is after the plan changes",
        "template specifies no PR",
        "Reviewer agents remain read-only",
    ):
        assert clause in text


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
def test_scope_reviewer_uses_nearest_required_pr_target():
    text = (PACKAGE / "agents/plan-scope-reviewer.md").read_text()
    assert "branch of its nearest `must_follow` prerequisite" in text
    assert "branch of layer n-1" not in text
    assert "branch of the layer below" not in text


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
    assert completed == {"success": True, "data": {"step": "atm-wisp-2ha", "verdict": "PASS|FAIL", "findings": ["<filed fix bead ids>"], "commands": [{"argv": "<command>", "output_path": "<scratch path>", "exit_code": 0}], "bd_writes": ["<bd write>"], "file_writes": ["<written file>"]}, "error": None}
    assert failed["success"] is False
    assert failed["data"] == {"step": "atm-wisp-2ha", "verdict": None, "findings": [], "commands": [{"argv": "<command>", "output_path": "<scratch path>", "exit_code": 1}], "bd_writes": ["<bd write>"], "file_writes": ["<written file>"]}
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
    script = next(block for block in re.findall(r"```bash\n(.*?)\n```", text, re.S) if "STEP='atm-wisp-2ha'" in block)
    script = script.replace("cd '/tmp/worktree'", f"cd '{tmp_path}'").replace("/tmp/eval-scratch/atm-wisp-2ha", str(tmp_path))
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
    result = subprocess.run(["bash", "-c", script], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30, check=False)
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
    filing = next(block for block in re.findall(r"```bash\n(.*?)\n```", text, re.S) if "STEP='atm-wisp-2ha'" in block)
    filing = filing.replace("cd '/tmp/worktree'", f"cd '{tmp_path}'").replace("/tmp/eval-scratch/atm-wisp-2ha", str(tmp_path))
    assert adapter is not None
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
    script = 'review_output="$1"; findings_file="$2";\n' + adapter.group(1) + filing
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
@pytest.mark.skipif(not EVALS.is_dir(), reason="evaluation assets intentionally excluded from installed skill")
def test_eval_fixture_keeps_all_planted_defects_in_sprints():
    rows = [json.loads(line) for line in (EVALS / "fixture-plan.jsonl").read_text().splitlines()]
    beads = {row["id"]: row for row in rows}
    planted = json.loads((EVALS / "planted.json").read_text())
    one, two, three, four = (beads[planted[key]] for key in (
        "overlapping_owned_paths", "unconsumed_ledger", "must_follow_without_artifact", "boundary_false_closure"))
    assert one["metadata"]["relation"] == two["metadata"]["relation"] == "parallel_safe"
    assert set(one["metadata"]["owned_paths"]) & set(two["metadata"]["owned_paths"])
    assert "ledger" in two["description"].lower()
    assert three["metadata"]["relation"] == "must_follow" and "without reading" in three["design"]
    assert four["metadata"]["closure_type"] == "boundary" and "end to end" in four["acceptance_criteria"]
    assert not any(".group-" in bead for bead in beads)


@pytest.mark.skipif(not EVALS.is_dir(), reason="evaluation assets intentionally excluded from installed skill")
def test_eval_server_refuses_foreign_process_context(tmp_path):
    (tmp_path / "server.json").write_text(json.dumps({"pid": os.getpid(), "socket": "/tmp/not-this-eval.sock", "data_dir": "/tmp/other"}))
    result = subprocess.run(["python3", str(EVALS / "db-server.py"), "stop", str(tmp_path)],
                            capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "does not belong to this scratch directory" in result.stderr


@pytest.mark.skipif(not EVALS.is_dir(), reason="evaluation assets intentionally excluded from installed skill")
def test_eval_answer_key_is_not_installed():
    manifest = yaml.safe_load((PACKAGE / "manifest.yaml").read_text())
    installed = [path for paths in manifest["artifacts"].values() for path in paths]
    assert not any("plan-hardening/evals/" in path or path.endswith("/planted.json") for path in installed)
    assert (EVALS / "planted.json").is_file()


@pytest.mark.skipif(not EVALS.is_dir(), reason="evaluation assets intentionally excluded from installed skill")
def test_eval_prompts_have_post_run_questions():
    questions = (
        "Which instruction was unclear?",
        "Where did you guess?",
        "Which instruction did you skip or reinterpret, and why?",
        "What did you need but not have?",
        "What would you change?",
    )
    for runner in ("subagent", "teammate"):
        text = (EVALS / f"{runner}.md").read_text()
        assert "## Post-run questions" in text
        assert all(question in text for question in questions)
        assert "bd import" in text and f'"$EVAL_ROOT/check.sh" atm-phase-qx {runner}' in text
        assert "BEADS_DIR" in text and "db-server.py" in text
        assert "independent" in text and "plan_pr" in text
        assert "bd delete --force" not in text


@pytest.mark.skipif(not EVALS.is_dir(), reason="evaluation assets intentionally excluded from installed skill")
def test_eval_check_script_rejects_missing_fix_bead(tmp_path):
    bd = tmp_path / "bd"
    bd.write_text('''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
scenario = os.environ.get("EVAL_SCENARIO", "ok")
if args[0] == "list" and "stage:sprint" in args:
    rows = [{"id": f"atm-qx-{i}", "status": "open"} for i in range(1, 5)]
    if scenario in ("closed_sprint", "closed_no_reason", "closed_with_group"):
        rows[2]["status"] = "closed"
        rows[2]["close_reason"] = "removed with scope absorbed" if scenario != "closed_no_reason" else " "
    print(json.dumps(rows))
elif args[0] == "list" and "--parent" in args and args[args.index("--parent") + 1].startswith("atm-qx-"):
    sprint = args[args.index("--parent") + 1]
    absent = scenario == "missing_group" or (sprint == "atm-qx-3" and scenario in ("closed_sprint", "closed_no_reason"))
    print(json.dumps([] if absent else [{"id": sprint + ".group-" + role} for role in ("dev", "sanity", "qa")]))
elif args[0] == "list" and "--parent" in args:
    ids = ["atm-qx-1", "atm-qx-2", "atm-qx-3", "atm-qx-4"]
    if scenario == "missing_fix": ids.pop()
    print(json.dumps([{"id": f"fix-{i}", "metadata": {"plan_bead": x, "filed_by_step": "step-0"}} for i, x in enumerate(ids)]))
elif args[0] == "list":
    rows = [("scope", "1"), ("critical", "1"), ("fix", "1"),
            ("ceremony", "final"), ("fix", "final"), ("verify", "final")]
    print(json.dumps([{"id": f"step-{i}", "metadata": {"root": "atm-phase-qx", "pass": p, "iteration": n}}
                      for i, (p, n) in enumerate(rows)]))
elif args[0] == "show" and ".group-" in args[1]:
    print(json.dumps([] if scenario == "missing_group" else [{"id": args[1]}]))
elif args[0] == "show" and args[1].startswith("fix-"):
    print(json.dumps([{"status": "closed" if scenario != "unfixed" else "open", "notes": "fixed: resolved\\nrebutted: citation" if scenario == "mixed" else ("fixed in part / rebutted in part" if scenario == "partial" else "fixed: resolved the finding")}]))
elif args[0] == "show":
    reason = "VERDICT=PASS detected=0 filed=none verified=none"
    if args[1] == "step-0": reason = "VERDICT=FAIL detected=4 filed=fix-0,fix-1,fix-2,fix-3 verified=none"
    if scenario == "bad_verdict": reason = "not a verdict"
    if scenario == "missing_accounting": reason = "VERDICT=FAIL filed=none verified=none"
    if scenario == "unfiled" and args[1] == "step-0": reason = "VERDICT=FAIL detected=5 filed=fix-0,fix-1,fix-2,fix-3 verified=none"
    print(json.dumps([{"status": "closed", "close_reason": reason}]))
else:
    sys.exit(1)
''')
    atm = tmp_path / "atm"
    atm.write_text('''#!/usr/bin/env python3
import json, os
runner = os.environ["EVAL_RUNNER"]
scenario = os.environ.get("EVAL_SCENARIO", "ok")
events = []
if runner == "teammate":
    events = [{"event": "started"}, {"event": "completed"}]
    if scenario == "no_start": events = [{"event": "completed"}]
elif scenario == "rogue_task":
    events = [{"event": "assigned"}]
print(json.dumps({"events": events, "handoffs": []}))
''')
    bd.chmod(0o755)
    atm.chmod(0o755)
    script = EVALS / "check.sh"

    def check(runner: str, scenario: str = "ok") -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "BD": str(bd), "ATM": str(atm), "EVAL_RUNNER": runner, "EVAL_SCENARIO": scenario}
        return subprocess.run([str(script), "atm-phase-qx", runner], env=env, capture_output=True, text=True, check=False)

    for runner in ("teammate", "subagent"):
        assert check(runner).returncode == 0
        missing = check(runner, "missing_fix")
        assert missing.returncode != 0 and "atm-qx-4" in missing.stderr
        assert check(runner, "bad_verdict").returncode != 0
        assert check(runner, "missing_accounting").returncode != 0
        assert check(runner, "unfiled").returncode != 0
        assert check(runner, "missing_group").returncode != 0
        assert check(runner, "closed_sprint").returncode == 0
        assert check(runner, "closed_no_reason").returncode != 0
        assert check(runner, "closed_with_group").returncode != 0
        assert check(runner, "partial").returncode != 0
        assert check(runner, "mixed").returncode != 0
        unfixed = check(runner, "unfixed")
        assert unfixed.returncode != 0
        assert "fix-0" in unfixed.stderr and "fix-1" in unfixed.stderr
    assert check("teammate", "no_start").returncode != 0
    assert check("subagent", "rogue_task").returncode != 0
    assert check("bogus").returncode == 2
