"""Plan-hardening step and finding beads drive dispatch through real embedded bd."""
import json
from pathlib import Path
import sys

import pytest

from .beads_db import bd, init_db

SKILLS = Path(__file__).resolve().parents[3] / "skills"
sys.path.insert(0, str(SKILLS / "atm-beads" / "scripts"))
import sc_render  # noqa: E402

TEMPLATES = SKILLS / "plan-hardening"
ROOT = "tst-phase-bc"


def _bead(name: str, **variables) -> dict:
    return json.loads(sc_render.render(TEMPLATES / f"plan-hardening-{name}-bead.json.j2", variables))


def _step(step: int, route_to: str, blocked_by: list[str]) -> dict:
    return _bead("step", id=f"{ROOT}-ph-s{step}-c1", root=ROOT, phase="bc", step=step, cycle=1,
                 route_to=route_to, blocked_by=blocked_by)


def _import(root: Path, *beads: dict) -> None:
    path = root / "in.jsonl"
    path.write_text("".join(json.dumps(b) + "\n" for b in beads))
    bd(root, "import", str(path))


def _ready(root: Path) -> list[str]:
    return [b["id"] for b in json.loads(bd(root, "ready", "-l", "stage:plan-hardening", "-n", "0", "--json"))]


@pytest.fixture
def db(tmp_path: Path) -> Path:
    init_db(tmp_path)
    bd(tmp_path, "create", "root", "--id", ROOT, "--type", "epic")
    return tmp_path


def test_review_step_is_ready_only_after_the_planner_rules_on_every_finding(db: Path) -> None:
    review = _step(2, "plan-scope-reviewer", [])
    finding = _bead("finding", id=f"{review['id']}-plan-scope-001", root=ROOT, phase="bc",
                    step_bead=review["id"], reviewer="plan-scope-reviewer", finding_ref="PLAN-SCOPE-001",
                    severity="Blocking", category="SERIAL-RISK", issue="serial edge", correction="drop it")
    planner = _step(3, "planner", [review["id"]])
    next_review = _step(4, "critical-plan-reviewer", [planner["id"], finding["id"]])
    _import(db, review, finding, planner, next_review)

    assert _ready(db) == [review["id"]]
    bd(db, "close", review["id"], "--reason", "FAIL blocking=1 important=0 minor=0")
    assert _ready(db) == [planner["id"]]
    bd(db, "close", planner["id"], "--reason", "PASS")
    assert _ready(db) == []
    bd(db, "close", finding["id"], "--reason", "fixed: dropped the edge")
    assert _ready(db) == [next_review["id"]]


def test_finding_priority_and_labels_follow_severity() -> None:
    finding = _bead("finding", id="f", root=ROOT, phase="bc", step_bead="s", reviewer="ceremony-qa",
                    finding_ref="CQA-F001", severity="minor", category="unjustified_artifact",
                    issue="i", correction="c")
    assert finding["priority"] == 4
    assert "stage:plan-finding" in finding["labels"] and "severity:minor" in finding["labels"]
    with pytest.raises(sc_render.RenderError):
        _bead("finding", id="f", root=ROOT, phase="bc", step_bead="s", reviewer="r", finding_ref="x",
              severity="Critical", category="c", issue="i", correction="c")
