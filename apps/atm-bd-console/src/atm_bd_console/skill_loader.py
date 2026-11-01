# pyright: strict
"""Resolve and cache shared core scripts for console adapters."""
from __future__ import annotations

import importlib.util
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import NoReturn

from core_paths import core_scripts_dir, core_templates_dir
from result import Err


def _not_found(repo_root: str) -> NoReturn:
    raise RuntimeError(f"CORE.NOT_FOUND: install atm-bd skill --dest {repo_root}")


@cache
def load_skill(repo_root: str, script: str, required: str = "") -> tuple[ModuleType, Path]:
    scripts = core_scripts_dir(Path(repo_root))
    templates = core_templates_dir(Path(repo_root))
    if isinstance(scripts, Err):
        scripts = core_scripts_dir()
    if isinstance(templates, Err):
        templates = core_templates_dir()
    if isinstance(scripts, Err) or isinstance(templates, Err):
        _not_found(repo_root)
    name = Path(script).name
    path = scripts.value / name
    if not path.is_file() or (required and not (templates.value / Path(required).name).is_file()):
        raise RuntimeError(f"core script or required resource is not installed: {script}")
    spec = importlib.util.spec_from_file_location(f"atm_bd_skill_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load core script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, templates.value
