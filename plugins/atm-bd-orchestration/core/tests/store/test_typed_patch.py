"""Guarded writes and bead conversions cross the cache boundary without patch JSON."""
import json

import pytest
from atm_bd_core.store.cache import CacheStore
from atm_bd_types import BeadPatch, ErrorId, Merged, Refusal, Stage, Status
from atm_bd_types._native import _bead, _layer


class Cache:
    def __init__(self, status="open", labels=None):
        self.row = {"id": "bead", "status": status, "labels": labels or [], "metadata": {}}
        self.writes = []

    def get(self, bead_id):
        return {"row": {"bead": self.row, "blocked": []}}

    def list(self, phase):
        return {"rows": []}

    def write(self, *args):
        self.writes.append(args)


@pytest.mark.parametrize(("status", "expected"), [
    ("open", Status.OPEN), ("in_progress", Status.IN_PROGRESS), ("blocked", Status.BLOCKED),
    ("deferred", Status.DEFERRED), ("closed", Status.CLOSED),
])
def test_store_status_uses_rust_parser(status, expected):
    result = CacheStore(Cache(status, ["stage:unknown"]), "phase").show("bead")
    assert not isinstance(result, Refusal)
    assert result.status == expected and result.stage == Stage.OTHER


def test_unknown_status_is_typed_refusal():
    result = CacheStore(Cache("not-a-status"), "phase").show("bead")
    assert isinstance(result, Refusal) and result.id == ErrorId.CACHE_UNAVAILABLE
    assert "unknown bead status" in repr(result)


def test_all_patch_writes_preserve_guard_and_close_evidence():
    cache = Cache()
    store = CacheStore(cache, "phase")
    bead = _bead("bead", Status.IN_PROGRESS, Stage.DEV, "old")
    sha = "a" * 40
    patches = [BeadPatch.assign(bead, "new"), BeadPatch.start(bead), BeadPatch.reopen(bead),
               BeadPatch.close(bead, _layer("branch", sha, 7, "main")), BeadPatch.close(bead, Merged(sha=sha))]
    for patch in patches:
        assert store.update(patch, "actor") is None
    assert [(entry[0], entry[1], entry[2], entry[3], entry[5]) for entry in cache.writes] == [
        ("bead", "update", {"assignee": "new"}, {"status": "in_progress", "assignee": "old"}, "actor"),
        ("bead", "update", {"status": "in_progress"}, {"status": "in_progress", "assignee": "old"}, "actor"),
        ("bead", "update", {"status": "open", "assignee": ""}, {"status": "in_progress", "assignee": "old"}, "actor"),
        ("bead", "close", {"reason": json.dumps({"kind": "layer", "branch": "branch", "head": sha,
                                                    "pr": 7, "base": "main"}, sort_keys=True, separators=(",", ":"))},
         {"status": "in_progress", "assignee": "old"}, "actor"),
        ("bead", "close", {"reason": json.dumps({"kind": "merged", "sha": sha}, sort_keys=True,
                                                    separators=(",", ":"))},
         {"status": "in_progress", "assignee": "old"}, "actor"),
    ]


def test_close_reason_preserves_ascii_escaped_canonical_json():
    cache = Cache()
    store = CacheStore(cache, "phase")
    bead = _bead("bead", Status.OPEN, Stage.DEV)
    sha = "a" * 40
    branch = "ré🐦"
    assert store.update(BeadPatch.close(bead, _layer(branch, sha, 7, "main")), "actor") is None
    expected = json.dumps({"kind": "layer", "branch": branch, "head": sha, "pr": 7, "base": "main"},
                          sort_keys=True, separators=(",", ":"))
    assert cache.writes[0][2]["reason"] == expected
