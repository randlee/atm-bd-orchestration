"""Set package test import paths and run skill suites against an installed copy."""
import sys
import tomllib
from pathlib import Path

PKG = Path(__file__).resolve().parent
for path in (PKG, PKG / "tests", PKG / "skills/atm-bd-orchestration/scripts/tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

def _profile_suites(package: Path) -> list[str]:
    names = {tomllib.loads(path.read_text(encoding="utf-8")).get("name")
             for path in (package / "skills").glob("*/profile.toml")}
    tests = package / "tests"
    return [f"tests/{path.name}" for path in sorted(tests.iterdir()) if path.is_dir() and path.name in names]


collect_ignore = ["skills", "agents", *_profile_suites(PKG)]
