#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pydantic>=2", "pyyaml", "sc-compose>=1.7.0,<2", "atm-bd-types==0.20.0"]
# ///
# pyright: strict
"""Validated provider commands and their argv-only execution boundary."""
from __future__ import annotations

import json
import subprocess
import tempfile
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TypeAlias

from atm_bd_types import BodyTransport, Error, ErrorDetail, ErrorKind, OutputFormat, PrOp, PrRef, MergedPrRef, ProviderCommands
from core_paths import core_templates_dir
from result import Err, Ok, Result
from sprint_index_common import is_json_object

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


def _problem(kind: ErrorKind, message: str, fix: str) -> Err:
    return Err(Error(kind, message, fix))


def load_provider(repo_config: Mapping[str, object]) -> Result[ProviderCommands]:
    """Load and validate the configured command set, defaulting to GitHub."""
    name = repo_config.get("provider", "github")
    if name not in ("github", "azure"):
        return _problem(ErrorKind.CONFIG_INVALID, f"unknown provider {name!r}", "Set provider to github or azure.")
    if name == "azure":
        azure = repo_config.get("azure")
        for key in ("organization", "project", "repository"):
            value: object = azure.get(key) if is_json_object(azure) else None
            if not isinstance(value, str) or not value.strip():
                return _problem(ErrorKind.CONFIG_MISSING, f"azure.{key} is missing", f"Set azure.{key} in the repository config.")
    templates = core_templates_dir()
    if isinstance(templates, Err):
        return templates
    path = templates.value / "providers" / f"{name}.json"
    try:
        contents = path.read_text(encoding="utf-8")
    except OSError as exc:
        return _problem(ErrorKind.NOT_FOUND, f"{path}: {exc}", "Install atm-bd core templates.")
    commands, failure = ProviderCommands.parse_json(contents)
    if failure is not None:
        return Err(failure)
    if commands is None:
        return _problem(ErrorKind.PROVIDER_INVALID, f"{path}: provider validation returned no result", "Repair the provider file.")
    return Ok(commands)


def validate_installer_provider(provider: object, identity: object) -> Result[dict[str, str]]:
    """Validate provider selection and return the install-time config values."""
    if provider not in ("github", "azure"):
        return _problem(ErrorKind.PROVIDER_INVALID, f"unknown provider {provider!r}", "Select github or azure.")
    assert isinstance(provider, str)
    values = {"provider": provider}
    if provider == "azure":
        for key in ("organization", "project", "repository"):
            value: object = identity.get(key) if is_json_object(identity) else None
            if not isinstance(value, str) or not value.strip():
                return _problem(ErrorKind.CONFIG_MISSING, f"azure.{key} is missing", f"Set azure.{key} in the repository config or agent registry.")
            values[f"azure_{key}"] = value
    return Ok(values)


def operation_name(op: PrOp) -> str:
    """Name every provider operation explicitly for exhaustive type checking."""
    match op:
        case PrOp.CREATE: return "create"
        case PrOp.VIEW: return "view"
        case PrOp.EDIT_BASE: return "edit_base"
        case PrOp.EDIT_BODY: return "edit_body"
        case PrOp.COMMENT: return "comment"
        case PrOp.COMMENT_VIEW: return "comment_view"
        case PrOp.CHECKS: return "checks"
        case PrOp.LOOKUP_BY_HEAD: return "lookup_by_head"
        case PrOp.STACK_LINK: return "stack_link"
        case PrOp.STACK_VIEW: return "stack_view"


def _azure_invoke_payload(op: PrOp, values: Mapping[str, str], body_text: str) -> dict[str, JsonValue] | None:
    """Build Azure DevOps REST request bodies inside the provider adapter."""
    match op:
        case PrOp.COMMENT:
            return {"comments": [{"parentCommentId": 0, "content": body_text, "commentType": 1}], "status": 1}
        case PrOp.CREATE:
            def branch_ref(name: str) -> str:
                ref = values[name]
                return ref if ref.startswith("refs/heads/") else f"refs/heads/{ref}"

            return {
                "sourceRefName": branch_ref("head"),
                "targetRefName": branch_ref("base"),
                "title": values["title"],
                "description": body_text,
            }
        case _:
            return None


