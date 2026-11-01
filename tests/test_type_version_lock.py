# pyright: strict
"""The shared crate and all Python consumers track the release version."""
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_shared_type_versions_and_consumers_match_release() -> None:
    version = tomllib.loads((ROOT / "release-version.toml").read_text())["project"]["version"]
    crate = tomllib.loads((ROOT / "crates/atm-bd-types/Cargo.toml").read_text())
    wheel = tomllib.loads((ROOT / "crates/atm-bd-types/pyproject.toml").read_text())
    console = tomllib.loads((ROOT / "apps/atm-bd-console/pyproject.toml").read_text())
    expected = f"atm-bd-types=={version}"
    assert crate["package"]["version"] == version
    assert wheel["project"]["version"] == version
    assert [dep for dep in console["project"]["dependencies"] if dep.startswith("atm-bd-types")] == [expected]
    package = ROOT / "plugins/atm-bd-orchestration"
    scripts = [p for p in package.rglob("*") if p.is_file() and p.read_bytes().startswith(b"#!/usr/bin/env -S uv run --script\n")]
    assert scripts
    for script in scripts:
        header = script.read_text().splitlines()[2:4]
        metadata = tomllib.loads("\n".join(line.removeprefix("# ") for line in header))
        assert [dep for dep in metadata["dependencies"] if dep.startswith("atm-bd-types")] == [expected], script
    assert expected in (package / "installer_common.py").read_text()
