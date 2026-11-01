# pyright: strict
"""Profile gates execute before cron cache work, hooks, or template rendering."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from atm_bd_types import CloseVars, ErrorKind, Transition
from result import Err, Error, Ok, Result

ROOT = Path(__file__).parents[6]
CORE = ROOT / "plugins/atm-bd-orchestration/core/scripts"
sys.path.insert(0, str(CORE))
import phase_profile
import hook_runner


def unexpected_call(*_args: Any, **_kwargs: Any) -> Any:
    pytest.fail("profile gate must prevent this call")


def reject_profile(*_args: Any, **_kwargs: Any) -> Any:
    return Err(Error(ErrorKind.PROFILE_MISMATCH, "full profile", "use the full workflow"))


def test_template_render_refuses_full_profile_before_renderer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(phase_profile, "require_profile", reject_profile)
    called = False

    def renderer(_template: Path, _variables: dict[str, object]) -> Result[str]:
        nonlocal called
        called = True
        return Ok("rendered")

    outcome = hook_runner.render_lite_template(tmp_path / "phase.toml", tmp_path / "template.j2", {}, renderer)
    assert isinstance(outcome, Err)
    assert outcome.error.kind is ErrorKind.PROFILE_MISMATCH
    assert not called


def test_hook_runner_profile_gate_precedes_hook_or_execution(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(phase_profile, "require_profile", reject_profile)
    called = False

    def executor(_argv: Any) -> Result[str]:
        nonlocal called
        called = True
        return Ok("")

    outcome = hook_runner.run_transition(tmp_path / "phase.toml", Transition.DEV_CLOSE, CloseVars(),
                                        object(), tmp_path / "absent-hook.py", executor)
    assert isinstance(outcome, Err)
    assert outcome.error.kind is ErrorKind.PROFILE_MISMATCH
    assert not called


def test_cron_profile_gate_precedes_cache_sync(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    script = ROOT / "plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/lite_cron.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("lite_cron_profile_test", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    monkeypatch.setattr(phase_profile, "require_profile", reject_profile)

    class Cache:
        def sync(self, _phase: str) -> None:
            pytest.fail("cache must not refresh before profile gate")

    outcome, output = module.tick(tmp_path, "lt", cache=Cache(), queue_runner=unexpected_call)
    assert output is None
    assert isinstance(outcome, Error)
    assert outcome.kind is ErrorKind.PROFILE_MISMATCH
