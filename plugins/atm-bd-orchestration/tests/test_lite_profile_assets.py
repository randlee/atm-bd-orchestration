"""Contract tests for the standalone atm-bd-lite profile assets."""
import json
import re
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

import atm_bd_types as T
import pytest
from lite.lite_helpers import (
    FakePhases,
    FakeStore,
    action_template,
    action_vars,
    bead,
    hook_request,
    layer,
    load_hook,
    reply_actions,
)

SKILL = Path(__file__).resolve().parents[1] / "skills" / "atm-bd-lite"
TEMPLATES = SKILL / "templates"


def _captured_text(output: str | bytes | None) -> str:
    if output is None:
        return ""
    return output.decode(errors="replace") if isinstance(output, bytes) else output


def _run_with_timeout(
    command: list[str],
    *,
    timeout: float,
    capture_output: bool = True,
    check: bool = False,
    text: bool = True,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=capture_output, check=check, text=text, cwd=cwd,
                              timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(
            f"command {command!r} timed out after {timeout:g}s\n"
            f"partial stdout:\n{_captured_text(exc.stdout)}\n"
            f"partial stderr:\n{_captured_text(exc.stderr)}"
        ) from exc


def _hook_close_actions() -> list[dict]:
    hook = load_hook("atm-bd-task-hook")
    target = layer("feature/x", "a" * 40, 42, "main")
    stack = bead("stack", layers={target.branch: target})
    phases = FakePhases()

    def run(item, request, *extra, target_layer=None):
        reply = hook.hook(request, FakeStore(item, stack, *extra, target=target_layer), phases)
        actions = reply_actions(reply)
        assert len(actions) == 1, reply.to_json(None)
        return actions[0]

    dev = bead("dev-task", T.Status.IN_PROGRESS, assignee="dev", branch=target.branch,
               stack_bead="stack", sprint="sprint-10", phase="bo")
    refused = hook_request(caller="dev", task_id="dev-task", outcome="refused", close_reason="blocked")
    completed = hook_request(caller="dev", task_id="dev-task", outcome="completed", close_report="complete")
    qa = bead("qa-task", T.Status.IN_PROGRESS, assignee="qa", stage="qa", stack_bead="stack",
              sprint="sprint-10", phase="bo")
    passed = hook_request(caller="qa", task_id="qa-task", outcome="completed", verdict="PASS", verdict_sha=target.head)
    findings = hook_request(caller="qa", task_id="qa-task", outcome="completed", verdict="FINDINGS",
                            verdict_sha=target.head,
                            findings=[{"id": "F-1", "blocking": True}, {"id": "F-2", "blocking": False}])
    poured = [bead("F-1", blocks_ids=["sprint-10"]), bead("F-2", blocks_ids=["bo"])]
    return [run(dev, refused), run(dev, completed), run(qa, passed, target_layer=target),
            run(qa, findings, *poured, target_layer=target)]


def test_close_templates_strictly_render_vars_from_hook_actions(tmp_path: Path) -> None:
    actions = _hook_close_actions()
    assert len(actions) == 4
    assert [Path(action_template(action)).name for action in actions] == [
        "refuse.md", "dev-close.md", "qa-pass.md", "qa-findings.md",
    ]

    for action in actions:
        template = TEMPLATES / f"{Path(action_template(action)).name}.j2"
        variables = action_vars(action)
        source = template.read_text()
        match = re.search(r"^required_variables:\s*\[([^]]*)\]$", source, re.MULTILINE)
        assert match is not None
        required = {item.strip() for item in match.group(1).split(",")}
        assert set(variables) == required

        var_file = tmp_path / f"{template.name}.json"
        var_file.write_text(json.dumps(variables))
        rendered = _run_with_timeout(
            ["sc-compose", "render", "--strict", "--file", str(template), "--var-file", str(var_file)],
            timeout=10,
            check=True,
            cwd=SKILL.parents[1],
        ).stdout
        assert rendered.strip()
        assert "{{" not in rendered


def test_qa_assignment_template_strictly_renders_assign_vars() -> None:
    template = TEMPLATES / "qa.xml.j2"
    source = template.read_text()
    match = re.search(r"^required_variables:\s*\[([^]]*)\]$", source, re.MULTILINE)
    assert match is not None
    assert [item.strip() for item in match.group(1).split(",")] == ["task_id", "phase", "profile", "repo", "pr_number", "branch", "commit"]
    rendered = _run_with_timeout(
        ["sc-compose", "render", "--strict", "--file", str(template),
         "--var", "task_id=bo-14-qa", "--var", "phase=bo", "--var", "profile=atm-bd-lite",
         "--var", "repo=owner/repo", "--var", "pr_number=42", "--var", "branch=feature/x", "--var", "commit=" + "a" * 40],
        timeout=10,
        check=True,
    ).stdout
    assert '<qa-task id="bo-14-qa">' in rendered
    assert "owner/repo" in rendered and "42" in rendered
    assert "T-CLOSE-03" in rendered and "T-CLOSE-04" in rendered


@pytest.mark.parametrize(
    ("create_command", "expected"),
    [
        ("gh pr create --base '{base}' --head '{head}' --title '{title}' --body-file '{body_file}'",
         "gh pr create --base <top> --head <branch> --title <one-line title> --body-file <scratch>/bo-14-pr-body.md"),
        ("az repos pr create --source-branch '{head}' --target-branch '{base}' --title '{title}' --description @{body_file} --output json",
         "az repos pr create --source-branch <branch> --target-branch <top> --title <one-line title> --description @<scratch>/bo-14-pr-body.md --output json"),
    ],
)
def test_dev_assignment_uses_provider_create_command(create_command: str, expected: str, tmp_path: Path) -> None:
    template = TEMPLATES / "dev.xml.j2"
    variables = {
        "provider": {"create": create_command},
        "task_id": "bo-14",
        "phase": "bo",
        "profile": "atm-bd-lite",
    }
    var_file = tmp_path / "dev-vars.json"
    var_file.write_text(json.dumps(variables))
    rendered = _run_with_timeout(
        ["sc-compose", "render", "--strict", "--file", str(template), "--var-file", str(var_file)],
        timeout=10,
        check=True,
        cwd=SKILL.parents[1],
    ).stdout
    assert expected in rendered
    if create_command.startswith("az "):
        assert "gh pr create" not in rendered
    else:
        assert "gh pr create" in rendered
    assert "--repo \"$REPO\"" not in rendered


def test_policy_parameters_are_text_and_point_to_qa_template() -> None:
    policy = tomllib.loads((SKILL / "policy.toml").read_text())
    params = policy["params"]
    assert params["qa_agent"] == "quality-mgr"
    assert params["qa_template"] == "templates/qa.xml.j2"
    assert all(isinstance(value, str) for value in params.values())
    assert (SKILL / params["qa_template"]).is_file()


def test_skill_registers_each_profile_hook_once() -> None:
    profile = tomllib.loads((SKILL / "profile.toml").read_text())
    skill = (SKILL / "SKILL.md").read_text()
    assert profile["stages"] == ["dev", "qa", "land"]
    commands = [line for line in skill.splitlines() if line.startswith("atm hook register ")]
    assert len(commands) == len(profile["hooks"]) == 3
    for hook, script in profile["hooks"].items():
        assert sum(hook in command and f"--module .claude/skills/atm-bd-lite/{script}" in command for command in commands) == 1
    assert "followed by QA" in skill
    assert "does not add a sanity stage" in skill


def test_copied_behavior_suite_runs_isolated(tmp_path: Path) -> None:
    suite = Path(__file__).resolve().parent / "lite"
    junit_xml = tmp_path / "lite-suite.xml"
    result = _run_with_timeout(
        [sys.executable, "-m", "pytest", "-q", "-c", "/dev/null", "--rootdir", ".", "--confcutdir", ".",
         "--junitxml", str(junit_xml), "."],
        timeout=15,
        cwd=suite,
        check=False,
    )
    details = f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert result.returncode == 0, details
    root = ET.parse(junit_xml).getroot()
    test_count = sum(int(suite_report.attrib.get("tests", "0")) for suite_report in root.iter("testsuite"))
    assert test_count > 0, f"no nested tests ran\n{details}"


def test_subprocess_timeout_failure_includes_command_and_partial_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def expire(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert kwargs["timeout"] == 0.25
        raise subprocess.TimeoutExpired(command, 0.25, output=b"partial stdout", stderr=b"partial stderr")

    monkeypatch.setattr(subprocess, "run", expire)
    with pytest.raises(AssertionError) as raised:
        _run_with_timeout(["sc-compose", "render", "--strict"], timeout=0.25)

    message = str(raised.value)
    assert "sc-compose" in message
    assert "partial stdout" in message
    assert "partial stderr" in message



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
