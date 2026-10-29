#!/usr/bin/env python3
# pyright: strict
"""atm-bd-orchestration install hook and standalone installer.

Two ways in:

1. sc-install (synaptic-canvas) loads this file as the package's Tier-3
   install hook and calls prepare()/complete()/cleanup() around its own
   manifest-artifact copy step, once per target (.claude and/or .codex).
2. Standalone: `python3 install.py --dest <repo>/.claude [--set NAME=VALUE ...]`
   runs prepare() and complete(); complete() places every file itself.

Configuration. The only input is the consuming repository's
`.claude/agents/registry.yaml` (plus `--set NAME=VALUE`, which wins). The
variables are the `required_variables` of `config/atm-bd-orchestration.yaml.j2`;
each is read from the top-level registry key of the same name, except the two
role members, which are read from `roles:`:

    dev_sanity_member  -> roles.dev-sanity
    qa_member          -> roles.quality-mgr
    team_lead_member   -> roles.lead

The template is rendered strictly with the sc-compose wheel into
`<repo>/.claude/project/atm-bd-orchestration.yaml`; a missing variable is an
install error that names it. There are no defaults. The resolved role members are
written back into `roles:` so `resolve-role` agrees with the config file.

Ownership. `<repo>/.claude/project/atm-bd-orchestration.lock.json` records the
package version and the sha256 of every file the install wrote. A rerun replaces
a recorded file only when it is unchanged since it was written and fails, naming
it, when it was modified; it never writes over a file it does not own, and it
fails when a target skill directory exists that it does not own. Files a newer
version stops shipping are removed when unchanged. With `--overwrite` (sc-install:
`overwrite` or `force`), a modified or foreign file at a shipped path, or a
modified file no longer shipped, is warned about and moved to
`<repo>/.backup/<UTC time>/<path>` instead of failing the install; the package's
file then takes its place. A repository installed by
0.x (no lock file) is migrated once: an existing file is owned when its bytes are
the bytes this version ships or bytes some 0.x version shipped
(`config/legacy-owned.json`); any other existing file fails the install.

Checks before anything is written: the sc-compose CLI and the python3 wheel the
same version, in the manifest's `sc-compose >= X.Y.Z, < N` range, pydantic and PyYAML present;
`.beads/metadata.json` shows `dolt_mode: server`; every agent named in
`qa_member` and `reviewers_round1` has `.claude/agents/<name>.md` (in the
repository or shipped by this install). `dev_sanity_member` is not checked: it
names a team member, which may have no agent file.

Team. complete() adds `atm-bd@tool`, and for a .claude install adds the
`dev_sanity_member` to the repository's own team (`[atm] default_team` in
`.atm.toml`; claude-code, sonnet, herdr) when `atm members` does not list it.
Its host name (the alias of its `.atm.toml` `[[rmux.windows.panes]]` entry, else
the member name) must not be any other member's host name on this host; every
team is read and only our own is changed. When the member cannot be added the
install still succeeds and says what to run. complete() prints every change it
made and the `.atm.toml` additions it recommends; it never edits `.atm.toml`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import import_module
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Literal, Mapping, NotRequired, Optional, Tuple, TYPE_CHECKING, TypeAlias

try:
    from typing_extensions import TypedDict
except ImportError:
    from typing import TypedDict

if TYPE_CHECKING:
    from pydantic import JsonValue, TypeAdapter, ValidationError
    from typing_extensions import TypeForm

    JsonObject: TypeAlias = dict[str, JsonValue]
    _json_object_schema_type: TypeForm[JsonObject]

PKG_DIR = Path(__file__).resolve().parent
PACKAGE = "atm-bd-orchestration"
REGISTRY_FILE = "registry.yaml"
MANIFEST_FILE = "manifest.yaml"
CONFIG_TEMPLATE = "config/atm-bd-orchestration.yaml.j2"
LEGACY_OWNED = "config/legacy-owned.json"
BACKUP_DIR = ".backup"
OVERWRITE_HINT = f" (or rerun with --overwrite to move it to {BACKUP_DIR}/)"
CONFIG_OUT = ".claude/project/atm-bd-orchestration.yaml"
LOCK_OUT = ".claude/project/atm-bd-orchestration.lock.json"
CONSUMER_REGISTRY = ".claude/agents/registry.yaml"
BEADS_METADATA = ".beads/metadata.json"
ATM_CONFIG = ".atm.toml"

# Variables whose value is a list (YAML list in registry.yaml; `--set` takes a
# JSON array or a comma-separated list).
LIST_VARIABLES = frozenset({
    "requirements_globs", "adr_globs",
    "reviewers_round1",
})
# Variables read from registry.yaml `roles:` and written back there.
ROLE_KEYS = {"dev_sanity_member": "dev-sanity", "qa_member": "quality-mgr", "team_lead_member": "lead"}
# Variables naming agents that must have .claude/agents/<name>.md. dev_sanity_member
# is a team member running the dev-sanity directive and may have no agent file.
AGENT_VARIABLES = ("qa_member", "reviewers_round1")

# Install-time placeholders in installed skill/agent files (the files listed under
# `render:` in registry.yaml). repo_slug, repo_name and
# workflow_issues_root are derived from the repository, not configured.
RENDER_VARIABLES = (
    "dev_sanity_member",
    "bead_prefix",
    "workflow_issues_root",
    "repo_slug",
    "repo_name",
    "worktree_base",
    "console_install",
)
PLACEHOLDER_RE = re.compile(r"\{\{ (" + "|".join(RENDER_VARIABLES) + r") \}\}")

# Repository-root files an earlier version placed (0.10.4 and before); removed on upgrade like
# any file no longer shipped (repo path -> package source). The Jev transport now ships inside
# the atm-bd-orchestration skill.
RETIRED_REPO_FILES = {"scripts/jev_client.py": "assets/scripts/jev_client.py"}

CONSOLE_INSTALL = (
    "uv tool install "
    "git+https://github.com/randlee/atm-bd-orchestration.git#subdirectory=apps/atm-bd-console"
)
TOOL_INSTALLS = {
    "atm": "brew install randlee/tap/atm",
    "atm-bd": CONSOLE_INSTALL,
    "bd": "brew install beads",
    "git": "brew install git",
    "jq": "brew install jq",
}
HANDLED_ELSEWHERE_REQUIREMENTS = frozenset({"python3", "pyyaml", "pydantic", "sc-compose"})

ConfigValue: TypeAlias = str | int | bool | list[str]
Config: TypeAlias = dict[str, ConfigValue]
ConfigInputValue: TypeAlias = str | int | float | bool | None | list[str]


def json_object(value: object, context: str) -> JsonObject:
    try:
        adapter: TypeAdapter[JsonObject] = TypeAdapter(_json_object_schema_type)
        return adapter.validate_python(value, strict=True)
    except ValidationError as error:
        raise InstallError(f"{context}: expected a JSON-compatible string-keyed object: {error}") from error


class HookResult(TypedDict):
    result: Literal["success", "fail"]
    message: NotRequired[str]


class InstallOptions(TypedDict):
    global_: NotRequired[bool]
    local: NotRequired[bool]
    user: NotRequired[bool]
    project: NotRequired[bool]
    codex: NotRequired[bool]
    force: NotRequired[bool]
    overwrite: NotRequired[bool]
    expand: NotRequired[bool]
    args: NotRequired[Config]


InstallerHookOptions = TypedDict(
    "InstallerHookOptions",
    {"global": bool, "local": bool, "user": bool, "project": bool, "codex": bool,
     "force": bool, "overwrite": bool, "expand": bool, "args": Config},
    total=False,
)
InstallerHookInput: TypeAlias = Mapping[str, ConfigValue | Config]


class Registry(TypedDict):
    render: list[str]


class Manifest(TypedDict):
    version: str
    artifacts: dict[str, list[str]]
    requires: list[str]


class ConfigTemplate(TypedDict, total=False):
    required_variables: list[str]
    defaults: dict[str, ConfigValue]


class ConsumerRegistry(TypedDict, total=False):
    bead_prefix: str | None
    dev_sanity_member: str | None
    qa_member: str | None
    team_lead_member: str | None
    worktree_base: str | None
    test_command: str | None
    lint_command: str | None
    integration_branch_pattern: str | None
    plans_dir: str | None
    requirements_globs: str | list[str] | None
    adr_globs: str | list[str] | None
    policy_path: str | None
    reviewers_round1: str | list[str] | None
    max_sanity_rounds: int | str | None
    gate_timeout_s: int | str | None
    roles: dict[str, str | None]


class LegacyOwnership(TypedDict):
    files: dict[str, list[str]]


class BeadsMetadata(TypedDict, total=False):
    dolt_mode: str


class InstallLock(TypedDict):
    package: str
    files: dict[str, str]


class Member(TypedDict, total=False):
    name: str
    agent_type: str
    alias: str


class MembersResponse(TypedDict):
    members: list[Member]


class Team(TypedDict):
    name: str


class TeamsResponse(TypedDict):
    teams: list[Team]


class AtmTable(TypedDict, total=False):
    default_team: str


class Pane(TypedDict, total=False):
    name: str
    alias: str


class Window(TypedDict, total=False):
    panes: list[Pane]


class RmuxTable(TypedDict, total=False):
    windows: list[Window]


class StartupEntry(TypedDict, total=False):
    all: list[str]


class AtmToml(TypedDict, total=False):
    atm: AtmTable
    rmux: RmuxTable
    startup: dict[str, StartupEntry]
PYTHON_INSTALL = "install Python 3.11 or newer with your system package manager"


class InstallError(RuntimeError):
    """An install refusal; the message names what to fix."""


class UnsupportedPythonError(InstallError):
    """The interpreter is below the supported Python 3.11 floor."""


def _check_python_version(version: tuple[int, ...], interpreter: str) -> None:
    if version[:2] < (3, 11):
        raise UnsupportedPythonError(
            f"UNSUPPORTED_PYTHON: {interpreter} is {'.'.join(map(str, version))}; "
            "install and run under Python 3.11 or newer (the check that this interpreter can "
            "import the sc-compose wheel follows separately)"
        )


def _load_validation_dependencies() -> None:
    """Load optional validation libraries after CLI help and before validation."""
    global TypeAdapter, ValidationError, _json_object_schema_type
    try:
        from pydantic import JsonValue, TypeAdapter, ValidationError
    except (ImportError, AttributeError) as error:
        raise InstallError(
            "installer validation dependency is missing or incompatible; install a compatible "
            "Pydantic v2 with `python3 -m pip install 'pydantic>=2'` "
            "and rerun"
        ) from error
    _json_object_schema_type = dict[str, JsonValue]


@dataclass(frozen=True)
class YamlAPI:
    safe_load: Callable[[str], object]
    error_type: type[Exception]


# ---------------------------------------------------------------------------
# Package files
# ---------------------------------------------------------------------------


def _yaml() -> YamlAPI:
    try:
        module = import_module("yaml")
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise InstallError("PyYAML is required to read registry.yaml (pip install pyyaml)") from exc
    try:
        safe_load = TypeAdapter(Callable[[str], object]).validate_python(getattr(module, "safe_load"), strict=True)
        error_type = TypeAdapter(type[Exception]).validate_python(getattr(module, "YAMLError"), strict=True)
    except ValidationError as error:
        raise InstallError("PyYAML is installed but its safe_load/YAMLError interface is invalid") from error
    return YamlAPI(safe_load=safe_load, error_type=error_type)


def _load_yaml(path: Path) -> JsonObject:
    yaml_api = _yaml()
    try:
        loaded: object = yaml_api.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml_api.error_type as exc:
        raise InstallError(f"{path}: not valid YAML: {exc}") from exc
    return json_object(loaded, str(path))


def _string_list(value: object, context: str) -> list[str]:
    try:
        return TypeAdapter(list[str]).validate_python(value, strict=True)
    except ValidationError as error:
        raise InstallError(f"{context}: expected a list of strings") from error


def load_registry(pkg_dir: Path = PKG_DIR) -> Registry:
    try:
        return TypeAdapter(Registry).validate_python(_load_yaml(pkg_dir / REGISTRY_FILE), strict=True)
    except ValidationError as error:
        raise InstallError(f"{pkg_dir / REGISTRY_FILE}: invalid registry data: {error}") from error


def load_manifest(pkg_dir: Path = PKG_DIR) -> Manifest:
    try:
        return TypeAdapter(Manifest).validate_python(_load_yaml(pkg_dir / MANIFEST_FILE), strict=True)
    except ValidationError as error:
        raise InstallError(f"{pkg_dir / MANIFEST_FILE}: invalid manifest data: {error}") from error


def load_manifest_artifacts(pkg_dir: Path = PKG_DIR) -> dict[str, list[str]]:
    return load_manifest(pkg_dir)["artifacts"]


def package_version(pkg_dir: Path = PKG_DIR) -> str:
    return str(load_manifest(pkg_dir)["version"])


SC_COMPOSE_RANGE_RE = re.compile(r"sc-compose >= ([0-9]+\.[0-9]+\.[0-9]+), < ([0-9]+)")
TOOL_REQUIREMENT_RE = re.compile(r"([a-z][a-z0-9-]*)(?: >= ([0-9]+(?:\.[0-9]+){0,2})(?:, < [0-9]+(?:\.[0-9]+){0,2})?)?")


def sc_compose_range(pkg_dir: Path = PKG_DIR) -> Tuple[str, int]:
    """(floor, major ceiling) for the sc-compose CLI and Python wheel: the manifest's `sc-compose >= X.Y.Z, < N`."""
    requires = load_manifest(pkg_dir).get("requires", [])
    for entry in requires:
        m = SC_COMPOSE_RANGE_RE.fullmatch(str(entry))
        if m:
            return m.group(1), int(m.group(2))
    raise InstallError(f"{pkg_dir / MANIFEST_FILE}: requires has no `sc-compose >= X.Y.Z, < N` range")


