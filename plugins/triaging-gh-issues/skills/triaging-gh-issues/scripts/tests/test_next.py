import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from next import close_agent, main, next_agent, next_patch, role_labels

REPO = {
    "contributor": {"logins": ["repo-dev"]},
    "gates": {
        "whitelist": {"holds": ["pr"]},
        "approver": {"holds": []},
        "priority": {"blocks_above": 1, "holds": ["publish"]},
        "risk": {"labels": ["arch/impact", "security/review"], "holds": ["pr", "publish"]},
    },
}
HOME = {
    "contributor": {"logins": ["known"]},
    "approver": {"logins": ["ada"]},
}


class Roles(unittest.TestCase):
    def test_approver_is_also_contributor(self) -> None:
        self.assertEqual(role_labels("ada", HOME, REPO), ["approver", "contributor"])

    def test_home_or_repo_contributor(self) -> None:
        self.assertEqual(role_labels("known", HOME, REPO), ["contributor"])
        self.assertEqual(role_labels("repo-dev", HOME, REPO), ["contributor"])

    def test_blank_when_unlisted(self) -> None:
        self.assertEqual(role_labels("stranger", HOME, REPO), [])

    def test_repo_approver_key_is_ignored(self) -> None:
        repo = {**REPO, "approver": {"logins": ["sneak"]}}
        self.assertEqual(role_labels("sneak", HOME, repo), [])


class Next(unittest.TestCase):
    def test_import_then_duplicate_then_stop(self) -> None:
        self.assertEqual(next_agent(set(), has_bead=False, priority=None, repo=REPO, pr="", replacement=False)["agent"], "issue-import")
        step = next_agent({"status/needs-triage"}, has_bead=True, priority=1, repo=REPO, pr="", replacement=False)
        self.assertEqual(step["agent"], "issue-duplicate-judge")
        stop = next_agent({"dup/#4"}, has_bead=True, priority=1, repo=REPO, pr="", replacement=False)
        self.assertEqual(stop["stop"], "duplicate")

    def test_phase_done_stops_before_classify(self) -> None:
        labels = {"dup/none", "phase/bo-1", "phase-done/yes"}
        self.assertEqual(next_agent(labels, has_bead=True, priority=1, repo=REPO, pr="", replacement=False)["stop"], "phase-done")

    def test_clean_scan_classifies_then_verifies(self) -> None:
        labels = {"dup/none", "phase/none", "overlap/none", "prpair/none", "contributor"}
        self.assertEqual(next_agent(labels, has_bead=True, priority=1, repo=REPO, pr="", replacement=False)["agent"], "issue-kind-classify")
        labels.update({"kind/bug", "area/product", "size/s", "priority/p1", "status/needs-triage"})
        self.assertEqual(next_agent(labels, has_bead=True, priority=1, repo=REPO, pr="", replacement=False)["agent"], "issue-report-verify")

    def test_gates(self) -> None:
        base = {
            "dup/none", "phase/none", "overlap/none", "prpair/none",
            "kind/bug", "area/product", "size/s", "priority/p1",
            "status/verified", "arch/impact", "security/none", "contributor",
        }
        planned = next_agent(base, has_bead=True, priority=1, repo=REPO, pr="", replacement=False)
        self.assertEqual(planned["agent"], "issue-plan-write")
        opened = base | {"arch/none", "status/planned", "status/plan-accepted"}
        opened.discard("arch/impact")
        self.assertEqual(
            next_agent(opened, has_bead=True, priority=1, repo=REPO, pr="", replacement=False)["stop"],
            "open-pr",
        )
        self.assertEqual(
            next_agent(base | {"status/planned", "status/plan-accepted"}, has_bead=True, priority=1, repo=REPO, pr="", replacement=False)["hold"],
            "risk",
        )
        unlisted = base - {"contributor"}
        self.assertEqual(
            next_agent(unlisted | {"arch/none", "status/planned", "status/plan-accepted"}, has_bead=True, priority=1, repo=REPO, pr="", replacement=False)["hold"],
            "whitelist",
        )

    def test_priority_zero_passes_publish_gate(self) -> None:
        from next import holding

        self.assertIsNone(holding("publish", set(), 0, REPO))
        self.assertEqual(holding("publish", set(), 2, REPO), "priority")
        self.assertIsNone(holding("publish", {"approver"}, 1, REPO))

    def test_empty_approver_holds_do_not_block(self) -> None:
        from next import holding

        self.assertIsNone(holding("plan", set(), 1, REPO))
        repo = json.loads(json.dumps(REPO))
        repo["gates"]["approver"]["holds"] = ["plan"]
        self.assertEqual(holding("plan", set(), 1, repo), "approver")
        self.assertIsNone(holding("plan", {"approver"}, 1, repo))

    def test_close_cron(self) -> None:
        self.assertEqual(close_agent(set(), pr="", commit="", qa_all=False, release_due=False)["agent"], "issue-landed-record")
        self.assertEqual(
            close_agent(set(), pr="9", commit="a" * 40, qa_all=True, release_due=False)["agent"],
            "issue-close-mark",
        )
        self.assertEqual(
            close_agent({"status/close"}, pr="9", commit="a" * 40, qa_all=True, release_due=True)["agent"],
            "issue-release-close",
        )

    def test_patch(self) -> None:
        self.assertEqual(next_patch("0.19.12"), "0.19.13")


class Cli(unittest.TestCase):
    def test_repo_file_required_and_home_logins_not_written(self, tmp: Path | None = None) -> None:
        root = Path(__file__).parent
        home = root / "_home.toml"
        repo = root / "_repo.toml"
        home.write_text("[approver]\nlogins = ['ada']\n[contributor]\nlogins = []\n", encoding="utf-8")
        repo.write_text("[contributor]\nlogins = []\n[gates.whitelist]\nholds = ['pr']\n[gates.approver]\nholds = []\n[gates.priority]\nblocks_above = 1\nholds = ['publish']\n[gates.risk]\nlabels = []\nholds = []\n", encoding="utf-8")
        before = repo.read_text(encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            code = main(["--login", "ada", "--bead", "b1", "--labels", "dup/none,phase/none,overlap/none,prpair/none", "--repo", str(repo), "--home", str(home)])
        self.assertEqual(code, 0)
        self.assertEqual(repo.read_text(encoding="utf-8"), before)
        home.unlink()
        repo.unlink()


if __name__ == "__main__":
    unittest.main()
