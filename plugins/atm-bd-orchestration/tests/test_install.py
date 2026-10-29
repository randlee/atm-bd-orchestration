"""Package consistency and installer tests.

Run from the package root: `python3 -m pytest -q` (conftest.py sets the path).
The install tests need `sc-compose` on PATH; they are skipped (and say so) without it.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import io
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
import yaml

import gen_manifest
import install
from subprocess_helpers import run_command

PKG = Path(__file__).resolve().parents[1]
SC_COMPOSE = shutil.which("sc-compose") is not None
REPO_STRINGS = ("sc-observability", "sc-obs", "obs-", "randlee/sc-", "/Users/randlee", "atm-core", "atm-dev")
SPEC_VARIABLES = [
    "bead_prefix", "dev_sanity_member", "qa_member", "team_lead_member", "worktree_base", "test_command",
    "lint_command", "integration_branch_pattern", "plans_dir", "requirements_globs", "adr_globs",
    "policy_path", "reviewers_round1",
]
needs_sc_compose = pytest.mark.skipif(not SC_COMPOSE, reason="sc-compose not on PATH; install not verified")


@pytest.fixture(autouse=True)
def current_installer_tools(tmp_path, monkeypatch):
    """Only direct installer tests receive fakes; installed suites inherit real PATH."""
    bin_dir = tmp_path / "required-tools"
    bin_dir.mkdir()
    for name, version in dict(install.declared_tool_requirements()).items():
        if name in {"atm", "atm-bd", "bd", "jq"}:
            path = bin_dir / name
            path.write_text(f"#!/bin/sh\necho '{name} {version}'\n")
            path.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_provision_tool_identity_adds_member_and_accepts_verified_existing(tmp_path, monkeypatch):
    calls = []
    outcomes = iter([
        subprocess.CompletedProcess([], 0, "created", ""),
        subprocess.CompletedProcess([], 3, "", "already exists"),
        subprocess.CompletedProcess([], 0, json.dumps({"members": [{"name": "atm-bd", "agent_type": "tool"}]}), ""),
    ])

    def run(argv, **kwargs):
        calls.append((argv, kwargs["cwd"]))
        return next(outcomes)

    monkeypatch.setattr(subprocess, "run", run)
    install.provision_tool_identity(tmp_path)
    install.provision_tool_identity(tmp_path)
    assert calls == [
        (["atm", "teams", "add-member", "tool", "atm-bd", "--agent-type", "tool", "--model", "none"], tmp_path),
        (["atm", "teams", "add-member", "tool", "atm-bd", "--agent-type", "tool", "--model", "none"], tmp_path),
        (["atm", "members", "--team", "tool", "--json"], tmp_path),
    ]


def test_provision_tool_identity_does_not_mask_failures(tmp_path, monkeypatch):
    outcomes = iter([
        subprocess.CompletedProcess([], 3, "", "permission denied"),
        subprocess.CompletedProcess([], 0, '{"members": []}', ""),
    ])
    monkeypatch.setattr(subprocess, "run", lambda *_args, **_kwargs: next(outcomes))
    with pytest.raises(install.InstallError, match="permission denied"):
        install.provision_tool_identity(tmp_path)


def test_provision_failure_stops_install_before_writes_and_is_reported(tmp_path, monkeypatch):
    repo = tmp_path / "consumer"
    repo.mkdir()
    plan = SimpleNamespace(repo_root=repo)
    monkeypatch.setattr(install, "provision_tool_identity", lambda _root: (_ for _ in ()).throw(install.InstallError("provision failed")))
    with pytest.raises(install.InstallError, match="provision failed"):
        install.apply_plan(cast(install.Plan, plan), "1.0")
    assert list(repo.iterdir()) == []
    monkeypatch.setattr(install, "_plan_or_fail", lambda *_args: (plan, {}, None))
    monkeypatch.setattr(install, "package_version", lambda *_args: "1.0")
    assert install.complete("source", "destination", {}) == {"result": "fail", "message": "provision failed"}


def _atm_toml(repo: Path, team: str = "my-team", *, alias: str | None = None, startup: bool = False) -> None:
    text = f'[atm]\ndefault_team = "{team}"\n'
    if startup:
        text += '\n[startup.my-sanity]\nall = ["mine"]\n'
    text += '\n[[rmux.windows]]\nname = "agents"\n\n[[rmux.windows.panes]]\nname = "my-sanity"\n'
    if alias:
        text += f'alias = "{alias}"\n'
    (repo / ".atm.toml").write_text(text)


def _roster(*members) -> str:
    """members: names or (name, alias) pairs."""
    rows = [{"name": m, "agent_type": "claude-code"} if isinstance(m, str) else
            {"name": m[0], "agent_type": "claude-code", "alias": m[1]} for m in members]
    return json.dumps({"members": rows})


def _add_sanity(repo: Path, alias: str | None = None) -> list:
    return ["atm", "teams", "add-member", "my-team", "my-sanity", "--agent-type", "claude-code",
            "--model", "sonnet", "--home-dir", str(repo), "--backend", "herdr", *(["--alias", alias] if alias else [])]


class FakeAtm:
    """The atm roster boundary: `members --team T`, `teams`, `teams add-member`. Records every call."""

    def __init__(self, rosters: dict, *, add_rc: int = 0, fail: dict | None = None):
        self.rosters, self.add_rc, self.fail, self.calls = rosters, add_rc, fail or {}, []

    def __call__(self, argv, **_kwargs):
        argv = list(argv)
        self.calls.append(argv)
        key = " ".join(argv)
        if key in self.fail:
            result = self.fail[key]
            if isinstance(result, Exception):
                raise result
            return result
        if argv[1] == "members":
            return subprocess.CompletedProcess(argv, 0, self.rosters[argv[3]], "")
        if argv[1:] == ["teams", "--json"]:
            return subprocess.CompletedProcess(argv, 0, json.dumps({"teams": [{"name": t, "member_count": 0} for t in self.rosters]}), "")
        if argv[1:3] == ["teams", "add-member"]:
            return subprocess.CompletedProcess(argv, self.add_rc, "", "" if self.add_rc == 0 else "refused")
        raise AssertionError(f"unexpected atm call {argv}")


MEMBERS = lambda team: ["atm", "members", "--team", team, "--json"]
TEAMS = ["atm", "teams", "--json"]


def test_dev_sanity_member_missing_is_added_under_its_member_name(tmp_path, monkeypatch):
    _atm_toml(tmp_path)
    fake = FakeAtm({"my-team": _roster("my-lead"), "other": _roster("other-sanity")})
    monkeypatch.setattr(subprocess, "run", fake)
    result = install.provision_dev_sanity_member(tmp_path, "my-sanity")
    assert (result.added, result.notice, result.host_name) == (True, None, "my-sanity")
    assert fake.calls == [MEMBERS("my-team"), TEAMS, MEMBERS("other"), _add_sanity(tmp_path)]


def test_dev_sanity_member_is_added_with_the_pane_alias(tmp_path, monkeypatch):
    _atm_toml(tmp_path, alias="myr-sanity")
    fake = FakeAtm({"my-team": _roster("my-lead"), "other": _roster("my-sanity")})   # same member name elsewhere is fine
    monkeypatch.setattr(subprocess, "run", fake)
    result = install.provision_dev_sanity_member(tmp_path, "my-sanity")
    assert (result.added, result.notice, result.host_name) == (True, None, "myr-sanity")
    assert fake.calls[-1] == _add_sanity(tmp_path, "myr-sanity")


def test_dev_sanity_member_present_in_our_team_is_not_added(tmp_path, monkeypatch):
    _atm_toml(tmp_path)
    fake = FakeAtm({"my-team": _roster("my-lead", "my-sanity"), "other": _roster("my-sanity")})
    monkeypatch.setattr(subprocess, "run", fake)
    result = install.provision_dev_sanity_member(tmp_path, "my-sanity")
    assert (result.added, result.notice) == (False, None)
    assert fake.calls == [MEMBERS("my-team")]


@pytest.mark.parametrize("alias, other_roster, holder", [
    (None, _roster("my-sanity"), "my-sanity@other"),                     # member name is another member's name
    (None, _roster(("x", "my-sanity")), "x@other"),                       # member name is another member's alias
    ("myr-sanity", _roster(("y", "myr-sanity")), "y@other"),              # pane alias is another member's alias
    ("myr-sanity", _roster("myr-sanity"), "myr-sanity@other"),            # pane alias is another member's name
])
def test_dev_sanity_host_name_taken_in_another_team_is_not_added(tmp_path, monkeypatch, alias, other_roster, holder):
    repo = tmp_path / "raptor"
    repo.mkdir()
    _atm_toml(repo, alias=alias)
    fake = FakeAtm({"my-team": _roster("my-lead"), "other": other_roster})
    monkeypatch.setattr(subprocess, "run", fake)
    result = install.provision_dev_sanity_member(repo, "my-sanity")
    notice = result.notice
    assert not result.added and result.suggest_alias == "rap-sanity" and notice is not None
    assert all(call[1:3] != ["teams", "add-member"] for call in fake.calls)
    assert f"{alias or 'my-sanity'} is taken by {holder} on this host" in notice
    assert "such as rap-sanity, either as roles.dev-sanity in .claude/agents/registry.yaml" in notice
    assert "herdr agent rename <pane> rap-sanity, then rerun the install" in notice


@pytest.mark.parametrize("name, expected", [("raptor", "rap-sanity"), ("atm-core", "atm-sanity"),
                                            ("Atm_BD.orchestration", "atm-sanity"), ("ab", "ab-sanity")])
def test_suggested_alias_is_the_repo_name_prefix(tmp_path, name, expected):
    assert install.suggested_alias(tmp_path / name) == expected


def test_suggested_alias_skips_host_names_in_use(tmp_path):
    assert install.suggested_alias(tmp_path / "raptor", {"rap-sanity", "rap-sanity2"}) == "rap-sanity3"


def test_dev_sanity_suggestion_is_never_the_taken_name(tmp_path, monkeypatch):
    repo = tmp_path / "raptor"
    repo.mkdir()
    _atm_toml(repo, alias="rap-sanity")
    monkeypatch.setattr(subprocess, "run", FakeAtm({"my-team": _roster("my-lead"), "raptor": _roster(("dev-sanity", "rap-sanity"))}))
    result = install.provision_dev_sanity_member(repo, "my-sanity")
    notice = result.notice
    assert notice is not None and "rap-sanity is taken by dev-sanity@raptor on this host" in notice
    assert result.suggest_alias == "rap-sanity2" and "such as rap-sanity2," in notice


@pytest.mark.parametrize("fail, reason", [
    ({"atm members --team my-team --json": subprocess.CompletedProcess([], 1, "", "daemon unreachable")},
     "not checked: atm members --team my-team --json failed (daemon unreachable)"),
    ({"atm members --team my-team --json": subprocess.CompletedProcess([], 0, "atm 1.6.6", "")},
     "not checked: atm members --team my-team --json printed no JSON"),
    ({"atm teams --json": subprocess.CompletedProcess([], 1, "", "no teams")},
     "not checked for host name my-sanity on this host: atm teams --json failed (no teams)"),
    ({"atm members --team other --json": subprocess.CompletedProcess([], 1, "", "locked")},
     "not checked for host name my-sanity in team other: atm members --team other --json failed (locked)"),
    ({"atm members --team my-team --json": OSError("No such file or directory: 'atm'")},
     "not checked: atm members --team my-team --json: No such file or directory: 'atm'"),
])
def test_dev_sanity_read_failure_names_the_command_and_adds_nothing(tmp_path, monkeypatch, fail, reason):
    _atm_toml(tmp_path)
    fake = FakeAtm({"my-team": _roster("my-lead"), "other": _roster()}, fail=fail)
    monkeypatch.setattr(subprocess, "run", fake)
    result = install.provision_dev_sanity_member(tmp_path, "my-sanity")
    notice = result.notice
    assert not result.added and notice is not None and reason in notice
    assert notice.endswith(" ".join(_add_sanity(tmp_path)))
    assert all(call[1:3] != ["teams", "add-member"] for call in fake.calls)


def test_dev_sanity_refused_add_names_the_command(tmp_path, monkeypatch):
    _atm_toml(tmp_path)
    monkeypatch.setattr(subprocess, "run", FakeAtm({"my-team": _roster()}, add_rc=4))
    result = install.provision_dev_sanity_member(tmp_path, "my-sanity")
    assert not result.added
    assert result.notice == f"dev-sanity member my-sanity not added: refused; run: {' '.join(_add_sanity(tmp_path))}"


def test_dev_sanity_member_without_a_team_names_atm_toml_and_runs_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *_a, **_k: pytest.fail("no atm call without a team"))
    result = install.provision_dev_sanity_member(tmp_path, "my-sanity")
    assert result.notice == (f"dev-sanity member my-sanity not added: no [atm] default_team in {tmp_path / '.atm.toml'}; "
                             f"set it, then run: atm teams add-member <team> my-sanity --agent-type claude-code "
                             f"--model sonnet --home-dir {tmp_path} --backend herdr")


STARTUP_BLOCK = [
    "[startup.my-sanity]",
    'all = ["Your role is dev-sanity under atm-bd-orchestration: read .claude/agents/dev-sanity.md now (again after '
    'every compaction) and run its Startup section",',
    '       "Use native atm send or atm ack for messages to my-lead",',
    '       "Use native atm read to read messages from team-members" ]',
]


def _report_plan(repo: Path, **kw) -> install.Plan:
    plan = install.Plan(repo_root=repo, target_prefix=".claude/", dev_sanity_member="my-sanity", **kw)
    return plan


def test_change_report_lists_each_change_and_recommends_the_startup_block(tmp_path):
    _atm_toml(tmp_path)
    plan = _report_plan(tmp_path, removals=[".claude/old.md"], backups=[".claude/x.md"], registry_text="roles: {}\n")
    plan.written = [".claude/agents/dev-sanity.md", install.CONFIG_OUT]
    plan.members_added = ["atm-bd@tool", "my-sanity@my-team (host name my-sanity)"]
    plan.sanity = install.SanityMember(added=True, host_name="my-sanity")
    config = {"dev_sanity_member": "my-sanity", "qa_member": "quality-mgr", "team_lead_member": "my-lead"}
    assert install.change_report(plan, config) == [
        "Changes:",
        "  written: .claude/agents/dev-sanity.md",
        f"  written: {install.CONFIG_OUT}",
        "  removed: .claude/old.md",
        "  backed up to .backup/: .claude/x.md",
        "  roles set in .claude/agents/registry.yaml: dev-sanity: my-sanity, quality-mgr: quality-mgr, lead: my-lead",
        "  member added: atm-bd@tool",
        "  member added: my-sanity@my-team (host name my-sanity)",
        "  then: name the dev-sanity herdr agent my-sanity or nudges will not reach it: herdr agent rename <pane> my-sanity",
        "Recommended addition to .atm.toml (not written):",
        *STARTUP_BLOCK,
    ]
    assert install.tomllib.loads("\n".join(STARTUP_BLOCK))["startup"]["my-sanity"]["all"][1].endswith("to my-lead")


def test_change_report_omits_an_existing_startup_block_and_recommends_a_free_alias(tmp_path):
    _atm_toml(tmp_path, startup=True)
    plan = _report_plan(tmp_path)
    assert install.change_report(plan, {"team_lead_member": "my-lead"}) == ["Changes:", "  none"]
    plan.sanity = install.SanityMember(notice="taken", suggest_alias="tmp-sanity")
    assert install.change_report(plan, {"team_lead_member": "my-lead"}) == [
        "Changes:", "  none", "Recommended addition to .atm.toml (not written):",
        "[[rmux.windows.panes]]", 'name = "my-sanity"', 'alias = "tmp-sanity"']


def test_change_report_without_a_known_lead_says_lead(tmp_path):
    plan = _report_plan(tmp_path)   # no .atm.toml at all
    assert "messages to <lead>" in "\n".join(install.change_report(plan, {}))


def _intercept_atm(monkeypatch, fake: FakeAtm) -> FakeAtm:
    """Answer only atm roster calls; tool checks, sc-compose and git still run for real."""
    real = subprocess.run

    def run(argv, *args, **kwargs):
        if argv[:1] == ["atm"] and argv[1] in ("members", "teams"):
            return fake(argv, **kwargs)
        return real(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(install, "provision_tool_identity", lambda _root: True)
    return fake


@needs_sc_compose
def test_install_adds_the_missing_dev_sanity_member_and_lists_the_changes(tmp_path, monkeypatch, capsys):
    repo = make_repo(tmp_path)
    _atm_toml(repo)
    before = (repo / ".atm.toml").read_bytes()
    fake = _intercept_atm(monkeypatch, FakeAtm({"my-team": _roster("my-lead")}))
    rc = install.main(["--dest", str(repo / ".claude"), *QA], pkg_dir=PKG)
    out, err = capsys.readouterr()
    assert rc == 0, err
    assert fake.calls == [MEMBERS("my-team"), TEAMS, _add_sanity(repo.resolve())]
    assert (repo / ".atm.toml").read_bytes() == before   # recommended, never written
    lines = out.splitlines()
    assert "  written: .claude/agents/dev-sanity.md" in lines and f"  written: {install.CONFIG_OUT}" in lines
    assert "  roles set in .claude/agents/registry.yaml: dev-sanity: my-sanity, quality-mgr: quality-mgr, lead: my-lead" in lines
    assert "  member added: atm-bd@tool" in lines and "  member added: my-sanity@my-team (host name my-sanity)" in lines
    at = lines.index("Recommended addition to .atm.toml (not written):")
    assert lines[at + 1:at + 5] == STARTUP_BLOCK
    assert any(re.match(r"atm-bd-orchestration \S+: \d+ file\(s\) written", line) for line in lines)   # the count line stays


@needs_sc_compose
def test_install_reports_an_unadded_dev_sanity_member_and_succeeds(tmp_path, monkeypatch, capsys):
    repo = make_repo(tmp_path)
    _atm_toml(repo, startup=True)
    _intercept_atm(monkeypatch, FakeAtm({"my-team": _roster()}, add_rc=2))
    rc = install.main(["--dest", str(repo / ".claude"), *QA], pkg_dir=PKG)
    out, err = capsys.readouterr()
    assert rc == 0, err
    command = " ".join(_add_sanity(repo.resolve()))
    assert f"warning: dev-sanity member my-sanity not added: refused; run: {command}" in err
    assert f"NOT DONE: dev-sanity member my-sanity not added: refused; run: {command}" in out
    assert "Recommended addition" not in out and "member added: my-sanity" not in out


@needs_sc_compose
def test_codex_install_does_not_touch_the_dev_sanity_member(tmp_path, monkeypatch, capsys):
    repo = make_repo(tmp_path)
    _atm_toml(repo)
    fake = _intercept_atm(monkeypatch, FakeAtm({"my-team": _roster()}))
    rc, err = run(repo, *QA, target=".codex", capsys=capsys)
    assert rc == 0, err
    assert fake.calls == []


# ---------------------------------------------------------------- consistency


def test_generated_blocks_are_current():
    assert gen_manifest.main(["--check"]) == 0


def test_bead_queues_delegates_to_the_atm_bd_subcommand():
    source = (PKG / "skills/atm-bd-orchestration/scripts/bead-queues").read_text()
    assert source.splitlines() == ["#!/bin/sh", 'exec atm-bd queues "$@"']


def test_manifest_lists_every_skill_and_agent_file():
    assert install.load_manifest_artifacts(PKG) == gen_manifest.tree_artifacts()


def test_render_list_covers_exactly_the_placeholder_files():
    renders = install.load_registry(PKG)["render"]
    assert renders == gen_manifest.render_list(install.load_manifest_artifacts(PKG))
    assert not [r for r in renders if r.endswith(".j2")], "dispatch templates are never rendered at install"
    for rel in renders:
        assert install.PLACEHOLDER_RE.search((PKG / rel).read_text()), rel


def test_no_repo_or_team_specific_strings_in_sources():
    hits = []
    for cat in ("skills", "agents", "config"):
        for path in (PKG / cat).rglob("*"):
            if not path.is_file() or {"node_modules", "__pycache__", ".sc-compose"} & set(path.parts):  # .sc-compose/: gitignored render logs
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for needle in REPO_STRINGS:
                if needle in text:
                    hits.append(f"{path.relative_to(PKG)}: {needle}")
    assert hits == [], "\n".join(hits)


def test_workflow_issue_bead_declares_parent():
    text = (PKG / "skills/atm-bd-orchestration/templates/workflow-issue-bead.json.j2").read_text()
    assert "  - parent\n" in text and "{{ parent | tojson }}" in text


def test_config_template_declares_exactly_the_spec_variables_and_sanity_default():
    assert install.config_variables(PKG) == SPEC_VARIABLES
    front = yaml.safe_load((PKG / install.CONFIG_TEMPLATE).read_text().split("---\n")[1])
    assert front["defaults"] == {"max_sanity_rounds": 5, "gate_timeout_s": 180}
    assert set(install.ROLE_KEYS) | install.LIST_VARIABLES <= set(SPEC_VARIABLES)


def test_versions_agree():
    version = install.package_version(PKG)
    assert version == "0.19.12"
    assert json.loads((PKG / ".claude-plugin/plugin.json").read_text())["version"] == version
    assert f"## [{version}]" in (PKG / "CHANGELOG.md").read_text()



def shim_sc_compose(bin_dir: Path, cli: str, wheel: str, python_version: str = "3.11.0") -> None:
    """`sc-compose --version` prints `sc-compose <cli>`; `uv run --script ...` prints the wheel version <wheel>;
    `python3` on PATH reports <python_version> and is never consulted."""
    bin_dir.mkdir(exist_ok=True)
    for name, out in (("sc-compose", f"sc-compose {cli}"),
                      ("atm-bd", f"atm-bd {install.manifest_requirement_floor('atm-bd')}"),
                      ("atm", f"atm {install.manifest_requirement_floor('atm')}"), ("bd", "bd 1.3.0"),
                      ("jq", "jq-1.6"), ("git", "git version 2.27.0")):
        (bin_dir / name).write_text(f"#!/bin/sh\necho '{out}'\n")
        (bin_dir / name).chmod(0o755)
    (bin_dir / "python3").write_text(f"#!/bin/sh\necho 'Python {python_version}'\n")
    (bin_dir / "python3").chmod(0o755)
    (bin_dir / "uv").write_text(
        f"#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo 'uv 0.12.5'; else echo '{wheel}'; fi\n"
    )
    (bin_dir / "uv").chmod(0o755)


@pytest.mark.parametrize("cli, wheel, refusal", [
    ("1.7.0", "1.7.0", None),
    ("1.7.1", "1.7.1", None),
    ("1.12.0", "1.12.0", None),
    ("1.6.1", "1.6.1", "sc-compose CLI is sc-compose 1.6.1, the package needs >= 1.7.0, < 2"),
    ("2.0.0", "2.0.0", "sc-compose CLI is sc-compose 2.0.0, the package needs >= 1.7.0, < 2"),
    ("1.7.0", "1.6.1", "the script runtime has the sc-compose wheel 1.6.1, the package needs >= 1.7.0, < 2"),
    ("1.7.1", "1.7.0", "the sc-compose CLI is 1.7.1 and the script runtime's wheel is 1.7.0; they must be the same version"),
])
def test_check_tools_accepts_one_sc_compose_version_in_the_range(tmp_path, monkeypatch, cli, wheel, refusal):
    import importlib.metadata
    monkeypatch.setattr(importlib.metadata, "version", lambda _: wheel)
    shim_sc_compose(tmp_path / "bin", cli, wheel)
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))
    if refusal is None:
        install.check_tools()
        return
    with pytest.raises(install.InstallError) as caught:
        install.check_tools()
    assert refusal in str(caught.value)
    assert "brew upgrade randlee/tap/sc-compose" in str(caught.value)


def test_install_refuses_installer_interpreter_mismatch_before_writes(tmp_path, monkeypatch):
    import importlib.metadata
    bin_dir = tmp_path / "bin"
    shim_sc_compose(bin_dir, "1.7.0", "1.7.0")
    monkeypatch.setenv("PATH", str(bin_dir))
    monkeypatch.setattr(importlib.metadata, "version", lambda _: "1.7.1")
    destination = tmp_path / "repo" / ".claude"
    result = install.prepare(str(PKG), str(destination), {})
    assert not destination.exists()
    assert "installer interpreter wheel is 1.7.1" in str(result)
    assert "upgrade the app or host" in str(result)


@pytest.mark.parametrize(("tool", "reported", "expected"), [
    ("atm-bd", None, "uv tool install"),
    ("atm-bd", "atm-bd 0.0.9", "older than required 0.1.0"),
])
def test_check_tools_requires_current_console(tmp_path, monkeypatch, tool, reported, expected):
    bin_dir = tmp_path / "bin"
    shim_sc_compose(bin_dir, "1.7.0", "1.7.0")
    path = bin_dir / tool
    if reported is None:
        path.unlink()
    else:
        path.write_text(f"#!/bin/sh\necho '{reported}'\n")
        path.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(install.InstallError, match=expected):
        install.check_tools()


@pytest.mark.parametrize(("tool", "expected"), [
    ("jq", "jq is not on PATH; install it with: brew install jq"),
    ("bd", "bd is not on PATH; install it with: brew install beads"),
])
def test_prepare_refuses_missing_declared_tool_before_writing(tmp_path, monkeypatch, tool, expected):
    repo = make_repo(tmp_path)
    bin_dir = tmp_path / "bin"
    shim_sc_compose(bin_dir, "1.7.0", "1.7.0")
    (bin_dir / tool).unlink()
    monkeypatch.setenv("PATH", str(bin_dir))

    result = install.prepare(str(PKG), str(repo / ".claude"), {"args": {"qa_member": "quality-mgr"}})

    assert result == {"result": "fail", "message": expected}
    assert not (repo / install.LOCK_OUT).exists()


def test_check_tools_refuses_a_declared_tool_below_its_manifest_floor(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    shim_sc_compose(bin_dir, "1.7.0", "1.7.0")
    (bin_dir / "git").write_text("#!/bin/sh\necho 'git version 2.26.0'\n")
    (bin_dir / "git").chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(install.InstallError, match=r"git is 2\.26\.0, older than required 2\.27"):
        install.check_tools()


def test_check_tools_refuses_an_atm_without_hook_and_cron(tmp_path, monkeypatch):
    # atm prerelease 1.6.3 is the first with `atm hook` and `atm cron`, which the phase setup and the sanity
    # close hook run; 1.6.2 has neither.
    bin_dir = tmp_path / "bin"
    shim_sc_compose(bin_dir, "1.7.0", "1.7.0")
    (bin_dir / "atm").write_text("#!/bin/sh\necho 'atm 1.6.2'\n")
    (bin_dir / "atm").chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(install.InstallError, match=r"atm is 1\.6\.2, older than required 1\.6\.3"):
        install.check_tools()


def test_check_tools_ignores_the_python3_on_path(tmp_path, monkeypatch):
    import importlib.metadata
    monkeypatch.setattr(importlib.metadata, "version", lambda _: "1.7.0")
    bin_dir = tmp_path / "bin"
    shim_sc_compose(bin_dir, "1.7.0", "1.7.0", python_version="3.14.7")
    monkeypatch.setenv("PATH", str(bin_dir))

    install.check_tools()


def test_check_tools_requires_uv_for_the_script_runtime(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    shim_sc_compose(bin_dir, "1.7.0", "1.7.0")
    (bin_dir / "uv").unlink()
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(install.InstallError, match=r"uv is not on PATH; install it with: brew install uv"):
        install.check_tools()


def test_check_tools_reports_a_script_runtime_that_cannot_resolve(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    shim_sc_compose(bin_dir, "1.7.0", "1.7.0")
    (bin_dir / "uv").write_text("#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo 'uv 0.12.5'; else "
                                "echo 'error: No interpreter found for Python >=3.11, <3.12' >&2; exit 2; fi\n")
    monkeypatch.setenv("PATH", str(bin_dir))

    with pytest.raises(install.InstallError, match=r"SCRIPT_RUNTIME: .*No interpreter found for Python >=3\.11.*uv python install 3\.11"):
        install.check_tools()


def test_the_manifest_requires_sc_compose_from_1_7_0_below_2():
    assert install.sc_compose_range() == ("1.7.0", 2)


def test_manifest_declares_every_installer_verified_cli():
    assert install.declared_tool_requirements() == [
        ("uv", "0.4"),
        ("atm", "1.6.3"),
        ("bd", "1.3.0"),
        ("jq", "1.6"),
        ("git", "2.27"),
        ("atm-bd", "0.1.0"),
    ]


def test_manifest_rejects_requirements_without_a_verifier(monkeypatch):
    manifest = install.load_manifest()
    monkeypatch.setattr(install, "load_manifest", lambda _pkg_dir=install.PKG_DIR: {
        **manifest,
        "requires": [*manifest["requires"], "unverified-tool >= 1.0"],
    })

    with pytest.raises(install.InstallError, match=r"unrecognized requirement 'unverified-tool'"):
        install.declared_tool_requirements()


VERSIONED_SKILLS = sorted(p for p in PKG.glob("skills/*/SKILL.md")
                          if "version" in yaml.safe_load(p.read_text().split("---\n", 2)[1]))


def test_some_skills_carry_a_version_marker():
    assert len(VERSIONED_SKILLS) >= 2, VERSIONED_SKILLS


@pytest.mark.parametrize("skill", VERSIONED_SKILLS, ids=lambda p: p.parent.name)
def test_a_skill_version_marker_is_the_package_version(skill):
    """Drift audits read SKILL.md `version:`; it must be the version plugin.json ships."""
    front = yaml.safe_load(skill.read_text().split("---\n", 2)[1])
    assert str(front["version"]) == json.loads((PKG / ".claude-plugin/plugin.json").read_text())["version"]


def test_legacy_owned_table_is_frozen_at_0_2_3():
    data = json.loads((PKG / install.LEGACY_OWNED).read_text())
    assert data["through"] == "d5b7301"
    files = data["files"]
    assert "skills/atm-beads/scripts/validate-plan" in files and "assets/scripts/jev_client.py" in files
    assert all(shas and all(len(s) == 64 for s in shas) for shas in files.values())


# ---------------------------------------------------------------- fixtures


REGISTRY = """\
# consumer registry: comments and other keys survive the roles write
agents:
  quality-mgr:
    path: .claude/agents/quality-mgr.md