def sc_compose_supported(version: str, pkg_dir: Path = PKG_DIR) -> bool:
    """True when `version` (X.Y.Z) is in the manifest's sc-compose range."""
    floor, ceiling = sc_compose_range(pkg_dir)
    m = re.fullmatch(r"([0-9]+)\.([0-9]+)\.([0-9]+)", version)
    if not m:
        return False
    parts = tuple(int(p) for p in m.groups())
    return tuple(int(p) for p in floor.split(".")) <= parts and parts[0] < ceiling


def sc_compose_upgrade(pkg_dir: Path = PKG_DIR) -> str:
    floor, ceiling = sc_compose_range(pkg_dir)
    return (f"python3 -m pip install 'sc-compose>={floor},<{ceiling}' and "
            f"brew upgrade randlee/tap/sc-compose (or cargo install sc-compose --version '>={floor}, <{ceiling}' --locked), "
            "the CLI and wheel at the same version")


def declared_tool_requirements(pkg_dir: Path = PKG_DIR) -> list[tuple[str, str]]:
    """CLI version floors declared in the manifest, excluding sc-compose's range."""
    requirements: list[tuple[str, str]] = []
    requires = load_manifest(pkg_dir).get("requires", [])
    for entry in requires:
        requirement = str(entry).split("#", 1)[0].strip()
        if SC_COMPOSE_RANGE_RE.fullmatch(requirement):
            continue
        match = TOOL_REQUIREMENT_RE.fullmatch(requirement)
        if match is None:
            raise InstallError(f"{pkg_dir / MANIFEST_FILE}: unrecognized requirement {requirement!r}")
        name, floor = match.groups()
        if name in HANDLED_ELSEWHERE_REQUIREMENTS:
            continue
        if name not in TOOL_INSTALLS:
            raise InstallError(f"{pkg_dir / MANIFEST_FILE}: unrecognized requirement {name!r}")
        if floor is None:
            raise InstallError(f"{pkg_dir / MANIFEST_FILE}: {name} must declare a version floor")
        requirements.append((name, floor))
    return requirements


