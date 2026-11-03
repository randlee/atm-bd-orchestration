"""Shared helpers: one way to load a hook, one fake store, one fake phase file, one runner."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import fake_atm_bd_types as T  # noqa: E402

SCRIPTS = HERE.parent.parent / "skills" / "atm-bd-lite" / "scripts"
LEAD, DEV, QA = "lead", "dev", "qa"


def load_hook(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    previous = sys.modules.get("atm_bd_types")
    sys.modules["atm_bd_types"] = T
    try:
        spec.loader.exec_module(mod)
    finally:
        if previous is None:
            sys.modules.pop("atm_bd_types", None)
        else:
            sys.modules["atm_bd_types"] = previous
    return mod


class FakeStore:
    """BeadStore over a dict; records every write; can be told to fail the next write (BEAD_RACED)."""

    def __init__(self, *beads: T.Bead, target: T.Layer | T.Refusal | None = None, race: bool = False) -> None:
        self.beads = {b.id: b for b in beads}
        self.target, self.race = target, race
        self.refreshes: list[list[str]] = []
        self.writes: list[tuple[str, str, object, str]] = []  # (kind, bead id, arg, actor)

    def refresh(self, bead_ids: list[str]) -> T.Refusal | None:
        self.refreshes.append(bead_ids)
        return None

    def show(self, bead_id: str) -> T.Bead | T.Refusal:
        return self.beads.get(bead_id) or T.Refusal(T.ErrorId.BEAD_NOT_FOUND, bead=bead_id)

    def target_layer(self, qa_bead: T.Bead) -> T.Layer | T.Refusal:
        return self.target if self.target is not None else T.Refusal(T.ErrorId.QA_NOTHING_TO_REVIEW, bead=qa_bead.id)

    def update(self, patch: T.BeadPatch, actor: str) -> T.Refusal | None:
        self.writes.append((patch.kind, patch.snapshot.id, patch.arg, actor))
        return T.Refusal(T.ErrorId.BEAD_RACED, bead=patch.snapshot.id) if self.race else None


class FakePhases:
    def __init__(self, lead: str = LEAD, profile: str = "lite", readable: bool = True) -> None:
        self.lead, self.profile, self.readable = lead, profile, readable

    def load(self, path: str, profile: str) -> T.PhaseFile | T.Refusal:
        if not self.readable:
            return T.Refusal(T.ErrorId.PHASE_UNREADABLE, path=path)
        if profile != self.profile:
            return T.Refusal(T.ErrorId.PROFILE_MISMATCH, path=path, profile=self.profile)
        return T.PhaseFile(lead=self.lead)


@pytest.fixture(scope="session")
def hooks() -> dict[str, ModuleType]:
    return {n: load_hook(f"atm-bd-task-{n}") for n in ("assign-hook", "start-hook", "hook")}


def expect_refused(reply: T.HookReply, code: T.ErrorId, store: FakeStore, writes: int = 0) -> None:
    assert reply.kind == "refused", reply
    assert reply.refusal is not None and reply.refusal.id is code, reply
    assert len(store.writes) == writes, store.writes
