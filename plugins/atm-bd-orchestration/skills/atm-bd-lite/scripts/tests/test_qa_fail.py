from atm_bd_types import Transition

from helpers import command_argv, run_hook


def test_qa_fail_pours_notifies_then_closes_task() -> None:
    assert command_argv(run_hook(Transition.QA_FAIL)) == [
        ("atm-bd", "pour", "--source", "findings.json", "--formula", "finding-group.formula.toml.j2"),
        ("atm", "send", "fenix", "QA FAIL", "--task-id", "atm-bo-5.group-dev"),
        ("atm", "task", "close", "atm-bo-5.group-dev", "completed"),
    ]
