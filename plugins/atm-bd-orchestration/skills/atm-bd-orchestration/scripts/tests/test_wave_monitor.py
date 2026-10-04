from __future__ import annotations

from contextlib import redirect_stdout
import importlib.machinery
import importlib.util
import io
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).parents[1]
sys.path.insert(0, str(SCRIPTS))
LOADER = importlib.machinery.SourceFileLoader("wave_monitor", str(SCRIPTS / "wave-monitor"))
SPEC = importlib.util.spec_from_loader("wave_monitor", LOADER)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

ROOT = "myp-phase-d"


def bead(id, parent, status="closed", labels=(), close_reason="", notes="", **metadata):
    return {"id": id, "parent": parent, "status": status, "labels": ["phase-d", *labels],
            "close_reason": close_reason, "notes": notes, "metadata": metadata}


def sprint(n, wave, *, dev=None, sanity=None, qa="closed", sanity_reason=None, notes=""):
    """A sprint container and its group; `dev` is the dev step's integration metadata."""
    s = f"myp-d-{n}"
    head = (dev or {}).get("stack_head", "")
    return [
        bead(s, ROOT, "open", ["stage:sprint", f"wave:{wave}"], wave=wave, sprint=f"d-{n}"),
        bead(f"{s}.group-dev", s, "closed", notes=notes, role="dev", sprint_bead=s, **(dev or {})),
        bead(f"{s}.group-sanity", s, sanity or "closed", (),
             sanity_reason or f"PASS at {head}", sprint_bead=s, dev_bead=f"{s}.group-dev"),
        bead(f"{s}.group-qa", s, qa, role="qa", sprint_bead=s, checked_bead=f"{s}.group-dev"),
    ]


def finding(id, parent, severity, status="open", close_reason="", **metadata):
    return bead(id, parent, status, ["stage:finding", f"severity:{severity}"], close_reason, severity=severity, **metadata)


def phase_beads():
    return [
        *sprint(30, 1, dev={"stack_head": "h30", "sanity_pass_commit": "h30"}),  # complete
        *sprint(31, 1, sanity="open"),  # dev closed, never integrated
        *sprint(32, 1, dev={"stack_head": "h32", "sanity_pass_commit": "h32old"}, sanity_reason="PASS at h32old",
                notes="restack: h32old -> h32"),
        *sprint(33, 1, dev={"stack_head": "h33", "sanity_pass_commit": "h33"}, qa="open"),
        *sprint(34, 1, dev={"stack_head": "h34", "sanity_pass_commit": "h34"}),
        bead("myp-d-34.qa1-f1-r1-fix", "myp-d-34", "open", role="fix", severity="blocking", sprint_bead="myp-d-34"),
        *sprint(40, 2),  # another wave, not integrated
        # an important finding left open by its fixer, with sanity and QA at its head
        finding("myp-phase-d-f1", ROOT, "important", fixed_at_commit="hf1", exec_wave=1, stack_head="hf1",
                sanity_pass_commit="hf1", sprint_bead="myp-d-30"),
        bead("myp-phase-d-f1-sanity", "myp-phase-d-f1", "closed", ["stage:dev-sanity"], "PASS at hf1", dev_bead="myp-phase-d-f1"),
        bead("myp-phase-d-f1-qa", "myp-phase-d-f1", "closed", ["stage:qa"], "PASS", commit="hf1", checked_bead="myp-phase-d-f1"),
        finding("myp-phase-d-f2", ROOT, "minor"),
        finding("myp-phase-d-f3", ROOT, "important", status="closed", close_reason="fixed at abc"),
        # a planned sanity bead beside its dev bead (dev-sanity-bead.json.j2), never integrated
        bead("myp-d-8", ROOT, "closed", ["stage:dev", "stage:sprint"], sanity_pass_commit="c8"),
        bead("myp-d-8-sanity", ROOT, "closed", ["stage:dev-sanity"], "PASS at c8 by lead ruling", dev_bead="myp-d-8"),
        bead("myp-d-9-sanity", ROOT, "closed", ["stage:dev-sanity"], "PASS at c9", dev_bead="myp-d-9"),
    ]


