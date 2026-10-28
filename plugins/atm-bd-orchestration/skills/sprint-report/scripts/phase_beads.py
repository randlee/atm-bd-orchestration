"""One phase's beads for sprint-report, read through the bd-cache.

Never `bd list --all`: that reads every bead in the database, which is slow
and loads the backend on a large one. The cache syncs the phase label once
(incremental after the first run) and serves the rows with pending journal
writes replayed on top.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, TypeAlias, TypeGuard

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "atm-bd-orchestration/scripts"))
import bd_cache  # noqa: E402

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


class PhaseBeadCache(Protocol):
    def sync(self, phase: str) -> object: ...

    def list(self, phase: str) -> object: ...


def is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def is_object_mapping(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def is_json_value(value: object) -> TypeGuard[JsonValue]:
    if value is None or isinstance(value, (bool, int, float, str)):
        return True
    if is_object_list(value):
        return all(is_json_value(item) for item in value)
    if is_object_mapping(value):
        return all(isinstance(key, str) and is_json_value(item) for key, item in value.items())
    return False


def is_json_object(value: object) -> TypeGuard[JsonObject]:
    if not is_object_mapping(value):
        return False
    return all(isinstance(key, str) and is_json_value(item) for key, item in value.items())


def is_bead_row(value: object) -> TypeGuard[JsonObject]:
    return is_json_object(value) and isinstance(value.get("id"), str)


def bead_rows(value: object) -> list[JsonObject]:
    if not is_object_list(value):
        raise ValueError("bd list did not return a list")
    rows: list[JsonObject] = []
    for row in value:
        if not is_bead_row(row):
            raise ValueError("bd list returned a row without a string id")
        rows.append(row)
    return rows


def direct(repo: Path, phase: str) -> list[JsonObject]:
    """The phase's beads straight from bd, scoped to its label."""
    command = ["bd", "list", "-l", f"phase-{phase}", "-n", "0", "--status", bd_cache.STATUSES, "--json"]
    result = subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=bd_cache.BD_TIMEOUT)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(command[:4])} failed: {(result.stderr or result.stdout).strip()[:500]}")
    value: object = json.loads(result.stdout or "[]")
    return bead_rows(value)


def phase_beads(
    repo: Path,
    phase: str,
    cache_factory: Callable[[Path], PhaseBeadCache] | None = None,
) -> list[JsonObject]:
    """Sync the phase into the cache, then read it; every fallback is announced on stderr."""
    factory = cache_factory if cache_factory is not None else bd_cache.BdCache
    try:
        cache: PhaseBeadCache = factory(repo)
    except (bd_cache.CacheError, OSError) as error:
        print(f"sprint-report: bd-cache unavailable ({error}); reading phase-{phase} from bd", file=sys.stderr)
        return direct(repo, phase)
    try:
        cache.sync(phase)
    except (bd_cache.CacheError, OSError) as error:
        print(f"sprint-report: bd-cache sync failed ({error}); rendering from cached rows", file=sys.stderr)
    rows = bead_rows(cache.list(phase))
    if not rows:
        raise RuntimeError(f"no phase-{phase} beads in the bd-cache or in bd")
    return rows
