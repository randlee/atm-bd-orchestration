#!/usr/bin/env python3
"""atm-bd-orchestration install hook and standalone installer.

Two ways in:

1. sc-install (synaptic-canvas) loads this file as the package's Tier-3
   install hook and calls prepare()/complete()/cleanup() around its own
   manifest-artifact copy step, once per target (.claude and/or .codex).
2. Standalone: `python3 install.py --dest <repo>/.claude [--codex] [--force]
   [--set KEY=VALUE ...]` copies the manifest artifacts itself and then runs
   the same complete() step.

complete() renders the repository-specific values (team, lead, dev-sanity
member, bead prefix, workflow-issues root, repo slug, worktree base) into
the installed copies of the files listed under `render:` in registry.yaml,
with `sc-compose render --strict`. The values come from the consuming
repository, never from this package:

    .atm.toml                    [atm] default_team           -> team
    .claude/agents/registry.yaml roles.lead                   -> lead
                                 roles.dev-sanity             -> dev_sanity_member
                                 bead_prefix                  -> bead_prefix
                                 workflow_issues_root         -> workflow_issues_root
    .beads/config.yaml           issue-prefix (fallback)      -> bead_prefix
    git remote origin            owner/name                   -> repo_slug, repo_name
    the repository path                                       -> repo_root, worktree_base

Any value can be overridden with `--set NAME=VALUE` (sc-install) or
`--set NAME=VALUE` (standalone); the hook reads them from options["args"].
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

PKG_DIR = Path(__file__).resolve().parent
REGISTRY_FILE = "registry.yaml"
MANIFEST_FILE = "manifest.yaml"
VARIABLE_NAMES = (
    "team",
    "lead",
    "dev_sanity_member",
    "bead_prefix",
    "workflow_issues_root",
    "repo_slug",
    "repo_name",
    "repo_root",
    "worktree_base",
)
SCHEMA_ASSET = "assets/docs/plans/sprints.schema.json"
PLACEHOLDER_RE = re.compile(r"\{\{ (" + "|".join(VARIABLE_NAMES) + r") \}\}")

# Every path this package has ever installed, across all versions.
# Only append - never remove an entry. If a version stops shipping a
# path listed here, add a matching `if (Path(destination_path) / path
# ).exists(): ...unlink()` line to complete() before removing that
# artifact from manifest.yaml, or CI will fail.
INVENTORY = [
    # INVENTORY-BEGIN (generated from manifest.yaml by tests/gen_manifest.py)
    "skills/atm-bd-orchestration/SKILL.md",
    "skills/atm-bd-orchestration/examples/arch-qa-assignment-vars.json",
    "skills/atm-bd-orchestration/examples/dev-complete-vars.json",
    "skills/atm-bd-orchestration/examples/dev-fix-vars.json",
    "skills/atm-bd-orchestration/examples/dev-sanity-assignment-vars.json",
    "skills/atm-bd-orchestration/examples/dev-sanity-complete-vars.json",
    "skills/atm-bd-orchestration/examples/dev-sanity-template-vars.json",
    "skills/atm-bd-orchestration/examples/dev-template-vars.json",
    "skills/atm-bd-orchestration/examples/finding-bead-vars.json",
    "skills/atm-bd-orchestration/examples/fix-assignment-vars.json",
    "skills/atm-bd-orchestration/examples/fix-complete-vars.json",
    "skills/atm-bd-orchestration/examples/flaky-test-qa-assignment-vars.json",
    "skills/atm-bd-orchestration/examples/plan-review-complete-vars.json",
    "skills/atm-bd-orchestration/examples/plan-review-template-fix-round-vars.json",
    "skills/atm-bd-orchestration/examples/plan-review-template-vars.json",
    "skills/atm-bd-orchestration/examples/plan-scope-reviewer-assignment-vars.json",
    "skills/atm-bd-orchestration/examples/qa-bead-vars.json",
    "skills/atm-bd-orchestration/examples/qa-complete-vars.json",
    "skills/atm-bd-orchestration/examples/qa-template-fix-round-vars.json",
    "skills/atm-bd-orchestration/examples/qa-template-vars.json",
    "skills/atm-bd-orchestration/examples/req-qa-assignment-vars.json",
    "skills/atm-bd-orchestration/examples/review-complete-vars.json",
    "skills/atm-bd-orchestration/examples/review-template-vars.json",
    "skills/atm-bd-orchestration/examples/ruthless-boundary-qa-assignment-vars.json",
    "skills/atm-bd-orchestration/examples/schema-reviewer-assignment-vars.json",
    "skills/atm-bd-orchestration/examples/task-refused-vars.json",
    "skills/atm-bd-orchestration/examples/workflow-issue-bead-vars.json",
    "skills/atm-bd-orchestration/roles/dev-sanity.md",
    "skills/atm-bd-orchestration/roles/quality-mgr.md",
    "skills/atm-bd-orchestration/scripts/assignment-gates.py",
    "skills/atm-bd-orchestration/scripts/bd_commands.py",
    "skills/atm-bd-orchestration/scripts/blocking-finding-gates.py",
    "skills/atm-bd-orchestration/scripts/sanity-create-findings",
    "skills/atm-bd-orchestration/scripts/sanity-merge",
    "skills/atm-bd-orchestration/scripts/sanity-split",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/dev-ready.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/difficulty-mismatch.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/dirty-tree.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/not-ready.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/plan-invalid.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/pr-required.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/qa-head-mismatch.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/qa-ready.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/sanity-frozen.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/sanity-ready.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/stale-base.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/stale-sanity.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/transition-first-fail.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/transition-minor-pass.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/transition-round-cap.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/transition-sanity-pass.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/unclaimable.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/wrong-base.json",
    "skills/atm-bd-orchestration/scripts/tests/fixtures/zero-delta.json",
    "skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py",
    "skills/atm-bd-orchestration/scripts/tests/test_blocking_finding_gates.py",
    "skills/atm-bd-orchestration/scripts/tests/test_templates.py",
    "skills/atm-bd-orchestration/scripts/tests/test_transitions.py",
    "skills/atm-bd-orchestration/scripts/transitions.py",
    "skills/atm-bd-orchestration/templates/arch-qa-assignment.json.j2",
    "skills/atm-bd-orchestration/templates/dev-complete.md.j2",
    "skills/atm-bd-orchestration/templates/dev-fix.xml.j2",
    "skills/atm-bd-orchestration/templates/dev-sanity-assignment.json.j2",
    "skills/atm-bd-orchestration/templates/dev-sanity-complete.md.j2",
    "skills/atm-bd-orchestration/templates/dev-sanity-template.xml.j2",
    "skills/atm-bd-orchestration/templates/dev-template.xml.j2",
    "skills/atm-bd-orchestration/templates/finding-bead.json.j2",
    "skills/atm-bd-orchestration/templates/fix-assignment.xml.j2",
    "skills/atm-bd-orchestration/templates/fix-complete.md.j2",
    "skills/atm-bd-orchestration/templates/flaky-test-qa-assignment.json.j2",
    "skills/atm-bd-orchestration/templates/plan-review-complete.md.j2",
    "skills/atm-bd-orchestration/templates/plan-review-template.xml.j2",
    "skills/atm-bd-orchestration/templates/plan-scope-reviewer-assignment.json.j2",
    "skills/atm-bd-orchestration/templates/qa-bead.json.j2",
    "skills/atm-bd-orchestration/templates/qa-complete.md.j2",
    "skills/atm-bd-orchestration/templates/qa-template.xml.j2",
    "skills/atm-bd-orchestration/templates/req-qa-assignment.json.j2",
    "skills/atm-bd-orchestration/templates/review-complete.md.j2",
    "skills/atm-bd-orchestration/templates/review-template.xml.j2",
    "skills/atm-bd-orchestration/templates/ruthless-boundary-qa-assignment.json.j2",
    "skills/atm-bd-orchestration/templates/schema-reviewer-assignment.json.j2",
    "skills/atm-bd-orchestration/templates/task-refused.md.j2",
    "skills/atm-bd-orchestration/templates/workflow-issue-bead.json.j2",
    "skills/atm-beads/SKILL.md",
    "skills/atm-beads/examples/dev-sanity-bead-vars-d-4.json",
    "skills/atm-beads/examples/plan-root-vars.json",
    "skills/atm-beads/examples/sprint-bead-vars-d-4.json",
    "skills/atm-beads/examples/sprint-bead-vars-d-5.json",
    "skills/atm-beads/references/installation-and-troubleshooting.md",
    "skills/atm-beads/resources/atm-beads-plan-guidelines.md",
    "skills/atm-beads/resources/dev-sanity.md",
    "skills/atm-beads/resources/importing-md-plan.md",
    "skills/atm-beads/resources/orchestrating.md",
    "skills/atm-beads/resources/planning.md",
    "skills/atm-beads/resources/troubleshooting.md",
    "skills/atm-beads/scripts/check-phase-artifact",
    "skills/atm-beads/scripts/check-plan.jq",
    "skills/atm-beads/scripts/migrate-phase-contract",
    "skills/atm-beads/scripts/phase-index-path",
    "skills/atm-beads/scripts/phase_contract_check.py",
    "skills/atm-beads/scripts/plan_contract.py",
    "skills/atm-beads/scripts/resolve-role",
    "skills/atm-beads/scripts/sprint_index_common.py",
    "skills/atm-beads/scripts/validate-plan",
    "skills/atm-beads/templates/dev-sanity-bead.json.j2",
    "skills/atm-beads/templates/plan-root.json.j2",
    "skills/atm-beads/templates/sprint-bead.json.j2",
    "skills/atm-beads/tests/fixtures/acceptance_key_5_of_3.json",
    "skills/atm-beads/tests/fixtures/deliverables_1_2_4.json",
    "skills/atm-beads/tests/fixtures/dev_without_sprint_label.json",
    "skills/atm-beads/tests/fixtures/difficulty_medium.json",
    "skills/atm-beads/tests/fixtures/finding_parented_on_root.json",
    "skills/atm-beads/tests/fixtures/finding_under_root_caused_by.json",
    "skills/atm-beads/tests/fixtures/finding_without_severity.json",
    "skills/atm-beads/tests/fixtures/handoff_outside_consumer_fence.json",
    "skills/atm-beads/tests/fixtures/important_finding_p3.json",
    "skills/atm-beads/tests/fixtures/in_progress_with_open_blocker.json",
    "skills/atm-beads/tests/fixtures/index_undeclared_key.json",
    "skills/atm-beads/tests/fixtures/index_waiver_bad_check.json",
    "skills/atm-beads/tests/fixtures/listed_pair_missing_from_beads.json",
    "skills/atm-beads/tests/fixtures/live_pair_missing_from_index.json",
    "skills/atm-beads/tests/fixtures/open_finding_without_difficulty.json",
    "skills/atm-beads/tests/fixtures/owned_path_overlap.json",
    "skills/atm-beads/tests/fixtures/pass_without_qa.json",
    "skills/atm-beads/tests/fixtures/pr_base_mismatch.json",
    "skills/atm-beads/tests/fixtures/pr_target_sanity_outside_closure.json",
    "skills/atm-beads/tests/fixtures/qa_under_root_validates.json",
    "skills/atm-beads/tests/fixtures/r16_blocking_finding_without_sanity.json",
    "skills/atm-beads/tests/fixtures/r16_deferred_finding_exempts_upstream.json",
    "skills/atm-beads/tests/fixtures/r16_downstream_not_gated.json",
    "skills/atm-beads/tests/fixtures/r16_gate_not_blocked_by_finding.json",
    "skills/atm-beads/tests/fixtures/r16_in_progress_exempt_warns.json",
    "skills/atm-beads/tests/fixtures/reopened_pass_sanity.json",
    "skills/atm-beads/tests/fixtures/root_feature_under_task.json",
    "skills/atm-beads/tests/fixtures/root_task_at_top_level.json",
    "skills/atm-beads/tests/fixtures/sanity_base_sha_commit_short.json",
    "skills/atm-beads/tests/fixtures/second_fix_round.json",
    "skills/atm-beads/tests/fixtures/sprint_bead_p3.json",
    "skills/atm-beads/tests/fixtures/sprint_without_difficulty.json",
    "skills/atm-beads/tests/fixtures/started_before_blocker_closed.json",
    "skills/atm-beads/tests/fixtures/unlisted_human_gate.json",
    "skills/atm-beads/tests/fixtures/valid_closed_finding_p3.json",
    "skills/atm-beads/tests/fixtures/valid_closed_finding_without_difficulty.json",
    "skills/atm-beads/tests/fixtures/valid_index_with_policy.json",
    "skills/atm-beads/tests/fixtures/valid_ordered_overlap.json",
    "skills/atm-beads/tests/fixtures/valid_pass_with_qa.json",
    "skills/atm-beads/tests/fixtures/valid_phase.json",
    "skills/atm-beads/tests/fixtures/valid_r16_gated.json",
    "skills/atm-beads/tests/fixtures/valid_root_feature_under_epic.json",
    "skills/atm-beads/tests/fixtures/valid_waived_reopen.json",
    "skills/atm-beads/tests/test_phase_contract_check.py",
    "skills/sprint-report/SKILL.md",
    "skills/sprint-report/dag-view.html",
    "skills/sprint-report/renderer/.gitignore",
    "skills/sprint-report/renderer/package-lock.json",
    "skills/sprint-report/renderer/package.json",
    "skills/sprint-report/renderer/render.cjs",
    "skills/sprint-report/report-detailed.md.j2",
    "skills/sprint-report/report.md.j2",
    "skills/sprint-report/scripts/phase_artifact.py",
    "skills/sprint-report/scripts/sprint-report",
    "skills/sprint-report/scripts/sprint_dag.py",
    "skills/sprint-report/scripts/sprint_qa.py",
    "skills/sprint-report/tests/test_sprint_dag.py",
    "skills/sprint-report/tests/test_sprint_report.py",
    "skills/sprint-report/tests/test_sprint_review.py",
    "skills/sprint-review/SKILL.md",
    "skills/sprint-review/scripts/sprint-review",
    "agents/dev-sanity-jev.md",
    "agents/dev-sanity-llm.md",
    "agents/sc-sanity-jev.md",
    "agents/sc-sanity-llm.md",
    # INVENTORY-END
]


# ---------------------------------------------------------------------------
# Small YAML/TOML readers (pyyaml for the repository files, like resolve-role)
# ---------------------------------------------------------------------------


def _yaml():
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "PyYAML is required to read registry.yaml (pip install pyyaml)"
        ) from exc
    return yaml


def _load_yaml(path: Path) -> Dict[str, Any]:
    data = _yaml().safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"{path}: expected a mapping at the top level")
    return data


def load_registry(pkg_dir: Path = PKG_DIR) -> Dict[str, Any]:
    return _load_yaml(pkg_dir / REGISTRY_FILE)


def load_manifest_artifacts(pkg_dir: Path = PKG_DIR) -> Dict[str, List[str]]:
    data = _load_yaml(pkg_dir / MANIFEST_FILE)
    artifacts = data.get("artifacts") or {}
    return {k: list(v or []) for k, v in artifacts.items()}


def _atm_default_team(atm_toml: Path) -> Optional[str]:
    text = atm_toml.read_text(encoding="utf-8")
    try:
        import tomllib  # Python 3.11+

        data = tomllib.loads(text)
        value = (data.get("atm") or {}).get("default_team")
        return str(value) if value else None
    except ImportError:  # pragma: no cover - old python
        pass
    m = re.search(r"^\[atm\]\s*$(.*?)(?=^\[|\Z)", text, re.M | re.S)
    if not m:
        return None
    m2 = re.search(r'^\s*default_team\s*=\s*"([^"]+)"', m.group(1), re.M)
    return m2.group(1) if m2 else None


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


# ---------------------------------------------------------------------------
# Variable resolution
# ---------------------------------------------------------------------------


def repo_root_for(destination_path: Path) -> Path:
    """The consuming repository: the parent of <repo>/.claude or <repo>/.codex,
    or the git toplevel above an explicit --dest."""
    dest = Path(destination_path).resolve()
    if dest.name in (".claude", ".codex"):
        return dest.parent
    try:
        top = subprocess.run(
            ["git", "-C", str(dest.parent), "rev-parse", "--show-toplevel"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        ).stdout.strip()
        if top:
            return Path(top)
    except (OSError, subprocess.CalledProcessError):
        pass
    return dest.parent


def resolve_variables(repo_root: Path, overrides: Dict[str, str]) -> Tuple[Dict[str, str], List[str]]:
    """Return (variables, problems). problems is empty when every variable resolved."""
    repo_root = Path(repo_root).resolve()
    vals: Dict[str, Optional[str]] = {name: None for name in VARIABLE_NAMES}
    problems: List[str] = []

    atm_toml = repo_root / ".atm.toml"
    if atm_toml.is_file():
        vals["team"] = _atm_default_team(atm_toml)
    registry = repo_root / ".claude" / "agents" / "registry.yaml"
    reg: Dict[str, Any] = {}
    if registry.is_file():
        try:
            reg = _load_yaml(registry)
        except Exception as exc:  # noqa: BLE001 - reported, not raised
            problems.append(f"{registry}: {exc}")
    roles = reg.get("roles") or {}
    vals["lead"] = str(roles.get("lead") or "team-lead")
    if roles.get("dev-sanity"):
        vals["dev_sanity_member"] = str(roles["dev-sanity"])
    if reg.get("bead_prefix"):
        vals["bead_prefix"] = str(reg["bead_prefix"])
    else:
        beads_cfg = repo_root / ".beads" / "config.yaml"
        if beads_cfg.is_file():
            m = re.search(r'^\s*issue-prefix:\s*"?([A-Za-z0-9_-]+)"?\s*$', beads_cfg.read_text(encoding="utf-8"), re.M)
            if m:
                vals["bead_prefix"] = m.group(1)
    if reg.get("workflow_issues_root"):
        vals["workflow_issues_root"] = str(reg["workflow_issues_root"])
    vals["repo_slug"] = _git_origin_slug(repo_root)
    vals["repo_root"] = str(repo_root)

    for key, value in overrides.items():
        name = key.lower()
        if name in vals:
            vals[name] = value

    if vals["repo_slug"] and not vals["repo_name"]:
        vals["repo_name"] = vals["repo_slug"].rsplit("/", 1)[-1]
    if not vals["repo_name"]:
        vals["repo_name"] = repo_root.name
    if vals["bead_prefix"] and not vals["workflow_issues_root"]:
        vals["workflow_issues_root"] = f"{vals['bead_prefix']}-workflow-issues"
    if not vals["worktree_base"]:
        vals["worktree_base"] = str(repo_root.parent / f"{vals['repo_name']}-worktrees")

    sources = {
        "team": f"{atm_toml} [atm] default_team",
        "dev_sanity_member": f"{registry} roles.dev-sanity",
        "bead_prefix": f"{registry} bead_prefix (or .beads/config.yaml issue-prefix)",
        "repo_slug": "git remote get-url origin",
    }
    for name, source in sources.items():
        if not vals[name]:
            problems.append(f"{name} is not set: add it to {source}, or pass --set {name}=<value>")
    return {k: v for k, v in vals.items() if v is not None}, problems


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _split_frontmatter(text: str) -> Tuple[str, str]:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[: end + 5], text[end + 5 :]
    return "", text


def render_text(text: str, variables: Dict[str, str]) -> str:
    """Render one file body with sc-compose (strict: every referenced token must be declared)."""
    front, body = _split_frontmatter(text)
    declared = "".join(f"  - {name}\n" for name in VARIABLE_NAMES)
    template = f"---\nname: atm-bd-install\nversion: 1.0.0\nformat: markdown\nrequired_variables:\n{declared}---\n{body}"
    with tempfile.TemporaryDirectory(prefix="atm-bd-install-") as tmp:
        tmp_dir = Path(tmp)
        (tmp_dir / "body.md").write_text(template, encoding="utf-8")
        (tmp_dir / "vars.json").write_text(json.dumps({n: variables.get(n, "") for n in VARIABLE_NAMES}), encoding="utf-8")
        proc = subprocess.run(
            ["sc-compose", "render", "--file", "body.md", "--var-file", "vars.json", "--strict"],
            cwd=tmp_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
    if proc.returncode != 0:
        first = (proc.stderr or proc.stdout).strip().splitlines()[:1]
        raise RuntimeError(f"sc-compose render failed: {first[0] if first else 'no output'}")
    rendered = proc.stdout
    if body.endswith("\n") and not rendered.endswith("\n"):
        rendered += "\n"
    leftover = PLACEHOLDER_RE.search(rendered)
    if leftover:
        raise RuntimeError(f"placeholder {leftover.group(0)} survived rendering")
    return front + rendered


def _copy_mode(src: Path, dst: Path) -> None:
    mode = src.stat().st_mode
    if mode & stat.S_IXUSR:
        dst.chmod(dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def render_into(source_path: Path, destination_path: Path, variables: Dict[str, str], *, force: bool) -> List[str]:
    """Render every registry `render:` file whose installed copy exists.

    A copy is rendered when it is byte-identical to the package source (sc-install
    or the standalone copy just wrote it) or when force is set. A copy that already
    differs from the source was rendered by an earlier install and is left alone
    unless force is set, matching sc-install's skip-existing behaviour.
    """
    registry = load_registry(source_path)
    rendered: List[str] = []
    for rel in registry.get("render") or []:
        src = source_path / rel
        dst = destination_path / rel
        if not dst.is_file():
            continue  # not installed on this target (agents are .claude-only)
        src_text = src.read_text(encoding="utf-8")
        if not force and dst.read_text(encoding="utf-8") != src_text:
            continue
        dst.write_text(render_text(src_text, variables), encoding="utf-8")
        _copy_mode(src, dst)
        rendered.append(rel)
    return rendered


# ---------------------------------------------------------------------------
# sc-install hook contract
# ---------------------------------------------------------------------------


def _ok() -> Dict[str, str]:
    return {"result": "success"}


def _fail(message: str) -> Dict[str, str]:
    return {"result": "fail", "message": message}


def prepare(source_path: str, destination_path: str, options: dict) -> dict:
    """Check the tools and repository values before anything is copied. Writes nothing."""
    if shutil.which("sc-compose") is None:
        return _fail("sc-compose is not on PATH; install it (brew install randlee/tap/sc-compose) and rerun")
    try:
        _, problems = resolve_variables(repo_root_for(Path(destination_path)), options.get("args") or {})
    except RuntimeError as exc:
        return _fail(str(exc))
    if problems:
        return _fail("; ".join(problems))
    return _ok()


def complete(source_path: str, destination_path: str, options: dict) -> dict:
    """Render the repository values into the installed copies (idempotent)."""
    src = Path(source_path).resolve()
    dst = Path(destination_path).resolve()
    try:
        variables, problems = resolve_variables(repo_root_for(dst), options.get("args") or {})
        if problems:
            return _fail("; ".join(problems))
        rendered = render_into(src, dst, variables, force=bool(options.get("force")))
    except RuntimeError as exc:
        return _fail(f"{exc}; fix the named file or value and rerun the install with --force")
    # The sprint index schema is a repository document (docs/plans/sprints.json instances point at it),
    # so the asset is also placed at <repo>/docs/plans/; the repository owns it from then on.
    schema_src = src / SCHEMA_ASSET
    schema_dst = repo_root_for(dst) / "docs" / "plans" / schema_src.name
    if schema_src.is_file() and (bool(options.get("force")) or not schema_dst.exists()):
        schema_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(schema_src, schema_dst)
    # Conditional delete-if-present lines for INVENTORY entries this version dropped go here.
    print(f"atm-bd-orchestration: rendered {len(rendered)} file(s) for {variables['repo_slug']} "
          f"(team {variables['team']}, prefix {variables['bead_prefix']}, dev-sanity {variables['dev_sanity_member']})")
    return _ok()


def cleanup(source_path: str, destination_path: str, options: dict) -> dict:
    """The only file created beyond the manifest artifacts is <repo>/docs/plans/sprints.schema.json,
    which the repository owns once installed (its sprints.json files reference it), so it stays."""
    return _ok()


# ---------------------------------------------------------------------------
# Standalone installer (same copy semantics as sc-install: skip existing unless --force)
# ---------------------------------------------------------------------------


def iter_artifacts(artifacts: Dict[str, List[str]], *, codex: bool) -> Iterable[str]:
    order = ["skills", "scripts", "assets"] if codex else ["commands", "skills", "agents", "scripts", "assets"]
    for key in order:
        yield from artifacts.get(key, [])


def _copy_artifacts(dest: Path, *, codex: bool, force: bool) -> Tuple[int, int]:
    copied = skipped = 0
    for rel in iter_artifacts(load_manifest_artifacts(), codex=codex):
        src = PKG_DIR / rel
        dst = dest / rel
        if not src.is_file():
            raise RuntimeError(f"manifest artifact missing from the package: {rel}")
        if dst.exists() and not force:
            skipped += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    return copied, skipped


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Install atm-bd-orchestration into a repository's .claude (or .codex) directory.")
    parser.add_argument("--dest", required=True, help="<repo>/.claude or <repo>/.codex")
    parser.add_argument("--codex", action="store_true", help="the destination is a .codex directory (skills only, no agents)")
    parser.add_argument("--force", action="store_true", help="overwrite and re-render files that already exist")
    parser.add_argument("--set", action="append", default=[], metavar="NAME=VALUE", help="override a resolved variable")
    parser.add_argument("--print-vars", action="store_true", help="resolve and print the variables, install nothing")
    args = parser.parse_args(argv)

    overrides: Dict[str, str] = {}
    for item in args.set:
        if "=" not in item:
            parser.error(f"--set expects NAME=VALUE, got {item!r}")
        k, v = item.split("=", 1)
        overrides[k.strip()] = v.strip()

    dest = Path(args.dest).expanduser().resolve()
    codex = args.codex or dest.name == ".codex"
    options = {"global": False, "local": True, "user": False, "project": False,
               "codex": codex, "force": args.force, "expand": True, "args": overrides}

    if args.print_vars:
        variables, problems = resolve_variables(repo_root_for(dest), overrides)
        print(json.dumps(variables, indent=2, sort_keys=True))
        for p in problems:
            print(f"problem: {p}", file=sys.stderr)
        return 1 if problems else 0

    result = prepare(str(PKG_DIR), str(dest), options)
    if result["result"] != "success":
        print(f"install.py: {result['message']}", file=sys.stderr)
        return 1
    dest.mkdir(parents=True, exist_ok=True)
    try:
        copied, skipped = _copy_artifacts(dest, codex=codex, force=args.force)
    except RuntimeError as exc:
        print(f"install.py: {exc}", file=sys.stderr)
        return 1
    print(f"atm-bd-orchestration: copied {copied} file(s), skipped {skipped} existing (use --force to overwrite) into {dest}")
    result = complete(str(PKG_DIR), str(dest), options)
    if result["result"] != "success":
        print(f"install.py: {result['message']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
