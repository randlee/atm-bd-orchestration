"""Contract tests for the standalone atm-bd-lite profile assets."""
import importlib.util
import json
import re
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest

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


@dataclass(frozen=True)
class _Layer:
    branch: str
    head: str
    pr: int
    base: str


class _Store:
    def __init__(self, *beads, target=None) -> None:
        self.beads = {bead.id: bead for bead in beads}
        self.target = target

    def show(self, bead_id: str):
        return self.beads.get(bead_id)

    def target_layer(self, bead):
        return self.target

    def update(self, patch, actor: str):
        return None


def _load_close_hook(monkeypatch: pytest.MonkeyPatch) -> tuple[ModuleType, ModuleType]:
    test_types_path = Path(__file__).parent / "lite" / "fake_atm_bd_types.py"
    types_spec = importlib.util.spec_from_file_location("lite_profile_test_types", test_types_path)
    assert types_spec and types_spec.loader
    test_types = importlib.util.module_from_spec(types_spec)
    monkeypatch.setitem(sys.modules, types_spec.name, test_types)
    types_spec.loader.exec_module(test_types)
    monkeypatch.setitem(sys.modules, "atm_bd_types", test_types)

    hook_path = SKILL / "scripts" / "atm-bd-task-hook.py"
    hook_spec = importlib.util.spec_from_file_location("lite_profile_task_close_hook", hook_path)
    assert hook_spec and hook_spec.loader
    hook = importlib.util.module_from_spec(hook_spec)
    hook_spec.loader.exec_module(hook)
    return hook, test_types


def _close_action_vars(action) -> dict[str, object]:
    value = action.vars
    if isinstance(value, str):
        return {"reason": value}
    if hasattr(value, "findings"):
        return {"sha": value.sha, "ids": [finding.id for finding in value.findings]}
    if hasattr(value, "sha"):
        return {"sha": value.sha}
    return {name: getattr(value, name) for name in ("branch", "head", "pr", "base")}


def _hook_close_actions(hook: ModuleType, T: ModuleType) -> list:
    layer = _Layer("feature/x", "a" * 40, 42, "main")
    stack = T.Bead("stack", layers={layer.branch: layer})
    phases = type("Phases", (), {"load": lambda self, path, profile: T.PhaseFile(lead="lead")})()

    def run(bead, request, *extra, target=None):
        store = _Store(bead, stack, *extra, target=target)
        reply = hook.hook(request, store, phases)
        assert reply.kind == "handled", reply
        assert len(reply.actions) == 1
        return reply.actions[0]

    dev = T.Bead("dev-task", T.Status.IN_PROGRESS, assignee="dev", branch=layer.branch,
                 stack_bead="stack", sprint="sprint-10", phase="bo")
    refused = T.HookRequest(caller="dev", task_id="dev-task", outcome="refused", close_reason="blocked")
    completed = T.HookRequest(caller="dev", task_id="dev-task", outcome="completed", close_report="complete")
    qa = T.Bead("qa-task", T.Status.IN_PROGRESS, assignee="qa", stage="qa", stack_bead="stack",
                sprint="sprint-10", phase="bo")
    passed = T.HookRequest(caller="qa", task_id="qa-task", outcome="completed", verdict="PASS",
                           verdict_sha=layer.head)
    findings = T.HookRequest(caller="qa", task_id="qa-task", outcome="completed", verdict="FINDINGS",
                             verdict_sha=layer.head, findings=[T.Finding("F-1", True), T.Finding("F-2", False)])
    poured = [T.Bead("F-1", blocks_ids=["sprint-10"]), T.Bead("F-2", blocks_ids=["bo"])]
    return [
        run(dev, refused),
        run(dev, completed),
        run(qa, passed, target=layer),
        run(qa, findings, *poured, target=layer),
    ]


def test_close_templates_strictly_render_vars_from_hook_actions(monkeypatch: pytest.MonkeyPatch,
                                                                 tmp_path: Path) -> None:
    hook, test_types = _load_close_hook(monkeypatch)
    actions = _hook_close_actions(hook, test_types)
    assert len(actions) == 4
    assert [Path(action.template).name for action in actions] == [
        "refuse.md", "dev-close.md", "qa-pass.md", "qa-findings.md",
    ]

    for action in actions:
        template = TEMPLATES / f"{Path(action.template).name}.j2"
        variables = _close_action_vars(action)
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
    assert [item.strip() for item in match.group(1).split(",")] == ["task_id", "phase", "profile"]
    rendered = _run_with_timeout(
        ["sc-compose", "render", "--strict", "--file", str(template),
         "--var", "task_id=bo-14-qa", "--var", "phase=bo", "--var", "profile=atm-bd-lite"],
        timeout=10,
        check=True,
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


def test_copied_behavior_suite_runs_isolated_and_reports_67_passes(tmp_path: Path) -> None:
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
    assert test_count == 67, f"expected 67 nested tests, got {test_count}\n{details}"


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
