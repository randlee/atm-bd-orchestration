"""Single-call GitHub pull-request source."""
from __future__ import annotations

import json
import re
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from . import command
from .ci import ci_failure_key
from .enums import CiState, PrState
from .pr_selection import select_pr
from .result import CommandFailed, ConfigInvalid, Err, Ok, ParseFailed, Rejected, Result, Timeout, Unreachable
from .types import GhStatus, PullRequest

PR_FIELDS = "number url state isDraft headRefName baseRefName headRefOid commits(last: 1) { nodes { commit { statusCheckRollup { state contexts(first: 100) { totalCount nodes { ... on CheckRun { name conclusion } ... on StatusContext { context state } } } } } } }"
# Closed/merged PRs read per phase head; a head with more history than this sets `truncated`.
HEAD_HISTORY = 10


def graphql_query(heads: int = 0, numbers: int = 0) -> str:
    """The PR query: every OPEN PR (paged), plus, on the first page only, the closed/merged PRs of each named phase
    head (h<i>) and each named PR number (n<i>, the stack's members). History outside the phase is never read."""
    variables = "".join(f", $h{i}: String!" for i in range(heads)) + "".join(f", $n{i}: Int!" for i in range(numbers))
    extra = "".join(
        f" h{i}: pullRequests(headRefName: $h{i}, states: [CLOSED, MERGED], first: {HEAD_HISTORY}, "
        f"orderBy: {{field: CREATED_AT, direction: DESC}}) {{ totalCount nodes {{ {PR_FIELDS} }} }}" for i in range(heads)
    ) + "".join(f" n{i}: pullRequest(number: $n{i}) {{ {PR_FIELDS} }}" for i in range(numbers))
    return (f"query($owner: String!, $name: String!, $cursor: String{variables}) {{ repository(owner: $owner, name: $name) "
            f"{{ pullRequests(states: [OPEN], first: 100, after: $cursor, orderBy: {{field: CREATED_AT, direction: DESC}}) "
            f"{{ totalCount pageInfo {{ hasNextPage endCursor }} nodes {{ {PR_FIELDS} }} }}{extra} }} }}")


GRAPHQL = graphql_query()
FAILURES = {"FAILURE", "ERROR", "CANCELLED", "TIMED_OUT"}
REQUEST_TIMEOUT_S = 20


def _repo_parts(github_repo: str) -> tuple[str, str]:
    owner, separator, name = github_repo.partition("/")
    if not separator or not owner or not name or "/" in name:
        raise ValueError("github_repo must be owner/name")
    return owner, name


def graphql_argv(github_repo: str, heads: tuple[str, ...] = (), numbers: tuple[int, ...] = ()) -> tuple[str, ...]:
    owner, name = _repo_parts(github_repo)
    # -f passes each head as a raw string variable, so a branch name is never spliced into the query text.
    named = tuple(item for i, head in enumerate(heads) for item in ("-f", f"h{i}={head}")) + tuple(
        item for i, number in enumerate(numbers) for item in ("-F", f"n{i}={int(number)}"))
    return ("gh", "api", "graphql", "-F", f"owner={owner}", "-F", f"name={name}", *named,
            "-f", f"query={graphql_query(len(heads), len(numbers))}")


def rest_argv(github_repo: str) -> tuple[str, ...]:
    _repo_parts(github_repo)
    return ("gh", "api", f"repos/{github_repo}/pulls?state=all&per_page=100")


def quota_argv(github_repo: str) -> tuple[str, ...]:
    _repo_parts(github_repo)
    return ("gh", "api", "rate_limit")


def _quota_entry(resources, resource):
    entry = resources[resource]
    remaining, limit, reset = entry["remaining"], entry["limit"], entry["reset"]
    if any(type(value) is not int for value in (remaining, limit, reset)) or limit <= 0 or remaining < 0 or reset < 0:
        raise ValueError("invalid quota values")
    return remaining, limit, datetime.fromtimestamp(reset, UTC)


