# pyright: strict
"""The console's Azure flag installs and renders an Azure-configured skill."""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest
import sc_render
import yaml
from providers import render_context
from result import Ok

from atm_bd_console import skill, skill_integrity, skill_source

PACKAGE = Path(__file__).resolve().parents[3] / "plugins/atm-bd-orchestration"
EXAMPLES = PACKAGE / "skills/atm-bd-orchestration/examples"


def test_azure_install_writes_identity_and_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "path", [str(PACKAGE), *sys.path])
    spec = importlib.util.spec_from_file_location("_azure_test_installer", PACKAGE / "install.py")
    assert spec is not None and spec.loader is not None
    install = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, install)
    spec.loader.exec_module(install)
    installer_common = importlib.import_module("installer_common")
    installer_execution = importlib.import_module("installer_execution")
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
