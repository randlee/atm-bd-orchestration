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


@pytest.mark.parametrize('mismatch', [None, 'head', 'pr'])
def test_recorded_layer_replay_checks_its_base_and_freezes_identity(tmp_path: Any, monkeypatch: Any, mismatch: str | None) -> None:
    world: Any = World(tmp_path, monkeypatch)
    branch = world.values['branch']
    world.pr_base_override = 'integrate/phase-bj'
    world.beads[world.values['stack_bead']]['metadata']['layers'] = [{
        'branch': branch,
        'head': 'f' * 40 if mismatch == 'head' else world.head,
        'pr': 999 if mismatch == 'pr' else int(world.pr_number),
        'base': 'integrate/phase-bj', 'linked': True,
    }]
    # The top's remote tracking ref is the frozen head in this simulated world.
    world.overrides[('git', 'rev-parse', f'origin/{branch}')] = (0, 'f' * 40 if mismatch == 'head' else world.head)
    result = world.run()
    if mismatch:
        assert result['err']['code'] == 'STACK.GATE_FAILED'
        assert 'frozen' in result['err']['fix']
        assert not world.writes
    else:
        assert 'ok' in result, result
        assert any(argv == ['git', 'rev-parse', '--verify', 'refs/remotes/origin/integrate/phase-bj^{commit}']
                   for argv, _ in world.calls)
