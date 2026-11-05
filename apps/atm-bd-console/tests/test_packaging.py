"""The published wheel installs from PyPI alone: framework packages that are not on PyPI stay in the `lite` extra."""
import tomllib
from pathlib import Path

PROJECT = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))["project"]
FRAMEWORK = {"atm-bd-types", "atm-bd-core", "bd-cache-rs"}


def _name(requirement: str) -> str:
    return requirement.split(";")[0].split("[")[0].split("<")[0].split(">")[0].split("=")[0].split("!")[0].strip()


def test_default_dependencies_name_no_framework_package():
    assert {_name(r) for r in PROJECT["dependencies"]} & FRAMEWORK == set()


def test_the_lite_extra_declares_the_framework():
    assert {_name(r) for r in PROJECT["optional-dependencies"]["lite"]} == {"atm-bd-types", "atm-bd-core"}
