from __future__ import annotations

from contextlib import redirect_stdout
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).parents[1]
sys.path.insert(0, str(SCRIPTS))
LOADER = importlib.machinery.SourceFileLoader("sprint_closable", str(SCRIPTS / "sprint-closable"))
SPEC = importlib.util.spec_from_loader("sprint_closable", LOADER)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

SPRINT = "myp-d-30"


def bead(id, parent, status="closed", labels=(), **metadata):
    return {"id": id, "parent": parent, "status": status, "labels": list(labels), "metadata": metadata}


def group(dev="closed", sanity="closed", qa="closed"):
    return [
        bead(f"{SPRINT}.group-dev", SPRINT, status=dev, role="dev"),
        bead(f"{SPRINT}.group-sanity", SPRINT, status=sanity),
        bead(f"{SPRINT}.group-qa", SPRINT, status=qa, role="qa"),
    ]


def finding(id, parent, severity, status="open"):
    return bead(id, parent, status=status, labels=["stage:finding", f"severity:{severity}"], severity=severity)


class FakeBd:
    """Answers `bd show` and `bd list --parent` from a flat bead list, as bd returns direct children."""

    def __init__(self, rows, fail=False):
        self.rows, self.fail = rows, fail

    def __call__(self, args, **kwargs):
        if self.fail:
            return subprocess.CompletedProcess(args, 1, "", "dolt server unreachable")
        if args[:2] == ["bd", "show"]:
            return subprocess.CompletedProcess(args, 0, json.dumps([bead(SPRINT, "myp-phase-d", "open", ["stage:sprint"])]), "")
        parent = args[args.index("--parent") + 1]
        return subprocess.CompletedProcess(args, 0, json.dumps([r for r in self.rows if r["parent"] == parent]), "")


def closable(rows, fail=False):
    out = io.StringIO()
    with redirect_stdout(out):
        code = module.main([SPRINT], FakeBd(rows, fail))
    return code, out.getvalue().splitlines()


class SprintClosableTests(unittest.TestCase):
    def test_closed_group_without_blocking_findings_is_closable(self):
        rows = group() + [finding(f"{SPRINT}-qa-f1", SPRINT, "blocking", status="closed")]
        self.assertEqual(closable(rows), (0, ["closable"]))

    def test_open_step_is_reported(self):
        code, lines = closable(group(qa="open"))
        self.assertEqual(code, 1)
        self.assertEqual(lines, [f"qa step {SPRINT}.group-qa is open"])

    def test_open_blocking_finding_under_a_step_is_found_at_depth(self):
        rows = group() + [finding(f"{SPRINT}.group-dev.1", f"{SPRINT}.group-dev", "blocking", status="in_progress")]
        code, lines = closable(rows)
        self.assertEqual(code, 1)
        self.assertEqual(lines, [f"blocking finding {SPRINT}.group-dev.1 is in_progress (parent {SPRINT}.group-dev)"])

    def test_open_important_and_minor_findings_hold_the_sprint(self):  # bd refuses a parent with an open child
        rows = group() + [finding(f"{SPRINT}-qa-f2", SPRINT, "important"), finding(f"{SPRINT}-qa-f3", SPRINT, "minor")]
        self.assertEqual(closable(rows), (1, [f"important finding {SPRINT}-qa-f2 is open (parent {SPRINT})",
                                              f"minor finding {SPRINT}-qa-f3 is open (parent {SPRINT})"]))

    def test_sprint_without_a_group(self):
        self.assertEqual(closable([finding(f"{SPRINT}-qa-f1", SPRINT, "blocking")]), (1, ["no sprint group"]))

    def test_bd_failure_exits_2(self):
        self.assertEqual(closable(group(), fail=True), (2, []))


SKILL = SCRIPTS.parent
ATM_BEADS = SKILL.parent / "atm-beads"
MISSING = [tool for tool in ("bd", "dolt", "sc-compose") if shutil.which(tool) is None]


def clean_env() -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("BEADS_", "BD_"))}
    env.update({"BD_NON_INTERACTIVE": "1", "BEADS_ACTOR": "closable-test"})
    return env


def stop_server(root: Path) -> None:
    subprocess.run(["bd", "dolt", "stop"], cwd=root, env=clean_env(), capture_output=True)
    marker = str(root / ".beads" / "dolt")
    for line in subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True).stdout.splitlines():
        pid, _, command = line.strip().partition(" ")
        if marker in command:
            try:
                os.kill(int(pid), signal.SIGTERM)
            except (ProcessLookupError, ValueError):
                pass


