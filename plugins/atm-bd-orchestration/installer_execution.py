"""Apply plans, back up changes and provision installer identities."""
# pyright: strict
from __future__ import annotations

import json
import re
import stat
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Tuple, TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from pydantic import JsonValue
    from typing_extensions import TypeForm
    JsonObject: TypeAlias = dict[str, JsonValue]
    _json_object_schema_type: TypeForm[JsonObject]

import installer_common as common
from installer_ownership import backup_files
from installer_common import (
    ATM_CONFIG,
    AtmToml,
    BACKUP_DIR,
    CONSUMER_REGISTRY,
    ConfigValue,
    InstallError,
    LOCK_OUT,
    Member,
    MembersResponse,
    PACKAGE,
    Plan,
    SanityMember,
    ROLE_KEYS,
    TeamsResponse,
)

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
        return common.TypeAdapter(MembersResponse).validate_python(json.loads(data), strict=True)["members"]
    except (json.JSONDecodeError, common.ValidationError):
        return None


def _team_names(data: str | None) -> Optional[List[str]]:
    if data is None:
        return None
    try:
        teams = common.TypeAdapter(TeamsResponse).validate_python(json.loads(data), strict=True)["teams"]
    except (json.JSONDecodeError, common.ValidationError):
        return None
    return [team["name"] for team in teams]


def _atm_toml(repo_root: Path) -> AtmToml:
    try:
        return common.TypeAdapter(AtmToml).validate_python(
            tomllib.loads((repo_root / ATM_CONFIG).read_text(encoding="utf-8")), strict=True
        )
    except (OSError, tomllib.TOMLDecodeError, common.ValidationError):
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
    backup_files(root, plan.backups)
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