bead_prefix: myp
worktree_base: {worktree_base}
test_command: just test
lint_command: just lint
integration_branch_pattern: integrate/phase-{{phase}}
plans_dir: docs/plans
requirements_globs: [docs/requirements.md, "docs/**/requirements.md"]
adr_globs: ["docs/adr/*.md"]
policy_path: .claude/project/quality-policy.md
reviewers_round1: [req-qa, arch-qa]

roles:
  dev-sanity: my-sanity   # the member running the dev-sanity directive
  lead: my-lead
skills:
  atm-beads:
"""
AGENTS = ("quality-mgr", "req-qa", "arch-qa", "ruthless-boundary-qa", "my-sanity")


def make_repo(tmp_path: Path, *, drop: tuple = (), agents: tuple = AGENTS, dolt_mode: str = "server") -> Path:
    repo = tmp_path / "my-repo"
    (repo / ".claude" / "agents").mkdir(parents=True)
    run_command(["git", "init", "-q", str(repo)], check=True)
    run_command(["git", "-C", str(repo), "remote", "add", "origin", "git@github.com:owner/my-repo.git"], check=True)
    text = REGISTRY.format(worktree_base=repo.resolve().parent / "my-repo-worktrees")
    lines = [line for line in text.splitlines(keepends=True) if not any(line.startswith(f"{d}:") for d in drop)]
    (repo / ".claude/agents/registry.yaml").write_text("".join(lines))
    for name in agents:
        (repo / ".claude/agents" / f"{name}.md").write_text(f"---\nname: {name}\n---\n")
    (repo / ".beads").mkdir()
    (repo / ".beads/metadata.json").write_text(json.dumps({"backend": "dolt", "dolt_mode": dolt_mode}))
    return repo


QA = ["--set", "qa_member=quality-mgr"]


def run(repo: Path, *extra: str, target: str = ".claude", pkg: Path = PKG, capsys=None):
    rc = install.main(["--dest", str(repo / target), *extra], pkg_dir=pkg)
    err = capsys.readouterr().err if capsys else ""
    return rc, err


def snapshot(repo: Path) -> dict:
    return {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(repo).parts}


def lock(repo: Path) -> dict:
    return json.loads((repo / install.LOCK_OUT).read_text())


@pytest.fixture
def pkg_copy(tmp_path):
    dst = tmp_path / "pkg"
    shutil.copytree(PKG, dst, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "node_modules"))
    return dst


def regenerate(pkg: Path) -> None:
    run_command([sys.executable, str(pkg / "tests/gen_manifest.py")], check=True)


# ---------------------------------------------------------------- values (no sc-compose)


def test_unknown_set_key_is_rejected(tmp_path):
    repo = make_repo(tmp_path)
    with pytest.raises(install.InstallError, match=r"unknown --set variable\(s\): bogus, team"):
        install.resolve_config(repo, {"bogus": "1", "team": "x", "test_command": "make"})


def test_set_wins_and_lists_parse(tmp_path):
    repo = make_repo(tmp_path)
    vals = install.resolve_config(repo, {"test_command": "make test", "reviewers_round1": "a, b",
                                         "adr_globs": '["x/*.md"]'})
    assert vals["test_command"] == "make test" and "lead" not in vals
    assert vals["reviewers_round1"] == ["a", "b"] and vals["adr_globs"] == ["x/*.md"]
    assert vals["dev_sanity_member"] == "my-sanity" and "qa_member" not in vals


def test_max_sanity_rounds_installer_defaults_and_registry_override(tmp_path):
    repo = make_repo(tmp_path)
    assert install.resolve_config(repo, {})["max_sanity_rounds"] == 5
    registry = repo / install.CONSUMER_REGISTRY
    registry.write_text(registry.read_text() + "max_sanity_rounds: 2\n")
    assert install.resolve_config(repo, {})["max_sanity_rounds"] == 2
    assert install.resolve_config(repo, {"max_sanity_rounds": "3"})["max_sanity_rounds"] == 3


@pytest.mark.parametrize("value, expected", [(1, 1), (7, 7), ("2", 2), ("005", 5)])
def test_max_sanity_rounds_installer_accepts_positive_integer_overrides(tmp_path, value, expected):
    resolved = install.resolve_config(make_repo(tmp_path), {"max_sanity_rounds": value})
    assert resolved["max_sanity_rounds"] == expected
    assert type(resolved["max_sanity_rounds"]) is int


@pytest.mark.parametrize("value", [0, -1, True, False, None, 1.5, "", "0", "-1", "2.5", "two", [], {}])
@pytest.mark.parametrize("source", ["registry", "override"])
def test_max_sanity_rounds_installer_rejects_invalid_values(tmp_path, value, source):
    repo = make_repo(tmp_path)
    overrides = {"max_sanity_rounds": value}
    if source == "registry":
        registry = repo / install.CONSUMER_REGISTRY
        registry.write_text(registry.read_text() + yaml.safe_dump(overrides))
        overrides = {}
    with pytest.raises(install.InstallError, match="max_sanity_rounds must be a positive integer"):
        install.resolve_config(repo, overrides)


@pytest.fixture
def runtime_repo_config():
    path = PKG / "skills/atm-beads/scripts/repo_config.py"
    spec = importlib.util.spec_from_file_location("installer_test_repo_config", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("values, expected", [({}, 5), ({"max_sanity_rounds": 2}, 2)])
def test_max_sanity_rounds_runtime_exposes_default_and_override(tmp_path, runtime_repo_config, values, expected):
    path = tmp_path / runtime_repo_config.RELATIVE_PATH
    path.parent.mkdir(parents=True)
    original = yaml.safe_dump({"bead_prefix": "consumer", **values})
    path.write_text(original)
    config = runtime_repo_config.load(tmp_path)
    assert config["max_sanity_rounds"] == expected
    assert config["bead_prefix"] == "consumer"
    assert path.read_text() == original


@needs_sc_compose
@pytest.mark.parametrize("overrides, expected", [({}, 5), ({"max_sanity_rounds": "2"}, 2)])
def test_max_sanity_rounds_rendered_config_loads_as_integer(tmp_path, runtime_repo_config, overrides, expected):
    repo = make_repo(tmp_path)
    values = install.resolve_config(repo, {"qa_member": "quality-mgr", **overrides})
    path = repo / runtime_repo_config.RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_bytes(install.render_config(values))
    config = runtime_repo_config.load(repo)
    assert config["max_sanity_rounds"] == expected
    assert type(config["max_sanity_rounds"]) is int


@needs_sc_compose
@pytest.mark.parametrize("registry_value, expected", [(None, 5), (2, 2)])
def test_install_carries_registry_max_sanity_rounds_into_consumer_config(tmp_path, capsys, registry_value, expected):
    repo = make_repo(tmp_path)
    if registry_value is not None:
        registry = repo / install.CONSUMER_REGISTRY
        registry.write_text(registry.read_text() + f"max_sanity_rounds: {registry_value}\n")
    rc, err = run(repo, *QA, capsys=capsys)
    assert rc == 0, err
    installed = yaml.safe_load((repo / install.CONFIG_OUT).read_text())
    assert installed["max_sanity_rounds"] == expected
    assert type(installed["max_sanity_rounds"]) is int


@pytest.mark.parametrize("value", [0, -1, True, False, None, 1.5, "2", "", [], {}])
def test_max_sanity_rounds_runtime_rejects_invalid_values(tmp_path, runtime_repo_config, value):
    path = tmp_path / runtime_repo_config.RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump({"max_sanity_rounds": value}))
    with pytest.raises(runtime_repo_config.ConfigError, match="max_sanity_rounds must be a positive integer") as caught:
        runtime_repo_config.load(tmp_path)
    assert str(path) in str(caught.value)


def test_gate_timeout_s_installer_default_registry_override_and_validation(tmp_path):
    repo = make_repo(tmp_path)
    assert install.resolve_config(repo, {})["gate_timeout_s"] == 180
    assert install.resolve_config(repo, {"gate_timeout_s": "600"})["gate_timeout_s"] == 600
    for bad in (0, -1, True, "x", 1.5):
        with pytest.raises(install.InstallError, match="gate_timeout_s must be a positive integer"):
            install.resolve_config(repo, {"gate_timeout_s": bad})


@pytest.mark.parametrize("value", [0, -1, True, None, 1.5, "2", []])
def test_gate_timeout_s_runtime_rejects_invalid_values(tmp_path, runtime_repo_config, value):
    path = tmp_path / runtime_repo_config.RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump({"gate_timeout_s": value}))
    with pytest.raises(runtime_repo_config.ConfigError, match="gate_timeout_s must be a positive integer"):
        runtime_repo_config.load(tmp_path)


@pytest.mark.parametrize("removed", ["reviewers_fix_round", "reviewers_scope_locked"])
def test_removed_reviewer_lists_are_ignored_in_registry_and_rejected_by_set(tmp_path, removed):
    """0.5.0 dropped reviewers_fix_round and reviewers_scope_locked: a leftover registry key is not read; --set names it unknown."""
    repo = make_repo(tmp_path)
    reg = repo / ".claude/agents/registry.yaml"
    reg.write_text(reg.read_text() + f"{removed}: [req-qa]\n")
    assert removed not in install.resolve_config(repo, {})
    with pytest.raises(install.InstallError, match=f"unknown --set variable\\(s\\): {removed}"):
        install.resolve_config(repo, {removed: "req-qa"})


def test_wrong_type_and_misplaced_role_are_named(tmp_path):
    repo = make_repo(tmp_path)
    reg = repo / ".claude/agents/registry.yaml"
    reg.write_text(reg.read_text().replace("reviewers_round1: [req-qa, arch-qa]", "reviewers_round1: req-qa"))
    with pytest.raises(install.InstallError, match="reviewers_round1 must be a list"):
        install.resolve_config(repo, {})
    reg.write_text(reg.read_text() + "dev_sanity_member: x\n")
    with pytest.raises(install.InstallError, match="dev_sanity_member belongs under roles.dev-sanity"):
        install.resolve_config(repo, {})


def test_phase_lead_is_not_an_installer_input(tmp_path):
    repo = make_repo(tmp_path)
    reg = repo / ".claude/agents/registry.yaml"
    before = reg.read_text()
    assert "lead" not in install.resolve_config(repo, {})
    with pytest.raises(install.InstallError, match=r"unknown --set variable\(s\): lead"):
        install.resolve_config(repo, {"lead": "phase-lead"})
    reg.write_text(before.replace("  lead: my-lead\n", ""))
    assert "lead" not in install.resolve_config(repo, {})


def test_write_roles_updates_in_place_and_keeps_comments(tmp_path):
    reg = tmp_path / "registry.yaml"
    reg.write_text("# top\nroles:\n    lead: old   # keep me\n    dev-sanity: s\n\nskills:\n  a:\n")
    assert install.write_roles(reg, {"lead": "new", "dev-sanity": "s", "quality-mgr": "q"})
    assert reg.read_text() == "# top\nroles:\n    lead: new   # keep me\n    dev-sanity: s\n    quality-mgr: q\n\nskills:\n  a:\n"
    assert not install.write_roles(reg, {"lead": "new", "dev-sanity": "s", "quality-mgr": "q"})
    fresh = tmp_path / "none.yaml"
    fresh.write_text("bead_prefix: x")
    install.write_roles(fresh, {"lead": "l"})
    assert yaml.safe_load(fresh.read_text()) == {"bead_prefix": "x", "roles": {"lead": "l"}}


def test_dest_must_be_a_claude_or_codex_dir(tmp_path):
    with pytest.raises(install.InstallError, match="--dest must be"):
        install.repo_root_for(tmp_path / "somewhere")


# ---------------------------------------------------------------- fresh install


@needs_sc_compose
def test_fresh_install(tmp_path, capsys):
    repo = make_repo(tmp_path)
    rc, err = run(repo, *QA, capsys=capsys)
    assert rc == 0, err
    dest = repo / ".claude"
    artifacts = install.load_manifest_artifacts(PKG)
    for rel in artifacts["skills"] + artifacts["agents"]:
        assert (dest / rel).is_file(), rel
        assert not install.PLACEHOLDER_RE.search((dest / rel).read_text(errors="ignore")), rel
    # the config file: every declared variable, from registry.yaml and --set
    config = yaml.safe_load((repo / install.CONFIG_OUT).read_text())
    assert list(config) == [*SPEC_VARIABLES, "max_sanity_rounds", "gate_timeout_s"]
    assert config["gate_timeout_s"] == 180
    assert config["max_sanity_rounds"] == 5
    assert config["qa_member"] == "quality-mgr" and config["team_lead_member"] == "my-lead" and "lead" not in config
    assert config["integration_branch_pattern"] == "integrate/phase-{phase}"
    assert config["requirements_globs"] == ["docs/requirements.md", "docs/**/requirements.md"]
    assert config["reviewers_round1"] == ["req-qa", "arch-qa"]
    # the install record: version and the sha256 of every file written
    record = lock(repo)
    assert record["package"] == "atm-bd-orchestration" and record["version"] == "0.19.12"
    expected = {f".claude/{rel}" for rel in artifacts["skills"] + artifacts["agents"]} | {install.CONFIG_OUT}
    assert set(record["files"]) == expected
    assert all(sha((repo / k).read_bytes()) == v for k, v in record["files"].items())
    # roles written, the rest of registry.yaml kept
    reg_text = (repo / ".claude/agents/registry.yaml").read_text()
    reg = yaml.safe_load(reg_text)
    assert reg["roles"] == {"dev-sanity": "my-sanity", "lead": "my-lead", "quality-mgr": "quality-mgr"}
    assert "# the member running the dev-sanity directive" in reg_text and "skills" in reg
    # rendered values, the Jev transport, executable scripts, byte-identical templates
    role = (dest / "agents/dev-sanity.md").read_text()
    assert role.startswith("---\nname: dev-sanity\n")
    assert "| Setting | Where | my-repo |" in role and "`my-sanity`" in role
    send_commands = re.findall(r"\batm\s+send\b[^`]*", role)
    assert not any("rebase-required.xml.j2" in command for command in send_commands)
    assert "sanity-stack-link notifies the lead" in role
    assert all(not re.search(r"(?<!\S)--task-id(?:=|\s|$)", command) for command in send_commands)
    example = (dest / "skills/atm-bd-orchestration/examples/dev-sanity-template-vars.json").read_text()
    assert "https://github.com/owner/my-repo/pull/" in example and str(repo.resolve().parent / "my-repo-worktrees") in example
    assert '"parent": "myp-workflow-issues"' in (dest / "skills/atm-bd-orchestration/examples/workflow-issue-bead-vars.json").read_text()
    assert (dest / "skills/atm-bd-orchestration/scripts/jev_client.py").read_bytes() == \
        (PKG / "skills/atm-bd-orchestration/scripts/jev_client.py").read_bytes()
    assert not (repo / "scripts").exists()
    assert (dest / "skills/atm-beads/scripts/validate-plan").stat().st_mode & 0o111
    assert (dest / "skills/atm-bd-orchestration/templates/qa-template.xml.j2").read_bytes() == \
        (PKG / "skills/atm-bd-orchestration/templates/qa-template.xml.j2").read_bytes()


@needs_sc_compose
def test_install_places_sanity_stack_agent_and_linker(tmp_path, capsys):
    repo = make_repo(tmp_path)
    rc, err = run(repo, *QA, capsys=capsys)
    assert rc == 0, err
    assert (repo / ".claude/agents/sanity-stack.md").is_file()
    assert (repo / ".claude/skills/atm-bd-orchestration/scripts/sanity-stack-link").is_file()


@needs_sc_compose
def test_rerun_is_idempotent(tmp_path, capsys):
    repo = make_repo(tmp_path)
    assert run(repo, *QA)[0] == 0
    before = snapshot(repo)
    assert run(repo)[0] == 0   # qa_member is now in roles.quality-mgr
    assert snapshot(repo) == before


# ---------------------------------------------------------------- refusals (nothing written)


@needs_sc_compose
def test_missing_variable_fails_naming_it(tmp_path, capsys):
    repo = make_repo(tmp_path, drop=("test_command", "adr_globs"))
    before = snapshot(repo)
    rc, err = run(repo, *QA, capsys=capsys)
    assert rc == 1
    assert "missing required variable(s): " in err and "test_command" in err and "adr_globs" in err
    assert ".claude/agents/registry.yaml test_command (or --set test_command=...)" in err
    assert snapshot(repo) == before


@needs_sc_compose
def test_missing_role_variable_names_the_roles_key(tmp_path, capsys):
    repo = make_repo(tmp_path)
    rc, err = run(repo, capsys=capsys)   # no roles.quality-mgr and no --set qa_member
    assert rc == 1 and "qa_member in .claude/agents/registry.yaml roles.quality-mgr" in err


@needs_sc_compose
def test_missing_roles_lead_names_team_lead_member(tmp_path, capsys):
    repo = make_repo(tmp_path)
    registry = repo / ".claude/agents/registry.yaml"
    registry.write_text(registry.read_text().replace("  lead: my-lead\n", ""))
    rc, err = run(repo, *QA, capsys=capsys)
    assert rc == 1 and "team_lead_member in .claude/agents/registry.yaml roles.lead" in err


@needs_sc_compose
def test_unknown_set_fails_the_install(tmp_path, capsys):
    repo = make_repo(tmp_path)
    rc, err = run(repo, *QA, "--set", "bogus_var=1", capsys=capsys)
    assert rc == 1 and "unknown --set variable(s): bogus_var" in err
    assert not (repo / install.LOCK_OUT).exists()


@needs_sc_compose
def test_missing_reviewer_agent_fails(tmp_path, capsys):
    # no agent file for the reviewer arch-qa nor for the dev-sanity member my-sanity:
    # only the reviewer fails
    repo = make_repo(tmp_path, agents=("quality-mgr", "req-qa"))
    rc, err = run(repo, *QA, capsys=capsys)
    assert rc == 1
    assert "no .claude/agents/<name>.md for: arch-qa (reviewers_round1)" in err
    assert "dev_sanity_member" not in err
    assert not (repo / ".claude/skills").exists()


@needs_sc_compose
def test_agent_shipped_by_the_package_counts(tmp_path, capsys):
    repo = make_repo(tmp_path, agents=("quality-mgr", "req-qa", "arch-qa", "ruthless-boundary-qa"))
    rc, err = run(repo, *QA, "--set", "dev_sanity_member=dev-sanity", capsys=capsys)
    assert rc == 0, err


@needs_sc_compose
def test_dev_sanity_member_without_an_agent_file_installs(tmp_path, capsys):
    # roles.dev-sanity names a team member (atm-core: atm-sanity), not an agent file
    repo = make_repo(tmp_path, agents=("quality-mgr", "req-qa", "arch-qa"))
    rc, err = run(repo, *QA, "--set", "dev_sanity_member=atm-sanity", capsys=capsys)
    assert rc == 0, err
    assert not (repo / ".claude/agents/atm-sanity.md").exists()
    assert "atm-sanity" in (repo / install.CONFIG_OUT).read_text()


@needs_sc_compose
@pytest.mark.parametrize("mode", ["embedded", None])
def test_non_server_beads_fails(tmp_path, capsys, mode):
    repo = make_repo(tmp_path, dolt_mode=mode or "server")
    if mode is None:
        (repo / ".beads/metadata.json").unlink()
    rc, err = run(repo, *QA, capsys=capsys)
    assert rc == 1 and "BEADS_NOT_SERVER_MODE" in err
    assert (f"dolt_mode '{mode}', not 'server'" in err) if mode else ("metadata.json not found" in err)
    assert not (repo / ".claude/skills").exists()


@needs_sc_compose
def test_foreign_skill_directory_fails(tmp_path, capsys):
    repo = make_repo(tmp_path)
    own = repo / ".claude/skills/sprint-report"
    own.mkdir(parents=True)
    (own / "SKILL.md").write_text("---\nname: sprint-report\n---\nthe repository's own skill\n")
    (own / "report-detailed.md.j2").write_text("mine\n")
    before = snapshot(repo)
    rc, err = run(repo, *QA, capsys=capsys)
    assert rc == 1
    assert "skill 'sprint-report' exists at .claude/skills/sprint-report and is not owned by atm-bd-orchestration" in err
    assert "sprint-report/SKILL.md" not in err   # one message per foreign directory
    assert snapshot(repo) == before


@needs_sc_compose
def test_foreign_file_at_a_shipped_path_fails(tmp_path, capsys):
    repo = make_repo(tmp_path)
    (repo / ".claude/agents/dev-sanity.md").write_text("the repository's own agent\n")
    rc, err = run(repo, *QA, capsys=capsys)
    assert rc == 1 and ".claude/agents/dev-sanity.md exists and is not owned by atm-bd-orchestration" in err
    assert "rerun with --overwrite" in err
    assert (repo / ".claude/agents/dev-sanity.md").read_text() == "the repository's own agent\n"
    rc, err = run(repo, *QA, "--overwrite", capsys=capsys)
    assert rc == 0, err
    assert "warning: .claude/agents/dev-sanity.md" in err
    [backup] = [p for p in (repo / ".backup").iterdir() if p.name != ".gitignore"]
    assert (backup / ".claude/agents/dev-sanity.md").read_text() == "the repository's own agent\n"
    assert (repo / ".backup/.gitignore").read_text() == "*\n"
    assert lock(repo)["files"][".claude/agents/dev-sanity.md"] == sha((repo / ".claude/agents/dev-sanity.md").read_bytes())


# ---------------------------------------------------------------- re-install / upgrade


@needs_sc_compose
def test_reinstall_updates_unmodified_files_and_rerenders(tmp_path, pkg_copy, capsys):
    repo = make_repo(tmp_path)
    assert run(repo, *QA)[0] == 0
    unrelated = repo / ".claude/skills/atm-beads/notes-of-my-own.md"
    unrelated.write_text("not the package's\n")
    # a new package version changes a copied file and a rendered file
    script = "skills/atm-beads/scripts/resolve-role"
    (pkg_copy / script).write_text((pkg_copy / script).read_text() + "# upgraded\n")
    (pkg_copy / "agents/dev-sanity.md").write_text(
        (pkg_copy / "agents/dev-sanity.md").read_text() + "\nupgraded for {{ dev_sanity_member }}\n")
    # and the repository renames its dev-sanity member
    reg = repo / ".claude/agents/registry.yaml"
    reg.write_text(reg.read_text().replace("dev-sanity: my-sanity", "dev-sanity: quality-mgr"))
    rc, err = run(repo, pkg=pkg_copy, capsys=capsys)
    assert rc == 0, err
    assert (repo / ".claude" / script).read_text().endswith("# upgraded\n")
    assert (repo / ".claude" / script).stat().st_mode & 0o111
    role = (repo / ".claude/agents/dev-sanity.md").read_text()
    assert role.endswith("upgraded for quality-mgr\n") and "`my-sanity`" not in role
    assert yaml.safe_load((repo / install.CONFIG_OUT).read_text())["dev_sanity_member"] == "quality-mgr"
    assert lock(repo)["files"][f".claude/{script}"] == sha((repo / ".claude" / script).read_bytes())
    assert unrelated.read_text() == "not the package's\n"


@needs_sc_compose
def test_reinstall_fails_naming_modified_files_and_changes_nothing(tmp_path, pkg_copy, capsys):
    repo = make_repo(tmp_path)
    assert run(repo, *QA)[0] == 0
    edited = [".claude/skills/atm-beads/SKILL.md", install.CONFIG_OUT]
    for key in edited:
        (repo / key).write_text((repo / key).read_text() + "local edit\n")
    script = "skills/atm-beads/scripts/resolve-role"
    (pkg_copy / script).write_text((pkg_copy / script).read_text() + "# upgraded\n")
    before = snapshot(repo)
    rc, err = run(repo, pkg=pkg_copy, capsys=capsys)
    assert rc == 1
    for key in edited:
        assert f"{key} was modified since atm-bd-orchestration installed it" in err
    assert snapshot(repo) == before   # the unmodified upgrade target was not touched either
    rc, err = run(repo, "--overwrite", pkg=pkg_copy, capsys=capsys)
    assert rc == 0, err
    [backup] = [p for p in (repo / ".backup").iterdir() if p.name != ".gitignore"]
    for key in edited:
        assert (backup / key).read_bytes() == before[key]
        assert not (repo / key).read_text().endswith("local edit\n")
    assert (repo / ".claude" / script).read_text().endswith("# upgraded\n")


@needs_sc_compose
def test_files_no_longer_shipped_are_removed_when_unchanged(tmp_path, pkg_copy, capsys):
    repo = make_repo(tmp_path)
    assert run(repo, *QA)[0] == 0
    gone = ["skills/sprint-review/SKILL.md", "skills/sprint-review/scripts/sprint-review", "agents/sc-sanity-jev.md"]
    for rel in gone:
        (pkg_copy / rel).unlink()
    shutil.rmtree(pkg_copy / "skills/sprint-review")
    regenerate(pkg_copy)
    (repo / ".claude/agents/sc-sanity-jev.md").write_text("edited\n")
    rc, err = run(repo, pkg=pkg_copy, capsys=capsys)
    assert rc == 1 and ".claude/agents/sc-sanity-jev.md was modified" in err and "no longer ships it" in err
    rc, err = run(repo, "--overwrite", pkg=pkg_copy, capsys=capsys)
    assert rc == 0, err
    [backup] = [p for p in (repo / ".backup").iterdir() if p.name != ".gitignore"]
    assert (backup / ".claude/agents/sc-sanity-jev.md").read_text() == "edited\n"
    assert not (repo / ".claude/agents/sc-sanity-jev.md").exists()
    assert ".claude/agents/sc-sanity-jev.md" not in lock(repo)["files"]
    assert not (repo / ".claude/skills/sprint-review").exists()
    assert not any(k.startswith(".claude/skills/sprint-review/") for k in lock(repo)["files"])


@needs_sc_compose
def test_upgrade_removes_the_repo_root_jev_client_0_10_4_placed(tmp_path, capsys):
    # 0.10.4 placed the Jev transport at <repo>/scripts/jev_client.py and recorded it in the lock
    repo = make_repo(tmp_path)
    assert run(repo, *QA)[0] == 0
    old = (PKG / "skills/atm-bd-orchestration/scripts/jev_client.py").read_bytes()
    (repo / "scripts").mkdir()
    (repo / "scripts/jev_client.py").write_bytes(old)
    record = lock(repo)
    record["files"]["scripts/jev_client.py"] = sha(old)
    (repo / install.LOCK_OUT).write_text(json.dumps(record))
    rc, err = run(repo, capsys=capsys)
    assert rc == 0, err
    assert not (repo / "scripts").exists() and "scripts/jev_client.py" not in lock(repo)["files"]
    assert (repo / ".claude/skills/atm-bd-orchestration/scripts/jev_client.py").read_bytes() == old


@needs_sc_compose
def test_upgrade_refuses_a_modified_repo_root_jev_client_and_backs_it_up_with_overwrite(tmp_path, capsys):
    repo = make_repo(tmp_path)
    assert run(repo, *QA)[0] == 0
    old = (PKG / "skills/atm-bd-orchestration/scripts/jev_client.py").read_bytes()
    (repo / "scripts").mkdir()
    (repo / "scripts/jev_client.py").write_bytes(b"edited\n")
    (repo / "scripts/other.sh").write_text("the repository's own script\n")
    record = lock(repo)
    record["files"]["scripts/jev_client.py"] = sha(old)
    (repo / install.LOCK_OUT).write_text(json.dumps(record))
    rc, err = run(repo, capsys=capsys)
    assert rc == 1 and "scripts/jev_client.py was modified" in err and "no longer ships it" in err
    assert (repo / "scripts/jev_client.py").read_bytes() == b"edited\n"
    rc, err = run(repo, "--overwrite", capsys=capsys)
    assert rc == 0, err
    [backup] = [p for p in (repo / ".backup").iterdir() if p.name != ".gitignore"]
    assert (backup / "scripts/jev_client.py").read_bytes() == b"edited\n"
    assert not (repo / "scripts/jev_client.py").exists() and (repo / "scripts/other.sh").is_file()
    assert "scripts/jev_client.py" not in lock(repo)["files"]



@needs_sc_compose
def test_upgrade_from_0_6_removes_the_legacy_sanity_teammates_and_role_sheet(tmp_path, pkg_copy, capsys):
    # 0.6.x shipped dev-sanity-llm/-jev teammates and roles/dev-sanity.md; 0.7.0 folds them into agents/dev-sanity.md
    legacy = ["agents/dev-sanity-llm.md", "agents/dev-sanity-jev.md", "skills/atm-bd-orchestration/roles/dev-sanity.md"]
    for rel in legacy:
        (pkg_copy / rel).write_text(f"0.6.x {rel}\n")
    regenerate(pkg_copy)
    repo = make_repo(tmp_path)
    assert run(repo, *QA, pkg=pkg_copy)[0] == 0
    assert all((repo / ".claude" / rel).is_file() for rel in legacy)
    rc, err = run(repo, capsys=capsys)
    assert rc == 0, err
    assert not any((repo / ".claude" / rel).exists() for rel in legacy)
    assert not any(f".claude/{rel}" in lock(repo)["files"] for rel in legacy)
    assert (repo / ".claude/agents/dev-sanity.md").is_file()

# ---------------------------------------------------------------- migration from 0.x (no lock file)


@needs_sc_compose
def test_migration_owns_shipped_and_legacy_bytes_and_fails_on_others(tmp_path, pkg_copy, capsys):
    repo = make_repo(tmp_path)
    assert run(repo, *QA)[0] == 0
    (repo / install.LOCK_OUT).unlink()          # a 0.x install had no record
    old_script = b"#!/usr/bin/env python3\n# as 0.2.x shipped it\n"
    script = "skills/atm-beads/scripts/resolve-role"
    (repo / ".claude" / script).write_bytes(old_script)
    dropped = "skills/atm-beads/scripts/export-sprint-index"
    (repo / ".claude" / dropped).write_bytes(b"old dropped script\n")
    legacy = json.loads((pkg_copy / install.LEGACY_OWNED).read_text())
    legacy["files"][script] = [sha(old_script)]
    legacy["files"][dropped] = [sha(b"old dropped script\n")]
    (pkg_copy / install.LEGACY_OWNED).write_text(json.dumps(legacy))
    # a file whose bytes no version shipped: not owned
    (repo / ".claude/skills/atm-beads/SKILL.md").write_text("hand edited\n")
    rc, err = run(repo, pkg=pkg_copy, capsys=capsys)
    assert rc == 1
    assert ".claude/skills/atm-beads/SKILL.md exists and is not owned by atm-bd-orchestration" in err
    assert script not in err and not (repo / install.LOCK_OUT).exists()
    (repo / ".claude/skills/atm-beads/SKILL.md").unlink()
    rc, err = run(repo, pkg=pkg_copy, capsys=capsys)
    assert rc == 0, err
    assert (repo / ".claude" / script).read_bytes() == (PKG / script).read_bytes()
    assert not (repo / ".claude" / dropped).exists()
    assert lock(repo)["version"] == "0.19.12"


def _git_has(rev: str) -> bool:
    return run_command(["git", "-C", str(PKG), "cat-file", "-e", f"{rev}^{{commit}}"],
                       stderr=subprocess.PIPE).returncode == 0


@needs_sc_compose
@pytest.mark.skipif(not _git_has("d5b7301"), reason="package history (d5b7301) not in this checkout; fetch-depth 0 needed")
def test_real_upgrade_from_a_0_2_3_install(tmp_path, capsys):
    """Install with the 0.2.3 installer itself, then upgrade with this one."""
    top = run_command(["git", "-C", str(PKG), "rev-parse", "--show-toplevel"], check=True, text=True).stdout.strip()
    archive = run_command(["git", "-C", top, "archive", "d5b7301:plugins/atm-bd-orchestration"],
                          check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as package:
        if hasattr(tarfile, "data_filter"):
            package.extractall(tmp_path / "old", filter="data")
        else:
            package.extractall(tmp_path / "old")
    old_pkg = tmp_path / "old"
    repo = make_repo(tmp_path)
    (repo / ".atm.toml").write_text('[atm]\ndefault_team = "my-team"\n')
    old = run_command([sys.executable, str(old_pkg / "install.py"), "--dest", str(repo / ".claude")],
                      stderr=subprocess.STDOUT, text=True)
    assert old.returncode == 0, old.stdout
    assert not (repo / install.LOCK_OUT).exists()
    # Copied files from 0.2.3 are owned through config/legacy-owned.json. A rendered file
    # is owned only when it equals what this version renders, so a rendered file whose
    # source changed since 0.2.3 is refused by name; deleting it lets the upgrade through.
    # The set is what 0.2.3 rendered, which includes files this version only copies.
    # A rendered file this version no longer ships (roles/dev-sanity.md) is not installed, so not refused.
    renders = set(install.load_registry(old_pkg)["render"])
    changed = sorted(f".claude/{rel}" for rel in renders
                     if (old_pkg / rel).is_file() and (PKG / rel).is_file()
                     and (old_pkg / rel).read_bytes() != (PKG / rel).read_bytes())
    rc, err = run(repo, *QA, capsys=capsys)
    if changed:
        assert rc == 1
        refused = sorted(line.split(" exists and is not owned")[0] for line in err.split("; ") if "is not owned" in line)
        assert sorted(r.replace("install.py: ", "") for r in refused) == changed
        for key in changed:
            (repo / key).unlink()
        rc, err = run(repo, *QA, capsys=capsys)
    assert rc == 0, err
    files = lock(repo)["files"]
    assert ".claude/skills/atm-beads/scripts/validate-plan" in files and "scripts/jev_client.py" not in files
    assert ".claude/skills/atm-bd-orchestration/scripts/jev_client.py" in files and not (repo / "scripts/jev_client.py").exists()
    assert all(sha((repo / k).read_bytes()) == v for k, v in files.items())


# ---------------------------------------------------------------- targets and the sc-install hook


@needs_sc_compose
def test_codex_target_installs_skills_only_and_keeps_the_claude_record(tmp_path, capsys):
    repo = make_repo(tmp_path)
    assert run(repo, *QA)[0] == 0
    claude_keys = {k for k in lock(repo)["files"] if k.startswith(".claude/")}
    rc, err = run(repo, target=".codex", capsys=capsys)
    assert rc == 0, err
    assert not (repo / ".codex/agents").exists() and (repo / ".codex/skills/atm-beads/SKILL.md").is_file()
    files = lock(repo)["files"]
    assert claude_keys <= set(files) and ".codex/skills/atm-beads/SKILL.md" in files


@needs_sc_compose
def test_sc_install_hook_flow_matches_standalone(tmp_path):
    """prepare() -> sc-install's raw copy (skip existing) -> complete() -> cleanup()."""
    hooked = make_repo(tmp_path / "a")
    dest = hooked / ".claude"
    options = {"global": False, "local": True, "user": False, "project": False,
               "codex": False, "force": False, "expand": True, "args": {}}
    failed = install.prepare(str(PKG), str(dest), options)
    assert failed["result"] == "fail" and "qa_member" in failed["message"]
    options["args"] = {"qa_member": "quality-mgr"}
    assert install.prepare(str(PKG), str(dest), options) == {"result": "success"}
    assert not (hooked / install.LOCK_OUT).exists()   # prepare writes nothing
    artifacts = install.load_manifest_artifacts(PKG)
    for rel in artifacts["skills"] + artifacts["agents"]:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        if not (dest / rel).exists():
            shutil.copy2(PKG / rel, dest / rel)
    assert install.complete(str(PKG), str(dest), options) == {"result": "success"}
    assert install.cleanup(str(PKG), str(dest), options) == {"result": "success"}
    standalone = make_repo(tmp_path / "b")
    assert run(standalone, *QA)[0] == 0
    a, b = snapshot(hooked), snapshot(standalone)
    norm = lambda snap, root: {k: v.replace(str(root.resolve()).encode(), b"ROOT").replace(str(root.resolve().parent).encode(), b"PARENT")
                               for k, v in snap.items() if k != install.LOCK_OUT}
    assert norm(a, hooked) == norm(b, standalone)