CLOCK = itertools.count()


def run(task, sprint, iteration, verdict, findings=0, commit="c0", pr=500, jev=None):
    """One sanity run as sanity-run-history appends it: an LLM row then a JEV row, sharing run_id and final_verdict."""
    run_id = f"{task}-{iteration}"
    out = []
    for reviewer, (own_verdict, own_findings) in (("sanity-llm", (verdict, findings)), ("sanity-jev", jev or (verdict, findings))):
        minute = next(CLOCK)
        out.append({"run_id": run_id, "reviewer": reviewer, "commit": commit, "task": task, "sprint": sprint,
                    "phase": "d", "pr_number": pr, "findings": own_findings, "verdict": own_verdict, "error": None,
                    "final_verdict": verdict, "iteration": iteration, "started_at": f"2026-09-29T00:{minute:02d}:00Z",
                    "completed_at": f"2026-09-29T00:{minute:02d}:30Z", "completed_local": f"09-29 00:{minute:02d}",
                    "duration": "0m30s", "duration_seconds": 30})
    return out


LEDGER = [
    *run("myp-d-8-sanity", "d-8", 1, "FAIL", 3, commit="c8a"),
    *run("myp-d-8-sanity", "d-8", 2, "FAIL", 2, commit="c8b"),
    *run("myp-d-8-sanity", "d-8", 3, "FAIL", 1, commit="c8c"),
    *run("myp-d-7-sanity", "d-7", 2, "PASS", 1, commit="c7"),
    *run("myp-d-30.group-sanity", "d-30", 1, "PASS", commit="h30"),
    *run("myp-d-32.group-sanity", "d-32", 4, "PASS", commit="h32old"),
    *run("myp-d-33.group-sanity", "d-33", 1, "PASS", commit="h33"),
    *run("myp-d-34.group-sanity", "d-34", 1, "PASS", commit="h34", jev=("FAIL", 2)),  # JEV disagreed; dev-sanity chose PASS
    *run("myp-phase-d-f1-sanity", "d-30", 1, "PASS", commit="hf1"),
]


class FakeRunner:
    def __init__(self, common_dir, beads, fail_bd=False):
        self.common_dir, self.beads, self.fail_bd = common_dir, beads, fail_bd

    def __call__(self, args, **kwargs):
        if args[0] == "bd" and self.fail_bd:
            return subprocess.CompletedProcess(args, 1, "", "dolt server unreachable")
        if args[:2] == ["bd", "show"]:
            return subprocess.CompletedProcess(args, 0, json.dumps([bead(ROOT, None, "open", [], phase="d")]), "")
        if args[:2] == ["bd", "list"]:
            assert args[args.index("--label") + 1] == "phase-d"
            return subprocess.CompletedProcess(args, 0, json.dumps(self.beads), "")
        if args[:2] == ["git", "rev-parse"]:
            return subprocess.CompletedProcess(args, 0, str(self.common_dir) + "\n", "")
        return subprocess.run(args, **kwargs)  # sc-compose renders the real template


