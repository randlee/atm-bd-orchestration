# pyright: strict
"""Provider flags reject ambiguous choices and choose a stable default."""
import pytest
from atm_bd_types import ErrorKind
from result import Err, Ok

from atm_bd_console.skill import select_provider


def test_provider_selection_and_typed_conflict() -> None:
    for github, azure, expected in ((False, False, "github"), (True, False, "github"), (False, True, "azure")):
        selected = select_provider(github, azure)
        assert isinstance(selected, Ok)
        assert selected.value == expected
    bad = select_provider(True, True)
    assert isinstance(bad, Err)
    assert bad.error.kind == ErrorKind.CONFIG_INVALID
    assert bad.error.fix


def test_conflicting_provider_flags_fail_before_install(capsys: pytest.CaptureFixture[str]) -> None:
    from atm_bd_console import skill
    assert skill.run(["--github", "--azure"]) == 2
    captured = capsys.readouterr()
    assert "CONFIG_INVALID" in captured.err
    assert "Select one provider flag" in captured.err


def test_azure_qa_dispatch_injects_configured_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    import providers
    import test_atm_bd
    from result import Ok

    from atm_bd_console import atm_bd

    def load_config(_path: object) -> dict[str, object]:
        return {"provider": "azure", "azure": {"organization": "org", "project": "project", "repository": "repo"}}

    monkeypatch.setattr(atm_bd.provider_repo_config, "load", load_config)
    context = test_atm_bd.context(test_atm_bd.mapped(test_atm_bd.SPRINT_QA), test_atm_bd.PR)
    spec = atm_bd.dispatch_spec(context, test_atm_bd.PHASE_TEMPLATES)
    assert isinstance(spec, Ok)
    provider = spec.value.vars["provider"]
    assert provider["create"].startswith("az repos pr create")
    assert provider["stack_view"].startswith("bd show")
    assert providers.render_context({"provider": "azure", "azure": {"organization": "org", "project": "project", "repository": "repo"}}) == Ok(provider)
