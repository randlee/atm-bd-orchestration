"""Install a profile from a checkout: python -m atm_bd_core.install PROFILE PRIMARY PHASE."""
from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import tomllib
from collections.abc import Callable
from pathlib import Path

from atm_bd_types import Refusal

from atm_bd_core.profile import LoadedProfile, load_profile


def timeout(path: Path, name: str) -> int:
    for node in ast.parse(path.read_text(encoding="utf-8"), filename=str(path)).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            value = ast.literal_eval(node.value)
            if type(value) is int and value > 0:
                return value
    raise ValueError(f"{path}: missing positive {name}")


def launcher(path: Path, python: Path, module: Path, limit: int, *, cron: bool = False) -> None:
    constant = "CRON_TIMEOUT_MS" if cron else "TIMEOUT_MS"
    path.write_text(f"{constant} = {limit}\nimport os, sys\nos.execv({str(python)!r}, "
                    f"[{str(python)!r}, {str(module)!r}, *sys.argv[1:]])\n", encoding="utf-8")


def _rewrite(path: Path, transform: Callable[[str], str], *, missing_ok: bool = False) -> None:
    """Validate the original and transformed TOML before atomically replacing it."""
    try:
        source = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        if not missing_ok:
            raise
        source = ""
    tomllib.loads(source)
    updated = transform(source)
    tomllib.loads(updated)
    temp = path.with_suffix(".toml.tmp")
    try:
        temp.write_text(updated, encoding="utf-8")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def set_repo(primary: Path, phase: str, repo: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("--repo must be owner/name")
    path = primary / ".atm-bd" / f"phase-{phase}.toml"

    def transform(source: str) -> str:
        parts = re.split(r"(?m)^(?=\s*\[)", source, maxsplit=1)
        prefix = re.sub(r"(?m)^\s*repo\s*=.*\n?", "", parts[0])
        return f"repo = {json.dumps(repo)}\n" + prefix + "".join(parts[1:])

    _rewrite(path, transform)


def set_phase_paths(primary: Path, phase: str, manifest: Path) -> None:
    """Publish the installed profile manifest as the phase's template source."""
    path = primary / ".atm-bd" / f"phase-{phase}.toml"
    manifest = manifest.resolve(strict=True)
    if not manifest.is_file():
        raise ValueError("installed profile path must be an absolute file")

    def transform(source: str) -> str:
        parts = re.split(r"(?m)^(?=\s*\[)", source, maxsplit=1)
        prefix = re.sub(r"(?m)^\s*profile_path\s*=.*\n?", "", parts[0])
        source = f"profile_path = {json.dumps(str(manifest))}\n" + prefix + "".join(parts[1:])
        return re.sub(r"(?ms)^[ \t]*\[templates(?:\.[^\]]+)?\][^\n]*(?:\n|\Z).*?(?=^[ \t]*\[(?!templates(?:\.[^\]]+)?\])|\Z)", "", source)

    _rewrite(path, transform)


def set_startup(primary: Path, installed: LoadedProfile) -> None:
    """Install role instructions without changing unrelated configuration blocks."""
    policy = tomllib.loads(installed.path(installed.profile.policy).read_text(encoding="utf-8"))
    params = policy.get("params", {})
    pairs = [(params.get(agent), params.get(message)) for agent, message in installed.profile.startup.items()]
    if any(not isinstance(agent, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", agent) for agent, _ in pairs):
        raise ValueError("startup agent params must name valid identities")
    if len({agent for agent, _ in pairs}) != len(pairs):
        raise ValueError("startup entries must use distinct agent identities")
    if any(not isinstance(message, str) or not message for _, message in pairs):
        raise ValueError("startup message params must contain non-empty text")

    def transform(source: str) -> str:
        for agent, message in pairs:
            header = f"startup.{agent}"
            pattern = rf"(?ms)^[ \t]*\[{re.escape(header)}\][^\n]*(?:\n|\Z).*?(?=^[ \t]*\[|\Z)"
            source = re.sub(pattern, "", source)
            source += f"\n[{header}]\nall = [{json.dumps(message)}]\n"
        return source

    _rewrite(primary / ".atm.toml", transform, missing_ok=True)


def cache_requirement(core: Path) -> str:
    """Use the same cache source and revision as the core project."""
    with (core / "pyproject.toml").open("rb") as source:
        cache = tomllib.load(source)["tool"]["uv"]["sources"]["bd-cache-rs"]
    return f"bd-cache-rs @ git+{cache['git']}@{cache['rev']}#subdirectory={cache['subdirectory']}"


def list_registrations(kind: str, phase: str) -> list[dict]:
    result = subprocess.run(["atm", kind, "list", "--phase", phase, "--json"], check=True,
                            capture_output=True, text=True)
    rows = json.loads(result.stdout)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"atm {kind} list did not return a JSON array of registrations")
    return rows


def cron_matches(row: dict, phase: str, entry: Path, primary: Path, expression: str, args: list[str]) -> bool:
    stop = row.get("stop")
    return (row.get("active") is True and row.get("phase") == phase and row.get("name") == "profile"
            and row.get("module_path") == str(entry) and row.get("cron_expr") == expression
            and row.get("cwd") == str(primary) and row.get("args") == args
            and isinstance(stop, dict) and stop.get("kind") == "hook")


def verify_registrations(phase: str, primary: Path, hooks: dict[str, Path], entry: Path,
                         expression: str, cron_args: list[str], schedules: list[dict] | None = None) -> None:
    rows = list_registrations("hook", phase)
    if schedules is None:
        schedules = list_registrations("cron", phase)
    for hook, module in hooks.items():
        if not any(row.get("active") is True and row.get("phase") == phase and row.get("hook") == hook
                   and row.get("module_path") == str(module) and row.get("cwd") == str(primary) for row in rows):
            raise RuntimeError(f"active hook {hook} for {phase} is missing or does not match {module}")
    if not any(cron_matches(row, phase, entry, primary, expression, cron_args) for row in schedules):
        raise RuntimeError(f"active profile cron for {phase} is missing or does not match {entry}")


def install(profile_path: Path, primary: Path, phase: str, checkout: Path, expression: str, repo: str) -> None:
    loaded = load_profile(profile_path)
    if isinstance(loaded, Refusal):
        raise TypeError(str(loaded))
    if not loaded.profile.cron:
        raise ValueError("profile does not declare a cron decision script")
    if not phase or phase in {".", ".."} or Path(phase).name != phase:
        raise ValueError("phase must be a single path component")
    primary = primary.resolve()
    set_repo(primary, phase, repo)
    set_startup(primary, loaded)
    target = primary / ".atm-bd" / "install" / phase
    target.mkdir(parents=True, exist_ok=True)
    python = target / "venv" / "bin" / "python"
    if not python.is_file():
        subprocess.run(["uv", "venv", "--python", "3.11", str(python.parent.parent)], check=True)
    core = checkout / "plugins/atm-bd-orchestration/core"
    types = checkout / "crates/atm-bd-types"
    subprocess.run(["uv", "pip", "install", "--python", str(python), str(types), str(core),
                    cache_requirement(core)], check=True)
    subprocess.run([str(python), "-m", "atm_bd_core.install.sync", str(primary), phase], check=True)
    skill = target / "profile"
    shutil.copytree(loaded.root, skill, dirs_exist_ok=True)
    installed = load_profile(skill / profile_path.name)
    if isinstance(installed, Refusal):
        raise RuntimeError(str(installed))
    set_phase_paths(primary, phase, skill / profile_path.name)
    hooks: dict[str, Path] = {}
    for hook, relative in installed.profile.hooks.items():
        module = installed.path(relative)
        hook_name = hook.name.lower().replace("_", ".")
        entry = target / f"{hook_name}.py"
        launcher(entry, python, module, timeout(module, "TIMEOUT_MS"))
        hooks[hook_name] = entry
        subprocess.run(["atm", "hook", "register", hook_name, "--module", str(entry), "--phase", phase,
                        "--cwd", str(primary)], check=True)
    cron_source = core / "atm_bd_core/cron_entry.py"
    cron_module = target / "cron_entry.py"
    shutil.copy2(cron_source, cron_module)
    entry = target / "cron.py"
    launcher(entry, python, cron_module, timeout(cron_module, "CRON_TIMEOUT_MS"), cron=True)
    cron_args = [str(skill / profile_path.name), str(primary)]
    schedules = None
    try:
        subprocess.run(["atm", "cron", "start", "profile", "--cron", expression, "--module", str(entry),
                        "--phase", phase, "--until-hook", "--cwd", str(primary),
                        "--arg", cron_args[0], "--arg", cron_args[1]], check=True)
    except subprocess.CalledProcessError:
        schedules = list_registrations("cron", phase)
        if not any(cron_matches(row, phase, entry, primary, expression, cron_args) for row in schedules):
            raise
    verify_registrations(phase, primary, hooks, entry, expression, cron_args, schedules)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("primary", type=Path)
    parser.add_argument("phase")
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--repo", required=True, help="provider repository in owner/name form")
    parser.add_argument("--cron", default="0 * * * * *")
    args = parser.parse_args()
    install(args.profile.resolve(), args.primary, args.phase, args.checkout.resolve(), args.cron, args.repo)


if __name__ == "__main__":
    main()
