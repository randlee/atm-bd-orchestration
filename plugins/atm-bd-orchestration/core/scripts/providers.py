# pyright: strict
"""Validated provider commands and their argv-only execution boundary."""
from __future__ import annotations

import json
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TypeAlias

from atm_bd_types import BodyTransport, Error, ErrorDetail, ErrorKind, OutputFormat, PrOp, PrRef, MergedPrRef, ProviderCommands
from core_paths import core_templates_dir
from result import Err, Ok, Result
from sprint_index_common import is_json_object, is_json_value

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


def operation_name(op: PrOp) -> str:
    """Name every provider operation explicitly for exhaustive type checking."""
    match op:
        case PrOp.CREATE: return "create"
        case PrOp.VIEW: return "view"
        case PrOp.EDIT_BASE: return "edit_base"
        case PrOp.COMMENT: return "comment"
        case PrOp.COMMENT_VIEW: return "comment_view"
        case PrOp.CHECKS: return "checks"
        case PrOp.LOOKUP_BY_HEAD: return "lookup_by_head"
        case PrOp.STACK_LINK: return "stack_link"
        case PrOp.STACK_VIEW: return "stack_view"


def uses_json_file(transport: BodyTransport) -> bool:
    match transport:
        case BodyTransport.NONE: return False
        case BodyTransport.FILE: return False
        case BodyTransport.JSON_FILE: return True


def execute(commands: ProviderCommands, op: PrOp, values: Mapping[str, str], *, cwd: Path,
            runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
            accept_merged: Callable[[MergedPrRef], bool] | None = None) -> Result[PrRef | MergedPrRef | JsonValue]:
    """Execute one configured command, sending JSON bodies through a temporary file."""
    command = commands.command(operation_name(op))
    if command is None:
        return _problem(ErrorKind.PROVIDER_INVALID, f"missing provider operation {operation_name(op)}", "Repair the provider file.")
    if not command.argv:  # Azure stack link is intentionally a no-op.
        return Ok(None)
    with tempfile.TemporaryDirectory(prefix="atm-bd-provider-") as directory:
        substitutions = dict(values)
        if op == PrOp.LOOKUP_BY_HEAD:
            substitutions.setdefault("state", "open")
            if command.argv[0] == "az":
                substitutions["state"] = {"open": "active", "merged": "completed"}.get(substitutions["state"], substitutions["state"])
        if uses_json_file(command.body):
            if command.payload_json is None:
                return _problem(ErrorKind.CONFIG_MISSING, "JSON payload is missing", "Supply the provider payload.")
            try:
                payload: object = json.loads(command.payload_json)
                if not is_json_object(payload):
                    return _problem(ErrorKind.PROVIDER_INVALID, "JSON payload is not an object", "Repair the provider file.")
                if op == PrOp.COMMENT:
                    comments: object = payload.get("comments")
                    if not is_json_value(comments) or not isinstance(comments, list) or not comments or not is_json_object(comments[0]):
                        return _problem(ErrorKind.PROVIDER_INVALID, "JSON payload has no comment", "Repair the provider file.")
                    comments[0]["content"] = substitutions["text"]
                elif op == PrOp.CREATE:
                    for field, name in (("sourceRefName", "head"), ("targetRefName", "base")):
                        ref = substitutions[name]
                        payload[field] = ref if ref.startswith("refs/heads/") else f"refs/heads/{ref}"
                    payload["title"] = substitutions["title"]
                    payload["description"] = Path(substitutions["body_file"]).read_text(encoding="utf-8")
                else:
                    return _problem(ErrorKind.PROVIDER_INVALID, "unsupported JSON body operation", "Repair the provider file.")
                body = Path(directory) / "body.json"
                body.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                substitutions["body_file"] = str(body)
            except KeyError as exc:
                return _problem(ErrorKind.CONFIG_MISSING, f"missing provider value {exc}", "Supply the required provider value.")
            except (OSError, ValueError) as exc:
                return _problem(ErrorKind.IO_FAILED, str(exc), "Check temporary directory access and provider JSON.")
        try:
            argv = [argument.format_map(substitutions) for argument in command.argv]
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
            number, url, base = (parsed.get(fields.get(name, "")) for name in ("number", "url", "base"))
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
                return Ok(PrRef(str(number), url, normalized, head_sha))
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
    for op in (PrOp.CREATE, PrOp.VIEW, PrOp.EDIT_BASE, PrOp.COMMENT, PrOp.COMMENT_VIEW,
               PrOp.CHECKS, PrOp.LOOKUP_BY_HEAD, PrOp.STACK_LINK, PrOp.STACK_VIEW):
        name = operation_name(op)
        command = loaded.value.command(name)
        if command is None:
            return _problem(ErrorKind.PROVIDER_INVALID, f"missing provider operation {name}", "Repair the provider file.")
        result[name] = shlex.join(command.argv)
    return Ok(result)
