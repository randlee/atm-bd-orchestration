from atm_bd_types import Transition

from helpers import command_argv, run_hook


def test_qa_pass_closes_notifies_then_closes_task() -> None:
    assert command_argv(run_hook(Transition.QA_PASS)) == [
        ("bd", "close", "atm-bo-5.group-dev"),
        ("atm", "send", "fenix", "QA PASS", "--task-id", "atm-bo-5.group-dev"),
        ("atm", "task", "close", "atm-bo-5.group-dev", "completed"),
    ]