class Budget:
    def __init__(self, mode: Literal["graphql", "rest"], code_root: str | Path | None,
                 threshold: int, interval_s: int, now: datetime, previous: GhStatus, github_repo: str):
        self.mode, self.code_root, self.now, self.github_repo = mode, code_root, now, github_repo
        if previous.mode != mode:
            previous = GhStatus(mode, None, None, None, False)
        self.status = replace(previous, mode=mode, quota_threshold=threshold, poll_interval_s=interval_s)

    def run(self, argv, fix, resource: Literal["graphql", "core"] | None = None, **kwargs):
        """Run one GitHub call behind the quota gate. The mode's resource (graphql, or core for rest) pauses all
        reads when it is below the threshold; a call that spends the other resource (`resource`, e.g. the REST
        stack read in graphql mode) is also refused, without a call, when that resource is below the threshold."""
        status = self.status
        if status.paused and status.quota_reset is not None and self.now < status.quota_reset:
            return Err(CommandFailed("command_failed", argv, 1, "GitHub polling paused until reset", "wait for the quota reset"))
        quota = command.run(quota_argv(self.github_repo), "check GitHub quota and retry", cwd=self.code_root,
                            timeout_s=REQUEST_TIMEOUT_S)
        if isinstance(quota, Err):
            return quota
        own_resource = "graphql" if self.mode == "graphql" else "core"
        try:
            resources = json.loads(quota.value.stdout)["resources"]
            remaining, limit, reset_at = _quota_entry(resources, own_resource)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, OverflowError, OSError) as exc:
            return Err(ParseFailed("parse_failed", "github quota", str(exc), "retry the GitHub quota request"))
        other_resource = "core" if own_resource == "graphql" else "graphql"
        try:
            other = _quota_entry(resources, other_resource)
        except (KeyError, TypeError, ValueError, OverflowError, OSError):
            other = (None, None, None)
        core = (remaining, limit, reset_at) if own_resource == "core" else other
        graphql = (remaining, limit, reset_at) if own_resource == "graphql" else other
        paused = remaining * 100 < limit * status.quota_threshold
        self.status = replace(status, quota_remaining=remaining, quota_limit=limit, quota_reset=reset_at,
                              paused=paused, rate_limited=False, core_remaining=core[0], core_limit=core[1],
                              core_reset=core[2], graphql_remaining=graphql[0], graphql_limit=graphql[1],
                              graphql_reset=graphql[2], quota_at=self.now)
        if paused:
            return Err(CommandFailed("command_failed", argv, 1, "GitHub quota below threshold", "wait for quota recovery"))
        if resource is not None and resource != own_resource:
            spent = core if resource == "core" else graphql
            if spent[0] is None or spent[1] is None or spent[0] * 100 < spent[1] * status.quota_threshold:
                return Err(CommandFailed("command_failed", argv, 1, f"GitHub {resource} quota below threshold",
                                         "wait for quota recovery"))
        response = command.run(argv, fix, **kwargs)
        if isinstance(response, Err):
            detail = str(response.error).lower()
        else:
            try:
                body = json.loads(response.value.stdout)
                detail = json.dumps(body.get("errors", [])).lower() if isinstance(body, dict) else ""
            except (json.JSONDecodeError, TypeError):
                detail = ""
        if any(marker in detail for marker in ("rate_limit", "rate limit", "rate-limited", "rate limited", "http 429")):
            self.status = replace(self.status, paused=True, rate_limited=True)
            if isinstance(response, Ok):
                return Err(CommandFailed("command_failed", argv, 1, detail, "wait for the quota reset"))
        return response


def ci_state_of(conclusion: str | None, status: str | None, failed_checks: tuple[str, ...]) -> CiState:
    conclusion = conclusion.upper() if conclusion else None
    status = status.upper() if status else None
    if failed_checks or conclusion in FAILURES:
        return ci_failure_key(failed_checks)
    if conclusion not in (None, "", "PENDING", "EXPECTED", "SUCCESS", "SKIPPED", "NEUTRAL"):
        return CiState.UNKNOWN
    if status not in (None, "", "COMPLETED", "QUEUED", "IN_PROGRESS", "PENDING", "WAITING", "REQUESTED"):
        return CiState.UNKNOWN
    if conclusion in ("PENDING", "EXPECTED") or status in ("QUEUED", "IN_PROGRESS", "PENDING", "WAITING", "REQUESTED"):
        return CiState.RUNNING
    if conclusion == "SUCCESS":
        return CiState.PASS
    if conclusion in (None, "", "SKIPPED", "NEUTRAL"):
        if status not in (None, "", "COMPLETED"):
            return CiState.UNKNOWN
        return CiState.NONE
    return CiState.UNKNOWN


