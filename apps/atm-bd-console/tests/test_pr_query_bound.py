"""The GraphQL PR read fetches only what the console uses, in one call per poll on a large repository.

The fake gh below is a 2,250-PR repository that answers the PR query the way GitHub does: it honours the
states filter, headRefName filters, pullRequest(number:) lookups and cursor paging, and records every call.
"""

from __future__ import annotations

import json
import re
from datetime import timedelta

import pytest
from test_stack_cadence import (
    QUOTA_ARGV,
    REAL_OPEN_PRS,
    REAL_STACK_MEMBERSHIP,
    REPO,
    STACK_ARGV,
    T0,
    TRUNK,
    World,
    stack_body,
    tick,
)

from atm_bd_console import github_source, runner
from atm_bd_console.command import Output
from atm_bd_console.enums import PrState
from atm_bd_console.result import Ok

TOTAL = 2250
# Phase PRs: bk-1 merged long ago (deep in history), bk-2 and bk-3 open and linked in the stack.
PHASE_PRS = {100: ("sprint/bk-1", TRUNK, "MERGED"), 2249: ("sprint/bk-2", TRUNK, "OPEN"),
             2250: ("sprint/bk-3", "sprint/bk-2", "OPEN")}
OPEN_FILLER = set(range(2200, 2220))  # other teams' open PRs


def pr_row(number: int) -> dict:
    head, base, state = PHASE_PRS.get(number, (f"other/{number}", "main", "OPEN" if number in OPEN_FILLER else "MERGED"))
    return {"number": number, "url": f"https://x/{number}", "state": state, "isDraft": False, "headRefName": head,
            "baseRefName": base, "headRefOid": f"sha{number}", "commits": {"nodes": []}}


class LargeRepo:
    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.calls: list[str] = []
        self.rows = [pr_row(number) for number in range(TOTAL, 0, -1)]  # CREATED_AT DESC
        real_run = github_source.command.run
        repo = self

        def run(argv, *args, **kwargs):
            argv = tuple(argv)
            if argv[:1] != ("gh",):
                return real_run(argv, *args, **kwargs)
            if argv == QUOTA_ARGV:
                repo.calls.append("rate_limit")
                body = {"resources": {name: {"remaining": 4000, "limit": 5000, "reset": int((T0 + timedelta(hours=1)).timestamp())}
                                      for name in ("graphql", "core")}}
            elif argv == STACK_ARGV:
                repo.calls.append("stack")
                body = stack_body((2249, 2250))
            elif argv[:3] == ("gh", "api", "graphql"):
                repo.calls.append("graphql")
                body = repo.answer(argv)
            else:
                raise AssertionError(f"unexpected command {argv}")
            return Ok(Output(0, json.dumps(body)))

        monkeypatch.setattr(github_source.command, "run", run)

    def answer(self, argv) -> dict:
        fields = dict(argv[index + 1].split("=", 1) for index in range(len(argv) - 1) if argv[index] in ("-f", "-F"))
        query = fields["query"]
        found = re.search(r"pullRequests\(states: \[([A-Z, ]+)\]", query)
        assert found is not None, query
        states = found.group(1).split(", ")
        offset = int(fields["cursor"][1:]) if "cursor" in fields else 0
        main = [row for row in self.rows if row["state"] in states]
        page = main[offset:offset + 100]
        more = offset + 100 < len(main)
        repository: dict = {"pullRequests": {"totalCount": len(main), "nodes": page,
                                             "pageInfo": {"hasNextPage": more, "endCursor": f"p{offset + 100}" if more else None}}}
        for alias, variable in re.findall(r"(h\d+): pullRequests\(headRefName: \$(h\d+)", query):
            matching = [row for row in self.rows if row["headRefName"] == fields[variable] and row["state"] != "OPEN"]
            repository[alias] = {"totalCount": len(matching), "nodes": matching[:10]}
        for alias, variable in re.findall(r"(n\d+): pullRequest\(number: \$(n\d+)\)", query):
            number = int(fields[variable])
            repository[alias] = pr_row(number) if 1 <= number <= TOTAL else None
        return {"data": {"repository": repository}}


@pytest.fixture
def large(monkeypatch):
    world = World(monkeypatch)
    monkeypatch.setattr(runner.github_source, "open_prs", REAL_OPEN_PRS)
    monkeypatch.setattr(runner.github_source, "stack_membership", REAL_STACK_MEMBERSHIP)
    return world, LargeRepo(monkeypatch)


def test_one_graphql_call_per_poll_on_a_2250_pr_repository(large, tmp_path) -> None:
    world, repo = large
    for seconds in range(0, 1260, 60):  # 21 one-minute ticks, polls at 0s, 600s, 1200s
        world.now = T0 + timedelta(seconds=seconds)
        tick(world, tmp_path)

    assert repo.calls.count("graphql") == 3, f"{repo.calls.count('graphql')} GraphQL calls for 3 polls"
    assert repo.calls == ["rate_limit", "stack", "rate_limit", "graphql"] * 3


def test_the_bounded_read_keeps_every_pr_the_model_uses(large, tmp_path) -> None:
    world, _ = large
    snapshot, _ = tick(world, tmp_path)

    rows = {row.pr.number: row.pr for row in snapshot.prs}
    assert set(rows) == {100, 2249, 2250}, "every phase-branch PR, including one merged 2,150 PRs ago"
    assert rows[100].state is PrState.MERGED
    assert snapshot.top_pr == 2250
    assert "stack_snapshot:stale" not in {problem.key for problem in snapshot.problems}


def test_graphql_query_names_the_phase_heads_and_stack_numbers() -> None:
    argv = github_source.graphql_argv(REPO, heads=("sprint/bk-1", 'odd"name'), numbers=(2249,))
    fields = dict(argv[index + 1].split("=", 1) for index in range(len(argv) - 1) if argv[index] in ("-f", "-F"))

    assert "pullRequests(states: [OPEN]," in fields["query"], "history comes only from the named heads"
    assert (fields["h0"], fields["h1"], fields["n0"]) == ("sprint/bk-1", 'odd"name', "2249")
    assert "h1: pullRequests(headRefName: $h1, states: [CLOSED, MERGED]" in fields["query"]
    assert "n0: pullRequest(number: $n0)" in fields["query"]


def test_a_head_with_more_history_than_is_read_marks_the_read_truncated(monkeypatch) -> None:
    rows = [pr_row(100)]
    body = {"data": {"repository": {
        "pullRequests": {"totalCount": 0, "nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}},
        "h0": {"totalCount": github_source.HEAD_HISTORY + 1, "nodes": rows},
        "n0": None,  # a stack number GitHub no longer resolves is absent, not an error
    }}}
    monkeypatch.setattr(github_source.command, "run", lambda *_args, **_kwargs: Ok(Output(0, json.dumps(body))))

    result, status = github_source.open_prs("graphql", "/code", (), None, REPO, ("sprint/bk-1",), (9999,))

    assert isinstance(result, Ok) and [pr.number for pr in result.value] == [100]
    assert status.truncated is True