def _uses_azure_invoke_json_body(argv: list[str], op: PrOp) -> bool:
    return argv[:3] == ["az", "devops", "invoke"] and op in (PrOp.CREATE, PrOp.COMMENT)


def execute(commands: ProviderCommands, op: PrOp, values: Mapping[str, str | list[str]], *, cwd: Path,
            runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
            accept_merged: Callable[[MergedPrRef], bool] | None = None) -> Result[PrRef | MergedPrRef | JsonValue]:
    """Execute one configured command, sending JSON bodies through a temporary file."""
    command = commands.command(operation_name(op))
    if command is None:
        return _problem(ErrorKind.PROVIDER_INVALID, f"missing provider operation {operation_name(op)}", "Repair the provider file.")
    # The template-facing Azure command re-enters this adapter. Execute the
    # underlying REST invocation here, avoiding recursive CLI execution.
    command_argv = command.argv
    if op == PrOp.COMMENT and command_argv[:5] == ["uv", "run", "--script", ".atm-bd/scripts/providers.py", "exec"]:
        command_argv = ["az", "devops", "invoke", "--area", "git", "--resource", "pullRequestThreads",
                        "--route-parameters", "project={project}", "repositoryId={repository}",
                        "pullRequestId={number}", "--org", "https://dev.azure.com/{organization}",
                        "--http-method", "POST", "--in-file", "{body_file}"]
    if not command_argv:  # Azure stack link is intentionally a no-op.
        return Ok(None)
    with tempfile.TemporaryDirectory(prefix="atm-bd-provider-") as directory:
        substitutions = {key: value for key, value in values.items() if isinstance(value, str)}
        lists = {key: value for key, value in values.items() if isinstance(value, list)}
        # GitHub's CLI resolves these two placeholders from the current repository.
        substitutions.setdefault("owner", "{owner}")
        substitutions.setdefault("repo", "{repo}")
        if op == PrOp.VIEW:
            substitutions.setdefault("fields", "number,url,baseRefName,mergedAt,mergeCommit,body,headRefOid,updatedAt,author,isDraft")
            substitutions.setdefault("jq", "@" if command_argv[0] == "az" else ".")
        if op == PrOp.LOOKUP_BY_HEAD:
            substitutions.setdefault("state", "open")
            if command.argv[0] == "az":
                substitutions["state"] = {"open": "active", "merged": "completed"}.get(substitutions["state"], substitutions["state"])
            elif substitutions["state"] == "merged":
                substitutions["state"] = "closed"
        if command.body == BodyTransport.FILE and _uses_azure_invoke_json_body(command_argv, op):
            try:
                body_text = Path(substitutions["body_file"]).read_text(encoding="utf-8")
                payload = _azure_invoke_payload(op, substitutions, body_text)
                if payload is None:
                    return _problem(ErrorKind.PROVIDER_INVALID, "unsupported Azure invoke body operation", "Repair the provider command configuration.")
                body = Path(directory) / "body.json"
                body.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                substitutions["body_file"] = str(body)
            except KeyError as exc:
                return _problem(ErrorKind.CONFIG_MISSING, f"missing provider value {exc}", "Supply the required provider value.")
            except OSError as exc:
                return _problem(ErrorKind.IO_FAILED, str(exc), "Check temporary directory access and provider JSON.")
        try:
            argv: list[str] = []
            for argument in command_argv:
                if argument.startswith("{") and argument.endswith("}") and argument[1:-1] in lists:
                    argv.extend(lists[argument[1:-1]])
                else:
                    argv.append(argument.format_map(substitutions))
        except KeyError as exc:
            return _problem(ErrorKind.CONFIG_MISSING, f"missing provider value {exc}", "Supply the required provider value.")
        try:
            completed = (runner or subprocess.run)(argv, cwd=cwd, capture_output=True, text=True, check=False, timeout=180)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return _problem(ErrorKind.UNREACHABLE, str(exc), "Install the provider CLI and verify connectivity.")
        if completed.returncode:
            return Err(Error(ErrorKind.COMMAND_FAILED, completed.stderr, "Inspect the provider command output.",
                             ErrorDetail.CommandFailed(argv, completed.returncode, completed.stderr)))
        match command.output:
            case OutputFormat.EXIT_CODE:
                return Ok(None)
            case OutputFormat.TEXT:
                return Ok(completed.stdout.strip())
            case OutputFormat.JSON:
                pass
        try:
            parsed: JsonValue = json.loads(completed.stdout)
        except ValueError as exc:
            return _problem(ErrorKind.PARSE_FAILED, str(exc), "Inspect the provider JSON output.")
        if op == PrOp.LOOKUP_BY_HEAD and isinstance(parsed, list):
            if values.get("state") == "merged":
                fields = command.result
                for item in parsed:
                    number = field_at(item, fields.get("number", ""))
                    url = field_at(item, fields.get("url", ""))
                    base = field_at(item, fields.get("base", ""))
                    merged = field_at(item, fields.get("merged_at", ""))
                    commit = field_at(item, fields.get("merge_commit", ""))
                    if (isinstance(number, (str, int)) and isinstance(url, str) and isinstance(base, str)
                            and isinstance(merged, str) and merged and isinstance(commit, str) and commit):
                        candidate = MergedPrRef(str(number), url, base.removeprefix("refs/heads/"), merged, commit)
                        if accept_merged is None or accept_merged(candidate):
                            return Ok(candidate)
                return _problem(ErrorKind.NOT_FOUND, "no matching merged pull request", "Check the branch and provider repository.")
            if values.get("head_sha"):
                key = command.result.get("head_sha", "")
                parsed = [item for item in parsed if field_at(item, key) == values["head_sha"]]
            if not parsed:
                return _problem(ErrorKind.NOT_FOUND, "no pull request matches the head", "Check the branch and provider repository.")
            if len(parsed) > 1:
                return _problem(ErrorKind.REJECTED, f"{len(parsed)} pull requests match the head", "Close duplicate pull requests.")
            parsed = parsed[0]
        if op == PrOp.LOOKUP_BY_HEAD and isinstance(parsed, dict):
            fields = command.result
            number, url, base = (field_at(parsed, fields.get(name, "")) for name in ("number", "url", "base"))
            if number in (None, "", 0):
                return _problem(ErrorKind.CONFIG_MISSING, "pr_number is empty", "Repair the pull request identity.")
            if isinstance(number, (str, int)) and isinstance(url, str) and isinstance(base, str):
                normalized = base.removeprefix("refs/heads/")
                if values.get("state") == "merged":
                    merged = field_at(parsed, fields.get("merged_at", ""))
                    commit = field_at(parsed, fields.get("merge_commit", ""))
                    if isinstance(merged, str) and isinstance(commit, str) and merged and commit:
                        return Ok(MergedPrRef(str(number), url, normalized, merged, commit))
                    return _problem(ErrorKind.PARSE_FAILED, "merged pull request lacks merge metadata", "Check the provider field mapping.")
                head_sha = field_at(parsed, fields.get("head_sha", ""))
                if not isinstance(head_sha, str) or not head_sha:
                    return _problem(ErrorKind.PARSE_FAILED, "pull request lacks head SHA", "Check the provider field mapping.")
                draft = field_at(parsed, fields.get("draft", ""))
                if not isinstance(draft, bool):
                    return _problem(ErrorKind.PARSE_FAILED, "pull request lacks draft status", "Check the provider field mapping.")
                return Ok(PrRef(str(number), url, normalized, head_sha, draft))
            return _problem(ErrorKind.PARSE_FAILED, "provider result lacks number, url or base", "Check the provider field mapping.")
        return Ok(parsed)


