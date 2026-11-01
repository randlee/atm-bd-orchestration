# pyright: strict
from __future__ import annotations

import json
import runpy
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from result import Ok

from atm_bd_console import queues
from atm_bd_console.command import Output

FIXTURES = Path(__file__).parent / "fixtures" / "lite-phase"
ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / "plugins/atm-bd-orchestration/core/scripts"
REPORT = ROOT / "plugins/atm-bd-orchestration/skills/sprint-report/scripts"


def test_lite_queue_report_has_only_profile_columns(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    phase_dir = tmp_path / ".atm-bd"
    phase_dir.mkdir()
    shutil.copyfile(FIXTURES / "phase.toml", phase_dir / "phase-lt.toml")
    plan = tmp_path / "docs/plans/phase-lt.jsonl"
    plan.parent.mkdir(parents=True)
    shutil.copyfile(FIXTURES / "plan.jsonl", plan)
    templates = tmp_path / ".claude/skills/atm-bd-lite/templates"
    shutil.copytree(FIXTURES / "templates", templates)
    beads: list[dict[str, Any]] = json.loads((FIXTURES / "beads.json").read_text())
    def code_repository(*_args: object) -> Ok[tuple[str, str]]:
        return Ok((str(tmp_path), "owner/repo"))

    monkeypatch.setattr(queues.config, "code_repository", code_repository)
    ready = {"atm-lt-1.group-dev", "atm-lt-1.group-qa"}

    def runner(argv: list[str], _fix: str, *, cwd: str | Path | None = None, **_kwargs: Any) -> Ok[Output]:
        del cwd
        if argv[:2] == ["bd", "--readonly"]:
            return Ok(Output(0, json.dumps(beads)))
        if argv[:2] == ["bd", "ready"]:
            return Ok(Output(0, json.dumps([bead for bead in beads if bead["id"] in ready])))
        if argv[:3] == ["atm", "task", "list"]:
            return Ok(Output(0, "[]"))
        raise AssertionError(f"unexpected deterministic queue read: {argv}")

    report = queues.build(SimpleNamespace(phase="lt", root=None, stack=False), tmp_path,
                          now=datetime(2026, 10, 31, tzinfo=UTC), runner=runner)
    assert set(report["queues"]) == {"needs_dev", "needs_dev_fix", "needs_qa", "needs_landing"}
    rendered = queues.render(report, False)
    assert "needs_sanity" not in rendered and "sanity" not in rendered
    assert "lt-1.group-dev" in rendered and "lt-1.group-qa" in rendered


def test_lite_report_index_and_dag_use_qa_groups() -> None:
    sys.path.insert(0, str(CORE))
    report = runpy.run_path(str(REPORT / "sprint-report"))
    index: dict[str, Any] = {
        "root_bead_id": "atm-phase-lt",
        "sprints": [
            {"sprint_bead_id": "atm-lt-1", "dev_bead_id": "atm-lt-1.group-dev",
             "sanity_bead_id": "atm-lt-1.group-sanity", "depends_on_sanity_bead_ids": []},
            {"sprint_bead_id": "atm-lt-2", "dev_bead_id": "atm-lt-2.group-dev",
             "sanity_bead_id": "atm-lt-2.group-sanity",
             "depends_on_sanity_bead_ids": ["atm-lt-1.group-sanity"]},
        ],
    }
    lite_index = report["use_lite_groups"](index)
    assert [row["sanity_bead_id"] for row in lite_index["sprints"]] == [
        "atm-lt-1.group-qa", "atm-lt-2.group-qa"
    ]
    assert lite_index["sprints"][1]["depends_on_sanity_bead_ids"] == ["atm-lt-1.group-qa"]

    dag = runpy.run_path(str(REPORT / "sprint_dag.py"))
    beads = json.loads((FIXTURES / "beads.json").read_text())
    graph = dag["build_graph"](lite_index, {bead["id"]: bead for bead in beads}, "lite")
    assert graph["nodes"] == [
        "atm-lt-1.group-dev", "atm-lt-1.group-qa", "atm-lt-2.group-dev", "atm-lt-2.group-qa"
    ]


def test_bv_lite_scope_omits_sanity_rows() -> None:
    sys.path.insert(0, str(CORE))
    analyze = runpy.run_path(str(CORE / "bv-analyze"))
    rows: list[dict[str, Any]] = json.loads((FIXTURES / "beads.json").read_text())
    without_sanity = analyze["without_lite_sanity"](rows)
    assert all(not row["id"].endswith(".group-sanity") for row in without_sanity)
    assert {row["id"] for row in without_sanity} == {row["id"] for row in rows}
