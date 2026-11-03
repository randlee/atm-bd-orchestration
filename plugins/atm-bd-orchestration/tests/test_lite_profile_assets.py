"""Contract tests for the standalone atm-bd-lite profile assets."""
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / "skills" / "atm-bd-lite"
TEMPLATES = SKILL / "templates"


@pytest.mark.parametrize(
    ("filename", "variables", "expected"),
    [
        ("dev-close.md.j2", {"branch": "feature/x", "head": "abc123", "pr": "#42", "base": "main"},
         ["branch", "head", "pr", "base"]),
        ("refuse.md.j2", {"reason": "blocked by prerequisite"}, ["reason"]),
        ("qa-pass.md.j2", {"sha": "abc123"}, ["sha"]),
        ("qa-findings.md.j2", {"sha": "abc123", "ids": "F-1, F-2"}, ["sha", "ids"]),
    ],
)
def test_close_templates_strictly_render_exact_contract(filename: str, variables: dict[str, str], expected: list[str]) -> None:
    template = TEMPLATES / filename
    source = template.read_text()
    match = re.search(r"^required_variables:\s*\[([^]]*)\]$", source, re.MULTILINE)
    assert match is not None
    declared = [item.strip() for item in match.group(1).split(",")]
    assert declared == expected
    rendered = subprocess.run(
        ["sc-compose", "render", "--strict", "--file", str(template),
         *[argument for key, value in variables.items() for argument in ("--var", f"{key}={value}")]],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    assert rendered.strip()
    assert "{{" not in rendered


def test_qa_assignment_template_strictly_renders_assign_vars() -> None:
    template = TEMPLATES / "qa.xml.j2"
    source = template.read_text()
    match = re.search(r"^required_variables:\s*\[([^]]*)\]$", source, re.MULTILINE)
    assert match is not None
    assert [item.strip() for item in match.group(1).split(",")] == ["task_id", "phase", "profile"]
    rendered = subprocess.run(
        ["sc-compose", "render", "--strict", "--file", str(template),
         "--var", "task_id=bo-14-qa", "--var", "phase=bo", "--var", "profile=atm-bd-lite"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    assert '<qa-task id="bo-14-qa">' in rendered
    assert "stack top" in rendered
    assert "T-CLOSE-03" in rendered and "T-CLOSE-04" in rendered


def test_policy_parameters_are_text_and_point_to_qa_template() -> None:
    policy = tomllib.loads((SKILL / "policy.toml").read_text())
    params = policy["params"]
    assert params == {"qa_agent": "quality-mgr", "qa_template": "templates/qa.xml.j2"}
    assert all(isinstance(value, str) for value in params.values())
    assert (SKILL / params["qa_template"]).is_file()


def test_skill_registers_each_profile_hook_once() -> None:
    profile = tomllib.loads((SKILL / "profile.toml").read_text())
    skill = (SKILL / "SKILL.md").read_text()
    commands = [line for line in skill.splitlines() if line.startswith("atm hook register ")]
    assert len(commands) == len(profile["hooks"]) == 3
    for hook, script in profile["hooks"].items():
        assert sum(hook in command and f"--module .claude/skills/atm-bd-lite/{script}" in command for command in commands) == 1
    assert "followed by QA" in skill
    assert "does not add a sanity stage" in skill


def test_copied_behavior_suite_runs_isolated_and_reports_67_passes() -> None:
    suite = Path(__file__).resolve().parent / "lite"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-c", "/dev/null", "--rootdir", ".", "--confcutdir", ".", "."],
        cwd=suite,
        capture_output=True,
        text=True,
        check=False,
    )
    details = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert result.returncode == 0, details
    assert re.search(r"(?m)^67 passed in \d+(?:\.\d+)?s$", result.stdout), details


def test_registered_profile_modules_declare_one_timeout_within_registrar_cap() -> None:
    profile = tomllib.loads((SKILL / "profile.toml").read_text())
    skill = (SKILL / "SKILL.md").read_text()
    registration_lines = [line for line in skill.splitlines() if line.startswith("atm hook register ")]
    registered = [line.split("--module ", 1)[1].split()[0].rsplit("/", 1)[-1] for line in registration_lines]
    hook_names = [Path(script).name for script in profile["hooks"].values()]
    assert registered == hook_names

    modules = [SKILL / script for script in profile["hooks"].values()] + [SKILL / profile["cron"]]
    for module in modules:
        values = []
        for line in module.read_text().splitlines():
            if not line.startswith("TIMEOUT_MS"):
                continue
            tail = line[len("TIMEOUT_MS"):].lstrip(" \t")
            if tail.startswith(": int"):
                tail = tail[len(": int"):].lstrip(" \t")
            if not tail.startswith("="):
                continue
            value = tail[1:].split("#", 1)[0].strip()
            assert value.isascii() and value.isdecimal(), f"invalid TIMEOUT_MS in {module}: {line}"
            values.append(int(value))
        assert len(values) == 1, f"expected exactly one TIMEOUT_MS in {module}, found {values}"
        assert 0 < values[0] <= 2500, f"TIMEOUT_MS exceeds registrar cap in {module}: {values[0]}"
