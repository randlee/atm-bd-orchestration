"""Collect read-only bead and stack facts through the cache port."""

from subprocess import SubprocessError

from atm_bd_types import CollectError, FactKind, Refusal, StackFact, Stage


def _cache_read(cache, method, phase, kind):
    try:
        value = getattr(cache, method)(phase)
        if isinstance(value, Refusal):
            raise TypeError(str(value))
        if not isinstance(value, list):
            raise TypeError("cache did not return a list")
        return value, None
    except (OSError, RuntimeError, SubprocessError, ValueError, TypeError, KeyError) as error:
        return None, CollectError(kind, [], str(error), "Check the beads cache and phase configuration.")


def beads(cache, phase):
    return _cache_read(cache, "list", phase, FactKind.BEADS)


def ready(cache, phase):
    return _cache_read(cache, "ready", phase, FactKind.READY)


def stack(bead_list, phase_file, stack_of):
    try:
        candidates = [bead for bead in bead_list if bead.stage == Stage.STACK]
        if len(candidates) != 1:
            raise ValueError(f"expected one stack bead, found {len(candidates)}")
        bead = candidates[0]
        ledger = stack_of(bead)
        trunk = phase_file.key("integration_branch")
        if ledger is None or not trunk:
            raise ValueError("stack ledger or integration branch missing")
        return StackFact(bead, ledger, trunk, None), None
    except (OSError, RuntimeError, SubprocessError, ValueError, TypeError, KeyError) as error:
        return None, CollectError(FactKind.STACK, [], str(error), "Check the stack bead and integration branch.")