@pytest.mark.parametrize("version", [(3, 10, 9), (3, 12, 0), (3, 14, 0)])
def test_python_boundary_refuses_unsupported_interpreters(version):
    with pytest.raises(install.UnsupportedPythonError, match="UNSUPPORTED_PYTHON.*Python 3.11"):
        install._check_python_version(version, "test interpreter")


def test_prepare_does_not_refuse_on_the_host_python3(tmp_path, monkeypatch):
    import importlib.metadata
    monkeypatch.setattr(importlib.metadata, "version", lambda _: "1.7.0")
    bin_dir = tmp_path / "bin"
    shim_sc_compose(bin_dir, "1.7.0", "1.7.0", python_version="3.14.0")
    monkeypatch.setenv("PATH", str(bin_dir))
    destination = tmp_path / ".claude"
    result = install.prepare(str(PKG), str(destination), {})
    assert "UNSUPPORTED_PYTHON" not in str(result)


def test_prepare_refuses_unsupported_installer_before_dependencies(tmp_path, monkeypatch):
    monkeypatch.setattr(install.sys, "version_info", (3, 14, 0))
    destination = tmp_path / ".claude"
    result = install.prepare(str(PKG), str(destination), {})
    assert "UNSUPPORTED_PYTHON: installer interpreter" in result["message"]
    assert "Python 3.11" in result["message"]
    assert not destination.exists()
