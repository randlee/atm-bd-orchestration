from types import SimpleNamespace

from atm_bd_core.collect.beads import beads, ready, stack
from atm_bd_types import FactKind


class Cache:
    def list(self, phase):
        return []

    def ready(self, phase):
        raise OSError("offline")


def test_bead_reads():
    assert beads(Cache(), "phase") == ([], None)
    value, error = ready(Cache(), "phase")
    assert error is not None
    assert value is None and error.kind == FactKind.READY


def test_stack_fails_when_no_stack_bead():
    value, error = stack([], SimpleNamespace(key=lambda key: "main"), lambda bead: None)
    assert error is not None
    assert value is None and error.kind == FactKind.STACK


def test_ready_success_and_bead_failure():
    class OtherCache:
        def ready(self, phase):
            return []

        def list(self, phase):
            raise OSError("offline")

    assert ready(OtherCache(), "phase") == ([], None)
    value, error = beads(OtherCache(), "phase")
    assert error is not None
    assert value is None and error.kind == FactKind.BEADS
