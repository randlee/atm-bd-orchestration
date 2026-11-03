"""Plan installation and determine ownership without writing files."""
# pyright: strict
from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Dict, Optional, Tuple, TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from pydantic import JsonValue
    from typing_extensions import TypeForm
    JsonObject: TypeAlias = dict[str, JsonValue]
    _json_object_schema_type: TypeForm[JsonObject]

import installer_common as common
from installer_ownership import ownership_state
from installer_common import (
    CONFIG_OUT,
    CONFIG_TEMPLATE,
    CONSUMER_REGISTRY,
    Config,
    InstallError,
    InstallLock,
    LOCK_OUT,
    OVERWRITE_HINT,
    PACKAGE,
    Plan,
    RENDER_VARIABLES,
    RETIRED_REPO_FILES,
    ROLE_KEYS,
    legacy_pkg_rel,
    string_list,
    check_agents,
    check_beads_server_mode,
    derived_values,
    load_legacy_owned,
    load_manifest_artifacts,
    load_registry,
    render_config,
    render_text,
    repo_root_for,
    resolve_config,
    roles_text,
    sha256,
)

def _read_lock(repo_root: Path) -> Optional[InstallLock]:
    path = repo_root / LOCK_OUT
    if not path.is_file():
        return None
    try:
        data = common.TypeAdapter(InstallLock).validate_python(json.loads(path.read_text(encoding="utf-8")), strict=True)
    except (json.JSONDecodeError, common.ValidationError) as exc:
        raise InstallError(f"{path}: not valid JSON ({exc}); restore it from git") from exc
    if data["package"] != PACKAGE:
        raise InstallError(f"{path}: not an {PACKAGE} install record; restore it from git")
    return data


def desired_files(pkg_dir: Path, target_prefix: str, *, codex: bool, render_values: dict[str, str],
                  config_bytes: bytes) -> dict[str, tuple[bytes, bool, str]]:
    """repo-relative path -> (bytes, executable, package source path)."""
    render_value = load_registry(pkg_dir).get("render", [])
    renders = set(string_list(render_value, f"{pkg_dir / 'registry.yaml'}: render"))
    artifacts = load_manifest_artifacts(pkg_dir)
    cats = ("skills",) if codex else ("skills", "agents")
    out: dict[str, tuple[bytes, bool, str]] = {}
    for cat in cats:
        for rel in artifacts.get(cat, []):
            src = pkg_dir / rel
            if not src.is_file():
                raise InstallError(f"manifest artifact missing from the package: {rel}")
            data = src.read_bytes()
            if rel in renders:
                data = render_text(data.decode("utf-8"), render_values).encode("utf-8")
            out[target_prefix + rel] = (data, bool(src.stat().st_mode & stat.S_IXUSR), rel)
    out[CONFIG_OUT] = (config_bytes, False, CONFIG_TEMPLATE)
    return out


