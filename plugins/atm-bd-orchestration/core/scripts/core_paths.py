# pyright: strict
"""Locate the shared core in a repository installation or a package tree."""
from __future__ import annotations

from pathlib import Path
from result import Err, NotFound, Ok, Result


def _core_dir(kind: str, start: Path | None) -> Result[Path]:
    origin = (start or Path(__file__)).resolve()
    for parent in (origin, *origin.parents):
        for candidate in (parent / '.atm-bd' / kind,
                          parent / 'plugins' / 'atm-bd-orchestration' / 'core' / kind,
                          parent / 'core' / kind):
            if candidate.is_dir() and (candidate.parent / "scripts/core_paths.py").is_file():
                return Ok(candidate)
    return Err(NotFound(kind='not_found', what=f'CORE.NOT_FOUND: {kind}',
                        fix='Run atm-bd skill --dest <repository> to install atm-bd core'))


def core_scripts_dir(start: Path | None = None) -> Result[Path]:
    return _core_dir('scripts', start)


def core_templates_dir(start: Path | None = None) -> Result[Path]:
    return _core_dir('templates', start)


def profile_formulas_dir(profile: str, start: Path | None = None) -> Result[Path]:
    """Resolve one profile's formulas from a repository install or package."""
    skill = "atm-bd-lite" if profile == "lite" else "atm-bd-orchestration"
    origin = (start or Path(__file__)).resolve()
    for parent in (origin, *origin.parents):
        for candidate in (parent / ".claude/skills" / skill / "formulas",
                          parent / ".codex/skills" / skill / "formulas",
                          parent / "plugins/atm-bd-orchestration/skills" / skill / "formulas",
                          parent / "skills" / skill / "formulas"):
            if candidate.is_dir():
                return Ok(candidate)
    return Err(NotFound(kind="not_found", what=f"CORE.NOT_FOUND: {skill} formulas",
                        fix="Run atm-bd skill --dest <repository> to install the profile"))
