from atm_bd_types import Transition

from helpers import command_argv, run_hook


def test_fix_close_uses_replay_safe_dev_sequence() -> None:
    result = run_hook(Transition.FIX_CLOSE)
    assert len(command_argv(result)) == 4
    assert command_argv(result)[0] == ("bd", "close", "atm-bo-5.group-dev")
