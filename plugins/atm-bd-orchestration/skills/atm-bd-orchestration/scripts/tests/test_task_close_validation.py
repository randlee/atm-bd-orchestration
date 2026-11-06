"""The extracted validators remain the hook's public objects."""
import pytest

from task_close_world import hook
import task_close_validation as validation


def test_hook_reexports_the_shared_validators_and_error():
    for name in ("CloseError", "assignment_details", "assignment_id_for_round", "sanity_round",
                 "sanity_round_key", "validate_command_json", "header", "reviewer_list", "validate"):
        assert getattr(hook, name) is getattr(validation, name)
    with pytest.raises(hook.CloseError) as error:
        validation.validate_command_json(["atm", "task", "events", "task", "--json"], {"events": "bad"})
    assert error.value.code == "COMMAND.INVALID"
    assert "atm task events task" in error.value.fix
