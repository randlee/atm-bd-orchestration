# pyright: strict
"""Construct altered immutable Rust errors for console behavior tests."""
from __future__ import annotations

from atm_bd_types import Error, ErrorDetail
from result import CommandFailed, ConfigInvalid, IoFailed, LockHeld, NotFound, ParseFailed, Rejected, Timeout, Unreachable


def replace_error(error: Error, *, fix: str | None = None, path: str | None = None,
                  message: str | None = None, source: str | None = None,
                  argv: tuple[str, ...] | None = None) -> Error:
    remedy = error.fix if fix is None else fix
    match error.detail:
        case ErrorDetail.CommandFailed(argv=old, code=code, stderr=stderr):
            return CommandFailed("command_failed", argv or tuple(old), code, stderr, remedy)
        case ErrorDetail.Timeout(argv=old, seconds=seconds):
            return Timeout("timeout", argv or tuple(old), seconds, remedy)
        case ErrorDetail.Rejected(argv=old, status=status, message=old_message):
            return Rejected("rejected", argv or tuple(old), status, message or old_message, remedy)
        case ErrorDetail.Unreachable(argv=old, message=old_message):
            return Unreachable("unreachable", argv or tuple(old), message or old_message, remedy)
        case ErrorDetail.ParseFailed(source=old_source, message=old_message):
            return ParseFailed("parse_failed", source or old_source, message or old_message, remedy)
        case ErrorDetail.NotFound(what=what):
            return NotFound("not_found", what, remedy)
        case ErrorDetail.ConfigInvalid(key=key, value=value):
            return ConfigInvalid("config_invalid", key, value, remedy)
        case ErrorDetail.LockHeld(snapshot_age_s=age):
            return LockHeld("lock_held", age, remedy)
        case ErrorDetail.IoFailed(path=old_path, message=old_message):
            return IoFailed("io_failed", path or old_path, message or old_message, remedy)
        case None:
            return Error(error.kind, message or error.message, remedy)
