"""Package consistency and install rendering tests.

Run from the package root: `python3 -m pytest tests -q`.
The install tests need `sc-compose` on PATH; they are skipped (and say so) without it.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG))
sys.path.insert(0, str(PKG / "tests"))
import install  # noqa: E402
import gen_manifest  # noqa: E402

SC_COMPOSE = shutil.which("sc-compose") is not None
REPO_STRINGS = ("sc-observability", "sc-obs", "obs-", "randlee/sc-", "/Users/randlee", "atm-core", "atm-dev")


# ---------------------------------------------------------------- consistency


def test_generated_blocks_are_current():
    assert gen_manifest.main(["--check"]) == 0


def test_manifest_lists_every_skill_and_agent_file():
    artifacts = install.load_manifest_artifacts(PKG)
    assert artifacts == gen_manifest.tree_artifacts()
    flat = [rel for cat in ("skills", "agents") for rel in artifacts[cat]]
    assert flat == install.INVENTORY


def test_render_list_covers_exactly_the_placeholder_files():
    renders = install.load_registry(PKG)["render"]
    assert renders == gen_manifest.render_list(install.load_manifest_artifacts(PKG))
    assert not [r for r in renders if r.endswith(".j2")], "dispatch templates are never rendered at install"
    for rel in renders:
        assert install.PLACEHOLDER_RE.search((PKG / rel).read_text()), rel


def test_no_repo_or_team_specific_strings_in_sources():
    hits = []
    for cat in ("skills", "agents"):
        for path in (PKG / cat).rglob("*"):
            if not path.is_file() or "node_modules" in path.parts or "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for needle in REPO_STRINGS:
                if needle in text:
                    hits.append(f"{path.relative_to(PKG)}: {needle}")
    assert hits == [], "\n".join(hits)


def test_dispatch_templates_carry_no_install_placeholders():
    for path in PKG.rglob("*.j2"):
        assert not install.PLACEHOLDER_RE.search(path.read_text()), path


def test_workflow_issue_bead_declares_parent():
    text = (PKG / "skills/atm-bd-orchestration/templates/workflow-issue-bead.json.j2").read_text()
    assert "  - parent\n" in text and "{{ parent | tojson }}" in text


# ---------------------------------------------------------------- variables


def make_repo(tmp_path: Path, *, prefix: bool = True) -> Path:
    repo = tmp_path / "my-repo"
    (repo / ".claude" / "agents").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", "git@github.com:owner/my-repo.git"], check=True)
    (repo / ".atm.toml").write_text('[atm]\ndefault_team = "my-team"\n\n[rmux]\nsession = "my-team"\n')
    reg = "roles:\n  dev-sanity: my-sanity\n  lead: my-lead\n"
    if prefix:
        reg += "bead_prefix: myp\n"
    (repo / ".claude" / "agents" / "registry.yaml").write_text(reg)
    return repo


def test_resolve_variables_from_repo_files(tmp_path):
    repo = make_repo(tmp_path)
    vals, problems = install.resolve_variables(repo, {})
    assert problems == []
    assert vals["team"] == "my-team" and vals["lead"] == "my-lead"
    assert vals["dev_sanity_member"] == "my-sanity" and vals["bead_prefix"] == "myp"
    assert vals["workflow_issues_root"] == "myp-workflow-issues"
    assert vals["repo_slug"] == "owner/my-repo" and vals["repo_name"] == "my-repo"
    assert vals["repo_root"] == str(repo.resolve())
    assert vals["worktree_base"] == str(repo.resolve().parent / "my-repo-worktrees")


def test_missing_prefix_names_the_source_and_the_override(tmp_path):
    repo = make_repo(tmp_path, prefix=False)
    _, problems = install.resolve_variables(repo, {})
    assert len(problems) == 1 and "bead_prefix" in problems[0] and "--set bead_prefix=" in problems[0]
    vals, problems = install.resolve_variables(repo, {"bead_prefix": "zz"})
    assert problems == [] and vals["workflow_issues_root"] == "zz-workflow-issues"


def test_prefix_falls_back_to_beads_config(tmp_path):
    repo = make_repo(tmp_path, prefix=False)
    (repo / ".beads").mkdir()
    (repo / ".beads" / "config.yaml").write_text('issue-prefix: "bc"\n')
    vals, problems = install.resolve_variables(repo, {})
    assert problems == [] and vals["bead_prefix"] == "bc"


# ---------------------------------------------------------------- rendering


needs_sc_compose = pytest.mark.skipif(not SC_COMPOSE, reason="sc-compose not on PATH; install rendering not verified")


@needs_sc_compose
def test_render_text_keeps_frontmatter_and_substitutes():
    out = install.render_text("---\nname: x\n---\n\nmember `{{ dev_sanity_member }}` of {{ team }}\n",
                              {"dev_sanity_member": "my-sanity", "team": "my-team"})
    assert out == "---\nname: x\n---\n\nmember `my-sanity` of my-team\n"


@needs_sc_compose
def test_standalone_install_renders_every_placeholder(tmp_path):
    repo = make_repo(tmp_path)
    dest = repo / ".claude"
    rc = install.main(["--dest", str(dest)])
    assert rc == 0
    installed = sorted(str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file() and "agents/registry.yaml" not in str(p))
    assert installed == sorted(install.INVENTORY)
    leftovers = [rel for rel in install.INVENTORY if install.PLACEHOLDER_RE.search((dest / rel).read_text())]
    assert leftovers == []
    skill = (dest / "skills/atm-bd-orchestration/SKILL.md").read_text()
    assert "myp-workflow-issues" in skill
    role = (dest / "skills/atm-bd-orchestration/roles/dev-sanity.md").read_text()
    assert "| Setting | Where | my-repo |" in role and "`my-sanity`" in role
    example = (dest / "skills/atm-bd-orchestration/examples/dev-sanity-template-vars.json").read_text()
    assert "https://github.com/owner/my-repo/pull/" in example and str(repo.resolve().parent / "my-repo-worktrees") in example
    # scripts stay executable
    assert (dest / "skills/atm-beads/scripts/validate-plan").stat().st_mode & 0o111
    # unrendered files are byte-identical to the package copy
    assert (dest / "skills/atm-bd-orchestration/templates/qa-template.xml.j2").read_bytes() == \
        (PKG / "skills/atm-bd-orchestration/templates/qa-template.xml.j2").read_bytes()


@needs_sc_compose
def test_install_is_idempotent_and_respects_force(tmp_path):
    repo = make_repo(tmp_path)
    dest = repo / ".claude"
    assert install.main(["--dest", str(dest)]) == 0
    snapshot = {rel: (dest / rel).read_bytes() for rel in install.INVENTORY}
    assert install.main(["--dest", str(dest)]) == 0
    assert {rel: (dest / rel).read_bytes() for rel in install.INVENTORY} == snapshot
    # a changed repository value is picked up only with --force
    (repo / ".claude/agents/registry.yaml").write_text("roles:\n  dev-sanity: renamed-sanity\nbead_prefix: myp\n")
    assert install.main(["--dest", str(dest)]) == 0
    assert "`my-sanity`" in (dest / "skills/atm-bd-orchestration/roles/dev-sanity.md").read_text()
    assert install.main(["--dest", str(dest), "--force"]) == 0
    assert "`renamed-sanity`" in (dest / "skills/atm-bd-orchestration/roles/dev-sanity.md").read_text()


@needs_sc_compose
def test_codex_target_installs_skills_only(tmp_path):
    repo = make_repo(tmp_path)
    dest = repo / ".codex"
    assert install.main(["--dest", str(dest)]) == 0
    assert not (dest / "agents").exists()
    assert (dest / "skills/atm-beads/SKILL.md").is_file()
    leftovers = [rel for rel in install.INVENTORY if (dest / rel).is_file() and install.PLACEHOLDER_RE.search((dest / rel).read_text())]
    assert leftovers == []


@needs_sc_compose
def test_hook_contract_prepare_fails_with_a_message(tmp_path):
    repo = make_repo(tmp_path, prefix=False)
    options = {"global": False, "local": True, "user": False, "project": False,
               "codex": False, "force": False, "expand": True, "args": {}}
    result = install.prepare(str(PKG), str(repo / ".claude"), options)
    assert result["result"] == "fail" and "--set bead_prefix=" in result["message"]
    options["args"] = {"bead_prefix": "ok"}
    assert install.prepare(str(PKG), str(repo / ".claude"), options) == {"result": "success"}
    assert install.cleanup(str(PKG), str(repo / ".claude"), options) == {"result": "success"}
