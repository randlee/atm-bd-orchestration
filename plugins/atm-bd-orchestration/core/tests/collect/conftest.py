"""Recorded, deterministic command-port responses for collector tests."""
from collections import deque
from types import SimpleNamespace

import pytest


class RecordingRunner:
    def __init__(self, *responses):
        self.responses = deque(responses)
        self.calls = []

    def run(self, argv, stdin):
        self.calls.append((list(argv), stdin))
        response = self.responses.popleft()
        if isinstance(response, Exception):
            raise response
        return SimpleNamespace(code=response.get("code", 0), stdout=response.get("stdout", ""),
                               stderr=response.get("stderr", ""))


@pytest.fixture
def recorded_runner():
    return RecordingRunner
