# pyright: strict
"""Provider-independent pull request lookup and evidence retrieval."""
from __future__ import annotations

from collections.abc import Callable, Mapping
import subprocess
from pathlib import Path

from atm_bd_types import Error, ErrorKind, Evidence, MergedPrRef, PrOp, PrRef, ProviderCommands
import repo_config
from providers import execute, field_at, load_provider
from result import Err, Ok, Result
from sprint_index_common import is_json_object


def _provider(repo: Path) -> Result[tuple[ProviderCommands, dict[str, str]]]:
    try:
        config = repo_config.load(repo)
    except repo_config.ConfigNotFound:
        config = {"provider": "github"}
    except (repo_config.ConfigError, OSError) as exc:
        return Err(Error(ErrorKind.CONFIG_INVALID, str(exc), "Repair the repository orchestration configuration."))
    loaded = load_provider(config)
    if isinstance(loaded, Err):
        return loaded
    context: dict[str, str] = {}
    raw = config.get("azure")
    if is_json_object(raw):
        for name in ("organization", "project", "repository"):
            value: object = raw.get(name)
            if isinstance(value, str):
                context[name] = value
    return Ok((loaded.value, context))


def find_pr_by_head(branch: str, repo: Path | None = None, *,
                    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None, expected_head: str = "") -> Result[PrRef]:
    """Find the unique open PR for the named branch."""
    root = repo or Path.cwd()
    provider = _provider(root)
    if isinstance(provider, Err):
        return provider
    commands, context = provider.value
    found = execute(commands, PrOp.LOOKUP_BY_HEAD, {**context, "head": branch, "state": "open", "head_sha": expected_head}, cwd=root, runner=runner)
    if isinstance(found, Err):
        return found
    if isinstance(found.value, PrRef):
        return Ok(found.value)
    return Err(Error(ErrorKind.PARSE_FAILED, "provider returned no pull request identity", "Check provider output."))


def find_merged_pr(branch: str, repo: Path | None = None, *,
                   runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
                   accept: Callable[[MergedPrRef], bool] | None = None) -> Result[MergedPrRef]:
    """Find a merged PR and preserve its merge commit for ancestry checks."""
    root = repo or Path.cwd()
    provider = _provider(root)
    if isinstance(provider, Err):
        return provider
    commands, context = provider.value
    found = execute(commands, PrOp.LOOKUP_BY_HEAD, {**context, "head": branch, "state": "merged"}, cwd=root, runner=runner, accept_merged=accept)
    if isinstance(found, Err):
        return found
    if isinstance(found.value, MergedPrRef):
        return Ok(found.value)
    return Err(Error(ErrorKind.PARSE_FAILED, "provider returned no merged pull request", "Check provider output."))


def _body(op: PrOp, values: Mapping[str, str], repo: Path) -> Result[Evidence]:
    provider = _provider(repo)
    if isinstance(provider, Err):
        return provider
    commands, context = provider.value
    if op == PrOp.COMMENT_VIEW and context and not values.get("thread"):
        return Err(Error(ErrorKind.CONFIG_MISSING, "Azure comment evidence does not name a thread", "Supply an Azure PR thread URL."))
    result = execute(commands, op, {**values, **context}, cwd=repo)
    if isinstance(result, Err):
        return result
    command = commands.command("view" if op == PrOp.VIEW else "comment_view")
    if command is None or isinstance(result.value, (PrRef, MergedPrRef)):
        return Err(Error(ErrorKind.PARSE_FAILED, "provider returned no evidence object", "Check provider output."))
    body = field_at(result.value, command.result.get("body", ""))
    if body is None and isinstance(result.value, dict) and command.result.get("body") in result.value:
        body = ""
    if not isinstance(body, str):
        return Err(Error(ErrorKind.PARSE_FAILED, "provider evidence has no body", "Check provider output."))
    url = field_at(result.value, command.result.get("url", ""))
    author = field_at(result.value, command.result.get("author", ""))
    updated = field_at(result.value, command.result.get("updated_at", ""))
    return Ok(Evidence(body, url if isinstance(url, str) else None,
                       author if isinstance(author, str) else None,
                       updated if isinstance(updated, str) else None))


def pr_body(number: str, repo: Path, repository: str = "") -> Result[Evidence]:
    return _body(PrOp.VIEW, {"number": number, "repository": repository}, repo)


def comment_body(number: str, repo: Path, repository: str = "", thread: str = "") -> Result[Evidence]:
    return _body(PrOp.COMMENT_VIEW, {"number": number, "repository": repository, "thread": thread}, repo)
