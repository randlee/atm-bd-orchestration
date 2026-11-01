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
