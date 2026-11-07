"""The dev close of a sprint split into subtask beads (stage:subtask children `<sprint>.sub-<n>`).

Mixed into the close hook: it discovers each child's sanity task, refuses a close while a child is open, and on close
assigns the children's sanity tasks in place of the sprint's own (the sanity hook releases that one when the last child passes).
"""

from __future__ import annotations

import re
from typing import Any

import close_fields
from task_close_validation import ASSIGNMENT_EVENTS, CloseError


TERMINAL_STATES = frozenset(("complete",))  # as atm-task-close.py


def is_terminal(events):
    return bool(events) and events[-1].get("to_state") in TERMINAL_STATES


class SubtaskClose:
    """Mixed into Hook (atm-task-close.py), which supplies every attribute and method named here."""

    assign: Any
    assignment_id: Any
    bead: Any
    child_sanities: Any
    close_bead: Any
    close_task: Any
    config: Any
    events: Any
    json: Any
    lead: Any
    metadata: Any
    pr_base: Any
    read_bead: Any
    sanity_dispatch: Any
    send: Any
    task: Any
    task_history: Any
    update: Any
    values: Any

    def subtask_rows(self, checked):
        """The QA template's `children` for the sprint `checked` belongs to."""
        sprint_bead = (checked.get("metadata") or {}).get("sprint_bead")
        return close_fields.subtask_children(self.json(["bd", "children", sprint_bead, "--json", "--limit", "0"])) if sprint_bead else []

    def discover_child_sanities(self):
        """[(subtask id, its sanity bead)] for the sprint's stage:subtask children, ordered by number; [] when it has none."""
        sprint_bead = (self.read_bead(self.values["checked_bead"]).get("metadata") or {}).get("sprint_bead")
        if not sprint_bead:
            return []
        rows = self.json(["bd", "children", sprint_bead, "--json", "--limit", "0"])
        pattern = re.compile(re.escape(sprint_bead) + r"\.sub-([1-9][0-9]*)")
        found = []
        for row in rows:
            metadata = row.get("metadata") or {}
            match = pattern.fullmatch(str(metadata.get("checked_bead") or ""))
            if "stage:dev-sanity" in (row.get("labels") or []) and match:
                found.append((int(match.group(1)), metadata["checked_bead"], row["id"]))
        return [(child, sanity) for _, child, sanity in sorted(found)]

    def open_subtasks(self):
        """Ids of the sprint's stage:subtask children that are not closed."""
        sprint_bead = (self.bead(self.values["checked_bead"]).get("metadata") or {}).get("sprint_bead")
        if not sprint_bead:
            return []
        rows = self.json(["bd", "children", sprint_bead, "--json", "--limit", "0"])
        return [row["id"] for row in rows if "stage:subtask" in (row.get("labels") or []) and row.get("status") != "closed"]

    def verify_child_sanity(self, sanity, *, allow_pass=False):
        """A subtask's sanity task is assigned to the dev-sanity member (or already closed PASS at this commit)."""
        events = self.task_history[sanity]
        assignments = [event for event in events if event.get("event") in ASSIGNMENT_EVENTS]
        member = self.config["dev_sanity_member"].split("@", 1)[0]
        recipient = assignments[-1].get("assignee") if assignments else None
        state = events[-1].get("to_state") if events else None
        record = self.bead(sanity)
        passed = allow_pass and record.get("status") == "closed" and str(record.get("close_reason", "")).startswith("PASS at ")
        if not (isinstance(recipient, str) and recipient.split("@", 1)[0] == member) or (state not in ("assigned", "active") and not passed):
            raise CloseError("CLOSE.POSTCONDITION", f"{sanity}: expected an assignment to {member} in state assigned or active; "
                             f"observed recipient {recipient!r}, state {state!r}",
                             f"Inspect `atm task events {sanity} --all --json`, assign the subtask sanity task to {member} with the dev-sanity template, then retry.")

    def finish_dev_with_children(self, template, assignment_values):
        """A sprint with subtasks: the dev close assigns each subtask's sanity task and not the sprint's own.

        The sprint's sanity is blocked by every subtask sanity; the sanity hook assigns it when the last one passes.
        """
        values = self.values
        checked = values["checked_bead"]
        assigns = []
        for child, child_sanity in self.child_sanities:
            events = self.task_history[child_sanity]
            terminal = is_terminal(events)
            open_assignment = bool(events) and not terminal
            if open_assignment or (terminal and self.bead(child_sanity).get("status") == "closed"):
                continue
            context = {**assignment_values, "checked_bead": child, "sanity_bead": child_sanity, "sanity_task_id": child_sanity,
                       "task_id": child_sanity}
            assigns.append((child_sanity, self.sanity_dispatch(context)))
        reason = f"dev complete at {values['commit']}"
        checked_record = self.bead(checked)
        # The sprint's base is recorded here so the sprint sanity assignment, sent later by the sanity hook, names it.
        self.metadata(checked, {"commit": assignment_values["commit"], "close_assignment_id": str(self.assignment_id), "branch": assignment_values["branch"],
                                "pr_number": values.get("pr_number", ""), "pr_url": values["pr_url"],
                                "sanity_base": assignment_values.get("rebased_onto") or assignment_values.get("base", ""), **({"pr_base": self.pr_base} if self.pr_base else {})})
        if checked_record.get("status") == "closed" and checked_record.get("close_reason") != reason:
            self.update(checked, status="open")
        self.close_bead(checked, reason)
        if assigns:
            self.send(self.lead, template)
        for child_sanity, dispatch in assigns:
            self.assign(self.config["dev_sanity_member"], child_sanity, "dev-sanity-template.xml.j2", due=True, dispatch=dispatch)
        actual = self.read_bead(checked)
        if actual.get("status") != "closed" or actual.get("close_reason") != reason:
            raise CloseError("CLOSE.POSTCONDITION", f"expected {checked} closed with reason {reason!r}; read status {actual.get('status')!r}, reason {actual.get('close_reason')!r}",
                             f"Inspect `bd show {checked} --json`, repair the state and retry.")
        for _, child_sanity in self.child_sanities:
            self.task_history[child_sanity] = self.events(child_sanity)
            self.verify_child_sanity(child_sanity, allow_pass=True)
        self.close_task(self.task, reason=reason)
