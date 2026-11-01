from atm_bd_types import Transition

from helpers import command_argv, run_hook


def test_refused_updates_notifies_then_closes_task() -> None:
    assert command_argv(run_hook(Transition.REFUSED)) == [
        ("bd", "update", "atm-bo-5.group-dev", "--status", "open", "--append-notes", "blocked by upstream"),
        ("atm", "send", "fenix", "task refused", "--task-id", "atm-bo-5.group-dev"),
        ("atm", "task", "close", "atm-bo-5.group-dev", "refused", "blocked by upstream"),
    ]
