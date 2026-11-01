# pyright: strict
"""Shared Result envelope and constructors for crate-owned errors."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Literal, TypeAlias, TypeVar

from atm_bd_types import Error, ErrorDetail, ErrorKind

T = TypeVar("T")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T


@dataclass(frozen=True)
class Err:
    error: Error


Result: TypeAlias = Ok[T] | Err


def CommandFailed(kind: Literal["command_failed"], argv: tuple[str, ...], code: int, stderr: str, fix: str) -> Error:
    return Error(ErrorKind.COMMAND_FAILED, f"{' '.join(argv)} (exit {code}): {stderr.strip()}", fix,
                 ErrorDetail.CommandFailed(argv, code, stderr))


def Timeout(kind: Literal["timeout"], argv: tuple[str, ...], seconds: int, fix: str) -> Error:
    return Error(ErrorKind.TIMEOUT, f"{' '.join(argv)} timed out after {seconds}s", fix, ErrorDetail.Timeout(argv, seconds))


def Rejected(kind: Literal["rejected"], argv: tuple[str, ...], status: int, message: str, fix: str) -> Error:
    return Error(ErrorKind.REJECTED, f"{' '.join(argv)} (status {status}): {message}", fix,
                 ErrorDetail.Rejected(argv, status, message))


def Unreachable(kind: Literal["unreachable"], argv: tuple[str, ...], message: str, fix: str) -> Error:
    return Error(ErrorKind.UNREACHABLE, f"{' '.join(argv)}: {message}", fix, ErrorDetail.Unreachable(argv, message))


def ParseFailed(kind: Literal["parse_failed"], source: str, message: str, fix: str) -> Error:
    return Error(ErrorKind.PARSE_FAILED, f"{source}: {message}", fix, ErrorDetail.ParseFailed(source, message))


def NotFound(kind: Literal["not_found"], what: str, fix: str) -> Error:
    return Error(ErrorKind.NOT_FOUND, what, fix, ErrorDetail.NotFound(what))


def ConfigInvalid(kind: Literal["config_invalid"], key: str, value: str, fix: str) -> Error:
    return Error(ErrorKind.CONFIG_INVALID, f"{key}={value}", fix, ErrorDetail.ConfigInvalid(key, value))


def LockHeld(kind: Literal["lock_held"], snapshot_age_s: int | None, fix: str) -> Error:
    age = "unknown" if snapshot_age_s is None else f"{snapshot_age_s}s"
    return Error(ErrorKind.LOCK_HELD, f"snapshot age {age}", fix, ErrorDetail.LockHeld(snapshot_age_s))


def IoFailed(kind: Literal["io_failed"], path: str, message: str, fix: str) -> Error:
    return Error(ErrorKind.IO_FAILED, f"{path}: {message}", fix, ErrorDetail.IoFailed(path, message))


def kind_name(kind: ErrorKind) -> str:
    match kind:
        case ErrorKind.COMMAND_FAILED: return "command_failed"
        case ErrorKind.TIMEOUT: return "timeout"
        case ErrorKind.REJECTED: return "rejected"
        case ErrorKind.UNREACHABLE: return "unreachable"
        case ErrorKind.PARSE_FAILED: return "parse_failed"
        case ErrorKind.NOT_FOUND: return "not_found"
        case ErrorKind.CONFIG_INVALID: return "config_invalid"
        case ErrorKind.CONFIG_MISSING: return "config_missing"
        case ErrorKind.LOCK_HELD: return "lock_held"
        case ErrorKind.IO_FAILED: return "io_failed"
        case ErrorKind.PROFILE_MISMATCH: return "profile_mismatch"
        case ErrorKind.PROVIDER_INVALID: return "provider_invalid"


def with_fix(error: Error, fix: str) -> Error:
    return Error(error.kind, error.message, fix, error.detail)


def error_data(error: Error) -> dict[str, object]:
    """Encode the existing public error fields from typed crate context."""
    data: dict[str, object] = {"kind": kind_name(error.kind), "fix": error.fix}
    detail = error.detail
    match detail:
        case ErrorDetail.CommandFailed(argv=argv, code=code, stderr=stderr):
            data.update(argv=tuple(argv), code=code, stderr=stderr)
        case ErrorDetail.Timeout(argv=argv, seconds=seconds):
            data.update(argv=tuple(argv), seconds=seconds)
        case ErrorDetail.Rejected(argv=argv, status=status, message=message):
            data.update(argv=tuple(argv), status=status, message=message)
        case ErrorDetail.Unreachable(argv=argv, message=message):
            data.update(argv=tuple(argv), message=message)
        case ErrorDetail.ParseFailed(source=source, message=message):
            data.update(source=source, message=message)
        case ErrorDetail.NotFound(what=what):
            data.update(what=what)
        case ErrorDetail.ConfigInvalid(key=key, value=value):
            data.update(key=key, value=value)
        case ErrorDetail.LockHeld(snapshot_age_s=age):
            data.update(snapshot_age_s=age)
        case ErrorDetail.IoFailed(path=path, message=message):
            data.update(path=path, message=message)
        case None:
            data.update(message=error.message)
    return data


def argv_of(error: Error) -> tuple[str, ...] | None:
    detail = error.detail
    match detail:
        case ErrorDetail.CommandFailed(argv=argv) | ErrorDetail.Timeout(argv=argv) | ErrorDetail.Rejected(argv=argv) | ErrorDetail.Unreachable(argv=argv):
            return tuple(argv)
        case ErrorDetail.ParseFailed() | ErrorDetail.NotFound() | ErrorDetail.ConfigInvalid() | ErrorDetail.LockHeld() | ErrorDetail.IoFailed() | None:
            return None


def with_argv(error: Error, argv: tuple[str, ...]) -> Error:
    match error.detail:
        case ErrorDetail.CommandFailed(code=code, stderr=stderr):
            return CommandFailed("command_failed", argv, code, stderr, error.fix)
        case ErrorDetail.Timeout(seconds=seconds):
            return Timeout("timeout", argv, seconds, error.fix)
        case ErrorDetail.Rejected(status=status, message=message):
            return Rejected("rejected", argv, status, message, error.fix)
        case ErrorDetail.Unreachable(message=message):
            return Unreachable("unreachable", argv, message, error.fix)
        case ErrorDetail.ParseFailed() | ErrorDetail.NotFound() | ErrorDetail.ConfigInvalid() | ErrorDetail.LockHeld() | ErrorDetail.IoFailed() | None:
            return error