def pr_state_of(state: str, is_draft: bool) -> PrState:
    if state.upper() == "OPEN":
        return PrState.DRAFT if is_draft else PrState.OPEN
    if state.upper() == "MERGED":
        return PrState.MERGED
    if state.upper() == "CLOSED":
        return PrState.CLOSED
    return PrState.UNKNOWN


def _status(mode: Literal["graphql", "rest", "off"], ok: bool | None, error=None, truncated: bool = False) -> GhStatus:
    return GhStatus(mode, ok, error, datetime.now(UTC) if ok is not None else None, truncated)


def _http_status(stderr: str) -> int | None:
    match = re.search(r"HTTP (\d{3})", stderr)
    return int(match.group(1)) if match else None


def _error(mode: Literal["graphql", "rest", "off"], argv: tuple[str, ...], code: int, stderr: str):
    lower = stderr.lower()
    if "timed out" in lower or "timeout" in lower:
        error = Timeout("timeout", argv, REQUEST_TIMEOUT_S, "check GitHub connectivity and retry")
    elif (status := _http_status(stderr)) is not None and (status in (401, 403) or 500 <= status <= 599):
        error = Rejected("rejected", argv, status, stderr, "check GitHub credentials or retry")
    elif "connect" in lower or "dns" in lower or "network" in lower:
        error = Unreachable("unreachable", argv, stderr, "check network connectivity and retry")
    else:
        error = CommandFailed("command_failed", argv, code, stderr, "check gh and retry")
    return Err(error), _status(mode, False, error)


def _from_graphql(node: dict) -> PullRequest:
    rollup = (((node.get("commits") or {}).get("nodes") or [{}])[-1].get("commit") or {}).get("statusCheckRollup") or {}
    contexts = (rollup.get("contexts") or {}).get("nodes") or []
    # CheckRun reports name/conclusion, StatusContext (commit statuses) context/state.
    failed = tuple(str(row.get("name") or row.get("context")) for row in contexts
                   if row.get("conclusion") in FAILURES or row.get("state") in FAILURES)
    state = pr_state_of(node.get("state", "OPEN"), bool(node.get("isDraft")))
    raw_ci = rollup.get("state") or ""
    raw_state = node.get("state", "OPEN")
    return PullRequest(node["number"], node["url"], node["headRefName"], node["baseRefName"], node["headRefOid"],
                       ci_state_of(raw_ci, None, failed), failed, state, raw_ci, raw_state)


THROTTLED = ("GitHub polling paused until reset", "GitHub quota below threshold",
             "GitHub core quota below threshold", "GitHub graphql quota below threshold")


def throttled(error) -> bool:
    """True when the quota gate refused the call before it was made (no GitHub request was sent)."""
    return isinstance(error, CommandFailed) and error.stderr in THROTTLED


def open_prs(mode: Literal["graphql", "rest", "off"], code_root: str | Path | None,
             branch_groups: tuple[tuple[str, ...], ...], budget: Budget | None, github_repo: str,
             heads: tuple[str, ...] = (), numbers: tuple[int, ...] = ()):
    """Pull requests for an explicit GitHub repo, using its checkout as the command directory.

    GraphQL reads every open PR plus the closed/merged history of `heads` (the phase's branches) and the PRs
    `numbers` (the stack's members); REST reads the newest 100 PRs of any state."""
    result, status = _open_prs(mode, code_root, branch_groups, budget, github_repo, heads, numbers)
    if budget is not None:
        status = replace(status, quota_remaining=budget.status.quota_remaining, quota_limit=budget.status.quota_limit,
                         quota_reset=budget.status.quota_reset, paused=budget.status.paused,
                         rate_limited=budget.status.rate_limited, poll_interval_s=budget.status.poll_interval_s,
                         quota_threshold=budget.status.quota_threshold, core_remaining=budget.status.core_remaining,
                         core_limit=budget.status.core_limit, core_reset=budget.status.core_reset,
                         graphql_remaining=budget.status.graphql_remaining, graphql_limit=budget.status.graphql_limit,
                         graphql_reset=budget.status.graphql_reset, quota_at=budget.status.quota_at)
    return result, status


