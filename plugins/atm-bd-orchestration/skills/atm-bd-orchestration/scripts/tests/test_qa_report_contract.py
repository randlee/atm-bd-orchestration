"""qa-report (consumer) reads exactly the logs qa-template step j (producer) writes.

Step j is rendered, its two jq programs are executed to produce real rows, and
every path, sort key and column qa-report/SKILL.md names must exist in them.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from subprocess_helpers import HANG_GUARD_SECONDS, run_command

from test_templates import ROOT, _example, _render

QA_REPORT = ROOT.parent / "qa-report" / "SKILL.md"


def _step_j(values: dict) -> str:
    result = _render("qa-template.xml.j2", values)
    if result.returncode:
        raise AssertionError(result.stderr)
    text = result.stdout[result.stdout.index('<step id="j">'):]
    start = text.index("```")
    return text[start:text.index("```", start + 3)]


def _produce(step: str, workdir: Path, findings: list[dict] | None = None,
             bd_rows: list[dict] | None = None, blocking: dict | None = None,
             screened: list[dict] | None = None) -> tuple[dict, dict]:
    """Run step j's count lines and two row writers on real finding rows (bd replaced by `bd_rows`)."""
    counts = step[step.index("FNDFILE="):step.index("TESTED=")].replace("<scratch>", str(workdir))
    round_cmd = step[step.index("ROW=$(jq -nc"):step.index("\n\nTOTAL_FILED=")]
    stats_cmd = step[step.index("TOTAL_FILED="):].rstrip()
    (workdir / "bd-list.json").write_text(json.dumps(bd_rows or []))
    stats_cmd = stats_cmd.replace("bd list --all --json 2>/dev/null", "cat bd-list.json", 1)
    if findings:
        task = step[step.index("FNDFILE=<scratch>/") + len("FNDFILE=<scratch>/"):step.index("-findings.jsonl")]
        (workdir / f"{task}-findings.jsonl").write_text("".join(json.dumps(f) + "\n" for f in findings))
    if blocking:
        task = step[step.index("BLKFILE=<scratch>/") + len("BLKFILE=<scratch>/"):step.index("-blocking.json")]
        (workdir / f"{task}-blocking.json").write_text(json.dumps(blocking))
    if screened is not None:
        task = step[step.index("SCREENFILE=<scratch>/") + len("SCREENFILE=<scratch>/"):step.index("-screen.json")]
        (workdir / f"{task}-screen.json").write_text(json.dumps({"success": True, "data": {"screened": screened}}))
    env = {**os.environ, "NOW": "2026-10-02T12:00:00Z", "LOCAL": "05:00", "DURATION": "3m",
           "VERDICT": "PASS", "TESTED": "x"}
    script = "set -eu\nmkdir -p .sc/qa-log\n" + counts + "\n" + round_cmd + "\n" + stats_cmd + "\n"
    run_command(["bash", "-c", script], timeout=HANG_GUARD_SECONDS, cwd=workdir, env=env, check=True, capture_output=True, text=True)
    logs = workdir / ".sc/qa-log"
    round_rows = (logs / "phase-d.jsonl").read_text().splitlines()
    stats_rows = (logs / "phase-d-stats.jsonl").read_text().splitlines()
    assert len(round_rows) == 1 and len(stats_rows) == 1, (round_rows, stats_rows)
    return json.loads(round_rows[0]), json.loads(stats_rows[0])


def _produce_plan(workdir: Path, screened: list[dict]) -> tuple[dict, dict]:
    values = _concrete(_example("plan-review-template-vars.json"))
    result = _render("plan-review-template.xml.j2", values)
    assert result.returncode == 0, result.stderr
    step = result.stdout[result.stdout.index('<step id="g">'):]
    commands = step[step.index("SCREENFILE="):step.index("\n```", step.index("SCREENFILE="))]
    commands = commands.replace("<scratch>", str(workdir)).replace("bd list --all --json 2>/dev/null", "cat bd-list.json", 1)
    (workdir / f"{values['task_id']}-screen.json").write_text(json.dumps({"success": True, "data": {"screened": screened}}))
    env = {**os.environ, "NOW": "2026-10-02T12:01:00Z", "LOCAL": "05:01", "VERDICT": "FAIL"}
    run_command(["bash", "-c", "set -eu\n" + commands], timeout=HANG_GUARD_SECONDS, cwd=workdir, env=env, check=True, capture_output=True, text=True)
    logs = workdir / ".sc/qa-log"
    return (json.loads((logs / "phase-d.jsonl").read_text().splitlines()[-1]),
            json.loads((logs / "phase-d-stats.jsonl").read_text().splitlines()[-1]))


def _concrete(values: dict) -> dict:
    """An example var file with its install-time bead prefix placeholder filled, as installed."""
    return json.loads(json.dumps(values).replace("{{ " + "bead_prefix }}", "p"))


def _finding(n: int, severity: str, screen: str) -> dict:
    """A finding row exactly as qa-template step g renders it from finding-bead.json.j2."""
    values = {**_concrete(_example("finding-bead-vars.json")), "id": f"p-d-4-qa1-f{n}", "severity": severity, "screen": screen}
    result = _render("finding-bead.json.j2", values)
    if result.returncode:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


def _columns(skill: str, log_label: str) -> list[str]:
    block = re.search(rf"\*\*{log_label}[^*]*\*\*.*?columns(.*?)\.\n", skill, re.S)
    if block is None:
        raise AssertionError(f"qa-report/SKILL.md has no column list for {log_label}")
    return re.findall(r"`([a-z_]+)`", block.group(1))