def manifest_requirement_floor(name: str, pkg_dir: Path = PKG_DIR) -> str:
    """The required version floor for one non-range manifest requirement."""
    requires = load_manifest(pkg_dir).get("requires", [])
    for entry in requires:
        match = TOOL_REQUIREMENT_RE.fullmatch(str(entry).split("#", 1)[0].strip())
        if match is not None and match.group(1) == name:
            floor = match.group(2)
            if floor is None:
                raise InstallError(f"{pkg_dir / MANIFEST_FILE}: {name} must declare a version floor")
            return floor
    raise InstallError(f"{pkg_dir / MANIFEST_FILE}: requires has no {name} version floor")


def _version_parts(text: str) -> tuple[int, int, int] | None:
    match = re.search(r"\b([0-9]+)\.([0-9]+)(?:\.([0-9]+))?\b", text)
    if match is None:
        return None
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch or 0)


def _check_required_tool(name: str, required: str, install_command: str) -> None:
    if shutil.which(name) is None:
        raise InstallError(f"{name} is not on PATH; install it with: {install_command}")
    probe = subprocess.run([name, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    reported = (probe.stdout or probe.stderr).strip()
    if probe.returncode != 0:
        raise InstallError(f"{name} --version failed: {reported or 'no output'}; install it with: {install_command}")
    actual, floor = _version_parts(reported), _version_parts(required)
    if actual is None:
        raise InstallError(f"{name} --version did not report a semantic version: {reported or 'no output'}; install it with: {install_command}")
    assert floor is not None
    if name == "python3":
        _check_python_version(actual, "python3 on PATH")
    if actual < floor:
        raise InstallError(f"{name} is {'.'.join(map(str, actual))}, older than required {required}; install it with: {install_command}")


def config_variables(pkg_dir: Path = PKG_DIR) -> List[str]:
    """The required_variables of the config template: the one declaration of the inputs."""
    text = (pkg_dir / CONFIG_TEMPLATE).read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise InstallError(f"{CONFIG_TEMPLATE}: no front matter")
    try:
        loaded = TypeAdapter(ConfigTemplate).validate_python(_yaml().safe_load(m.group(1)) or {}, strict=True)
        return loaded.get("required_variables", [])
    except ValidationError as error:
        raise InstallError(f"{CONFIG_TEMPLATE}: required_variables must be a list of strings") from error


def load_legacy_owned(pkg_dir: Path = PKG_DIR) -> dict[str, set[str]]:
    path = pkg_dir / LEGACY_OWNED
    if not path.is_file():
        return {}
    try:
        value = TypeAdapter(LegacyOwnership).validate_python(json.loads(path.read_text(encoding="utf-8")), strict=True)
    except (json.JSONDecodeError, ValidationError) as error:
        raise InstallError(f"{path}: files must map paths to sha256 lists") from error
    return {relative_path: set(hashes) for relative_path, hashes in value["files"].items()}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Repository values
# ---------------------------------------------------------------------------


def repo_root_for(destination_path: Path) -> Path:
    """The consuming repository: the parent of <repo>/.claude or <repo>/.codex."""
    dest = Path(destination_path).resolve()
    if dest.name in (".claude", ".codex"):
        return dest.parent
    raise InstallError(f"--dest must be a repository's .claude or .codex directory, got {dest}")


def _git_origin_slug(repo_root: Path) -> Optional[str]:
    try:
        url = subprocess.run(
            ["git", "-C", str(repo_root), "remote", "get-url", "origin"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", url)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def _registry_location(name: str) -> str:
    if name in ROLE_KEYS:
        return f"{CONSUMER_REGISTRY} roles.{ROLE_KEYS[name]}"
    return f"{CONSUMER_REGISTRY} {name}"


def parse_set(items: Iterable[str]) -> Config:
    overrides: Config = {}
    for item in items:
        if "=" not in item:
            raise InstallError(f"--set expects NAME=VALUE, got {item!r}")
        k, v = item.split("=", 1)
        overrides[k.strip()] = v.strip()
    return overrides


def _coerce_set_value(name: str, raw: ConfigInputValue) -> ConfigInputValue:
    if name not in LIST_VARIABLES or not isinstance(raw, str):
        return raw
    text = raw.strip()
    if text.startswith("["):
        try:
            parsed: object = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InstallError(f"--set {name}: not a JSON array: {exc}") from exc
        if not isinstance(parsed, list):
            raise InstallError(f"--set {name}: JSON value must be an array of non-empty strings")
        try:
            values = TypeAdapter(list[str]).validate_python(parsed, strict=True)
        except ValidationError as exc:
            raise InstallError(f"--set {name}: JSON value must be an array of non-empty strings") from exc
        if not all(values):
            raise InstallError(f"--set {name}: JSON value must be an array of non-empty strings")
        return values
    return [part.strip() for part in text.split(",") if part.strip()]


def resolve_config(repo_root: Path, overrides: Mapping[str, ConfigInputValue], pkg_dir: Path = PKG_DIR) -> Config:
    """Read the declared variables from registry.yaml and --set. Missing ones are left
    out (the strict render names them); unknown --set keys and wrong types are errors."""
    names = [*config_variables(pkg_dir), "max_sanity_rounds", "gate_timeout_s"]
    unknown = sorted(k for k in overrides if k not in names)
    if unknown:
        raise InstallError(
            "unknown --set variable(s): " + ", ".join(unknown)
            + f"; the variables are the required_variables of {CONFIG_TEMPLATE}: " + ", ".join(names))
    registry = repo_root / CONSUMER_REGISTRY
    try:
        reg = TypeAdapter(ConsumerRegistry).validate_python(_load_yaml(registry), strict=True) if registry.is_file() else ConsumerRegistry()
    except ValidationError as error:
        for item in error.errors():
            location = item.get("loc", ())
            if not location:
                continue
            field = str(location[0])
            if field == "max_sanity_rounds":
                raise InstallError("max_sanity_rounds must be a positive integer") from error
            if field == "gate_timeout_s":
                raise InstallError("gate_timeout_s must be a positive integer number of seconds") from error
            if field in LIST_VARIABLES:
                raise InstallError(f"{field} must be a list of non-empty strings ({_registry_location(field)})") from error
            if field == "roles" and len(location) > 1:
                role = str(location[1])
                raise InstallError(f"roles.{role} must be a non-empty string ({CONSUMER_REGISTRY} roles.{role})") from error
            if field in names:
                raise InstallError(f"{field} must be a non-empty string ({_registry_location(field)})") from error
        raise InstallError(f"{registry}: invalid registry configuration: {error}") from error
    misplaced = sorted(n for n in ROLE_KEYS if n in reg)
    if misplaced:
        raise InstallError(
            f"{registry}: " + ", ".join(f"{n} belongs under roles.{ROLE_KEYS[n]}" for n in misplaced))
    roles = reg.get("roles", {})
    values: Config = {}
    rounds = overrides.get("max_sanity_rounds", reg.get("max_sanity_rounds", 5))
    if isinstance(rounds, str) and rounds.isdecimal():
        rounds = int(rounds)
    if isinstance(rounds, bool) or not isinstance(rounds, int) or rounds < 1:
        raise InstallError("max_sanity_rounds must be a positive integer")
    values["max_sanity_rounds"] = rounds
    timeout = overrides.get("gate_timeout_s", reg.get("gate_timeout_s", 180))
    if isinstance(timeout, str) and timeout.isdecimal():
        timeout = int(timeout)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
        raise InstallError("gate_timeout_s must be a positive integer number of seconds")
    values["gate_timeout_s"] = timeout
    for name in names:
        if name in ("max_sanity_rounds", "gate_timeout_s"):
            continue
        if name in overrides:
            value = _coerce_set_value(name, overrides[name])
        elif name in ROLE_KEYS:
            value = roles.get(ROLE_KEYS[name])
        else:
            value = reg.get(name)
        if value is None:
            continue
        if name in LIST_VARIABLES:
            if not isinstance(value, list):
                raise InstallError(f"{name} must be a list of non-empty strings ({_registry_location(name)}), got {value!r}")
            try:
                values_list = TypeAdapter(list[str]).validate_python(value, strict=True)
            except ValidationError as error:
                raise InstallError(f"{name} must be a list of non-empty strings ({_registry_location(name)}), got {value!r}") from error
            if not all(values_list):
                raise InstallError(f"{name} must be a list of non-empty strings ({_registry_location(name)}), got {value!r}")
            value = values_list
        elif not isinstance(value, str) or not value:
            raise InstallError(f"{name} must be a non-empty string ({_registry_location(name)}), got {value!r}")
        values[name] = value
    return values


def derived_values(repo_root: Path, config: Config) -> dict[str, str]:
    """The install-time render values that come from the repository itself."""
    slug = _git_origin_slug(repo_root)
    if not slug:
        raise InstallError(f"{repo_root}: no git remote 'origin' with an owner/name URL; add one (git remote add origin ...)")
    return {
        "repo_slug": slug,
        "repo_name": slug.rsplit("/", 1)[-1],
        "workflow_issues_root": f"{config['bead_prefix']}-workflow-issues",
        "console_install": CONSOLE_INSTALL,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _sc_compose(template_text: str, variables: JsonObject, *, suffix: str) -> Tuple[Optional[str], str]:
    """(rendered text, "") or (None, the sc-compose error), rendered strictly by the sc-compose wheel."""
    sys.path.insert(0, str(PKG_DIR / "skills/atm-beads/scripts"))
    try:
        import sc_render
    except ImportError as exc:
        raise InstallError(f"this python cannot import the sc-compose wheel ({exc}); "
                           f"install {sc_compose_upgrade()} and rerun") from exc
    finally:
        sys.path.pop(0)
    with tempfile.TemporaryDirectory(prefix="atm-bd-install-") as tmp:
        body = Path(tmp) / f"body{suffix}"
        body.write_text(template_text, encoding="utf-8")
        try:
            return sc_render.render(body, variables), ""
        except sc_render.RenderError as exc:
            return None, sc_render.error_text(exc)


MISSING_RE = re.compile(r"missing required variable: ([A-Za-z0-9_]+)")


def render_config(values: Config, pkg_dir: Path = PKG_DIR) -> bytes:
    """Render the config template strictly. A missing variable fails, naming it."""
    out, error = _sc_compose((pkg_dir / CONFIG_TEMPLATE).read_text(encoding="utf-8"),
                             json_object(values, "render configuration"), suffix=".yaml.j2")
    if out is None:
        missing = list(dict.fromkeys(MISSING_RE.findall(error)))
        if missing:
            raise InstallError(
                "sc-compose --strict: missing required variable(s): " + ", ".join(missing) + "; set "
                + "; ".join(f"{n} in {_registry_location(n)} (or --set {n}=...)" for n in missing))
        first = error.strip().splitlines()[:1]
        raise InstallError(f"sc-compose render of {CONFIG_TEMPLATE} failed: {first[0] if first else 'no output'}")
    return out.encode("utf-8")


def _split_frontmatter(text: str) -> Tuple[str, str]:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[: end + 5], text[end + 5 :]
    return "", text


def render_text(text: str, variables: Dict[str, str]) -> str:
    """Render one skill/agent file body with sc-compose (strict: every referenced token must be declared)."""
    front, body = _split_frontmatter(text)
    declared = "".join(f"  - {name}\n" for name in RENDER_VARIABLES)
    template = f"---\nname: atm-bd-install\nversion: 1.0.0\nformat: markdown\nrequired_variables:\n{declared}---\n{body}"
    rendered, error = _sc_compose(template, {n: variables[n] for n in RENDER_VARIABLES}, suffix=".md")
    if rendered is None:
        first = error.strip().splitlines()[:1]
        raise InstallError(f"sc-compose render failed: {first[0] if first else 'no output'}")
    if body.endswith("\n") and not rendered.endswith("\n"):
        rendered += "\n"
    leftover = PLACEHOLDER_RE.search(rendered)
    if leftover:
        raise InstallError(f"placeholder {leftover.group(0)} survived rendering")
    return front + rendered


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_tools() -> None:
    _check_python_version(tuple(sys.version_info[:3]), "installer interpreter")
    _check_required_tool("python3", manifest_requirement_floor("python3"), PYTHON_INSTALL)
    floor, ceiling = sc_compose_range()
    needs = f"the package needs >= {floor}, < {ceiling}"
    if shutil.which("sc-compose") is None:
        raise InstallError(f"sc-compose is not on PATH; install {sc_compose_upgrade()} and rerun")
    cli = subprocess.run(["sc-compose", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    cli_version = (cli.stdout.split() or [""])[-1]
    if cli.returncode != 0 or not sc_compose_supported(cli_version):
        raise InstallError(f"sc-compose CLI is {cli.stdout.strip() or cli.stderr.strip()}, {needs}; "
                           f"install {sc_compose_upgrade()} and rerun")
    # validate-plan runs scripts/bead_schema.py (pydantic) and the scripts render with the
    # sc-compose wheel, all with the python3 on PATH.
    probe = subprocess.run(["python3", "-c", "from pydantic import JsonValue, TypeAdapter; "
                            "import yaml, sc_compose, importlib.metadata as m; print(m.version('sc-compose'))"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if probe.returncode != 0:
        raise InstallError("python3 on PATH cannot import Pydantic v2 JsonValue/TypeAdapter, PyYAML and the sc-compose wheel, "
                           "which the scripts need; install them (python3 -m pip "
                           f"install 'pydantic>=2' pyyaml 'sc-compose=={cli_version}') and rerun")
    wheel_version = probe.stdout.strip()
    if not sc_compose_supported(wheel_version):
        raise InstallError(f"python3 on PATH has the sc-compose wheel {wheel_version}, {needs}; "
                           f"install {sc_compose_upgrade()} and rerun")
    if wheel_version != cli_version:
        raise InstallError(f"the sc-compose CLI is {cli_version} and the python3 wheel is {wheel_version}; they must "
                           f"be the same version; install {sc_compose_upgrade()} and rerun")
    try:
        from importlib.metadata import version
        __import__("sc_compose")
        interpreter_version = version("sc-compose")
    except (ImportError, PackageNotFoundError) as exc:
        raise InstallError(f"the installer interpreter {sys.executable} cannot load sc-compose; "
                           f"upgrade the app or install sc-compose=={cli_version} in the host interpreter") from exc
    if interpreter_version != cli_version:
        raise InstallError(f"the sc-compose CLI is {cli_version} but the installer interpreter wheel is "
                           f"{interpreter_version}; upgrade the app or host to sc-compose=={cli_version} and rerun")
    for name, floor in declared_tool_requirements():
        _check_required_tool(name, floor, TOOL_INSTALLS[name])


def check_beads_server_mode(repo_root: Path) -> None:
    path = repo_root / BEADS_METADATA
    if not path.is_file():
        raise InstallError(f"BEADS_NOT_SERVER_MODE: {path} not found; the loop needs a beads database in "
                           "Dolt server mode (bd doctor --json), so initialise it against a dolt sql-server")
    try:
        metadata = TypeAdapter(BeadsMetadata).validate_python(json.loads(path.read_text(encoding="utf-8")), strict=True)
        mode = metadata.get("dolt_mode")
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise InstallError(f"BEADS_NOT_SERVER_MODE: {path}: unreadable: {exc}") from exc
    if mode != "server":
        raise InstallError(f"BEADS_NOT_SERVER_MODE: {path} has dolt_mode {mode!r}, not 'server'; validate-plan needs "
                           "bd doctor --json, which only server mode provides")


def check_agents(repo_root: Path, config: Config, shipped_agents: Iterable[str]) -> None:
    shipped = {Path(rel).stem for rel in shipped_agents}
    missing: List[str] = []
    for var in AGENT_VARIABLES:
        configured = config[var]
        if isinstance(configured, str):
            names = [configured]
        elif isinstance(configured, list):
            names = configured
        else:
            raise InstallError(f"{var} must name agents as strings")
        for name in names:
            if name in shipped or (repo_root / ".claude" / "agents" / f"{name}.md").is_file():
                continue
            missing.append(f"{name} ({var})")
    if missing:
        raise InstallError("no .claude/agents/<name>.md for: " + ", ".join(dict.fromkeys(missing)))


# ---------------------------------------------------------------------------
# Install plan: what to write, what to remove, what is in the way
# ---------------------------------------------------------------------------


@dataclass
class Plan:
    repo_root: Path
    target_prefix: str                                   # ".claude/" or ".codex/"
    writes: dict[str, tuple[bytes, bool]] = field(default_factory=lambda: dict[str, tuple[bytes, bool]]())   # repo-rel -> (bytes, executable)
    removals: list[str] = field(default_factory=lambda: list[str]())
    problems: list[str] = field(default_factory=lambda: list[str]())
    lock_files: dict[str, str] = field(default_factory=lambda: dict[str, str]())
    backups: list[str] = field(default_factory=lambda: list[str]())     # files in the way, moved to .backup/ by --overwrite
    registry_text: Optional[str] = None                  # registry.yaml with the roles written, if it changes
    dev_sanity_member: Optional[str] = None              # team member to add for the dev-sanity role (.claude only)
    notices: list[str] = field(default_factory=lambda: list[str]())     # steps the install could not do; printed for the user
    written: list[str] = field(default_factory=lambda: list[str]())     # files whose bytes changed (filled by apply_plan)
    members_added: list[str] = field(default_factory=lambda: list[str]())  # team members created (filled by apply_plan)
    sanity: Optional["SanityMember"] = None              # the dev-sanity roster outcome (filled by apply_plan)


def _read_lock(repo_root: Path) -> Optional[InstallLock]:
    path = repo_root / LOCK_OUT
    if not path.is_file():
        return None
    try:
        data = TypeAdapter(InstallLock).validate_python(json.loads(path.read_text(encoding="utf-8")), strict=True)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise InstallError(f"{path}: not valid JSON ({exc}); restore it from git") from exc
    if data["package"] != PACKAGE:
        raise InstallError(f"{path}: not an {PACKAGE} install record; restore it from git")
    return data


def desired_files(pkg_dir: Path, target_prefix: str, *, codex: bool, render_values: dict[str, str],
                  config_bytes: bytes) -> dict[str, tuple[bytes, bool, str]]:
    """repo-relative path -> (bytes, executable, package source path)."""
    render_value = load_registry(pkg_dir).get("render", [])
    renders = set(_string_list(render_value, f"{pkg_dir / 'registry.yaml'}: render"))
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
            locked = TypeAdapter(dict[str, str]).validate_python(lock["files"], strict=True)
        except ValidationError as error:
            raise InstallError(f"{repo_root / LOCK_OUT}: files must map paths to hashes") from error
    legacy = load_legacy_owned(pkg_dir) if lock is None else {}
    dev_sanity_value = config.get("dev_sanity_member")
    if dev_sanity_value is not None and not isinstance(dev_sanity_value, str):
        raise InstallError("dev_sanity_member must be a string")
    plan = Plan(repo_root=repo_root, target_prefix=target_prefix,
                dev_sanity_member=None if codex else dev_sanity_value)

    def owned(key: str, data: bytes, pkg_rel: Optional[str]) -> Optional[bool]:
        """True owned and unmodified, False in the way, None for locked-but-modified."""
        digest = sha256(data)
        if key in locked:
            return True if locked[key] == digest else None
        if pkg_rel is None:
            return False
        shipped: set[str] = {sha256(wanted[key][0])} if key in wanted else set()
        src = pkg_dir / pkg_rel
        if src.is_file() and pkg_rel != CONFIG_TEMPLATE:
            shipped.add(sha256(src.read_bytes()))   # sc-install copies the raw source before complete()
        shipped |= legacy.get(pkg_rel, set())
        return digest in shipped

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
            pkg_rel = wanted[key][2] if key in wanted else _legacy_pkg_rel(key, target_prefix, legacy)
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


def _legacy_pkg_rel(key: str, target_prefix: str, legacy: dict[str, set[str]]) -> Optional[str]:
    rel = key[len(target_prefix):] if key.startswith(target_prefix) else None
    return rel if rel is not None and rel in legacy else None


# ---------------------------------------------------------------------------
# Applying a plan
# ---------------------------------------------------------------------------


def roles_text(registry: Path, roles: dict[str, str]) -> Optional[str]:
    """registry.yaml with roles.<role> set, keeping the rest of the file as written;
    None when nothing changes."""
    text = registry.read_text(encoding="utf-8") if registry.is_file() else ""
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if re.match(r"^roles:\s*(#.*)?$", line.rstrip("\n"))), None)
    if start is None:
        new = text + ("\n" if text and not text.endswith("\n") else "")
        new += "roles:\n" + "".join(f"  {k}: {v}\n" for k, v in roles.items())
    else:
        end = start + 1
        while end < len(lines) and (not lines[end].strip() or lines[end][:1] in (" ", "\t")):
            end += 1
        block = lines[start + 1:end]
        trailing: List[str] = []
        while block and not block[-1].strip():
            trailing.insert(0, block.pop())
        if block and not block[-1].endswith("\n"):
            block[-1] += "\n"
        indent = next((m.group(1) for m in (re.match(r"^([ \t]+)\S", line) for line in block) if m), "  ")
        for role, member in roles.items():
            pattern = re.compile(rf"^({re.escape(indent)}{re.escape(role)}:[ \t]*)([^#\n]*?)([ \t]*(?:#.*)?\n?)$")
            for i, line in enumerate(block):
                m = pattern.match(line)
                if m:
                    block[i] = f"{indent}{role}: {member}{m.group(3)}"
                    break
            else:
                block.append(f"{indent}{role}: {member}\n")
        new = "".join(lines[:start + 1] + block + trailing + lines[end:])
    yaml_api = _yaml()
    try:
        decoded: object = yaml_api.safe_load(new)
        decoded_object = json_object(decoded, str(registry)) if decoded is not None else {}
        roles_value = decoded_object.get("roles", {})
        new_roles = json_object(roles_value, f"{registry}: roles") if isinstance(roles_value, dict) else {}
    except yaml_api.error_type:
        new_roles = {}
    if any(new_roles.get(k) != v for k, v in roles.items()):
        raise InstallError(f"{registry}: could not write roles {roles} (is roles: a flow mapping?); set them by hand and rerun")
    return None if new == text else new


def write_roles(registry: Path, roles: dict[str, str]) -> bool:
    """Set roles.<role> in registry.yaml. Returns True when the file changed."""
    new = roles_text(registry, roles)
    if new is None:
        return False
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(new, encoding="utf-8")
    return True


def provision_tool_identity(repo_root: Path) -> bool:
    """Create the default notification identity, tolerating a verified existing member.
    Returns True when the member was created."""
    command = ["atm", "teams", "add-member", "tool", "atm-bd", "--agent-type", "tool", "--model", "none"]
    try:
        added = subprocess.run(command, cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if added.returncode == 0:
            return True
        existing = subprocess.run(["atm", "members", "--team", "tool", "--json"], cwd=repo_root,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if existing.returncode == 0:
            members = _members(existing.stdout)
            if members is None:
                raise ValueError("atm members response did not contain typed members")
            if any(member.get("name") == "atm-bd" and member.get("agent_type") == "tool"
                   for member in members):
                return False
    except (OSError, ValueError, AttributeError, TypeError) as exc:
        raise InstallError(f"could not provision atm-bd@tool: {exc}; run {' '.join(command)}") from exc
    raise InstallError(f"could not provision atm-bd@tool: {added.stderr.strip() or added.stdout.strip()}; run {' '.join(command)}")


def atm_default_team(repo_root: Path) -> Optional[str]:
    """`[atm] default_team` from the repository's .atm.toml, or None when absent or unreadable."""
    team = _atm_toml(repo_root).get("atm", {}).get("default_team")
    return team if isinstance(team, str) and team else None


def _atm_json(argv: List[str], repo_root: Path) -> Tuple[Optional[str], str]:
    """Run a read-only atm command; (its JSON response text, "") or (None, reason)."""
    try:
        done = subprocess.run(argv, cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except OSError as exc:
        return None, f"{' '.join(argv)}: {exc}"
    if done.returncode != 0:
        return None, f"{' '.join(argv)} failed ({done.stderr.strip() or done.stdout.strip() or f'exit {done.returncode}'})"
    try:
        json.loads(done.stdout)
        return done.stdout, ""
    except json.JSONDecodeError as exc:
        return None, f"{' '.join(argv)} printed no JSON ({exc})"


def _members(data: str | None) -> Optional[List[Member]]:
    if data is None:
        return None
    try:
        return TypeAdapter(MembersResponse).validate_python(json.loads(data), strict=True)["members"]
    except (json.JSONDecodeError, ValidationError):
        return None


def _team_names(data: str | None) -> Optional[List[str]]:
    if data is None:
        return None
    try:
        teams = TypeAdapter(TeamsResponse).validate_python(json.loads(data), strict=True)["teams"]
    except (json.JSONDecodeError, ValidationError):
        return None
    return [team["name"] for team in teams]


def _atm_toml(repo_root: Path) -> AtmToml:
    try:
        return TypeAdapter(AtmToml).validate_python(
            tomllib.loads((repo_root / ATM_CONFIG).read_text(encoding="utf-8")), strict=True
        )
    except (OSError, tomllib.TOMLDecodeError, ValidationError):
        return AtmToml()


def pane_alias(repo_root: Path, member: str) -> Optional[str]:
    """The `alias` of the .atm.toml `[[rmux.windows.panes]]` entry named `member`, if any."""
    rmux = _atm_toml(repo_root).get("rmux", {})
    for window in rmux.get("windows", []):
        for pane in window.get("panes", []):
            if pane.get("name") == member:
                alias = pane.get("alias")
                return alias if alias else None
    return None


def suggested_alias(repo_root: Path, taken: Iterable[str] = ()) -> str:
    """`<prefix>-sanity`: the prefix is the repository directory name's first word
    (split on -, _ or .), lowercased and cut to three letters: raptor -> rap-sanity,
    atm-core -> atm-sanity. A name in `taken` gets the first free number appended."""
    first = re.split(r"[-_.]", repo_root.name.lower(), maxsplit=1)[0] or "repo"
    base, used = f"{first[:3]}-sanity", set(taken)
    return next(name for name in (base, *(f"{base}{n}" for n in range(2, len(used) + 3))) if name not in used)


def herdr_rename_hint(name: str) -> str:
    return f"name the dev-sanity herdr agent {name} or nudges will not reach it: herdr agent rename <pane> {name}"


def _host_name(member: Member) -> Optional[str]:
    """The name Herdr targets a member by on this host: its alias, else its member name."""
    alias = member.get("alias")
    name = member.get("name")
    if isinstance(alias, str) and alias:
        return alias
    return name if isinstance(name, str) else None


@dataclass
class SanityMember:
    added: bool = False
    notice: Optional[str] = None
    host_name: Optional[str] = None        # the alias, else the member name, it was added under
    suggest_alias: Optional[str] = None    # an alias to recommend for the .atm.toml pane entry


def provision_dev_sanity_member(repo_root: Path, member: str) -> SanityMember:
    """Add the dev-sanity member to the repository's own team when the roster lacks it.

    The member name is team-scoped. Herdr targets a member by its host name: the
    roster alias when it has one, else the member name, and that must be unique on
    the host. The alias comes from the `.atm.toml` `[[rmux.windows.panes]]` entry
    named for the member; `--alias` is passed only when that entry declares one.
    The member is not added when any other member on this host already has the same
    host name: every team is read, none but our own is changed. The notice names
    what the user must do. Never fails the install."""
    team = atm_default_team(repo_root)
    alias = pane_alias(repo_root, member)
    host_name = alias or member

    def command(use_alias: Optional[str]) -> List[str]:
        argv = ["atm", "teams", "add-member", team or "<team>", member, "--agent-type", "claude-code",
                "--model", "sonnet", "--home-dir", str(repo_root), "--backend", "herdr"]
        return argv + (["--alias", use_alias] if use_alias else [])

    run_it = f"run: {' '.join(command(alias))}"
    if team is None:
        return SanityMember(notice=f"dev-sanity member {member} not added: no [atm] default_team in "
                                   f"{repo_root / ATM_CONFIG}; set it, then {run_it}")
    own, reason = _atm_json(["atm", "members", "--team", team, "--json"], repo_root)
    own_members = _members(own) if reason == "" else None
    if own_members is None:
        return SanityMember(notice=f"dev-sanity member {member} not checked: "
                                   f"{reason or 'atm members gave no members list'}; {run_it}")
    if any(m.get("name") == member for m in own_members):
        return SanityMember()
    listed, reason = _atm_json(["atm", "teams", "--json"], repo_root)
    teams = _team_names(listed) if reason == "" else None
    if teams is None:
        return SanityMember(notice=f"dev-sanity member {member} not checked for host name {host_name} on this host: "
                                   f"{reason or 'atm teams gave no teams list'}; check every team's members, then {run_it}")
    host_names: Dict[str, str] = {}   # host name -> member@team, our own team first
    for other in [team, *(t for t in teams if t != team)]:
        if other == team:
            members: Optional[List[Member]] = own_members
        else:
            data, reason = _atm_json(["atm", "members", "--team", other, "--json"], repo_root)
            members = _members(data) if reason == "" else None
        if members is None:
            return SanityMember(notice=f"dev-sanity member {member} not checked for host name {host_name} in team "
                                       f"{other}: {reason or 'atm members gave no members list'}; check it, then {run_it}")
        for m in members:
            name = _host_name(m)
            if isinstance(name, str):
                host_names.setdefault(name, f"{m.get('name')}@{other}")
    holder = host_names.get(host_name)
    if holder is not None:
        suggestion = suggested_alias(repo_root, host_names)
        return SanityMember(notice=f"dev-sanity member {member} not added: {host_name} is taken by {holder} "
                                   f"on this host, and agents with one name on one machine cannot be told apart; "
                                   f"give it a unique name such as {suggestion}, either as roles.dev-sanity in "
                                   f"{CONSUMER_REGISTRY} or as the alias of its pane in {ATM_CONFIG} (see the "
                                   f"recommended addition above), {herdr_rename_hint(suggestion)}, then rerun the install",
                            suggest_alias=suggestion)
    try:
        added = subprocess.run(command(alias), cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except OSError as exc:
        return SanityMember(notice=f"dev-sanity member {member} not added: {exc}; {run_it}")
    if added.returncode == 0:
        return SanityMember(added=True, host_name=host_name)
    reason = added.stderr.strip() or added.stdout.strip() or f"exit {added.returncode}"
    return SanityMember(notice=f"dev-sanity member {member} not added: {reason}; {run_it}")


def _toml_key(name: str) -> str:
    return name if re.fullmatch(r"[A-Za-z0-9_-]+", name) else json.dumps(name)


def recommended_startup_block(repo_root: Path, member: str, lead: Optional[str]) -> Optional[str]:
    """The `[startup.<member>]` block to recommend for .atm.toml, or None when it has one."""
    startup = _atm_toml(repo_root).get("startup", {})
    if member in startup:
        return None
    lines = [
        "Your role is dev-sanity under atm-bd-orchestration: read .claude/agents/dev-sanity.md now "
        "(again after every compaction) and run its Startup section",
        f"Use native atm send or atm ack for messages to {lead or '<lead>'}",
        "Use native atm read to read messages from team-members",
    ]
    body = ",\n       ".join(json.dumps(line) for line in lines)
    return f"[startup.{_toml_key(member)}]\nall = [{body} ]\n"


def change_report(plan: Plan, config: Mapping[str, ConfigValue]) -> List[str]:
    """The itemized list of what the install changed, plus the .atm.toml recommendation."""
    out = ["Changes:"]
    out += [f"  written: {key}" for key in plan.written]
    out += [f"  removed: {key}" for key in plan.removals]
    out += [f"  backed up to {BACKUP_DIR}/: {key}" for key in plan.backups]
    if plan.registry_text is not None:
        roles = ", ".join(f"{role}: {config[var]}" for var, role in ROLE_KEYS.items() if var in config)
        out.append(f"  roles set in {CONSUMER_REGISTRY}: {roles}")
    out += [f"  member added: {name}" for name in plan.members_added]
    if len(out) == 1:
        out.append("  none")
    sanity, member = plan.sanity, plan.dev_sanity_member
    if sanity is not None and sanity.added and sanity.host_name:
        out.append(f"  then: {herdr_rename_hint(sanity.host_name)}")
    if member:
        recommend: List[str] = []
        if sanity is not None and sanity.suggest_alias:
            recommend += ["[[rmux.windows.panes]]", f"name = {json.dumps(member)}", f"alias = {json.dumps(sanity.suggest_alias)}", ""]
        lead = config.get("team_lead_member")
        block = recommended_startup_block(plan.repo_root, member, lead if isinstance(lead, str) else None)
        if block:
            recommend += block.rstrip("\n").splitlines()
        if recommend:
            out += [f"Recommended addition to {ATM_CONFIG} (not written):", *(recommend if block else recommend[:-1])]
    return out


def completion_report(plan: Plan, config: Mapping[str, ConfigValue]) -> List[str]:
    """What every install front end prints after apply_plan: the change list, then one NOT DONE line per notice."""
    return [*change_report(plan, config), *(f"{PACKAGE}: NOT DONE: {notice}" for notice in plan.notices)]


def apply_plan(plan: Plan, version: str) -> int:
    """Write the plan; return the number of files whose bytes changed."""
    root = plan.repo_root
    if provision_tool_identity(root):
        plan.members_added.append("atm-bd@tool")
    if plan.dev_sanity_member:
        plan.sanity = provision_dev_sanity_member(root, plan.dev_sanity_member)
        if plan.sanity.added:
            plan.members_added.append(f"{plan.dev_sanity_member}@{atm_default_team(root)} (host name {plan.sanity.host_name})")
        if plan.sanity.notice:
            plan.notices.append(plan.sanity.notice)
            print(f"warning: {plan.sanity.notice}", file=sys.stderr)
    changed = 0
    if plan.backups:
        backup = root / BACKUP_DIR / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        for key in plan.backups:
            print(f"warning: {key} is modified or not {PACKAGE}'s; moved to {(backup / key).relative_to(root)}", file=sys.stderr)
            (backup / key).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(root / key), str(backup / key))
        ignore = root / BACKUP_DIR / ".gitignore"   # backups are for local review; git history already has the files
        if not ignore.exists():
            ignore.write_text("*\n")
    for key, (data, executable) in plan.writes.items():
        path = root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file() or path.read_bytes() != data:
            path.write_bytes(data)
            plan.written.append(key)
            changed += 1
        if executable:
            path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    for key in plan.removals:
        path = root / key
        path.unlink(missing_ok=True)   # a backed-up file is already gone
        parent = path.parent
        stop = root / plan.target_prefix
        while parent not in (stop, root) and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
    lock = {"package": PACKAGE, "version": version, "files": dict(sorted(plan.lock_files.items()))}
    lock_path = root / LOCK_OUT
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    if plan.registry_text is not None:
        (root / CONSUMER_REGISTRY).write_text(plan.registry_text, encoding="utf-8")
    return changed


# ---------------------------------------------------------------------------
# sc-install hook contract
# ---------------------------------------------------------------------------


def _ok() -> dict[str, str]:
    return {"result": "success"}


def _fail(message: str) -> dict[str, str]:
    return {"result": "fail", "message": message}


def _codex(destination_path: str, options: InstallerHookOptions) -> bool:
    return bool(options.get("codex")) or Path(destination_path).name == ".codex"


def _plan_or_fail(source_path: str, destination_path: str, options: InstallerHookInput) -> Tuple[Optional[Plan], Config, Optional[dict[str, str]]]:
    try:
        _check_python_version(tuple(sys.version_info[:3]), "installer interpreter")
        _load_validation_dependencies()
        check_tools()
        try:
            parsed_options = TypeAdapter(InstallerHookOptions).validate_python(options, strict=True)
        except ValidationError as error:
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
        _load_validation_dependencies()
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
        _load_validation_dependencies()
    except InstallError:
        # The install hook reports the missing dependency from prepare()/complete().
        pass
