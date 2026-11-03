"""Framework package integration with the types wheel."""

import atm_bd_core
import pytest
from atm_bd_types import CacheStore, PhaseFilesCli


def test_framework_package_imports() -> None:
    assert atm_bd_core.__name__ == "atm_bd_core"


def test_lazy_store_delegates_to_framework(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    import types

    class Store:
        @staticmethod
        def for_phase(phase: str):
            assert phase == "bo"
            return Store()

        def show(self, bead_id: str):
            return bead_id

    class Phases:
        def load(self, path: str, profile: str):
            return (path, profile)

    fake = types.ModuleType("atm_bd_core.store")
    fake.CacheStore = Store  # type: ignore[attr-defined]
    fake.PhaseFilesCli = Phases  # type: ignore[attr-defined]
    import atm_bd_core
    monkeypatch.setitem(sys.modules, "atm_bd_core.store", fake)
    monkeypatch.setattr(atm_bd_core, "store", fake, raising=False)
    assert CacheStore.for_phase("bo").show("bo-1") == "bo-1"
    assert PhaseFilesCli().load("phase.toml", "lite") == ("phase.toml", "lite")


