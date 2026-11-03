"""The generated stubs: current with the Rust, true to the runtime, and equal to the contract ignoring whitespace."""

from __future__ import annotations

import difflib
import importlib
import re
from pathlib import Path

import pytest
from conftest import CRATE

import gen_stubs

CONTRACT = CRATE / "tests" / "fixtures" / "contract"  # copies of atm-core docs/plans/phase-bo/contract/*.pyi


def without_whitespace(text: str) -> list[str]:
    """One entry per non-blank line, with every whitespace character removed."""
    return [re.sub(r"\s+", "", line) for line in text.splitlines() if line.strip()]


@pytest.mark.parametrize("name", sorted(gen_stubs.MODULES))
def test_checked_in_stub_is_generated_from_the_rust(name: str) -> None:
    assert (gen_stubs.STUBS / f"{name}.pyi").read_text(encoding="utf-8") == gen_stubs.stub_text(name), (
        "stale; run: uv run --frozen --no-editable python gen_stubs.py")


@pytest.mark.parametrize("name", sorted(gen_stubs.MODULES))
def test_stub_names_exactly_the_runtime_surface(name: str) -> None:
    module = importlib.import_module(gen_stubs.MODULES[name])
    assert gen_stubs.surface_mismatches(gen_stubs.stub_text(name), module) == []


@pytest.mark.parametrize("name", sorted(gen_stubs.MODULES))
def test_stub_equals_contract_ignoring_whitespace(name: str) -> None:
    generated = without_whitespace((gen_stubs.STUBS / f"{name}.pyi").read_text(encoding="utf-8"))
    contract = without_whitespace((CONTRACT / f"{name}.pyi").read_text(encoding="utf-8"))
    diff = "\n".join(difflib.unified_diff(contract, generated, "contract", "generated", lineterm=""))
    assert generated == contract, diff


def test_surface_check_catches_a_missing_binding() -> None:
    module = importlib.import_module("atm_bd_types")
    stub = gen_stubs.stub_text("atm_bd_types") + "\n@typing.final\nclass Ghost:\n    def haunt(self) -> None: ...\n"
    assert gen_stubs.surface_mismatches(stub, module) == [
        "Ghost: in the stub, not in atm_bd_types", "Ghost: in the stub, not in atm_bd_types.__all__"]


def test_surface_check_catches_a_missing_member() -> None:
    module = importlib.import_module("atm_bd_types")
    stub = gen_stubs.stub_text("atm_bd_types").replace("    CLOSED = ...\n", "    CLOSED = ...\n    REOPENED = ...\n", 1)
    assert gen_stubs.surface_mismatches(stub, module) == ["Status.REOPENED: in the stub, not on the binding"]


def test_whitespace_normalisation_keeps_every_other_difference() -> None:
    assert without_whitespace("a:  int\n\n  b = ...\n") == without_whitespace("a: int\nb = ...")
    assert without_whitespace("a: int\n") != without_whitespace("a: str\n")


def test_contract_copies_are_present() -> None:
    assert sorted(p.name for p in CONTRACT.iterdir()) == ["atm_bd_core.pyi", "atm_bd_types.pyi"]
    assert Path(CRATE / "stubs").is_dir()
