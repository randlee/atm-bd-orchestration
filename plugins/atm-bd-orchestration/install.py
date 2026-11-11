#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pydantic>=2", "pyyaml", "sc-compose>=1.8.0,<2"]
# ///
# pyright: strict
"""Standalone and sc-install entry points for atm-bd-orchestration."""
from __future__ import annotations
import sys
import argparse
import tomllib as tomllib
from pathlib import Path
from typing import List, Optional, Tuple

# sc-install may load the hook by file path without adding its directory.
_package_dir = str(Path(__file__).resolve().parent)
if _package_dir not in sys.path:
    sys.path.insert(0, _package_dir)

import installer_common as common
from installer_common import (
    AGENT_VARIABLES as AGENT_VARIABLES,
    ATM_CONFIG as ATM_CONFIG,
    AtmTable as AtmTable,
    AtmToml as AtmToml,
    BACKUP_DIR as BACKUP_DIR,
    BEADS_METADATA as BEADS_METADATA,
    BeadsMetadata as BeadsMetadata,
    CONFIG_OUT as CONFIG_OUT,
    CONFIG_TEMPLATE as CONFIG_TEMPLATE,
    CONSOLE_INSTALL as CONSOLE_INSTALL,
    CONSUMER_REGISTRY as CONSUMER_REGISTRY,
    Config as Config,
    ConfigInputValue as ConfigInputValue,
    ConfigTemplate as ConfigTemplate,
    ConfigValue as ConfigValue,
    ConsumerRegistry as ConsumerRegistry,
    HookResult as HookResult,
    InstallError as InstallError,
    InstallLock as InstallLock,
    InstallOptions as InstallOptions,
    InstallerHookInput as InstallerHookInput,
    InstallerHookOptions as InstallerHookOptions,
    LEGACY_OWNED as LEGACY_OWNED,
    LIST_VARIABLES as LIST_VARIABLES,
    LOCK_OUT as LOCK_OUT,
    LegacyOwnership as LegacyOwnership,
    MANIFEST_FILE as MANIFEST_FILE,
    MISSING_RE as MISSING_RE,
    Manifest as Manifest,
    Member as Member,
    MembersResponse as MembersResponse,
    OVERWRITE_HINT as OVERWRITE_HINT,
    PACKAGE as PACKAGE,
    PKG_DIR as PKG_DIR,
    PLACEHOLDER_RE as PLACEHOLDER_RE,
    Pane as Pane,
    Plan as Plan,
    REGISTRY_FILE as REGISTRY_FILE,
    RENDER_VARIABLES as RENDER_VARIABLES,
    RETIRED_REPO_FILES as RETIRED_REPO_FILES,
    ROLE_KEYS as ROLE_KEYS,
    Registry as Registry,
    RmuxTable as RmuxTable,
    SCRIPT_HEADER as SCRIPT_HEADER,
    SC_COMPOSE_RANGE_RE as SC_COMPOSE_RANGE_RE,
    StartupEntry as StartupEntry,
    TOOL_INSTALLS as TOOL_INSTALLS,
    TOOL_REQUIREMENT_RE as TOOL_REQUIREMENT_RE,
    Team as Team,
    TeamsResponse as TeamsResponse,
    UnsupportedPythonError as UnsupportedPythonError,
    Window as Window,
    YamlAPI as YamlAPI,
    _check_python_version as _check_python_version,  # pyright: ignore[reportPrivateUsage]
    legacy_pkg_rel as legacy_pkg_rel,
    load_validation_dependencies as load_validation_dependencies,
    string_list as string_list,
    check_agents as check_agents,
    check_beads_server_mode as check_beads_server_mode,
    check_tools as check_tools,
    config_variables as config_variables,
    declared_tool_requirements as declared_tool_requirements,
    derived_values as derived_values,
    json_object as json_object,
    load_legacy_owned as load_legacy_owned,
    load_manifest as load_manifest,
    load_manifest_artifacts as load_manifest_artifacts,
    load_registry as load_registry,
    manifest_requirement_floor as manifest_requirement_floor,
    package_version as package_version,
    parse_set as parse_set,
    render_config as render_config,
    render_text as render_text,
    repo_root_for as repo_root_for,
    resolve_config as resolve_config,
    roles_text as roles_text,
    sc_compose_range as sc_compose_range,
    sc_compose_supported as sc_compose_supported,
    sc_compose_upgrade as sc_compose_upgrade,
    script_runtime_sc_compose_version as script_runtime_sc_compose_version,
    sha256 as sha256,
    write_roles as write_roles,
)
from installer_planning import (
    desired_files as desired_files,
    plan_install as plan_install,
)
from installer_execution import (
    SanityMember as SanityMember,
    apply_plan as apply_plan,
    atm_default_team as atm_default_team,
    change_report as change_report,
    completion_report as completion_report,
    herdr_rename_hint as herdr_rename_hint,
    pane_alias as pane_alias,
    provision_dev_sanity_member as provision_dev_sanity_member,
    provision_tool_identity as provision_tool_identity,
    recommended_startup_block as recommended_startup_block,
    suggested_alias as suggested_alias,
)


