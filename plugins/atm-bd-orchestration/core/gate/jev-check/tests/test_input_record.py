from dataclasses import asdict
import hashlib

import pytest

from jev_check import Question, payload_bytes
from jev_check.checks import input_record


QUESTIONS: dict[str, Question] = {
    "implemented:T-1": {"type": "choice", "instructions": "Is it implemented?", "criteria": {"yes": "y", "no": "n"}}
}


def test_input_record_has_only_jev_usage() -> None:
    state = {"hook": "source"}
    record = input_record(state, QUESTIONS, 318, None, 0)

    assert asdict(record) == {
        "prompt_sha256": hashlib.sha256(payload_bytes(state, QUESTIONS)).hexdigest(),
        "input_tokens": 318,
        "prompt_tokens": None,
        "leak": None,
        "commands": 0,
        "equal": True,
    }


@pytest.mark.parametrize(("prompt_tokens", "commands"), [(100, 0), (None, 1)])
def test_input_record_rejects_non_jev_usage(prompt_tokens: int | None, commands: int) -> None:
    with pytest.raises(ValueError, match="only Jev usage"):
        input_record({}, QUESTIONS, 100, prompt_tokens, commands)