def field_at(value: JsonValue, path: str) -> JsonValue:
    """Read a named nested field from provider JSON, including array indexes."""
    current = value
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdecimal() and int(part) < len(current):
            current = current[int(part)]
        else:
            return None
    return current


def render_context(config: Mapping[str, object]) -> Result[dict[str, str]]:
    """Supply shell-quoted argv with placeholders intact for dispatch templates."""
    import shlex

    loaded = load_provider(config)
    if isinstance(loaded, Err):
        return loaded
    result: dict[str, str] = {}
    for op in (PrOp.CREATE, PrOp.VIEW, PrOp.EDIT_BASE, PrOp.EDIT_BODY, PrOp.COMMENT, PrOp.COMMENT_VIEW,
               PrOp.CHECKS, PrOp.LOOKUP_BY_HEAD, PrOp.STACK_LINK, PrOp.STACK_VIEW):
        name = operation_name(op)
        command = loaded.value.command(name)
        if command is None:
            return _problem(ErrorKind.PROVIDER_INVALID, f"missing provider operation {name}", "Repair the provider file.")
        argv = command.argv
        identity = config.get("azure")
        if config.get("provider") == "azure" and is_json_object(identity):
            for key in ("organization", "project", "repository"):
                value = identity.get(key)
                if isinstance(value, str):
                    argv = [arg.replace("{" + key + "}", value) for arg in argv]
        result[name] = shlex.join(argv)
    return Ok(result)


