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

TEMPLATES = ROOT / "plugins/atm-bd-orchestration/skills/atm-bd-lite/templates"


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
        "provider": {"name": provider}, "task_id": "atm-phase-lt.dev-1", "sprint": "lt-1",
        "worktree_path": "/tmp/work", "branch": "feature/lite", "pr_target": "main",
        "test_command": "just test", "lint_command": "just lint", "finding": "qa finding",
        "commit": "a" * 40, "pr_number": "123", "pr_url": "https://example.invalid/pr/123",
    }
    rendered = header(path, variables, tmp_path / "phase.toml", Profile.LITE)
    assert isinstance(rendered, Ok)
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
