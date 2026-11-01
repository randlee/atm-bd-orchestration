# pyright: strict
"""Provider commands validate and pass bodies as files without a shell."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from atm_bd_types import ErrorKind, MergedPrRef, PrOp, ProviderCommands
from pr_lookup import comment_body
from providers import execute, load_provider
from result import Err, Ok


def test_provider_files_are_valid_and_reject_missing_ops_and_placeholders() -> None:
    root = Path(__file__).resolve().parents[2] / "templates/providers"
    for path in root.glob("*.json"):
        document = json.loads(path.read_text())
        commands, error = ProviderCommands.parse_json(json.dumps(document))
        assert commands is not None and error is None
        missing = dict(document)
        del missing["view"]
        assert ProviderCommands.parse_json(json.dumps(missing))[1] is not None
        missing_checks = json.loads(path.read_text())
        missing_checks["checks"]["argv"] = ["no-check-identity"]
        assert ProviderCommands.parse_json(json.dumps(missing_checks))[1] is not None
        document["create"]["argv"] = ["no-placeholders"]
        assert ProviderCommands.parse_json(json.dumps(document))[1] is not None


def test_github_commands_do_not_use_blocked_pr_polling_operations() -> None:
    path = Path(__file__).resolve().parents[2] / "templates/providers/github.json"
    data = json.loads(path.read_text())
    for operation in data.values():
        assert operation["argv"][:3] not in (["gh", "pr", "list"], ["gh", "pr", "checks"])
    assert data["checks"]["argv"] == ["gh", "api", "repos/{owner}/{repo}/commits/{head_sha}/check-runs"]


def test_github_checks_uses_head_sha(tmp_path: Path) -> None:
    loaded = load_provider({})
    assert isinstance(loaded, Ok)
    seen: list[list[str]] = []

    def run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, '{"check_runs": []}', "")

    checked = execute(loaded.value, PrOp.CHECKS, {"head_sha": "abc123"}, cwd=tmp_path, runner=run)
    assert isinstance(checked, Ok)
    assert seen == [["gh", "api", "repos/{owner}/{repo}/commits/abc123/check-runs"]]


def test_azure_requires_each_config_key() -> None:
    for key in ("organization", "project", "repository"):
        values = {"organization": "org", "project": "project", "repository": "repo"}
        del values[key]
        result = load_provider({"provider": "azure", "azure": values})
        assert isinstance(result, Err)
        assert result.error.kind == ErrorKind.CONFIG_MISSING
        assert f"azure.{key}" in result.error.fix


def test_azure_comment_uses_json_file_and_literal_text(tmp_path: Path) -> None:
    result = load_provider({"provider": "azure", "azure": {"organization": "org", "project": "p", "repository": "r"}})
    assert isinstance(result, Ok)
    text = 'quotes " and newline\n; $(not a shell)'
    seen: list[list[str]] = []

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(argv)
        payload = json.loads(Path(argv[argv.index("--in-file") + 1]).read_text())
        assert payload["comments"][0]["content"] == text
        assert kwargs["cwd"] == tmp_path
        return subprocess.CompletedProcess(argv, 0, "{}", "")

    with patch("providers.subprocess.run", side_effect=run):
        executed = execute(result.value, PrOp.COMMENT, {"number": "12", "organization": "org", "project": "p", "repository": "r", "text": text}, cwd=tmp_path)
    assert isinstance(executed, Ok)
    assert seen[0][:3] == ["az", "devops", "invoke"]
    assert text not in seen[0]


def test_azure_create_serializes_file_contents_in_json(tmp_path: Path) -> None:
    loaded = load_provider({"provider": "azure", "azure": {"organization": "org", "project": "p", "repository": "r"}})
    assert isinstance(loaded, Ok)
    source = tmp_path / "description.md"
    source.write_text('A "quoted" body\nsecond line')
    seen: list[list[str]] = []

    def run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(argv)
        payload = json.loads(Path(argv[argv.index("--in-file") + 1]).read_text())
        assert payload == {"sourceRefName": "refs/heads/feature", "targetRefName": "refs/heads/main",
                           "title": "Title", "description": source.read_text()}
        return subprocess.CompletedProcess(argv, 0, "{}", "")

    result = execute(loaded.value, PrOp.CREATE, {"organization": "org", "project": "p", "repository": "r",
                     "head": "feature", "base": "main", "title": "Title", "body_file": str(source)},
                     cwd=tmp_path, runner=run)
    assert isinstance(result, Ok)
    assert source.read_text() not in seen[0]


def test_render_provider_context_and_unknown_operation(tmp_path: Path) -> None:
    import sc_render
    import pytest

    template = tmp_path / "dispatch.md.j2"
    template.write_text('---\nname: dispatch\nformat: text\nrequired_variables:\n  - provider.create\n---\n{{ provider.create }}\n')
    rendered = sc_render.render(template, {})
    assert "gh pr create" in rendered and "{base}" in rendered
    template.write_text('---\nname: dispatch\nformat: text\nrequired_variables:\n  - provider.not_an_op\n---\n{{ provider.not_an_op }}\n')
    with pytest.raises(sc_render.RenderError):
        sc_render.render(template, {})


def test_merged_lookup_checks_each_candidate(tmp_path: Path) -> None:
    loaded = load_provider({})
    assert isinstance(loaded, Ok)
    rows = [{"number": n, "html_url": f"https://example.test/{n}", "base": {"ref": "main"},
             "merged_at": "2026-01-01", "merge_commit_sha": sha}
            for n, sha in ((1, "old"), (2, "wanted"))]

    def run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, json.dumps(rows), "")

    result = execute(loaded.value, PrOp.LOOKUP_BY_HEAD, {"head": "branch", "state": "merged"},
                     cwd=tmp_path, runner=run, accept_merged=lambda pr: pr.merge_commit == "wanted")
    assert isinstance(result, Ok) and isinstance(result.value, MergedPrRef)
    assert result.value.number == "2" and result.value.merge_commit == "wanted"


def test_azure_comment_evidence_uses_configured_repo_and_thread(tmp_path: Path) -> None:
    config = {"provider": "azure", "azure": {"organization": "org", "project": "project", "repository": "actual-repo"}}
    seen: list[list[str]] = []

    def run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, json.dumps({"comments": [{"content": "evidence", "author": {"uniqueName": "dev"}}]}), "")

    with patch("pr_lookup.repo_config.load", return_value=config), patch("providers.subprocess.run", side_effect=run):
        result = comment_body("12", tmp_path, "other/repo", "34")
    assert isinstance(result, Ok) and result.value.body == "evidence"
    assert "repositoryId=actual-repo" in seen[0]
    assert "pullRequestId=12" in seen[0] and "threadId=34" in seen[0]
