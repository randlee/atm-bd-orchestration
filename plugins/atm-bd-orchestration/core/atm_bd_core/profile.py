"""Load a plug-in's profile.toml, its policy.toml and its cron script. Names no profile.

Refusals: an unreadable or malformed profile.toml or cron script is PROFILE_MISMATCH (the phase names a profile
that does not load); a missing or malformed policy.toml, or a param neither int nor text, is POLICY_BAD_PARAMS; a
policy.toml whose optional `profile` key differs from the manifest's name is PROFILE_MISMATCH.
"""
from __future__ import annotations

import importlib.util
import tomllib
import typing
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable
from types import ModuleType

from atm_bd_types import Action, Assign, ErrorId, Hook, Notify, Params, PhaseFacts, Profile, Refusal, Report, Template
from atm_bd_types._core import Policy

HOOKS = {"task.assign": Hook.TASK_ASSIGN, "task.start": Hook.TASK_START, "task.close": Hook.TASK_CLOSE}
TEMPLATES = {"refuse": Template.REFUSE, "dev-close": Template.DEV_CLOSE, "qa-pass": Template.QA_PASS,
             "qa-findings": Template.QA_FINDINGS}
PROFILE_KEYS = {"name", "stages", "hooks", "templates", "policy", "cron"}
POLICY_KEYS = {"profile", "notify_template", "params"}


@dataclass(frozen=True)
class CronScript:
    """The plug-in's `decide`, imported from its cron script; its result must be a list of Actions."""

    script: Path
    function: Callable[[PhaseFacts, Params], object]

    def decide(self, facts: PhaseFacts, params: Params) -> list[Action]:
        result = self.function(facts, params)
        if not isinstance(result, list):
            raise TypeError(f"{self.script}: decide returned {type(result).__name__}, not a list of Actions")
        actions: list[Action] = []
        for item in typing.cast(list[object], result):
            if not isinstance(item, (Assign, Report, Notify)):
                raise TypeError(f"{self.script}: decide returned {item!r}, not an Assign, Report or Notify")
            actions.append(item)
        return actions


@dataclass(frozen=True)
class LoadedProfile:
    """A profile manifest with its directory (paths in it are relative to that directory)."""

    profile: Profile
    root: Path

    def path(self, relative: str) -> Path:
        return (self.root / relative).resolve()


def _text_map(value: object, names: dict[str, Hook] | dict[str, Template], what: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"[{what}] must be a table")
    unknown = set(value) - set(names)
    if unknown:
        raise ValueError(f"unknown {what} {sorted(unknown)}; known: {sorted(names)}")
    if any(not isinstance(v, str) or not v for v in value.values()):
        raise ValueError(f"every {what} entry must be a non-empty path")
    return {names[k]: v for k, v in value.items()}


def load_profile(path: Path) -> LoadedProfile | Refusal:
    """Parse `profile.toml`; every named hook, template, policy and cron path must exist."""
    try:
        file = path.resolve()
        with file.open("rb") as source:
            raw = tomllib.load(source)
        unknown = set(raw) - PROFILE_KEYS
        if unknown:
            raise ValueError(f"unknown keys {sorted(unknown)}")
        name, stages, policy, cron = raw["name"], raw["stages"], raw["policy"], raw.get("cron")
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string")
        if not isinstance(stages, list) or not stages or any(not isinstance(s, str) or not s for s in stages):
            raise ValueError("stages must be a non-empty list of names")
        if not isinstance(policy, str) or not policy:
            raise ValueError("policy must be a path")
        if cron is not None and (not isinstance(cron, str) or not cron):
            raise ValueError("cron must be a path")
        hooks = _text_map(raw["hooks"], HOOKS, "hooks")
        templates = _text_map(raw["templates"], TEMPLATES, "templates")
        loaded = LoadedProfile(Profile(name, stages, hooks, templates, policy, cron), file.parent)
        for relative in [*hooks.values(), *templates.values(), *([cron] if cron else [])]:  # policy: load_policy
            if not loaded.path(relative).is_file():
                raise FileNotFoundError(f"{relative} named by {file} does not exist")
        return loaded
    except (OSError, KeyError, ValueError, tomllib.TOMLDecodeError) as exc:
        return Refusal(ErrorId.PROFILE_MISMATCH, path=str(path), reason=f"{type(exc).__name__}: {exc}")


def load_policy(loaded: LoadedProfile) -> Policy | Refusal:
    """Load the profile's policy.toml before any read: `[params]` of ints and strings."""
    path = loaded.path(loaded.profile.policy)
    try:
        with path.open("rb") as source:
            raw = tomllib.load(source)
        unknown = set(raw) - POLICY_KEYS
        if unknown:
            raise ValueError(f"unknown keys {sorted(unknown)}")
        named = raw.get("profile", loaded.profile.name)
        if named != loaded.profile.name:
            return Refusal(ErrorId.PROFILE_MISMATCH, path=str(path), profile=loaded.profile.name,
                           reason=f"policy.toml names profile {named!r}")
        notify = raw.get("notify_template", "")
        if not isinstance(notify, str):
            raise ValueError("notify_template must be a path")
        if notify and not loaded.path(notify).is_file():
            raise FileNotFoundError(f"notify_template {notify} does not exist")
        table = raw.get("params", {})
        if not isinstance(table, dict):
            raise ValueError("[params] must be a table")
        bad = [k for k, v in table.items() if isinstance(v, bool) or not isinstance(v, (int, str))]
        if bad:
            raise ValueError(f"params {sorted(bad)} are neither int nor text")
        return Policy(loaded.profile.name, Params(list(table.items())), notify)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        return Refusal(ErrorId.POLICY_BAD_PARAMS, path=str(path), reason=f"{type(exc).__name__}: {exc}")


def load_cron(loaded: LoadedProfile) -> CronScript | None | Refusal:
    """Import the profile's cron script; None when the profile has none (the cron decides nothing)."""
    if loaded.profile.cron is None:
        return None
    path = loaded.path(loaded.profile.cron)
    try:
        spec = importlib.util.spec_from_file_location(f"atm_bd_cron_{loaded.profile.name}", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot import {path}")
        module: ModuleType = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        decide = getattr(module, "decide", None)
        if not callable(decide):
            raise ImportError(f"{path} defines no decide(facts, params)")
        return CronScript(path, decide)
    except Exception as exc:  # a plug-in script may fail to import in any way; each is a typed refusal
        return Refusal(ErrorId.PROFILE_MISMATCH, path=str(path), reason=f"{type(exc).__name__}: {exc}")