def _open_prs(mode, code_root, branch_groups, budget, github_repo, heads=(), numbers=()):
    if mode == "off":
        return Ok(()), _status("off", None)
    run = budget.run if budget is not None else command.run
    heads = tuple(dict.fromkeys(head for head in heads if head))
    numbers = tuple(dict.fromkeys(numbers))
    argv = graphql_argv(github_repo, heads, numbers) if mode == "graphql" else rest_argv(github_repo)
    completed = run(argv, "check GitHub connectivity and retry", cwd=code_root, timeout_s=REQUEST_TIMEOUT_S)
    if isinstance(completed, Err):
        failure = completed.error
        if isinstance(failure, CommandFailed):
            return _error(mode, failure.argv, failure.code, failure.stderr)
        return completed, _status(mode, False, failure)
    try:
        body = json.loads(completed.value.stdout)
        if mode == "graphql":
            repository = body["data"]["repository"]
            pulls = repository["pullRequests"]
            extra: list[dict] = []
            truncated = False
            for i in range(len(heads)):
                history = repository[f"h{i}"]
                extra.extend(history["nodes"])
                truncated = truncated or history["totalCount"] > len(history["nodes"])
            extra.extend(node for node in (repository[f"n{i}"] for i in range(len(numbers))) if node is not None)
            rows = tuple(_from_graphql(node) for node in pulls["nodes"])
            for node in (*pulls["nodes"], *extra):
                commits = (node.get("commits") or {}).get("nodes") or []
                rollup = ((commits[-1].get("commit") or {}).get("statusCheckRollup") or {}) if commits else {}
                contexts = rollup.get("contexts") or {}
                truncated = truncated or contexts.get("totalCount", len(contexts.get("nodes") or [])) > len(contexts.get("nodes") or [])
            cursors = set()
            page = pulls.get("pageInfo")
            if page is not None and (not isinstance(page, dict) or type(page.get("hasNextPage")) is not bool):
                raise ValueError("invalid GitHub pagination information")
            while page and page["hasNextPage"]:
                cursor = page.get("endCursor")
                if not isinstance(cursor, str) or not cursor or cursor in cursors:
                    raise ValueError("invalid or repeated GitHub pagination cursor")
                cursors.add(cursor)
                page_argv = (*graphql_argv(github_repo), "-f", f"cursor={cursor}")
                response = run(page_argv, "check GitHub connectivity and retry", cwd=code_root, timeout_s=REQUEST_TIMEOUT_S)
                if isinstance(response, Err):
                    return response, _status(mode, False, response.error)
                pulls = json.loads(response.value.stdout)["data"]["repository"]["pullRequests"]
                page = pulls.get("pageInfo")
                if not isinstance(page, dict) or type(page.get("hasNextPage")) is not bool:
                    raise ValueError("invalid GitHub pagination information")
                rows += tuple(_from_graphql(node) for node in pulls["nodes"])
                for node in pulls["nodes"]:
                    commits = (node.get("commits") or {}).get("nodes") or []
                    rollup = ((commits[-1].get("commit") or {}).get("statusCheckRollup") or {}) if commits else {}
                    contexts = rollup.get("contexts") or {}
                    truncated = truncated or contexts.get("totalCount", len(contexts.get("nodes") or [])) > len(contexts.get("nodes") or [])
            if "pageInfo" not in pulls and pulls["totalCount"] > 100:
                if budget is not None:
                    raise ValueError("missing GitHub pagination information")
                truncated = True
            seen = {pr.number for pr in rows}
            for node in extra:
                if node["number"] not in seen:
                    seen.add(node["number"])
                    rows += (_from_graphql(node),)
        else:
            rows = tuple(PullRequest(row["number"], row["html_url"], row["head"]["ref"], row["base"]["ref"], row["head"]["sha"], CiState.NONE, (), pr_state_of("MERGED" if row.get("merged_at") else row["state"], bool(row.get("draft"))), "", row["state"]) for row in body)
            truncated = len(rows) >= 100
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError, IndexError, ValueError) as exc:
        # A body that is not JSON, or JSON of the wrong shape, is one typed failure; GitHub failing never stops work.
        error = ParseFailed("parse_failed", f"github {mode} response", f"{type(exc).__name__}: {exc}", "retry the GitHub request")
        return Err(error), _status(mode, False, error)
    if mode == "rest" and branch_groups:
        selected: dict[int, PullRequest] = {}
        for branches in branch_groups:
            matching = (pr for pr in rows if pr.head in branches)
            pr = select_pr(matching)
            if pr is not None:
                selected[pr.number] = pr
        updates: dict[int, PullRequest] = {}
        for pr in selected.values():
            checks_argv = ("gh", "api", f"repos/{github_repo}/commits/{pr.head_sha}/check-runs?per_page=100")
            response = run(checks_argv, "check GitHub connectivity and retry", cwd=code_root,
                                   timeout_s=REQUEST_TIMEOUT_S)
            if isinstance(response, Err):
                return response, _status(mode, False, response.error)
            try:
                checks = json.loads(response.value.stdout)
                runs = checks["check_runs"]
                truncated = truncated or checks["total_count"] > len(runs)
                failed = tuple(str(run["name"]) for run in runs if (run.get("conclusion") or "").upper() in FAILURES)
                statuses = tuple((run.get("status") or "").upper() for run in runs)
                unexpected_status = next((status for status in statuses if status not in (
                    "", "COMPLETED", "QUEUED", "IN_PROGRESS", "PENDING", "WAITING", "REQUESTED")), "")
                running = any(status in ("QUEUED", "IN_PROGRESS", "PENDING", "WAITING", "REQUESTED")
                              for status in statuses)
                success = any((run.get("conclusion") or "").upper() == "SUCCESS" for run in runs)
                unexpected = next((str(run.get("conclusion")) for run in runs
                                   if run.get("conclusion") and str(run["conclusion"]).upper()
                                   not in (*FAILURES, "SUCCESS", "SKIPPED", "NEUTRAL")), "")
                ci = ci_state_of(unexpected or ("SUCCESS" if success else None),
                                 unexpected_status or ("IN_PROGRESS" if running else None), failed)
                updates[pr.number] = replace(pr, ci=ci, failed_checks=failed, raw_ci=unexpected or unexpected_status)
            except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
                error = ParseFailed("parse_failed", "github rest check-runs", str(exc), "retry the GitHub request")
                return Err(error), _status(mode, False, error)
        rows = tuple(updates.get(pr.number, pr) for pr in rows)
    return Ok(rows), _status(mode, True, truncated=truncated)


