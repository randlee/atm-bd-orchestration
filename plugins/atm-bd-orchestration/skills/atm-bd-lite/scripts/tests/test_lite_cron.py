# pyright: strict
"""Exercise the installed ``atm-bd cron`` dispatch with a fixed queue fixture."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from atm_bd_types import Profile
from atm_bd_console import atm_bd, cli, queues
from atm_bd_console.command import Output
from result import Ok, Result

ROOT = Path(__file__).parents[6]
SCRIPT = ROOT / "plugins/atm-bd-orchestration/skills/atm-bd-lite/scripts/lite_cron.py"
FIXTURE = Path(__file__).parent / "fixtures/lite-tick.json"


class Cache:
    def __init__(self) -> None:
        self.phases: list[str] = []

    def sync(self, phase: str) -> None:
        self.phases.append(phase)


def test_atm_bd_cron_invokes_lite_tick_with_deterministic_queue_fixture(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    phase = tmp_path / ".atm-bd/phase-lt.toml"
    phase.parent.mkdir()
    phase.write_text('profile = "lite"\n', encoding="utf-8")
    installed = tmp_path / ".claude/skills/atm-bd-lite"
    (installed / "formulas").mkdir(parents=True)
    scripts = installed / "scripts"
    scripts.mkdir()
    shutil.copyfile(SCRIPT, scripts / SCRIPT.name)
    core_scripts = tmp_path / ".atm-bd/scripts"
    core_scripts.mkdir(parents=True)
    shutil.copyfile(ROOT / "plugins/atm-bd-orchestration/core/scripts/core_paths.py", core_scripts / "core_paths.py")
    monkeypatch.setattr(cli.config_source, "repo_root", lambda: tmp_path)

    core_path = ROOT / "plugins/atm-bd-orchestration/core/scripts"
    sys.path.insert(0, str(core_path))
    import phase_profile

    def allow_profile(_path: Path, _profile: Profile) -> Result[Profile]:
        return Ok(Profile.LITE)

    def phase_file(*_args: Any, **_kwargs: Any) -> Any:
        return Ok(SimpleNamespace(root_id="atm-phase-lt"))

    def queue_report(*_args: Any, **_kwargs: Any) -> Any:
        return {"queues": fixture["queues"], "generated_at": fixture["generated_at"]}

    monkeypatch.setattr(phase_profile, "require_profile", allow_profile)
    monkeypatch.setattr(atm_bd, "phase_file", phase_file)
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    monkeypatch.setattr(queues, "build", queue_report)
    cache = Cache()

    def fake_queue_runner(*_args: Any, **_kwargs: Any) -> Any:
        return Ok(Output(0, "[]"))

    def invoke(argv: list[str], _fix: str, *, cwd: str | Path | None = None) -> Any:
        assert cwd == tmp_path
        assert argv[0] == sys.executable and Path(argv[1]) == scripts / "lite_cron.py"
        spec = importlib.util.spec_from_file_location("invoked_lite_cron", argv[1])
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        error, output = module.tick(tmp_path, argv[3], cache=cache, queue_runner=fake_queue_runner)
        assert error is None
        return Ok(Output(0, "" if output is None else json.dumps(output)))

    monkeypatch.setattr(cli.command_source, "run", invoke)
    assert cli.main(["cron", "--phase", "lt"]) == 0
    emitted = json.loads(capsys.readouterr().out)
    assert emitted["queues"] == fixture["queues"]
    assert cache.phases == ["lt"]