def cli_execute(args: list[str], config: Mapping[str, object], *, cwd: Path,
                stdin: str | None = None, runner: Callable[..., subprocess.CompletedProcess[str]] | None = None) -> Result[PrRef | MergedPrRef | JsonValue]:
    """Execute a provider operation from an argv list using the same adapter boundary."""
    if len(args) < 2 or args[0] != "exec":
        return _problem(ErrorKind.CONFIG_INVALID, "expected exec <operation>", "Use providers.py exec comment --set number=... --body-file FILE.")
    operations = {operation_name(op): op for op in (PrOp.CREATE, PrOp.VIEW, PrOp.EDIT_BASE, PrOp.EDIT_BODY,
                  PrOp.COMMENT, PrOp.COMMENT_VIEW, PrOp.CHECKS, PrOp.LOOKUP_BY_HEAD, PrOp.STACK_LINK, PrOp.STACK_VIEW)}
    op = operations.get(args[1])
    if op is None:
        return _problem(ErrorKind.PROVIDER_INVALID, f"unknown operation {args[1]!r}", "Select a configured provider operation.")
    values: dict[str, str] = {}
    identity = config.get("azure")
    if is_json_object(identity):
        for key in ("organization", "project", "repository"):
            value = identity.get(key)
            if isinstance(value, str):
                values[key] = value
    index = 2
    while index < len(args):
        if index + 1 >= len(args):
            return _problem(ErrorKind.CONFIG_INVALID, "missing option value", "Supply --set KEY=VALUE or --body-file FILE.")
        option, value = args[index:index + 2]
        if option == "--set" and "=" in value:
            key, item = value.split("=", 1)
            values[key] = item
        elif option == "--body-file":
            values["body_file"] = value
        else:
            return _problem(ErrorKind.CONFIG_INVALID, f"unknown option {option!r}", "Use --set KEY=VALUE or --body-file FILE.")
        index += 2
    commands = load_provider(config)
    if isinstance(commands, Err):
        return commands
    if values.get("body_file") == "-":
        if stdin is None:
            return _problem(ErrorKind.CONFIG_MISSING, "stdin body missing", "Pipe the Markdown body into the command.")
        try:
            with tempfile.TemporaryDirectory(prefix="atm-bd-provider-input-") as directory:
                body = Path(directory) / "body.md"
                body.write_text(stdin, encoding="utf-8")
                values["body_file"] = str(body)
                return execute(commands.value, op, values, cwd=cwd, runner=runner)
        except OSError as error:
            return _problem(ErrorKind.IO_FAILED, str(error), "Check access to the temporary directory.")
    return execute(commands.value, op, values, cwd=cwd, runner=runner)


def main() -> int:
    import repo_config
    try:
        config = repo_config.load()
    except repo_config.ConfigError as error:
        print(f"CONFIG_INVALID: {error}; repair or install atm-bd configuration", file=sys.stderr)
        return 1
    result = cli_execute(sys.argv[1:], config, cwd=Path.cwd(), stdin=sys.stdin.read() if "-" in sys.argv else None)
    if isinstance(result, Err):
        print(f"{result.error.kind}: {result.error.message}; {result.error.fix}", file=sys.stderr)
        return 1
    value = result.value
    if isinstance(value, MergedPrRef):
        print(json.dumps({"number": value.number, "url": value.url, "base": value.base,
                          "merged_at": value.merged_at, "merge_commit": value.merge_commit}))
    elif isinstance(value, PrRef):
        print(json.dumps({"number": value.number, "url": value.url, "base": value.base, "head_sha": value.head_sha}))
    else:
        print(json.dumps(value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
