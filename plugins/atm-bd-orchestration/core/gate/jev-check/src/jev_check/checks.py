"""Record the bytes and usage for one Jev request."""
import hashlib
from dataclasses import dataclass
from typing import Any

from jev_check.client import Question, payload_bytes


@dataclass(frozen=True)
class InputRecord:
    """Audit fields emitted for the gate's Jev-only request."""
    prompt_sha256: str
    input_tokens: int | None
    prompt_tokens: int | None
    leak: int | None
    commands: int
    equal: bool


def input_record(state: Any, questions: dict[str, Question], input_tokens: int | None, prompt_tokens: int | None,
                 commands: int) -> InputRecord:
    if prompt_tokens is not None or commands != 0:
        raise ValueError("input_record accepts only Jev usage; prompt_tokens must be None and commands must be zero")
    sha = hashlib.sha256(payload_bytes(state, questions)).hexdigest()
    return InputRecord(sha, input_tokens, None, None, 0, True)
