"""Published wheel, hook requirements, and workspace locks use one types version."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CORE = ROOT / "plugins/atm-bd-orchestration/core"
TYPES = ROOT / "crates/atm-bd-types"
LITE = ROOT / "plugins/atm-bd-orchestration/skills/atm-bd-lite"


def read_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def test_types_version_is_consistent_across_wheel_hooks_and_locks() -> None:
    version = read_toml(TYPES / "Cargo.toml")["package"]["version"]
    assert read_toml(TYPES / "pyproject.toml")["project"]["version"] == version
    dependencies = read_toml(CORE / "pyproject.toml")["project"]["dependencies"]
    assert [dep for dep in dependencies if dep.startswith("atm-bd-types")] == [f"atm-bd-types=={version}"]
    profile = read_toml(LITE / "profile.toml")
    assert set(profile["hooks"]) == {"task.assign", "task.start", "task.close"}
    for script in profile["hooks"].values():
        lines = (LITE / script).read_text(encoding="utf-8").splitlines()
        header = []
        in_script = False
        for line in lines:
            if line == "# /// script":
                in_script = True
            elif in_script and line == "# ///":
                break
            elif in_script:
                header.append(line.removeprefix("# "))
        dependencies = tomllib.loads("\n".join(header))["dependencies"]
        assert [dep for dep in dependencies if dep.startswith("atm-bd-types")] == [f"atm-bd-types=={version}"], script
    for lock in (TYPES / "uv.lock", CORE / "uv.lock", ROOT / "apps/atm-bd-console/uv.lock"):
        packages = read_toml(lock)["package"]
        [package] = [item for item in packages if item["name"] == "atm-bd-types"]
        assert package["version"] == version, lock