class QaReportReadsWhatStepJWrites(unittest.TestCase):
    def setUp(self):
        self.skill = QA_REPORT.read_text()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_paths_sort_keys_and_columns_exist_in_the_produced_rows(self):
        for example in ("qa-template-vars.json", "qa-template-fix-round-vars.json"):
            with self.subTest(example=example):
                values = _concrete(_example(example))
                self.assertEqual(values["phase"], "d")
                workdir = Path(self.tmp.name) / example
                workdir.mkdir()
                round_row, stats_row = _produce(_step_j(values), workdir)

                # Paths: qa-report's directory and file patterns name the files step j appends to.
                self.assertIn("`.sc/qa-log/`", self.skill)
                self.assertIn("(`phase-<p>.jsonl`, \"Log B\")", self.skill)
                self.assertIn("(`phase-<p>-stats.jsonl`, \"Log A\")", self.skill)

                # Sort keys.
                self.assertIn("Log A by `snapshot_at`", self.skill)
                self.assertIn("Log B by `completed_at`", self.skill)
                self.assertIn("snapshot_at", stats_row)
                self.assertIn("completed_at", round_row)

                # Columns.
                stats_columns = _columns(self.skill, "Log A")
                round_columns = _columns(self.skill, "Log B")
                self.assertEqual(stats_columns, ["snapshot_local", "tot", "open", "blk", "imp", "min", "trigger_task"])
                self.assertEqual(round_columns, ["completed_local", "task", "sprint", "tested", "iteration", "verdict",
                                                 "blk", "imp", "min", "fnd", "duration", "pr_number"])
                self.assertEqual([c for c in stats_columns if c not in stats_row], [])
                self.assertEqual([c for c in round_columns if c not in round_row], [])

                # The display shortening keys off qa-pr<number> in the task id step j records.
                self.assertEqual(round_row["task"], values["task_id"])
                self.assertEqual(stats_row["trigger_task"], values["task_id"])


    def test_counts_come_from_real_finding_rows(self):
        # step g: the blocking finding is poured (blocking file), the others are finding beads
        findings = [_finding(2, "minor", "not_applicable"), _finding(3, "important", "ceremony")]
        blocking = {"sprint": "p-d-4", "round": 1, "filed_by": "p-d-4.group-qa", "found_at_commit": "abc1234",
                    "findings": [{"ref": "qa1-f1", "severity": "blocking", "reviewer": "r", "title": "t",
                                  "remedy": "m", "priority": 1}]}
        closed = {**findings[1], "status": "closed"}
        sanity_child = {**_finding(1, "blocking", "keep"), "id": "p-d-4.1"}  # a sanity child of the dev bead
        sanity_child["metadata"] = {**sanity_child["metadata"], "sanity_finding": True}
        other_phase = {**_finding(4, "blocking", "keep"), "metadata": {**findings[0]["metadata"], "phase": "e"}}

        def fix(n: int, status: str) -> dict:   # a poured fix bead of finding qa1-f1, round n
            return {"id": f"p-d-4.qa1-f1-r{n}-fix", "status": status, "labels": ["phase-d", "stage:fix"],
                    "metadata": {"phase": "d", "sprint_bead": "p-d-4", "finding_ref": "qa1-f1", "round": n,
                                 "severity": "blocking"}}
        workdir = Path(self.tmp.name) / "real"
        workdir.mkdir()
        round_row, stats_row = _produce(_step_j(_concrete(_example("qa-template-vars.json"))), workdir, findings,
                                        [findings[0], closed, sanity_child, other_phase, fix(1, "closed"), fix(2, "open")],
                                        blocking)
        self.assertEqual((round_row["fnd"], round_row["blk"], round_row["imp"], round_row["min"]), (2, 1, 0, 1))
        # one finding per poured fix lineage (its latest round decides open), plus the finding beads
        self.assertEqual({k: stats_row[k] for k in ("tot", "open", "blk", "imp", "min")},
                         {"tot": 3, "open": 2, "blk": 1, "imp": 0, "min": 1})

    def test_cumulative_screening_rates_cover_qa_and_plan_review(self):
        workdir = Path(self.tmp.name) / "both"
        workdir.mkdir()
        qa, qa_stats = _produce(_step_j(_concrete(_example("qa-template-vars.json"))), workdir,
                                screened=[{"id": "q1", "verdict": "ceremony"}, {"id": "q2", "verdict": "keep"}])
        plan, stats = _produce_plan(workdir, [{"id": "p1", "verdict": "ceremony"},
                                             {"id": "p2", "verdict": "not_applicable"},
                                             {"id": "p3", "verdict": "keep"}])
        self.assertEqual((qa["kind"], qa["round"], qa["findings_filed"], qa["findings_screened_out"], qa["screened_ids"]),
                         ("qa", 1, 2, 1, ["q1"]))
        self.assertEqual((qa_stats["findings_filed"], qa_stats["findings_screened_out"]), (2, 1))
        self.assertEqual((plan["kind"], plan["round"], plan["findings_filed"], plan["findings_screened_out"], plan["screened_ids"]),
                         ("plan-review", 1, 3, 1, ["p1"]))
        self.assertEqual((stats["findings_filed"], stats["findings_screened_out"]), (5, 2))
        self.assertIn("findings_screened_out/findings_filed", self.skill)
        self.assertIn("missing screening fields display `n/a`", self.skill)

    def test_invalid_screen_verdict_cannot_be_logged_as_zero(self):
        workdir = Path(self.tmp.name) / "invalid"
        workdir.mkdir()
        with self.assertRaises(subprocess.CalledProcessError) as error:
            _produce(_step_j(_concrete(_example("qa-template-vars.json"))), workdir,
                     screened=[{"id": "q1", "verdict": "invalid"}])
        self.assertIn("SCREEN.UNAVAILABLE", error.exception.stderr)
        self.assertFalse((workdir / ".sc/qa-log/phase-d.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
