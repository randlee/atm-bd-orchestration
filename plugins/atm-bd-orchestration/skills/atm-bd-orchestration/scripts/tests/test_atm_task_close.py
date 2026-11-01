# pyright: strict
"""The mandatory stack check precedes every write and ATM call."""
from __future__ import annotations

from typing import Any

import pytest
from task_close_world import World


@pytest.mark.parametrize('role', ['dev', 'fix'])
def test_wrong_pr_base_refuses_before_mutation(tmp_path: Any, monkeypatch: Any, role: str) -> None:
    world: Any = World(tmp_path, monkeypatch)
    world.pr_base_override = 'wrong-base'
    result = world.run(role)
    assert result['err']['code'] == 'STACK.GATE_FAILED'
    assert 'wrong-base' in result['err']['message']
    assert 'pr edit' in result['err']['fix']
    calls: list[list[str]] = [argv for argv, _ in world.calls if argv[0] in ('bd', 'atm')]
    assert calls == [['bd', 'show', world.values['stack_bead'], '--json']]
    assert world.writes == []
