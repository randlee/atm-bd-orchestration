# pyright: strict
"""Structural guards for the pure and exhaustive transition planner."""
from __future__ import annotations

import ast

from helpers import HOOK


def test_hook_imports_only_contract_types_and_has_one_match_arm_per_transition() -> None:
    source = HOOK.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= {"__future__", "dataclasses", "typing", "atm_bd_types"}
    transitions = {"DEV_CLOSE", "FIX_CLOSE", "QA_PASS", "QA_FAIL", "REFUSED"}
    arms = {
        node.pattern.value.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.match_case)
        and isinstance(node.pattern, ast.MatchValue)
        and isinstance(node.pattern.value, ast.Attribute)
        and isinstance(node.pattern.value.value, ast.Name)
        and node.pattern.value.value.id == "Transition"
    }
    assert arms == transitions
    assert len(source.splitlines()) < 400
