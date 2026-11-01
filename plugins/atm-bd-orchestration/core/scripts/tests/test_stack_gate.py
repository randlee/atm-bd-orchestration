# pyright: strict
"""The stack gate checks real local Git state without a hosted service."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
from atm_bd_types import ErrorKind, StackGateResult
from stack_gate import GitStackGate
from result import Err, Ok
from stack_top import select_stack_top


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


@pytest.fixture
def repository(tmp_path: Path) -> tuple[Path, Path, str]:
    remote = tmp_path / "origin.git"
    repo = tmp_path / "work"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True, text=True)
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.test")
    git(repo, "remote", "add", "origin", str(remote))
    (repo / "file").write_text("base\n")
    git(repo, "add", "file")
    git(repo, "commit", "-m", "base")
    git(repo, "push", "-u", "origin", "main")
    git(repo, "checkout", "-b", "feature")
    (repo / "file").write_text("feature\n")
    git(repo, "commit", "-am", "feature")
    head = git(repo, "rev-parse", "HEAD")
    git(repo, "push", "-u", "origin", "feature")
    git(repo, "fetch", "origin")
    return repo, remote, head


def test_correct_base_pushed_head_and_ancestry(repository: tuple[Path, Path, str]) -> None:
    repo, _, head = repository
    seen: list[list[str]] = []

    def run(argv: list[str], *, cwd: Path, capture_output: bool, text: bool,
            check: bool, timeout: int) -> subprocess.CompletedProcess[str]:
        seen.append(argv)
        return subprocess.run(argv, cwd=cwd, capture_output=capture_output, text=text, check=check, timeout=timeout)

    result = GitStackGate(repo, runner=run).check("main", "feature", head, "main")
    assert isinstance(result, Ok) and isinstance(result.value, StackGateResult.Stacked)
    assert seen and all(argv[0] == "git" for argv in seen)


def test_wrong_base_is_rejected(repository: tuple[Path, Path, str]) -> None:
    repo, _, head = repository
    result = GitStackGate(repo).check("other", "feature", head, "main")
    assert isinstance(result, Ok) and isinstance(result.value, StackGateResult.NotStacked)
    assert (result.value.expected_base, result.value.actual_base) == ("main", "other")


def test_head_that_was_not_pushed_is_rejected(repository: tuple[Path, Path, str]) -> None:
    repo, _, _ = repository
    (repo / "file").write_text("unpublished\n")
    git(repo, "commit", "-am", "local")
    head = git(repo, "rev-parse", "HEAD")
    result = GitStackGate(repo).check("main", "feature", head, "main")
    assert isinstance(result, Ok) and isinstance(result.value, StackGateResult.NotPushed)
    assert (result.value.branch, result.value.head) == ("feature", head)


def test_pushed_head_without_base_ancestry_is_rejected(repository: tuple[Path, Path, str]) -> None:
    repo, _, _ = repository
    git(repo, "checkout", "--orphan", "unrelated")
    git(repo, "rm", "-rf", ".")
    (repo / "other").write_text("unrelated\n")
    git(repo, "add", "other")
    git(repo, "commit", "-m", "unrelated")
    head = git(repo, "rev-parse", "HEAD")
    git(repo, "push", "origin", "unrelated")
    result = GitStackGate(repo).check("main", "unrelated", head, "main")
    assert isinstance(result, Ok) and isinstance(result.value, StackGateResult.NotAncestor)
    assert result.value.base_sha == git(repo, "rev-parse", "origin/main")
    assert result.value.head_sha == head


def test_azure_url_rewritten_to_local_origin(repository: tuple[Path, Path, str]) -> None:
    repo, remote, head = repository
    url = "https://dev.azure.com/example/project/_git/repo"
    git(repo, "config", f"url.{remote}.insteadOf", url)
    git(repo, "remote", "set-url", "origin", url)
    result = GitStackGate(repo).check("main", "feature", head, "main")
    assert isinstance(result, Ok) and isinstance(result.value, StackGateResult.Stacked)


def test_git_transport_failure_is_not_reported_as_a_repository_fact(tmp_path: Path) -> None:
    def fail(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 128, "", "remote unavailable")

    result = GitStackGate(tmp_path, runner=fail).check("main", "feature", "a" * 40, "main")
    assert isinstance(result, Err)
    assert result.error.kind == ErrorKind.COMMAND_FAILED
    assert "remote unavailable" in result.error.message and "git ls-remote" in result.error.fix


def test_missing_remote_branch_is_not_pushed(tmp_path: Path) -> None:
    def missing(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 2, "", "")

    result = GitStackGate(tmp_path, runner=missing).check("main", "feature", "a" * 40, "main")
    assert isinstance(result, Ok) and isinstance(result.value, StackGateResult.NotPushed)


def test_stack_top_uses_last_linked_layer_then_trunk_and_legacy_fallback() -> None:
    def resolve(branch: str) -> str:
        return f"sha-{branch}"
    assert select_stack_top({"metadata": {"trunk": "main", "layers": []}}, "other", resolve) == ("main", "sha-main")
    assert select_stack_top({"metadata": {"trunk": "main", "layers": [{"branch": "pending", "head": "x", "linked": False}]}},
                            "other", resolve) == ("main", "sha-main")
    assert select_stack_top({"metadata": {"trunk": "main", "layers": [
        {"branch": "linked", "head": "sha-linked"}, {"branch": "pending", "head": "x", "linked": False}]}},
        "other", resolve) == ("linked", "sha-linked")
    assert select_stack_top({"metadata": {"layers": []}}, "legacy", resolve) == ("legacy", "sha-legacy")
