# pyright: strict
"""Provider rendering preserves the captured GitHub contract and fills Azure commands."""
from __future__ import annotations

import base64
import json
import os
import sys
import re
from pathlib import Path
from typing import cast

import sc_render
from providers import render_context
from result import Ok

CONSOLE_SRC = os.environ.get("ATM_BD_CONSOLE_SRC")
PACKAGE = (Path(CONSOLE_SRC).resolve().parents[2] / "plugins/atm-bd-orchestration"
           if CONSOLE_SRC else Path(__file__).resolve().parents[4])
if str(PACKAGE) not in sys.path:
    sys.path.insert(0, str(PACKAGE))
EXAMPLES = PACKAGE / "skills/atm-bd-orchestration/examples"
TEMPLATES = {
    "dev-template": PACKAGE / "skills/atm-bd-orchestration/templates/dev-template.xml.j2",
    "fix-assignment": PACKAGE / "skills/atm-bd-orchestration/templates/fix-assignment.xml.j2",
    "qa-template": PACKAGE / "core/templates/qa-template.xml.j2",
}


def _render(name: str, provider: str) -> str:
    context = render_context({"provider": provider, "azure": {"organization": "org", "project": "project", "repository": "repo"}})
    assert isinstance(context, Ok)
    values = cast(dict[str, object], json.loads((EXAMPLES / f"{name}-vars.json").read_text()))
    values["provider"] = context.value
    return sc_render.render(TEMPLATES[name], values)


def test_github_renders_match_bo2_golden_except_stack_view_and_checks() -> None:
    for name in TEMPLATES:
        golden = base64.b64decode((EXAMPLES / f"provider-github-{name}.golden").read_text()).decode()
        if name == "qa-template":
            golden = golden.replace("`sc-gh-stack-view` skill", "`gh stack view --json` command")
            golden = golden.replace("gh pr checks 231 --json name,state,bucket", "gh api 'repos/{owner}/{repo}/commits/4f1c2a9e7b3d5f60812a4c9e0b7d3f5a1c2e4b6d/check-runs'")
        else:
            golden = golden.replace("`/sc-gh-stack-view` (read-only)", "`gh stack view --json` (read-only)")
        assert _render(name, "github") == golden


def test_azure_templates_use_provider_operations_and_fill_placeholders() -> None:
    for name in TEMPLATES:
        text = _render(name, "azure")
        assert "gh " not in text
        assert not re.search(r"\{(?:base|head|title|body_file|number|text)\}", text)
        assert "bd show <stack-bead> --json" in text
        if name != "qa-template":
            assert "az repos pr create" in text
            assert "sanity-stack records the layer in the stack bead" in text
        else:
            assert ".atm-bd/scripts/providers.py exec comment" in text


def test_installer_resolves_provider_and_azure_identity(tmp_path: Path) -> None:
    import installer_common
    import pytest

    installer_common.load_validation_dependencies()

    registry = tmp_path / ".claude/agents/registry.yaml"
    registry.parent.mkdir(parents=True)
    registry.write_text("azure:\n  organization: org\n  project: project\n  repository: repo\n")
    default = installer_common.resolve_config(tmp_path, {})
    assert default["provider"] == "github"
    values = installer_common.resolve_config(tmp_path, {"provider": "azure"})
    assert values["provider"] == "azure"
    assert [values[f"azure_{key}"] for key in ("organization", "project", "repository")] == ["org", "project", "repo"]
    import yaml
    values.update({"bead_prefix": "demo", "dev_sanity_member": "sanity", "qa_member": "qa",
                   "team_lead_member": "lead", "worktree_base": "/tmp/worktrees", "test_command": "just test",
                   "lint_command": "just lint", "integration_branch_pattern": "integrate/phase-{phase}",
                   "plans_dir": "docs/plans", "requirements_globs": ["docs/req.md"], "adr_globs": ["docs/adr.md"],
                   "policy_path": "policy.md", "reviewers_round1": ["qa"]})
    config = cast(dict[str, object], yaml.safe_load(installer_common.render_config(values)))
    assert config["provider"] == "azure"
    assert config["azure"] == {"organization": "org", "project": "project", "repository": "repo"}
    with pytest.raises(installer_common.InstallError, match="PROVIDER_INVALID"):
        installer_common.resolve_config(tmp_path, {"provider": "other"})
    registry.write_text("azure:\n  organization: org\n  project: project\n")
    with pytest.raises(installer_common.InstallError, match="CONFIG_MISSING.*azure.repository"):
        installer_common.resolve_config(tmp_path, {"provider": "azure"})