@unittest.skipIf(MISSING, f"{', '.join(MISSING)} not on PATH: real-bd sprint-closable tests not run")
class SprintClosableRealBdTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = root = Path(tempfile.mkdtemp(prefix="sprint-closable-")).resolve()
        cls.env = clean_env()
        cls.addClassCleanup(shutil.rmtree, root, ignore_errors=True)
        cls.addClassCleanup(stop_server, root)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        cls.bd("init", "--prefix", "t", "--proxied-server", "--non-interactive", "--quiet", "--skip-agents", "--skip-hooks")
        (root / ".beads" / "formulas").mkdir(exist_ok=True)
        ignore = shutil.ignore_patterns("__pycache__", "tests")
        shutil.copytree(SKILL, root / ".claude/skills/atm-bd-orchestration", ignore=ignore)
        shutil.copytree(ATM_BEADS, root / ".claude/skills/atm-beads", ignore=ignore)
        config = root / ".claude/project/atm-bd-orchestration.yaml"
        config.parent.mkdir(parents=True)
        config.write_text("bead_prefix: t\ndev_sanity_member: dev-sanity\nqa_member: quality-mgr\nplans_dir: docs/plans\n")
        cls.scripts = root / ".claude/skills/atm-bd-orchestration/scripts"

    @classmethod
    def run_cmd(cls, *argv, check=True):
        proc = subprocess.run([str(a) for a in argv], cwd=cls.root, env=cls.env, text=True, capture_output=True)
        if check and proc.returncode:
            raise AssertionError(f"{argv} exited {proc.returncode}\nstdout: {proc.stdout}\nstderr: {proc.stderr}")
        return proc

    @classmethod
    def bd(cls, *args, check=True):
        return cls.run_cmd("bd", *args, check=check)

    def close(self, bead, reason="done", check=True):
        assignee = json.loads(self.bd("show", bead, "--json").stdout)[0].get("assignee") or self.env["BEADS_ACTOR"]
        return self.bd("close", bead, "--reason", reason, "--actor", assignee, check=check)

    def sprint(self, phase: str) -> str:
        bead = f"t-{phase}-1"
        meta = {"phase": phase, "sprint": f"{phase}-1", "stack": f"phase-{phase}", "layer": 1, "difficulty": "normal"}
        self.bd("create", f"{phase}-1: sprint", "--id", bead, "--type", "feature",
                "--metadata", json.dumps(meta), "--silent")          # planned: difficulty, no assignee
        self.bd("update", bead, "--assignee", "arch-dev")           # dispatch picks the dev
        plan = self.root / "docs/plans" / f"phase-{phase}" / "sprints.jsonl"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text(json.dumps([f"{phase}-1", f"{bead}.group-sanity", []]) + "\n")
        self.run_cmd(sys.executable, self.scripts / "bead-groups", "--json", "--sprint", bead)
        return bead

    def pour_finding(self, sprint: str, ref: str) -> list[str]:
        path = self.root / f"findings-{sprint}-{ref}.json"
        path.write_text(json.dumps({"sprint": sprint, "round": 1, "filed_by": f"{sprint}.group-qa", "findings": [
            {"ref": ref, "severity": "blocking", "reviewer": "rbp", "title": "unchecked error",
             "remedy": "return the typed error", "priority": 1}]}))
        self.run_cmd(sys.executable, self.scripts / "bead-groups", "--json", "--findings", path)
        return [f"{sprint}.{ref}-r1-{step}" for step in ("fix", "sanity", "qa")]

    def closable(self, sprint: str):
        proc = self.run_cmd(sys.executable, self.scripts / "sprint-closable", sprint, check=False)
        return proc.returncode, proc.stdout.splitlines()

    def test_closable_when_every_child_is_closed(self):
        sprint = self.sprint("p")
        code, lines = self.closable(sprint)
        self.assertEqual(code, 1)
        self.assertEqual(lines, [f"dev step {sprint}.group-dev is open", f"sanity step {sprint}.group-sanity is open",
                                 f"qa step {sprint}.group-qa is open"])
        for step in ("dev", "sanity", "qa"):
            self.close(f"{sprint}.group-{step}")
        self.assertEqual(self.closable(sprint), (0, ["closable"]))
        self.close(sprint, "sprint-closable: closable")           # bd agrees: the close succeeds
        self.assertEqual(json.loads(self.bd("show", sprint, "--json").stdout)[0]["status"], "closed")

    def test_not_closable_with_an_open_poured_fix_group(self):
        sprint = self.sprint("q")
        self.close(f"{sprint}.group-dev")
        self.close(f"{sprint}.group-sanity", "PASS")
        fix, fix_sanity, fix_qa = self.pour_finding(sprint, "qa1-f1")   # quality-mgr pours before closing its QA bead
        self.close(f"{sprint}.group-qa", "FAIL: 1 blocking finding poured")
        self.close(fix, "fixed at abc123")
        code, lines = self.closable(sprint)
        self.assertEqual((code, lines), (1, [f"qa {fix_qa} is open (parent {sprint})",
                                             f"sanity {fix_sanity} is open (parent {sprint})"]))
        refused = self.close(sprint, "early", check=False)            # bd refuses the same close
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("open child", refused.stderr)
        self.close(fix_sanity, "PASS")
        self.close(fix_qa, "verified by rbp")
        self.assertEqual(self.closable(sprint), (0, ["closable"]))

    def test_missing_sprint_exits_2(self):
        code, _ = self.closable("t-nope-1")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
