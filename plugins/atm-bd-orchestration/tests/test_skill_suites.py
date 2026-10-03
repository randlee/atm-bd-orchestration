"""Run the skills' own test suites against an installed, rendered copy.

The upstream suites resolve paths from the repository layout (`.claude/skills/...`,
`scripts/jev_client.py`) and some scripts carry install-time values, so they run
inside a throwaway repository installed with a non-default bead prefix (`myp`).
Needs `sc-compose`; skipped (and says so) without it.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import install
from test_install import make_repo

PKG = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(shutil.which("sc-compose") is None, reason="sc-compose not on PATH; skill suites not run")

SUITES = (
    ".claude/skills/atm-bd-orchestration/scripts/tests",
    ".claude/skills/atm-beads/tests",
    ".claude/skills/sprint-report/tests",
)
# Reads the source repository's own docs/plans/phase-d/sprints.jsonl, which no consuming repository has.
REPO_DATA_TESTS = (
    ".claude/skills/sprint-report/tests/test_sprint_report.py::SprintReportTests::test_phase_d_index_excludes_folded_d11",
)


@pytest.fixture(scope="module")
def installed(tmp_path_factory):
    repo = make_repo(tmp_path_factory.mktemp("suites"))
    assert install.main(["--dest", str(repo / ".claude"), "--set", "qa_member=quality-mgr"]) == 0
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "install"], check=True)
    return repo


@pytest.mark.parametrize("suite", SUITES)
def test_installed_suite_passes(installed, suite):
    skill_dir = installed / suite
    scripts = skill_dir.parent if skill_dir.parent.name == "scripts" else skill_dir.parent / "scripts"
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(scripts), str(scripts.parent)])}
    deselect = [arg for t in REPO_DATA_TESTS if t.startswith(suite) for arg in ("--deselect", t)]
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", suite, *deselect],
                          cwd=installed, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.returncode == 0, proc.stdout[-4000:]


def test_dev_bead_ids_take_the_installed_prefix(installed):
    """The sprint index derives dev bead ids with the repository's bead prefix, not the source repository's."""
    plan = installed / "docs/plans/phase-x/sprints.jsonl"
    plan.parent.mkdir(parents=True)
    plan.write_text('["x-1", "myp-x-1-sanity", []]\n["x-2", "myp-x-2-sanity", ["x-1"]]\n')
    code = ("import json, sys; from pathlib import Path; sys.path.insert(0, '.claude/skills/atm-beads/scripts');"
            "import sprint_index_common as c; print(json.dumps(c.load_phase_plan(Path(sys.argv[1]))))")
    out = subprocess.run([sys.executable, "-c", code, str(plan)], cwd=installed, check=True,
                         stdout=subprocess.PIPE, text=True).stdout
    index = json.loads(out)
    assert index["root_bead_id"] == "myp-phase-x"
    assert [row["dev_bead_id"] for row in index["sprints"]] == ["myp-x-1", "myp-x-2"]


@pytest.mark.parametrize("example", ("sprint-bead-vars-d-4.json", "sprint-bead-vars-d-5.json"))
def test_sprint_bead_template_renders_a_valid_sprint_bead(installed, example):
    """A strict render of the sprint-bead template carries the SprintBead metadata (difficulty) and stage:sprint.

    Metadata only: the example descriptions are not numbered Deliverables lists."""
    skill = installed / ".claude/skills/atm-beads"
    out = subprocess.run(["sc-compose", "render", "--file", str(skill / "templates/sprint-bead.json.j2"),
                          "--var-file", str(skill / "examples" / example), "--strict"],
                         cwd=installed, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert out.returncode == 0, out.stderr[-4000:]
    bead = json.loads(out.stdout)
    sys.path.insert(0, str(skill / "scripts"))
    import bead_schema
    bead_schema.SprintMetadata.model_validate(bead["metadata"])
    assert "stage:sprint" in bead["labels"]
