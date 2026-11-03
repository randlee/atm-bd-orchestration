"""Lazy composition of framework stores without a types-to-core dependency."""
from __future__ import annotations

from importlib import import_module
from typing import Any

from atm_bd_types._native import ErrorId, Refusal


def _unavailable(error: ErrorId, **context: str) -> Refusal:
    return Refusal(error, reason="the atm_bd_core package is missing; install it with `uv add atm-bd-core`", **context)


def _core() -> Any:
    try:
        return import_module("atm_bd_core.store")
    except ModuleNotFoundError as exc:
        if exc.name not in ("atm_bd_core", "atm_bd_core.store"):
            raise
        return None


class PhaseFilesCli:
    def load(self, path: str, profile: str) -> Any:
        core = _core()
        if core is None:
            return _unavailable(ErrorId.PHASE_UNREADABLE, path=path, profile=profile)
        return core.PhaseFilesCli().load(path, profile)


class CacheStore:
    def __init__(self, store: Any) -> None:
        self._store = store

    @staticmethod
    def for_phase(phase: str) -> Any:
        core = _core()
        if core is None:
            return _unavailable(ErrorId.CACHE_UNAVAILABLE, phase=phase)
        result = core.CacheStore.for_phase(phase)
        return result if isinstance(result, Refusal) else CacheStore(result)

    def refresh(self, bead_ids: list[str | None]) -> Any:
        return self._store.refresh(bead_ids)

    def show(self, bead_id: str | None) -> Any:
        return self._store.show(bead_id)

    def target_layer(self, checked_bead: Any) -> Any:
        return self._store.target_layer(checked_bead)

    def update(self, patch: Any, actor: str) -> Any:
        return self._store.update(patch, actor)

    def list(self, phase: str) -> Any:
        return self._store.list(phase)

    def ready(self, phase: str) -> Any:
        return self._store.ready(phase)
