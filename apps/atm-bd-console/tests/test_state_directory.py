"""Reported bug: the console locks its state directory as atm-phase-<x> while the phase file's root id
carries the repo's bead prefix (myp-phase-<x>). Does a cache written through the lock come back on the next tick?

Controlled inputs only: fixed clock, recorded gh boundary, a real on-disk state store.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from contract_samples import PHASE_FILE
from test_stack_cadence import T0, World, tick

from atm_bd_console.types import State

PREFIXES = pytest.mark.parametrize("root_id", ("atm-phase-bk", "myp-phase-bk"))
LOCK_ID = "atm-phase-bk"  # cli.py: root_id = f"atm-phase-{args.phase}"


@PREFIXES
def test_any_prefix_running_ticks_refresh_github_once_per_poll_interval(monkeypatch, tmp_path, root_id) -> None:
    world = World(monkeypatch, replace(PHASE_FILE, root_id=root_id), LOCK_ID)
    calls: list[str] = world.calls

    for seconds in range(0, 1260, 60):  # 21 one-minute ticks, polls due at 0s, 600s and 1200s
        world.now = T0 + timedelta(seconds=seconds)
        tick(world, tmp_path)

    assert calls == ["stack", "prs"] * 3


@PREFIXES
def test_any_prefix_stopped_tick_reads_the_caches_the_running_ticks_wrote(monkeypatch, tmp_path, root_id) -> None:
    world = World(monkeypatch, replace(PHASE_FILE, root_id=root_id), LOCK_ID)
    running, _ = tick(world, tmp_path)
    assert [row.pr.number for row in running.prs] == [1, 2]

    world.root_closed = True
    world.now = T0 + timedelta(seconds=60)
    stopped, _ = tick(world, tmp_path, state=State((), None, None, None, None, (), (), {}))

    assert stopped.stopped == "closed"
    assert [row.pr.number for row in stopped.prs] == [1, 2], "the stopped view must show the cached PR rows"
    assert world.calls == ["stack", "prs"], "a stopped tick makes no GitHub call"