class WaveMonitorTests(unittest.TestCase):
    def monitor(self, *argv, ledger=LEDGER, beads=None, fail_bd=False):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / ".sc" / "sanity-log" / "phase-d.jsonl"
            log.parent.mkdir(parents=True)
            log.write_text(ledger if isinstance(ledger, str) else "".join(json.dumps(r) + "\n" for r in ledger))
            out = io.StringIO()
            with redirect_stdout(out):
                code = module.main(["--root", ROOT, *argv], FakeRunner(Path(tmp) / ".git", phase_beads() if beads is None else beads, fail_bd))
        return code, out.getvalue()

    def section(self, text, title):
        body = text.split(f"## {title}", 1)[1]
        return body.split("\n## ", 1)[0]

    def test_table_is_rendered_newest_run_first_two_rows_each_with_timezone(self):
        code, text = self.monitor("--limit", "3")
        self.assertEqual(code, 0)
        table = [line for line in self.section(text, "Sanity runs").splitlines() if line.startswith("| ")]
        self.assertEqual(table[0], "| S | PR | R | Find | Result | Match | Done | Iter |")
        self.assertEqual([l.split(" | ")[:6] + [l.split(" | ")[-1]] for l in table[1:]],
                         [["| d-30", "#500", "LLM", "0", "✅", "✓", "1 |"],
                          ["| d-30", "#500", "JEV", "0", "✅", "✓", "1 |"],
                          ["| d-34", "#500", "LLM", "0", "✅", "✓", "1 |"],
                          ["| d-34", "#500", "JEV", "2", "❌", "✗", "1 |"],
                          ["| d-33", "#500", "LLM", "0", "✅", "✓", "1 |"],
                          ["| d-33", "#500", "JEV", "0", "✅", "✓", "1 |"]])
        self.assertRegex(text, r"Done is local time: \S+ \(UTC[+-]\d\d:\d\d\)")

    def test_iteration_signals_for_each_threshold(self):
        _, text = self.monitor()
        signals = self.section(text, "Iteration signals")
        self.assertIn("separate from SANITY.ROUND_CAP", signals)
        self.assertIn("- **PROBLEM**: myp-d-32.group-sanity (d-32) iteration 4", signals)
        self.assertEqual(signals.count("myp-d-8-sanity (d-8) iteration 2"), 1)  # one line per run, not per reviewer row
        self.assertIn("- investigate: myp-d-8-sanity (d-8) iteration 3 FAIL", signals)
        self.assertIn("- suspect: myp-d-8-sanity (d-8) iteration 2 FAIL findings 2", signals)
        self.assertNotIn("myp-d-7-sanity", signals)  # iteration 2 with one finding
        self.assertNotIn("iteration 1", signals)  # iteration 1 FAIL is normal

    def test_ledger_missing_and_stale_rows(self):
        _, text = self.monitor()
        lines = self.section(text, "Ledger reconciliation").splitlines()
        self.assertIn("- missing: myp-d-9-sanity closed (PASS at c9) with no ledger row", lines)
        self.assertIn("- stale: myp-d-8-sanity ledger verdict FAIL but close reason 'PASS at c8 by lead ruling'", lines)
        self.assertIn("- stale: myp-d-32.group-sanity PASS but myp-d-32.group-dev sanity_pass_commit h32old is not stack_head h32", lines)
        self.assertFalse([l for l in lines if "myp-d-30.group-sanity" in l or "myp-phase-d-f1-sanity" in l])

    def test_run_verdict_is_final_verdict(self):
        _, text = self.monitor()
        lines = self.section(text, "Ledger reconciliation").splitlines()
        self.assertFalse([l for l in lines if "myp-d-34" in l])  # the JEV FAIL row does not contradict the PASS close

    def test_reads_a_ledger_written_by_sanity_run_history(self):
        sha = "a" * 40
        rows = [dict(r, commit=sha) for r in run("myp-d-30.group-sanity", "d-30", 1, "PASS", commit=sha)]
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / ".sc" / "sanity-log" / "phase-d.jsonl"
            for r in rows:
                module.HISTORY.append_record(log, r)   # the writer's own validation and locked append
            out = io.StringIO()
            with redirect_stdout(out):
                code = module.main(["--root", ROOT], FakeRunner(Path(tmp) / ".git", phase_beads()))
        self.assertEqual(code, 0)
        table = [l for l in self.section(out.getvalue(), "Sanity runs").splitlines() if l.startswith("| d-30")]
        self.assertEqual([l.split(" | ")[2] for l in table], ["LLM", "JEV"])

    def test_malformed_ledger_exits_2(self):
        code, text = self.monitor(ledger=json.dumps(LEDGER[0]) + "\n{not json\n")
        self.assertEqual((code, text), (2, ""))

    def test_each_handoff_stage(self):
        _, text = self.monitor("--wave", "1")
        handoffs = self.section(text, "Handoffs: wave 1").splitlines()
        self.assertIn("- myp-d-31.group-dev: missing integrated", handoffs)
        self.assertIn("- myp-d-32.group-dev: missing sanity", handoffs)
        self.assertIn("- stale: myp-d-32.group-dev restacked h32old -> h32; sanity_pass_commit h32old", handoffs)
        self.assertIn("- myp-d-33.group-dev: missing qa", handoffs)
        self.assertIn("- myp-d-34.group-dev: missing findings", handoffs)
        self.assertIn("- 2 complete", handoffs)  # myp-d-30.group-dev and the fixed important finding
        self.assertFalse([l for l in handoffs if "myp-d-40" in l or "myp-d-8" in l or "myp-phase-d-f3" in l])

    def test_whole_phase_includes_other_waves_and_closed_fixed_findings(self):
        _, text = self.monitor()
        handoffs = self.section(text, "Handoffs: whole phase").splitlines()
        self.assertIn("- myp-d-40.group-dev: missing integrated", handoffs)
        self.assertIn("- myp-phase-d-f3: missing integrated", handoffs)

    def test_qa_bead_at_head_satisfies_a_group_step_with_open_qa(self):
        beads = phase_beads() + [bead("myp-d-33-qa-r2", "myp-d-33.group-dev", "closed", ["stage:qa"], commit="h33",
                                      checked_bead="myp-d-33.group-dev")]
        _, text = self.monitor("--wave", "1", beads=beads)
        self.assertNotIn("myp-d-33.group-dev: missing", text)

    def test_open_verification_of_a_closed_fix_still_holds_the_sprint(self):
        beads = [b for b in phase_beads() if b["id"] != "myp-d-34.qa1-f1-r1-fix"] + [
            bead("myp-d-34.qa1-f1-r1-fix", "myp-d-34", "closed", role="fix", severity="blocking", finding_ref="qa1-f1",
                 sprint_bead="myp-d-34"),
            bead("myp-d-34.qa1-f1-r1-sanity", "myp-d-34", "closed", (), "PASS", dev_bead="myp-d-34.qa1-f1-r1-fix"),
            bead("myp-d-34.qa1-f1-r1-qa", "myp-d-34", "open", role="qa", finding_ref="qa1-f1", reviewer="rbp",
                 checked_bead="myp-d-34.qa1-f1-r1-fix", sprint_bead="myp-d-34")]
        _, text = self.monitor("--wave", "1", beads=beads)
        handoffs = self.section(text, "Handoffs: wave 1").splitlines()
        self.assertIn("- myp-d-34.group-dev: missing findings", handoffs)
        self.assertIn("- myp-d-34.qa1-f1-r1-fix: missing integrated", handoffs)  # a fix step is a handoff of its sprint's wave

    def test_sprint_whose_wave_label_disagrees_is_in_no_wave(self):
        beads = [dict(b, labels=["phase-d", "stage:sprint", "wave:2"]) if b["id"] == "myp-d-31" else b for b in phase_beads()]
        _, text = self.monitor("--wave", "1", beads=beads)
        self.assertNotIn("myp-d-31.group-dev", self.section(text, "Handoffs: wave 1"))
        _, text = self.monitor("--wave", "2", beads=beads)
        self.assertNotIn("myp-d-31.group-dev", self.section(text, "Handoffs: wave 2"))

    def test_open_finding_counts_by_severity(self):
        _, text = self.monitor()
        self.assertIn("- important: 1\n- minor: 1", self.section(text, "Open findings under the root"))

    def test_bd_failure_exits_2(self):
        code, text = self.monitor(fail_bd=True)
        self.assertEqual((code, text), (2, ""))


if __name__ == "__main__":
    unittest.main()
