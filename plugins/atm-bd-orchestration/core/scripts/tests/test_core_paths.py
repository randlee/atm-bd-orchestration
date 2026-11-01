# pyright: strict
from pathlib import Path
from tempfile import TemporaryDirectory

from core_paths import core_scripts_dir, core_templates_dir
from result import Err, NotFound, Ok


def test_installed_and_package_layouts() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        package = root / "plugins/atm-bd-orchestration/core"
        (package / "scripts").mkdir(parents=True)
        (package / "templates").mkdir()
        (package / "scripts/core_paths.py").touch()
        assert core_scripts_dir(root) == Ok(package / "scripts")
        assert core_templates_dir(root) == Ok(package / "templates")
        (root / ".atm-bd/scripts").mkdir(parents=True)
        (root / ".atm-bd/templates").mkdir()
        (root / ".atm-bd/scripts/core_paths.py").touch()
        assert core_scripts_dir(root) == Ok(root / ".atm-bd/scripts")
        assert core_templates_dir(root) == Ok(root / ".atm-bd/templates")


def test_missing_core_gives_actionable_error() -> None:
    with TemporaryDirectory() as directory:
        result = core_scripts_dir(Path(directory))
        assert isinstance(result, Err)
        assert isinstance(result.error, NotFound)
        assert "CORE.NOT_FOUND" in result.error.what
        assert "atm-bd skill" in result.error.fix
