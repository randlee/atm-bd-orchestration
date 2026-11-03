"""The generated stubs: current with the Rust, true to the runtime, and equal to the contract ignoring whitespace."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest
from conftest import CRATE

import gen_stubs

CONTRACT = CRATE / "tests" / "fixtures" / "contract"  # copies of atm-core docs/plans/phase-bo/contract/*.pyi


def framework_matches_contract(contract: str, generated: str) -> bool:
    """Preserve every contract AST node; permit only the two approved framework functions."""
    expected = ast.parse(contract).body
    actual = ast.parse(generated).body
    additions = {"patch_json", "stack_of"}
    filtered = []
    for node in actual:
        if isinstance(node, ast.FunctionDef) and node.name in additions:
            additions.remove(node.name)
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "atm_bd_types":
            allowed = {"BeadPatch", "Stack"}
            node.names = [name for name in node.names if name.name not in allowed]
        filtered.append(node)
    return not additions and [ast.dump(node) for node in filtered] == [ast.dump(node) for node in expected]


@pytest.mark.parametrize("name", sorted(gen_stubs.MODULES))
def test_checked_in_stub_is_generated_from_the_rust(name: str) -> None:
    assert (gen_stubs.STUBS / f"{name}.pyi").read_text(encoding="utf-8") == gen_stubs.stub_text(name), (
        "stale; run: uv run --frozen --no-editable python gen_stubs.py")


@pytest.mark.parametrize("name", sorted(gen_stubs.MODULES))
def test_stub_names_exactly_the_runtime_surface(name: str) -> None:
    module = importlib.import_module(gen_stubs.MODULES[name])
    assert gen_stubs.surface_mismatches(gen_stubs.stub_text(name), module) == []


def test_plugin_stub_equals_contract_exactly() -> None:
    assert (gen_stubs.STUBS / "atm_bd_types.pyi").read_bytes() == (CONTRACT / "atm_bd_types.pyi").read_bytes()


def test_framework_stub_contains_unchanged_contract() -> None:
    contract = (CONTRACT / "atm_bd_core.pyi").read_text(encoding="utf-8")
    generated = (gen_stubs.STUBS / "atm_bd_core.pyi").read_text(encoding="utf-8")
    assert framework_matches_contract(contract, generated)


def test_framework_comparison_rejects_contract_changes_and_unapproved_additions() -> None:
    contract = (CONTRACT / "atm_bd_core.pyi").read_text(encoding="utf-8")
    generated = (gen_stubs.STUBS / "atm_bd_core.pyi").read_text(encoding="utf-8")
    assert not framework_matches_contract(contract, generated.replace("class Ports:", "class ChangedPorts:"))
    assert not framework_matches_contract(contract, generated + "\ndef unexpected() -> None: ...\n")
    assert not framework_matches_contract(contract, generated.replace("    cache: BeadsCache", "    cache: str"))


def test_surface_check_catches_a_missing_binding() -> None:
    module = importlib.import_module("atm_bd_types")
    stub = gen_stubs.stub_text("atm_bd_types") + "\n@typing.final\nclass Ghost:\n    def haunt(self) -> None: ...\n"
    assert gen_stubs.surface_mismatches(stub, module) == [
        "Ghost: in the stub, not in atm_bd_types", "Ghost: in the stub, not in atm_bd_types.__all__"]


def test_surface_check_catches_a_missing_member() -> None:
    module = importlib.import_module("atm_bd_types")
    stub = gen_stubs.stub_text("atm_bd_types").replace("    CLOSED = ...\n", "    CLOSED = ...\n    REOPENED = ...\n", 1)
    assert gen_stubs.surface_mismatches(stub, module) == ["Status.REOPENED: in the stub, not on the binding"]



def test_contract_copies_are_present() -> None:
    assert sorted(p.name for p in CONTRACT.iterdir()) == ["atm_bd_core.pyi", "atm_bd_types.pyi"]
    assert Path(CRATE / "stubs").is_dir()
