from atm_bd_core.collect.git import ancestry, remote_branches
from atm_bd_types import FactKind


def test_remote_branches_success_and_failure(recorded_runner):
    argv = ["git", "ls-remote", "--heads", "origin"]
    runner = recorded_runner({"stdout": "a" * 40 + "\trefs/heads/main\n"})
    branches, error = remote_branches(runner)
    assert error is None and branches is not None
    assert [(branch.name, branch.head) for branch in branches] == [("main", "a" * 40)]
    assert runner.calls == [(argv, None)]
    runner = recorded_runner({"code": 1, "stderr": "offline"})
    branches, error = remote_branches(runner)
    assert branches is None and error is not None and error.kind == FactKind.REMOTE_BRANCHES
    assert runner.calls == [(argv, None)]


def test_ancestry_distinguishes_false_from_failure(recorded_runner):
    argv = ["git", "merge-base", "--is-ancestor", "a", "b"]
    for code, expected in [(0, True), (1, False)]:
        runner = recorded_runner({"code": code})
        facts, error = ancestry(runner, [("a", "b")])
        assert facts is not None and error is None and facts[0].is_ancestor is expected
        assert runner.calls == [(argv, None)]
    runner = recorded_runner({"code": 128, "stderr": "bad ref"})
    facts, error = ancestry(runner, [("a", "b")])
    assert facts is None and error is not None and error.kind == FactKind.ANCESTRY
    assert runner.calls == [(argv, None)]


def test_runner_exception_becomes_failed_fact(recorded_runner):
    runner = recorded_runner(RuntimeError("runner unavailable"))
    value, error = remote_branches(runner)
    assert value is None and error is not None and error.kind == FactKind.REMOTE_BRANCHES
    assert "runner unavailable" in error.message
    assert runner.calls == [(["git", "ls-remote", "--heads", "origin"], None)]
