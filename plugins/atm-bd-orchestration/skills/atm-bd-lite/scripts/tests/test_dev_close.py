from atm_bd_types import Transition

from helpers import command_argv, observed, run_hook


def test_dev_close_orders_close_link_qa_then_task() -> None:
    result = run_hook(Transition.DEV_CLOSE)
    assert command_argv(result) == [
        ("bd", "close", "atm-bo-5.group-dev"),
        ("atm-bd", "stack", "link", "atm-bo-5.group-dev"),
        ("atm", "task", "assign", "fenix", "--task-id", "atm-bo-5.group-dev.group-qa", "--template",
         "skills/atm-bd-lite/templates/qa-template.xml.j2"),
        ("atm", "task", "close", "atm-bo-5.group-dev", "completed"),
    ]


def test_dev_close_rejects_failed_stack_gate() -> None:
    result = run_hook(Transition.DEV_CLOSE, state=observed(gate_stacked=False))
    assert hasattr(result, "error")


def test_dev_close_replay_predicates_skip_completed_steps() -> None:
    result = run_hook(Transition.DEV_CLOSE)
    commands = result.value
    state = observed(bead_closed=True, layer_linked=True, qa_assigned=True, task_closed=False)
    assert [command.argv for command in commands if not command.idempotent_when(state)] == [
        ("atm", "task", "close", "atm-bo-5.group-dev", "completed")]
