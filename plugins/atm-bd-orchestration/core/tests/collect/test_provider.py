from types import SimpleNamespace

import pytest
from atm_bd_core.collect.provider import pr_bases, resolve_provider, top_checks
from atm_bd_types import CheckState, FactKind


@pytest.mark.parametrize(("remote", "head_argv", "checks_argv", "base_argv", "check_state", "base_response"), [
    ("https://github.com/example/repo.git",
     ["gh", "pr", "view", "5", "--json", "headRefOid", "--jq", ".headRefOid"],
     ["gh", "pr", "view", "5", "--json", "statusCheckRollup", "--jq", "[.statusCheckRollup[] | .conclusion // .state // .status]"],
     ["gh", "pr", "view", "5", "--json", "baseRefName", "--jq", ".baseRefName"], "success", "main"),
    ("https://dev.azure.com/example/repo",
     ["az", "repos", "pr", "show", "--id", "5", "--query", "lastMergeSourceCommit.commitId", "--output", "tsv"],
     ["az", "repos", "pr", "status", "list", "--id", "5", "--query", "[].state", "--output", "json"],
     ["az", "repos", "pr", "show", "--id", "5", "--query", "targetRefName", "--output", "tsv"], "succeeded", "refs/heads/main"),
])
def test_provider_commands_and_check_states(recorded_runner, remote, head_argv, checks_argv, base_argv, check_state, base_response):
    discover = recorded_runner({"stdout": remote})
    provider, error = resolve_provider(discover, None)
    assert provider is not None and error is None
    assert discover.calls == [(["git", "remote", "get-url", "origin"], None)]
    head = "a" * 40
    layer = SimpleNamespace(pr=5, head=head)
    runner = recorded_runner({"stdout": head}, {"stdout": f'["{check_state}"]'}, {"stdout": head})
    result, error = top_checks(runner, provider, layer)
    assert result is not None and error is None and result.state == CheckState.PASSING
    assert runner.calls == [(head_argv, None), (checks_argv, None), (head_argv, None)]
    runner = recorded_runner({"stdout": base_response + "\n"})
    result, error = pr_bases(runner, provider, [layer])
    assert result is not None and error is None and result[0].base == "main"
    assert runner.calls == [(base_argv, None)]
    runner = recorded_runner({"stdout": head}, {"code": 1, "stderr": "unavailable"})
    result, error = top_checks(runner, provider, layer)
    assert result is None and error is not None and error.kind == FactKind.TOP_CHECKS
    assert runner.calls == [(head_argv, None), (checks_argv, None)]
    runner = recorded_runner({"code": 1, "stderr": "unavailable"})
    result, error = pr_bases(runner, provider, [layer])
    assert result is None and error is not None and error.kind == FactKind.PR_BASES
    assert runner.calls == [(base_argv, None)]


def test_unknown_provider_remote(recorded_runner):
    runner = recorded_runner({"stdout": "https://unknown.example/repo"})
    provider, error = resolve_provider(runner, None)
    assert provider is None and error is not None and "unknown.example" in error
    assert runner.calls == [(["git", "remote", "get-url", "origin"], None)]


def test_checks_rejects_head_mismatch(recorded_runner):
    discover = recorded_runner({"stdout": "https://github.com/example/repo"})
    selected, error = resolve_provider(discover, None)
    assert selected is not None and error is None
    layer = SimpleNamespace(pr=5, head="a" * 40)
    runner = recorded_runner({"stdout": "b" * 40})
    value, error = top_checks(runner, selected, layer)
    assert value is None and error is not None and error.kind == FactKind.TOP_CHECKS
    assert "differs" in error.message
    assert runner.calls == [(["gh", "pr", "view", "5", "--json", "headRefOid", "--jq", ".headRefOid"], None)]


def test_provider_states_are_isolated_and_unknown_fails_closed(recorded_runner):
    layer = SimpleNamespace(pr=5, head="a" * 40)
    for remote, valid, pending, failing, foreign in [
        ("https://github.com/example/repo", "success", "queued", "timed_out", "succeeded"),
        ("https://dev.azure.com/example/repo", "succeeded", "notset", "failed", "success"),
    ]:
        provider, error = resolve_provider(recorded_runner({"stdout": remote}), None)
        assert provider is not None and error is None
        for state, expected in [(valid, CheckState.PASSING), (pending, CheckState.PENDING),
                                (failing, CheckState.FAILING)]:
            runner = recorded_runner({"stdout": layer.head}, {"stdout": f'["{state}"]'}, {"stdout": layer.head})
            value, error = top_checks(runner, provider, layer)
            assert value is not None and error is None and value.state == expected
        for states in (f'["{foreign}"]', '["pending", "not-a-real-state"]'):
            runner = recorded_runner({"stdout": layer.head}, {"stdout": states}, {"stdout": layer.head})
            value, error = top_checks(runner, provider, layer)
            assert value is None and error is not None and error.kind == FactKind.TOP_CHECKS
            assert "unknown check states" in error.message
        runner = recorded_runner({"stdout": layer.head}, {"stdout": "[]"}, {"stdout": layer.head})
        value, error = top_checks(runner, provider, layer)
        assert value is not None and error is None and value.state == CheckState.NONE


def test_base_prefix_is_provider_specific(recorded_runner):
    layer = SimpleNamespace(pr=5)
    for remote, expected in [
        ("https://github.com/example/repo", "refs/heads/main"),
        ("https://dev.azure.com/example/repo", "main"),
    ]:
        provider, error = resolve_provider(recorded_runner({"stdout": remote}), None)
        assert provider is not None and error is None
        bases, error = pr_bases(recorded_runner({"stdout": "refs/heads/main"}), provider, [layer])
        assert bases is not None and error is None and bases[0].base == expected


def test_github_reads_use_configured_repository(recorded_runner):
    provider, error = resolve_provider(recorded_runner(), "gh", "owner/other-repo")
    assert provider is not None and error is None
    layer = SimpleNamespace(pr=5, head="a" * 40)
    runner = recorded_runner({"stdout": layer.head}, {"stdout": '["success"]'}, {"stdout": layer.head},
                             {"stdout": "main"})
    checks, error = top_checks(runner, provider, layer)
    assert error is None and checks.state == CheckState.PASSING
    bases, error = pr_bases(runner, provider, [layer])
    assert bases is not None and error is None and bases[0].base == "main"
    assert all(argv[-2:] == ["--repo", "owner/other-repo"] for argv, _ in runner.calls)


@pytest.mark.parametrize("step", ["first-head", "checks", "last-head", "base"])
def test_provider_failure_reports_exact_executed_argv(recorded_runner, step):
    provider, error = resolve_provider(recorded_runner(), "gh", "owner/other-repo")
    assert provider is not None and error is None
    layer = SimpleNamespace(pr=42, head="a" * 40)
    ok_head = {"stdout": layer.head}
    ok_checks = {"stdout": '["success"]'}
    failed = {"code": 1, "stderr": "unavailable"}
    responses = {
        "first-head": [failed],
        "checks": [ok_head, failed],
        "last-head": [ok_head, ok_checks, failed],
        "base": [failed],
    }
    runner = recorded_runner(*responses[step])
    value, error = (pr_bases(runner, provider, [layer]) if step == "base"
                    else top_checks(runner, provider, layer))
    assert value is None and error is not None
    assert error.argv == runner.calls[-1][0]
    assert "42" in error.argv and error.argv[-2:] == ["--repo", "owner/other-repo"]
