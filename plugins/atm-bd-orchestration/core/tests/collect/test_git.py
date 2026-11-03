from types import SimpleNamespace

from atm_bd_types import FactKind

from atm_bd_core.collect.git import ancestry, remote_branches


class Runner:
    def __init__(self, code, stdout="", stderr=""):
        self.result = SimpleNamespace(code=code, stdout=stdout, stderr=stderr)
        self.calls = []

    def run(self, argv, stdin):
        self.calls.append((argv, stdin))
        return self.result


def test_remote_branches_success_and_failure():
    runner = Runner(0, "a" * 40 + "\trefs/heads/main\n")
    branches, error = remote_branches(runner)
    assert error is None and branches is not None
    assert [(branch.name, branch.head) for branch in branches] == [("main", "a" * 40)]
    branches, error = remote_branches(Runner(1, stderr="offline"))
    assert error is not None
    assert branches is None and error.kind == FactKind.REMOTE_BRANCHES


def test_ancestry_distinguishes_false_from_failure():
    yes, error = ancestry(Runner(0), [("a", "b")])
    assert yes is not None and error is None and yes[0].is_ancestor
    facts, error = ancestry(Runner(1), [("a", "b")])
    assert facts is not None
    assert error is None and not facts[0].is_ancestor
    facts, error = ancestry(Runner(128, stderr="bad ref"), [("a", "b")])
    assert error is not None
    assert facts is None and error.kind == FactKind.ANCESTRY
