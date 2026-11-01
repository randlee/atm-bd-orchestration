# pyright: strict
"""Both provider variants render the lite templates through the profile gate."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from atm_bd_types import Error, ErrorKind, Profile
from result import Err, Ok, Result

ROOT = Path(__file__).parents[6]
CORE = ROOT / "plugins/atm-bd-orchestration/core/scripts"
sys.path.insert(0, str(CORE))
import sc_render
from sprint_index_common import LITE_TEMPLATES

TEMPLATES = ROOT / "plugins/atm-bd-orchestration/skills/atm-bd-lite/templates"
PACKAGE = ROOT / "plugins/atm-bd-orchestration"


@pytest.mark.parametrize("emitted_path", LITE_TEMPLATES.values())
def test_every_emitted_lite_template_path_exists_in_package(emitted_path: str) -> None:
    relative = Path(emitted_path)
    if relative.parts[:3] == (".claude", "skills", "atm-bd-lite"):
        source = PACKAGE / "skills/atm-bd-lite/templates" / relative.name
    else:
        source = PACKAGE / "core/templates" / relative.name
    assert source.is_file(), f"{emitted_path} is not shipped; expected {source}"


@pytest.mark.parametrize("provider", ["github", "azure"])
@pytest.mark.parametrize("name", ["dev-template.xml.j2", "fix-assignment.xml.j2", "qa-template.xml.j2"])
def test_lite_assignment_templates_render_for_both_providers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, provider: str, name: str
) -> None:
    def allow_profile(_phase_file: Path, _expected: Profile) -> Result[Profile]:
        return Ok(Profile.LITE)

    monkeypatch.setattr(sc_render, "require_profile", allow_profile)
    path = TEMPLATES / name
    header = sc_render.render_dispatch
    variables: dict[str, Any] = {
        "provider": {"name": provider,
                     "create": "gh pr create --base '{base}' --head '{head}' --title '{title}' --body-file '{body_file}'" if provider == "github" else "az repos pr create --source-branch '{head}' --target-branch '{base}' --title '{title}' --description @{body_file} --output json",
                     "view": "gh pr view '{number}'" if provider == "github" else "az repos pr show --id '{number}'",
                     "comment": "gh pr comment '{number}'" if provider == "github" else "az repos pr update --id '{number}'",
                     "checks": "gh pr checks '{number}'" if provider == "github" else "az repos pr policy list --id '{number}'",
                     "stack_view": "gh stack view '{stack_bead}'" if provider == "github" else "az repos list"},
        "task_id": "atm-phase-lt.dev-1", "sprint": "lt-1", "phase": "lt",
        "worktree_path": "/tmp/work", "branch": "feature/lite", "pr_target": "main",
        "test_command": "just test", "lint_command": "just lint", "finding": "qa finding",
        "commit": "a" * 40, "pr_number": "123", "pr_url": "https://example.invalid/pr/123",
    }
    rendered = header(path, variables, tmp_path / "phase.toml", Profile.LITE)
    assert isinstance(rendered, Ok)
    if name in ("dev-template.xml.j2", "fix-assignment.xml.j2"):
        assert "provider-commands" in rendered.value
        assert "feature/lite" in rendered.value
        assert "--title \"<one-line title>\"" in rendered.value
        assert "<scratch>/atm-phase-lt.dev-1-pr-body.md" in rendered.value
        if provider == "github":
            assert "gh pr create" in rendered.value
        else:
            assert "az repos pr create" in rendered.value
            assert "--target-branch <top>" in rendered.value
    if provider == "azure":
        assert "gh " not in rendered.value


def test_full_profile_template_render_returns_typed_mismatch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mismatch = Err(Error(ErrorKind.PROFILE_MISMATCH, "wrong profile", "use full template"))

    def reject_profile(_phase_file: Path, _expected: Profile) -> Result[Profile]:
        return mismatch

    monkeypatch.setattr(sc_render, "require_profile", reject_profile)
    rendered = sc_render.render_dispatch(TEMPLATES / "dev-template.xml.j2", {}, tmp_path / "phase.toml", Profile.LITE)
    assert isinstance(rendered, Err)
    assert rendered.error.kind is ErrorKind.PROFILE_MISMATCH
