from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stack_top import JsonValue, StackTop, StackTopMismatch, select_confirmed_stack_top, select_stack_top


def test_confirmed_top_agrees_and_ignores_pending():
    layers: list[JsonValue] = [{"pr": 1, "branch": "one", "head": "aaa", "linked": True},
              {"pr": 2, "branch": "two", "head": "bbb", "linked": False}]
    expected = StackTop(1, "one", "aaa")
    assert select_confirmed_stack_top(layers, [1]) == expected
    assert select_stack_top({"metadata": {"layers": layers}}, "trunk", lambda _: "ccc") == (expected.branch, expected.head)


def test_ledger_ahead_of_hosted_is_typed_mismatch():
    layers: list[JsonValue] = [{"pr": 1, "branch": "one", "head": "aaa", "linked": True},
              {"pr": 2, "branch": "two", "head": "bbb", "linked": True}]
    assert select_confirmed_stack_top(layers, [1]) == StackTopMismatch(StackTop(2, "two", "bbb"), 1)


def test_hosted_ahead_of_ledger_is_typed_mismatch():
    layers: list[JsonValue] = [{"pr": 1, "branch": "one", "head": "aaa", "linked": True}]
    assert select_confirmed_stack_top(layers, [1, 2]) == StackTopMismatch(StackTop(1, "one", "aaa"), 2)


def test_empty_ledger_and_hosted_stack_selects_trunk_via_wrapper():
    assert select_confirmed_stack_top([], []) == StackTop(None, None, None)
    assert select_stack_top({"metadata": {"layers": []}}, "trunk", lambda _: "abc") == ("trunk", "abc")


def test_passed_first_layer_wins_over_trunk_but_held_layers_do_not():
    first = {"pr": 1, "branch": "first", "head": "aaa", "linked": False}
    held = {"pr": 2, "branch": "held", "head": "bbb", "linked": False,
            "held_on": {"pr": 1, "branch": "first"}}
    assert select_stack_top({"metadata": {"layers": [first, held]}}, "trunk", lambda _: "ccc") == ("first", "aaa")
    assert select_stack_top({"metadata": {"layers": [held]}}, "trunk", lambda _: "ccc") == ("trunk", "ccc")


@pytest.mark.parametrize("archive_numbers", [False, True])
def test_landing_state_is_metadata_bearing_and_old_wrapper_stays_compatible(archive_numbers):
    from stack_top import LedgerError, is_landed, select_live_top
    old = {"pr": 1, "branch": "old", "head": "aaa", "linked": True}
    new = {"pr": 2, "branch": "new", "head": "bbb", "linked": True}
    meta = {"landed_head": "merged", "landed_layers": [1] if archive_numbers else [old], "layers": [], "trunk": "trunk"}
    assert is_landed(meta)
    assert select_live_top(meta, [1]) == StackTop(None, "trunk", None)
    meta["layers"] = [new]
    assert not is_landed(meta)
    assert select_live_top(meta, [2]) == StackTop(2, "new", "bbb")
    meta["layers"] = [old]
    with pytest.raises(LedgerError) as error:
        select_live_top(meta, [1], bead="phase.stack")
    assert error.value.code == "LEDGER.STALE_LANDING"
    assert "phase.stack" in str(error.value)
    assert "stack-landed phase.stack" in error.value.fix
    # bs-2 consumes this compatibility API; it intentionally retains the old behavior.
    assert select_stack_top({"metadata": meta}, "trunk", lambda _: "ccc") == ("old", "aaa")