def _ok() -> dict[str, str]:
    return {"result": "success"}


def _fail(message: str) -> dict[str, str]:
    return {"result": "fail", "message": message}


def _codex(destination_path: str, options: InstallerHookOptions) -> bool:
    return bool(options.get("codex")) or Path(destination_path).name == ".codex"


def _plan_or_fail(source_path: str, destination_path: str, options: InstallerHookInput) -> Tuple[Optional[Plan], Config, Optional[dict[str, str]]]:
    try:
        _check_python_version(tuple(sys.version_info[:3]), "installer interpreter")
        common.load_validation_dependencies()
        check_tools()
        try:
            parsed_options = common.TypeAdapter(InstallerHookOptions).validate_python(options, strict=True)
        except common.ValidationError as error:
            if any(item.get("loc", (None,))[0] == "args" for item in error.errors()):
                raise InstallError("hook args must map variables to strings, positive integers, booleans or string lists") from error
            raise InstallError(f"invalid installer hook options: {error}") from error
        args = parsed_options.get("args", {})
        plan, config = plan_install(Path(source_path), Path(destination_path), args,
                                    codex=_codex(destination_path, parsed_options),
                                    overwrite=parsed_options.get("overwrite", False) or parsed_options.get("force", False))
    except InstallError as exc:
        return None, {}, _fail(str(exc))
    if plan.problems:
        return None, {}, _fail("; ".join(plan.problems))
    return plan, config, None


def prepare(source_path: str, destination_path: str, options: InstallerHookInput) -> dict[str, str]:
    """Check the tools, the repository values, the beads mode, the agents and file
    ownership before anything is copied. Writes nothing."""
    _, _, failure = _plan_or_fail(source_path, destination_path, options)
    return failure or _ok()


def complete(source_path: str, destination_path: str, options: InstallerHookInput) -> dict[str, str]:
    """Place every file (rendered where listed), remove unchanged files no longer
    shipped, write the config, the install record and the roles."""
    plan, config, failure = _plan_or_fail(source_path, destination_path, options)
    if failure:
        return failure
    assert plan is not None
    version = package_version(Path(source_path))
    try:
        changed = apply_plan(plan, version)
    except InstallError as exc:
        return _fail(str(exc))
    print(f"{PACKAGE} {version}: {changed} file(s) written, {len(plan.writes) - changed} unchanged, "
          f"{len(plan.removals)} removed, {len(plan.backups)} backed up to {BACKUP_DIR}/; roles {'updated' if plan.registry_text is not None else 'unchanged'} "
          f"in {CONSUMER_REGISTRY}; config {CONFIG_OUT}; record {LOCK_OUT}")
    for line in completion_report(plan, config):
        print(line)
    return _ok()


def cleanup(source_path: str, destination_path: str, options: InstallerHookInput) -> dict[str, str]:
    """Nothing to clean: prepare() writes nothing and complete() writes only recorded files."""
    return _ok()


# ---------------------------------------------------------------------------
# Standalone installer
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None, pkg_dir: Path = PKG_DIR) -> int:
    parser = argparse.ArgumentParser(description="Install atm-bd-orchestration into a repository's .claude (or .codex) directory.")
    parser.add_argument("--dest", required=True, help="<repo>/.claude or <repo>/.codex")
    parser.add_argument("--codex", action="store_true", help="the destination is a .codex directory (skills only, no agents)")
    parser.add_argument("--set", action="append", default=[], metavar="NAME=VALUE",
                        help="set a config variable (wins over registry.yaml); lists take a JSON array or a,b,c")
    parser.add_argument("--overwrite", action="store_true",
                        help=f"move modified or foreign files in the way to {BACKUP_DIR}/<time>/ and install over them")
    args = parser.parse_args(argv)
    try:
        _check_python_version(tuple(sys.version_info[:3]), "installer interpreter")
        common.load_validation_dependencies()
        overrides = parse_set(args.set)
    except InstallError as exc:
        print(f"install.py: {exc}", file=sys.stderr)
        return 1
    dest = Path(args.dest).expanduser().resolve()
    options: InstallerHookInput = {"global": False, "local": True, "user": False, "project": False,
               "codex": args.codex or dest.name == ".codex", "force": False, "overwrite": args.overwrite, "expand": True,
               "args": overrides}
    for step in (prepare, complete):
        result = step(str(pkg_dir), str(dest), options)
        if result["result"] != "success":
            print(f"install.py: {result.get('message', 'installer failed')}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
else:
    try:
        common.load_validation_dependencies()
    except InstallError:
        # The install hook reports the missing dependency from prepare()/complete().
        pass
