"""Install a profile from a checkout: python -m atm_bd_core.install PROFILE PRIMARY PHASE."""
from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
from pathlib import Path

from atm_bd_types import Refusal

from atm_bd_core.profile import load_profile


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


def install(profile_path: Path, primary: Path, phase: str, checkout: Path, expression: str) -> None:
    loaded = load_profile(profile_path)
    if isinstance(loaded, Refusal):
        raise RuntimeError(str(loaded))
    if not loaded.profile.cron:
        raise ValueError("profile does not declare a cron decision script")
    if not phase or phase in {".", ".."} or Path(phase).name != phase:
        raise ValueError("phase must be a single path component")
    primary = primary.resolve()
    target = primary / ".atm-bd" / "install" / phase
    target.mkdir(parents=True, exist_ok=True)
    python = target / "venv" / "bin" / "python"
    subprocess.run(["uv", "venv", "--python", "3.11", str(python.parent.parent)], check=True)
    core = checkout / "plugins/atm-bd-orchestration/core"
    types = checkout / "crates/atm-bd-types"
    subprocess.run(["uv", "pip", "install", "--python", str(python), str(types), str(core),
                    ("bd-cache-rs @ git+https://github.com/randlee/beads-cache@"
                     "f57859f5c01fa463eb57ef11679e00118532c993#subdirectory=crates/bd-cache-py")], check=True)
    skill = target / "profile"
    shutil.copytree(loaded.root, skill, dirs_exist_ok=True)
    installed = load_profile(skill / profile_path.name)
    if isinstance(installed, Refusal):
        raise RuntimeError(str(installed))
    for hook, relative in installed.profile.hooks.items():
        module = installed.path(relative)
        hook_name = hook.name.lower().replace("_", ".")
        entry = target / f"{hook_name}.py"
        launcher(entry, python, module, timeout(module, "TIMEOUT_MS"))
        subprocess.run(["atm", "hook", "register", hook_name, "--module", str(entry), "--phase", phase,
                        "--cwd", str(primary)], check=True)
    cron_source = core / "atm_bd_core/cron_entry.py"
    cron_module = target / "cron_entry.py"
    shutil.copy2(cron_source, cron_module)
    entry = target / "cron.py"
    launcher(entry, python, cron_module, timeout(cron_module, "CRON_TIMEOUT_MS"), cron=True)
    subprocess.run(["atm", "cron", "start", "profile", "--cron", expression, "--module", str(entry),
                    "--phase", phase, "--until-hook", "--cwd", str(primary),
                    "--arg", str(skill / profile_path.name), "--arg", str(primary)], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("primary", type=Path)
    parser.add_argument("phase")
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--cron", default="0 * * * * *")
    args = parser.parse_args()
    install(args.profile.resolve(), args.primary, args.phase, args.checkout.resolve(), args.cron)


if __name__ == "__main__":
    main()
