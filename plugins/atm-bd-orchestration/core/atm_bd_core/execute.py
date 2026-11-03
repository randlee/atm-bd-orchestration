"""Dedupe and execute the Actions a plug-in decided. The same for every profile; names no profile.

Failure output types an ErrorId only when it contains a delimited whole token.

State, under the phase's state directory:
- reported-keys.json: JSON list of Report keys already sent (append-only; collect reads it as REPORTED_KEYS).
- executed.json: Assign/Notify keys sent while the plug-in still decides them, and per-key failure counts.
  A key leaves it when decide stops returning it, so a re-released bead is assigned again.

A failed command is retried on the next tick; after RETRY_LIMIT failed attempts the key is no longer run and every
tick reports it FAILED with the last ErrorId until decide stops returning it.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import SubprocessError

from atm_bd_types import Action, Assign, ErrorId, Notify, Refusal, Report
from atm_bd_types._core import ActionOutcome, CommandRunner, Decision, OutcomeKind, ViewRow

RETRY_LIMIT = 3
REPORTED_KEYS = "reported-keys.json"
EXECUTED = "executed.json"
ERROR_IDS = {name: getattr(ErrorId, name)
             for name in sorted((n for n in dir(ErrorId) if n.isupper()), key=len, reverse=True)}


def action_key(action: Action) -> str:
    if isinstance(action, Notify):
        return f"notify:{action.to}:{','.join(action.keys)}"
    return action.key


@dataclass(frozen=True)
class Failure:
    attempts: int
    error: str
    message: str


@dataclass
class Ledger:
    """executed.json: Assign/Notify keys already sent, and failed attempts per key."""

    sent: set[str] = field(default_factory=set)
    failures: dict[str, Failure] = field(default_factory=dict)

    @staticmethod
    def load(state_dir: Path) -> Ledger | Refusal:
        path = state_dir / EXECUTED
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            sent, failures = raw["sent"], raw["failures"]
            if not isinstance(sent, list) or any(not isinstance(k, str) for k in sent):
                raise ValueError("sent must be a list of keys")
            if not isinstance(failures, dict):
                raise ValueError("failures must be an object")
            parsed = {key: Failure(int(v["attempts"]), str(v["error"]), str(v["message"]))
                      for key, v in failures.items()}
            if any(f.error not in ERROR_IDS for f in parsed.values()):
                raise ValueError("unknown error id in failures")
            return Ledger(set(sent), parsed)
        except FileNotFoundError:
            return Ledger()
        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
            return Refusal(ErrorId.PHASE_UNREADABLE, path=str(path),
                           reason=f"{type(exc).__name__}: {exc}; repair or delete {path}")

    def save(self, state_dir: Path) -> None:
        body = {"sent": sorted(self.sent),
                "failures": {k: {"attempts": f.attempts, "error": f.error, "message": f.message}
                             for k, f in sorted(self.failures.items())}}
        _write_json(state_dir / EXECUTED, body)


def _write_json(path: Path, body: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def dedupe(actions: list[Action], reported_keys: list[str] | None, ledger: Ledger) -> Decision:
    """Drop repeated keys within the tick, Assign/Notify keys already sent, and keep sent Reports as rows only."""
    seen: set[str] = set()
    kept: list[Action] = []
    rows: list[ViewRow] = []
    for action in actions:
        key = action_key(action)
        if key in seen:
            continue
        seen.add(key)
        if isinstance(action, Report):
            if reported_keys is not None and key in reported_keys:
                rows.append(ViewRow(action.queue, key, action.bead_id, action.text, None))
                continue
        elif key in ledger.sent:
            continue
        kept.append(action)
    return Decision(kept, rows)


@dataclass(frozen=True)
class Executor:
    """Runs decided actions through the CommandRunner. `lead` receives Reports; paths resolve under `root`."""

    runner: CommandRunner
    state_dir: Path
    root: Path
    lead: str
    notify_template: str

    def argv(self, action: Action) -> tuple[list[str], str]:
        if isinstance(action, Assign):
            variables = {"task_id": action.vars.task_id, "phase": action.vars.phase,
                         "profile": action.vars.profile}
            return (["atm", "task", "assign", action.to, "--task-id", action.bead_id,
                     "--template", str((self.root / action.template).resolve()), "--vars", "-"],
                    json.dumps(variables))
        if isinstance(action, Report):
            bead = f" ({action.bead_id})" if action.bead_id else ""
            return ["atm", "send", self.lead, "--stdin"], f"[{action.queue}]{bead} {action.text}"
        if isinstance(action, Notify):
            if self.notify_template:
                return (["atm", "send", action.to, "--template",
                         str((self.root / self.notify_template).resolve()), "--vars", "-"],
                        json.dumps({"keys": list(action.keys)}))
            return ["atm", "send", action.to, "--stdin"], "\n".join(action.keys)
        raise TypeError(f"not an Assign, Report or Notify: {action!r}")

    def run(self, decision: Decision, decided: list[Action], reported_keys: list[str] | None,
            ledger: Ledger, dry_run: bool, facts_complete: bool) -> list[ActionOutcome]:
        """Execute actions and prune stale ledger keys only when the collected facts were complete."""
        outcomes = []
        for action in decision.actions:
            outcomes.append(self._one(action, reported_keys, ledger, dry_run))
            if not dry_run:
                ledger.save(self.state_dir)
        if not dry_run and facts_complete:
            live = {action_key(a) for a in decided}
            ledger.sent &= live
            ledger.failures = {k: f for k, f in ledger.failures.items() if k in live}
            ledger.save(self.state_dir)
        return outcomes

    def _one(self, action: Action, reported_keys: list[str] | None, ledger: Ledger,
             dry_run: bool) -> ActionOutcome:
        key = action_key(action)
        if isinstance(action, Report) and reported_keys is None:
            return ActionOutcome(action, OutcomeKind.FAILED, Refusal(
                ErrorId.PHASE_UNREADABLE, key=key, path=str(self.state_dir / REPORTED_KEYS),
                reason="reported keys unreadable this tick; Report held so it is not sent twice"))
        previous = ledger.failures.get(key)
        if previous is not None and previous.attempts >= RETRY_LIMIT:
            return ActionOutcome(action, OutcomeKind.FAILED, Refusal(
                ERROR_IDS[previous.error], key=key, attempts=str(previous.attempts),
                reason=f"retry limit {RETRY_LIMIT} reached; last error: {previous.message}"))
        argv, stdin = self.argv(action)
        if dry_run:
            return ActionOutcome(action, OutcomeKind.DRY_RUN, None)
        try:
            result = self.runner.run(argv, stdin)
            code, message = result.code, (result.stderr or result.stdout).strip()
        except (OSError, SubprocessError) as exc:
            code, message = -1, f"{type(exc).__name__}: {exc}"
        if code == 0:
            ledger.failures.pop(key, None)
            if isinstance(action, Report) and reported_keys is not None:
                reported_keys.append(key)
                _write_json(self.state_dir / REPORTED_KEYS, reported_keys)
            else:
                ledger.sent.add(key)
            return ActionOutcome(action, OutcomeKind.SENT, None)
        error = next((match.group(0) for match in re.finditer(r"\b[A-Z][A-Z0-9_]*\b", message)
                      if match.group(0) in ERROR_IDS), "REQUEST_INVALID")
        attempts = (previous.attempts if previous else 0) + 1
        ledger.failures[key] = Failure(attempts, error, message or f"exit {code}")
        return ActionOutcome(action, OutcomeKind.FAILED, Refusal(
            ERROR_IDS[error], key=key, argv=argv, attempts=str(attempts), reason=message or f"exit {code}"))