def test_azure_layered_qa_has_no_unfilled_view_placeholders() -> None:
    context = render_context({"provider": "azure", "azure": {"organization": "org", "project": "project", "repository": "repo"}})
    assert isinstance(context, Ok)
    values = cast(dict[str, object], json.loads((EXAMPLES / "qa-template-vars.json").read_text()))
    values.update({"provider": context.value, "layer_prs": ["42"]})
    text = sc_render.render(TEMPLATES["qa-template"], values)
    assert "{jq}" not in text and "{fields}" not in text
    assert '"[targetRefName,lastMergeSourceCommit.commitId]"' in text
    assert "ltrimstr(\"refs/heads/\")" in text


def test_azure_install_writes_identity_and_provider(tmp_path: Path, monkeypatch: object) -> None:
    import installer_common
    import installer_execution
    import install
    import pytest
    import yaml
    from collections.abc import Generator
    from contextlib import contextmanager
    from types import ModuleType
    from atm_bd_console import skill, skill_integrity, skill_source

    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    installer_common.load_validation_dependencies()
    registry = tmp_path / ".claude/agents/registry.yaml"
    registry.parent.mkdir(parents=True)
    registry.write_text("""bead_prefix: test
worktree_base: /tmp/worktrees
test_command: just test
lint_command: just lint
integration_branch_pattern: integrate/phase-{phase}
plans_dir: docs/plans
requirements_globs: [docs/requirements.md]
adr_globs: [docs/adr.md]
policy_path: policy.md
reviewers_round1: [qa]
roles:
  dev-sanity: sanity
  quality-mgr: qa
  lead: lead
azure:
  organization: org
  project: project
  repository: repo
""")
    (registry.parent / "qa.md").write_text("---\nname: qa\n---\n")
    beads = tmp_path / ".beads/metadata.json"
    beads.parent.mkdir()
    beads.write_text('{"backend":"dolt","dolt_mode":"server"}')
    def git_origin(_root: Path) -> str:
        return "owner/repo"

    def provision(_root: Path) -> bool:
        return False

    monkeypatch.setattr(installer_common, "_git_origin_slug", git_origin)
    monkeypatch.setattr(installer_execution, "provision_tool_identity", provision)
    def installer() -> ModuleType:
        return install

    def check_tools() -> None:
        return None

    manifest = skill_integrity.build_manifest(PACKAGE, installer_common.package_version(PACKAGE))

    @contextmanager
    def source(*, version: str | None = None, latest: bool = False) -> Generator[skill_source.SkillSource, None, None]:
        assert version is None and not latest
        yield skill_source.SkillSource("test", PACKAGE, "a" * 40, parsed_manifest=manifest)

    monkeypatch.setattr(install, "check_tools", check_tools)
    monkeypatch.setattr(skill, "_installer", installer)
    monkeypatch.setattr(skill_source, "resolve_source", source)
    assert skill.run(["--azure", "--codex", "--dest", str(tmp_path)]) == 0
    config = cast(dict[str, object], yaml.safe_load((tmp_path / ".claude/project/atm-bd-orchestration.yaml").read_text()))
    assert config["provider"] == "azure"
    assert config["azure"] == {"organization": "org", "project": "project", "repository": "repo"}
    context = render_context(config)
    assert isinstance(context, Ok)
    values = cast(dict[str, object], json.loads((EXAMPLES / "dev-template-vars.json").read_text()))
    values["provider"] = context.value
    installed = tmp_path / ".codex/skills/atm-bd-orchestration/templates/dev-template.xml.j2"
    rendered = sc_render.render(installed, values)
    assert "az repos pr create" in rendered and "gh " not in rendered
