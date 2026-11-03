from types import SimpleNamespace

from atm_bd_types import CheckState, FactKind

from atm_bd_core.collect.provider import pr_bases, resolve_provider, top_checks


class Runner:
    def __init__(self, stdout, code=0):
        self.stdout, self.code = stdout, code

    def run(self, argv, stdin):
        return SimpleNamespace(stdout=self.stdout, stderr="failed", code=self.code)


def test_resolve_provider_from_remote_and_unknown():
    provider, error = resolve_provider(Runner("https://github.com/example/repo.git"), None)
    assert provider is not None and error is None
    provider, error = resolve_provider(Runner("https://unknown.example/repo"), None)
    assert error is not None
    assert provider is None and "unknown.example" in error


def test_checks_success_and_failed_read():
    provider, _ = resolve_provider(Runner(""), "gh")
    layer = SimpleNamespace(pr=5, head="a" * 40)
    class ChecksRunner:
        def run(self, argv, stdin):
            stdout = "a" * 40 if "headRefOid" in argv else '["SUCCESS"]'
            return SimpleNamespace(stdout=stdout, stderr="", code=0)

    result, error = top_checks(ChecksRunner(), provider, layer)
    assert result is not None
    assert error is None and result.state == CheckState.PASSING
    result, error = top_checks(Runner("", 1), provider, layer)
    assert error is not None
    assert result is None and error.kind == FactKind.TOP_CHECKS


def test_bases_success_and_failed_read():
    provider, _ = resolve_provider(Runner(""), "az")
    layer = SimpleNamespace(pr=5)
    result, error = pr_bases(Runner("refs/heads/main\n"), provider, [layer])
    assert result is not None
    assert error is None and result[0].base == "main"
    result, error = pr_bases(Runner("", 1), provider, [layer])
    assert error is not None
    assert result is None and error.kind == FactKind.PR_BASES


def test_checks_rejects_head_mismatch():
    selected, _ = resolve_provider(Runner(""), "gh")
    layer = SimpleNamespace(pr=5, head="a" * 40)
    value, error = top_checks(Runner("b" * 40), selected, layer)
    assert error is not None
    assert value is None and error.kind == FactKind.TOP_CHECKS
    assert "differs" in error.message
