"""lite cron decide (scripts/atm-bd-cron.py) against real wheel records: intent.md, "The close contract"."""
import atm_bd_types as T
from conftest import LEAD, QA, bead, load_hook, phase_file

S = T.Status
CRON = load_hook("atm-bd-cron")
PARAMS = T.Params([("qa_agent", QA), ("qa_template", "templates/qa.md.j2")])


def facts(*ready, read_failed: bool = False):
    return T.PhaseFacts("bo", 0, phase_file(lead=LEAD), ready=None if read_failed else list(ready))


def test_released_qa_bead_is_assigned_to_qa_agent() -> None:
    assert CRON.decide(facts(bead("q", stage="qa")), PARAMS) == [
        T.Assign("assign:q", QA, "q", "templates/qa.md.j2", T.AssignVars("q", "bo", "lite"))]


def test_held_closed_or_non_qa_beads_are_left_alone() -> None:
    ready = (bead("held", stage="qa", assignee=QA), bead("running", S.IN_PROGRESS, stage="qa"),
             bead("done", S.CLOSED, stage="qa"), bead("dev", stage="dev"))
    assert CRON.decide(facts(*ready), PARAMS) == []


def test_failed_ready_read_decides_nothing() -> None:
    assert CRON.decide(facts(read_failed=True), PARAMS) == []


def test_missing_params_report_instead_of_assigning() -> None:
    reply = CRON.decide(facts(bead("q", stage="qa")), T.Params([("qa_agent", QA)]))
    assert [type(action) for action in reply] == [T.Report] and reply[0].key == "cron:params"
