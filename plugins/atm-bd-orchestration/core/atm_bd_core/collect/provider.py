"""Provider reads: command names and remote matching live in providers.toml."""

import json
import tomllib
from pathlib import Path
from subprocess import SubprocessError
from urllib.parse import urlsplit

from atm_bd_types import CheckState, CollectError, FactKind, PrBase, TopChecks


def _table():
    with (Path(__file__).parent.parent / "providers.toml").open("rb") as stream:
        return tomllib.load(stream)


def resolve_provider(runner, configured):
    try:
        table = _table()
    except (OSError, RuntimeError, SubprocessError, ValueError, TypeError, KeyError) as error:
        return None, f"Cannot load provider command table: {error}"
    if configured:
        if configured in table:
            return table[configured], None
        return None, f"Unknown provider {configured!r}; set provider in the phase file."
    argv = ["git", "remote", "get-url", "origin"]
    try:
        result = runner.run(argv, None)
        if result.code:
            raise ValueError(result.stderr or f"exit {result.code}")
        remote = result.stdout.strip().lower()
        host = urlsplit(remote).hostname if "://" in remote else remote.split("@")[-1].split(":")[0]
        for provider in table.values():
            if host and any(host == item or host.endswith("." + item) for item in provider["hosts"]):
                return provider, None
        raise ValueError(f"unrecognized remote {remote!r}")
    except (OSError, RuntimeError, SubprocessError, ValueError, TypeError, KeyError) as error:
        return None, f"{error}; set provider in the phase file."


def _run(runner, template, pr):
    argv = [part.replace("{pr}", str(pr)) for part in template]
    result = runner.run(argv, None)
    if result.code:
        raise ValueError(result.stderr or f"exit {result.code}")
    return result.stdout


def top_checks(runner, provider, layer):
    argv = [part.replace("{pr}", str(layer.pr)) for part in provider["head"]]
    try:
        head = _run(runner, provider["head"], layer.pr).strip()
        if head.lower() != layer.head.lower():
            raise ValueError(f"pull request head {head!r} differs from recorded head {layer.head}")
        argv = [part.replace("{pr}", str(layer.pr)) for part in provider["checks"]]
        states = json.loads(_run(runner, provider["checks"], layer.pr))
        argv = [part.replace("{pr}", str(layer.pr)) for part in provider["head"]]
        if _run(runner, provider["head"], layer.pr).strip().lower() != layer.head.lower():
            raise ValueError("pull request head changed during check collection")
        if not isinstance(states, list) or any(not isinstance(state, str) for state in states):
            raise ValueError("expected list of check states")
        states = [state.lower() for state in states]
        if any(state in {"failure", "failed", "error", "cancelled", "timed_out", "action_required"} for state in states):
            state = CheckState.FAILING
        elif any(state in {"pending", "queued", "in_progress", "notset", "running", "expected", "waiting", "requested", "inprogress", ""} for state in states):
            state = CheckState.PENDING
        elif not states:
            state = CheckState.NONE
        elif all(state in {"success", "succeeded", "neutral", "skipped"} for state in states):
            state = CheckState.PASSING
        else:
            raise ValueError(f"unknown check states: {states}")
        return TopChecks(layer.head, state), None
    except (OSError, RuntimeError, SubprocessError, ValueError, TypeError, KeyError) as error:
        return None, CollectError(FactKind.TOP_CHECKS, argv, str(error), "Check provider access and retry.")


def pr_bases(runner, provider, layers):
    bases = []
    for layer in layers:
        argv = [part.replace("{pr}", str(layer.pr)) for part in provider["base"]]
        try:
            base = _run(runner, provider["base"], layer.pr).strip().removeprefix("refs/heads/")
            if not base:
                raise ValueError("empty pull request base")
            bases.append(PrBase(layer.pr, base))
        except (OSError, RuntimeError, SubprocessError, ValueError, TypeError, KeyError) as error:
            return None, CollectError(FactKind.PR_BASES, argv, str(error), "Check provider access and retry.")
    return bases, None