def stack_argv(github_repo: str, number: int) -> tuple[str, ...]:
    _repo_parts(github_repo)
    return ("gh", "api", f"repos/{github_repo}/stacks/{int(number)}")


def stack_membership(mode: Literal["graphql", "rest", "off"], code_root: str | Path | None,
                     github_repo: str, number: int, trunk: str,
                     budget: Budget | None = None) -> Result[tuple[int, ...]]:
    """The PR numbers registered in the hosted stack, in stack order: base first, top last.

    This is the canonical membership for top-PR selection: a PR absent from this list is not
    linked in the stack, whatever layer its sprint claims, and must never be named the top.
    The stack must be built on the configured trunk; a stack on any other base is the wrong
    stack and is refused. With a budget the read goes through the same quota gate as the PR read.
    """
    argv = stack_argv(github_repo, number)
    if mode == "off":
        return Err(Rejected("rejected", argv, 0, "github reads are off", "set console.github to graphql or rest"))
    if budget is not None:
        result = budget.run(argv, "check the phase stack membership on GitHub", resource="core", cwd=code_root,
                            timeout_s=REQUEST_TIMEOUT_S)
    else:
        result = command.run(argv, "check the phase stack membership on GitHub", cwd=code_root,
                             timeout_s=REQUEST_TIMEOUT_S)
    if isinstance(result, Err):
        return result
    try:
        view = json.loads(result.value.stdout)
    except ValueError as error:
        return Err(ParseFailed("parse_failed", "stack", str(error), "check the GitHub stack API response"))
    rows = view.get("pull_requests") if isinstance(view, dict) else None
    if not isinstance(rows, list):
        return Err(ParseFailed("parse_failed", "stack", "no pull_requests list",
                              "check the GitHub stack API response; stack membership names the linked PRs"))
    base = view.get("base")
    base_ref = base.get("ref") if isinstance(base, dict) else None
    if not isinstance(base_ref, str):
        return Err(ParseFailed("parse_failed", "stack", "no base.ref",
                              "check the GitHub stack API response; the stack's base is its trunk"))
    if base_ref != trunk:
        return Err(ConfigInvalid("config_invalid", "console.stack.trunk", repr(base_ref),
                                 f"stack {number} is built on {base_ref}, not {trunk}; set console.stack.number "
                                 f"to the stack on {trunk} or correct console.stack.trunk"))
    return Ok(tuple(int(row["number"]) for row in rows
                    if isinstance(row, dict) and isinstance(row.get("number"), int)))
