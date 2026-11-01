"""Shared installer configuration, types and package utilities."""
# pyright: strict
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
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
    "uv": "brew install uv (or: curl -LsSf https://astral.sh/uv/install.sh | sh)",
}

SCRIPT_HEADER = (
    "#!/usr/bin/env -S uv run --script\n"
    "# /// script\n"
    '# requires-python = ">=3.11,<3.12"\n'
    '# dependencies = ["pydantic>=2", "pyyaml", "sc-compose>=1.7.0,<2", "atm-bd-types==0.19.12"]\n'
    "# ///\n"
)
"""The first lines of every executable script. `uv run --script` gives each run Python 3.11 with the
scripts' dependencies from this inline metadata (PEP 723), whatever `python3` is first on PATH, and
one header means one cached environment, so a script may start a sibling with `sys.executable` (#629)."""

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


class InstallError(RuntimeError):
    """An install refusal; the message names what to fix."""


class UnsupportedPythonError(InstallError):
    """The interpreter is outside the supported Python 3.11 boundary."""


def _check_python_version(version: tuple[int, ...], interpreter: str) -> None:
    if version[:2] != (3, 11):
        raise UnsupportedPythonError(
            f"UNSUPPORTED_PYTHON: {interpreter} is {'.'.join(map(str, version))}; "
            "install and run under Python 3.11 (sc-compose 1.7.0 ships cp311 wheels only)"
        )


def load_validation_dependencies() -> None:
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


def string_list(value: object, context: str) -> list[str]:
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
    return (f"brew upgrade randlee/tap/sc-compose (or cargo install sc-compose --version '>={floor}, <{ceiling}' --locked) "
            "so the CLI is the version the script runtime resolves; `uv cache clean sc-compose` refreshes a stale wheel")


def script_runtime_sc_compose_version() -> str:
    """The sc-compose wheel version the scripts run with: `uv run --script` on a probe carrying SCRIPT_HEADER."""
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "probe.py"
        probe.write_text(SCRIPT_HEADER + "import importlib.metadata as m, pydantic, sc_compose, yaml\n"
                         "print(m.version('sc-compose'))\n", encoding="utf-8")
        run = subprocess.run(["uv", "run", "--script", str(probe)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, cwd=tmp)
    if run.returncode != 0:
        lines = (run.stderr or run.stdout).strip().splitlines()
        raise InstallError("SCRIPT_RUNTIME: `uv run --script` could not provide Python 3.11 with pydantic, PyYAML and the "
                           f"sc-compose wheel, which the scripts need: {lines[-1] if lines else 'no output'}; "
                           "run `uv python install 3.11` and rerun")
    return run.stdout.strip()


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
    sys.path.insert(0, str(PKG_DIR / "core/scripts"))
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
    for name, floor in declared_tool_requirements():
        _check_required_tool(name, floor, TOOL_INSTALLS[name])
    floor, ceiling = sc_compose_range()
    needs = f"the package needs >= {floor}, < {ceiling}"
    if shutil.which("sc-compose") is None:
        raise InstallError(f"sc-compose is not on PATH; install {sc_compose_upgrade()} and rerun")
    cli = subprocess.run(["sc-compose", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    cli_version = (cli.stdout.split() or [""])[-1]
    if cli.returncode != 0 or not sc_compose_supported(cli_version):
        raise InstallError(f"sc-compose CLI is {cli.stdout.strip() or cli.stderr.strip()}, {needs}; "
                           f"install {sc_compose_upgrade()} and rerun")
    # The scripts run under `uv run --script` (SCRIPT_HEADER): that runtime's sc-compose wheel is the one that counts.
    wheel_version = script_runtime_sc_compose_version()
    if not sc_compose_supported(wheel_version):
        raise InstallError(f"the script runtime has the sc-compose wheel {wheel_version}, {needs}; "
                           f"install {sc_compose_upgrade()} and rerun")
    if wheel_version != cli_version:
        raise InstallError(f"the sc-compose CLI is {cli_version} and the script runtime's wheel is {wheel_version}; they must "
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
class SanityMember:
    added: bool = False
    notice: Optional[str] = None
    host_name: Optional[str] = None        # the alias, else the member name, it was added under
    suggest_alias: Optional[str] = None    # an alias to recommend for the .atm.toml pane entry



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


def legacy_pkg_rel(key: str, target_prefix: str, legacy: dict[str, set[str]]) -> Optional[str]:
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