def plan_install(pkg_dir: Path, dest: Path, overrides: Config, *, codex: bool,
                 overwrite: bool = False) -> Tuple[Plan, Config]:
    """Resolve, render and check everything; return the plan. Writes nothing."""
    pkg_dir = Path(pkg_dir).resolve()
    repo_root = repo_root_for(dest)
    target_prefix = Path(dest).resolve().name + "/"
    config = resolve_config(repo_root, overrides, pkg_dir)
    config_bytes = render_config(config, pkg_dir)
    check_beads_server_mode(repo_root)
    artifacts = load_manifest_artifacts(pkg_dir)
    check_agents(repo_root, config, [] if codex else artifacts.get("agents", []))
    render_values = {k: v for k, v in config.items() if k in RENDER_VARIABLES and isinstance(v, str)}
    render_values.update(derived_values(repo_root, config))

    wanted = desired_files(pkg_dir, target_prefix, codex=codex, render_values=render_values, config_bytes=config_bytes)
    lock = _read_lock(repo_root)
    locked: dict[str, str] = {}
    if lock is not None:
        try:
            locked = common.TypeAdapter(dict[str, str]).validate_python(lock["files"], strict=True)
        except common.ValidationError as error:
            raise InstallError(f"{repo_root / LOCK_OUT}: files must map paths to hashes") from error
    legacy = load_legacy_owned(pkg_dir) if lock is None else {}
    dev_sanity_value = config.get("dev_sanity_member")
    if dev_sanity_value is not None and not isinstance(dev_sanity_value, str):
        raise InstallError("dev_sanity_member must be a string")
    plan = Plan(repo_root=repo_root, target_prefix=target_prefix,
                dev_sanity_member=None if codex else dev_sanity_value)

    def owned(key: str, data: bytes, pkg_rel: Optional[str]) -> Optional[bool]:
        return ownership_state(key, data, pkg_rel, locked, wanted, pkg_dir, legacy)

    # A target skill directory that exists must hold at least one file this package owns.
    skill_names = sorted({rel.split("/")[1] for rel in artifacts.get("skills", [])})
    foreign_dirs: set[str] = set()
    for name in skill_names:
        skill_dir = repo_root / target_prefix / "skills" / name
        if not skill_dir.is_dir():
            continue
        has_owned = False
        for path in skill_dir.rglob("*"):
            if not path.is_file():
                continue
            key = path.relative_to(repo_root).as_posix()
            pkg_rel = wanted[key][2] if key in wanted else legacy_pkg_rel(key, target_prefix, legacy)
            if owned(key, path.read_bytes(), pkg_rel) is not False:
                has_owned = True
                break
        if not has_owned:
            foreign_dirs.add(name)
            plan.problems.append(f"skill '{name}' exists at {target_prefix}skills/{name} and is not owned by {PACKAGE}; "
                                 "remove or rename it and rerun")

    for key, (data, executable, pkg_rel) in sorted(wanted.items()):
        if any(key.startswith(f"{target_prefix}skills/{n}/") for n in foreign_dirs):
            continue
        path = repo_root / key
        if path.is_file():
            state = owned(key, path.read_bytes(), pkg_rel)
            if state is not True and overwrite:
                plan.backups.append(key)
            elif state is None:
                plan.problems.append(f"{key} was modified since {PACKAGE} installed it; restore it (or delete it) and rerun{OVERWRITE_HINT}")
                continue
            elif state is False:
                plan.problems.append(f"{key} exists and is not owned by {PACKAGE}; remove or rename it and rerun{OVERWRITE_HINT}")
                continue
        elif path.exists():
            plan.problems.append(f"{key} exists and is not a file")
            continue
        plan.writes[key] = (data, executable)
        plan.lock_files[key] = sha256(data)

    # Files an earlier install placed that this version no longer ships (this target only).
    stale: Dict[str, Optional[str]] = {k: v for k, v in locked.items() if (k.startswith(target_prefix) or k in RETIRED_REPO_FILES) and k not in wanted}
    for pkg_rel in legacy:
        key = target_prefix + pkg_rel
        if pkg_rel.startswith(("skills/", "agents/")) and key not in wanted and key not in stale:
            stale[key] = None
    for key, pkg_rel in RETIRED_REPO_FILES.items():
        if pkg_rel in legacy and key not in stale:
            stale[key] = None
    for key, recorded in sorted(stale.items()):
        path = repo_root / key
        if not path.is_file():
            continue
        digest = sha256(path.read_bytes())
        if recorded is not None:
            if digest == recorded:
                plan.removals.append(key)
            elif overwrite:
                plan.backups.append(key)
                plan.removals.append(key)
            else:
                plan.problems.append(f"{key} was modified since {PACKAGE} installed it and this version no longer "
                                     f"ships it; move it out of the way and rerun{OVERWRITE_HINT}")
        elif digest in legacy.get(RETIRED_REPO_FILES.get(key, key[len(target_prefix):]), set()):
            plan.removals.append(key)

    try:
        role_values = {role: config[var] for var, role in ROLE_KEYS.items()}
        if not all(isinstance(member, str) for member in role_values.values()):
            raise InstallError("role config values must be strings")
        roles = {role: member for role, member in role_values.items() if isinstance(member, str)}
        plan.registry_text = roles_text(repo_root / CONSUMER_REGISTRY, roles)
    except InstallError as exc:
        plan.problems.append(str(exc))

    # Keep the other target's records.
    for key, digest in locked.items():
        if not key.startswith(target_prefix) and key not in plan.lock_files and key not in wanted and key not in RETIRED_REPO_FILES:
            plan.lock_files[key] = digest
    return plan, config
