# quality-mgr

**ID Range:** REQ-QM-0001 through REQ-QM-0044  
**Version:** 1.0.0  
**Status:** Draft  
**Created:** 2026-10-03  
**Last Updated:** 2026-10-26  
**Owner:** Rand Lee  

---

## REQ-QM-0001: All tasks

**Status:** Draft  
### Requirement Statement

Stay long-running; the role wins over the repo's `.claude/agents/quality-mgr.md` where they differ.


### Rationale

The role file states that it wins over `.claude/agents/quality-mgr.md` and carries a table of the differences (finding beads, `sprint_doc`, task start order); a long-running quality-mgr that followed the repo agent file alone would file no finding beads and close no ceremony findings.

### Success Criteria

**Acceptance Criteria:**

- [ ] `roles/quality-mgr.md` states that where the role and `quality-mgr.md` differ, the role wins, and that the role applies to every task until the lead switches the agent back.
- [ ] In a conflict listed in the role's difference table (for example finding beads, `sprint_doc`, task start order), the quality-mgr's observed bead and task actions match the role column.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0002: All tasks

**Status:** Draft  
### Requirement Statement

Treat every open task assigned to you as live and run them all at once, each with its own background reviewers: one active ATM task, the others claimed, worked and closed without starting; close each when its verdict is ready, in any order. The task close is the report; it returns to the task assigner.


### Rationale

QA never holds dev back, so the role runs every open QA task at once, each with its own background reviewers; ATM allows one active task per agent, hence the claimed-but-not-started rule (qa-template step a1 and the role's Tasks section).

### Success Criteria

**Acceptance Criteria:**

- [ ] With several open tasks assigned to quality-mgr, `atm task list --json` shows at most one task active and every other task claimed and worked, each with its own background reviewers.
- [ ] Each task is closed when its own verdict is ready, in any order, and the close is the report returned to the task assigner.
- [ ] A task worked without being started is still closed with `atm task close`.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0003: All tasks

**Status:** Draft  
### Requirement Statement

Cannot run: include the reason, command and failure evidence in the task refusal's `reason_md`; return the bead open, unassigned, and close the task `refused`.


### Rationale

Role text and qa-template step i1 require a refusal to carry the reason, command and failure evidence in `reason_md` and to hand the bead back, so the lead can act on the root cause instead of guessing why a task stopped.

### Success Criteria

**Acceptance Criteria:**

- [ ] When a task cannot run, the `atm task close ... refused` call carries a `reason_md` containing the reason, the failed command and its failure evidence.
- [ ] After the refusal the bead's status is `open` with an empty assignee, and the task state is `refused`.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0004: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Before claim: `bd ready` lists the QA bead, else do not claim or start; close the task `refused` (`bead_state` open) naming the blocker and the dependency to add (`bd dep add <bead> --blocked-by <blocker>`); never wait. A blocker met mid-round: return the bead open and close the task `refused` the same way. PR base = `metadata.pr_target` or a descendant of it, PR head starts with the checked bead's sanity PASS sha (skipped for a quick-fix QA bead, which has no sanity check), worktree HEAD = PR head; else refuse `SANITY_STALE`. Then claim and `atm task start`.


### Rationale

A QA bead that is not ready, or a PR whose head is not the sanity-passed commit, would be reviewed ahead of its blocker or at the wrong content; the pre-claim gate refuses with named causes and never waits. The CHANGELOG records that QA checks `bd ready` before claiming and that `SANITY_STALE` follows a rebase after sanity PASS.

### Success Criteria

**Acceptance Criteria:**

- [ ] Before any claim, `bd ready -n 0 --json` is checked for the QA bead; when it is absent the task is closed `refused` with `bead_state` `open`, naming the blocker bead and the `bd dep add <bead> --blocked-by <blocker>` edge, and the bead is not claimed.
- [ ] A blocker found mid-round returns the bead open and closes the task `refused` in the same form, without waiting.
- [ ] The round is refused `SANITY_STALE` unless the PR base is `metadata.pr_target` or a descendant, the PR head begins with the checked bead's sanity PASS sha (not required when `metadata.quick_fix` is true), and `git rev-parse HEAD` in the worktree equals the PR head.
- [ ] The bead is claimed and `atm task start` is run only after those checks pass.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::test_qa_refusals_and_ready`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::test_a_quick_fix_qa_skips_only_the_sanity_pass_check`

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0005: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Reject an assignment not rendered from the template; read `policy_path`.


### Rationale

Step b of qa-template tells quality-mgr to reject an assignment that is not the XML payload rendered from the template and to read the repository QA policy, because reviewer sets and conditional reviewers come from `policy_path`.

### Success Criteria

**Acceptance Criteria:**

- [ ] A task whose assignment is not an XML payload rendered from `qa-template.xml.j2` is rejected immediately and no reviewer is dispatched.
- [ ] The file at `policy_path` is read before reviewers are selected.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0006: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Review against the checked bead (and `sprint_bead` if set) with its governing requirements and ADRs as `sprint_doc`; extract every deliverable, criterion, deletion, validation item and artifact; completion `X/Y (Z%)`.


### Rationale

Without a fixed review target a QA could pass a layer that misses deliverables; qa-template steps b and c make the checked bead the sprint plan and require extraction of every deliverable with an `X/Y (Z%)` completion.

### Success Criteria

**Acceptance Criteria:**

- [ ] The sprint input file passed to reviewers as `sprint_doc` contains the checked bead's description, design, acceptance criteria and metadata, plus `sprint_bead` when set, with its governing requirements and ADRs.
- [ ] The QA report lists every deliverable, acceptance criterion, deletion requirement, validation item and expected artifact of the checked bead, and gives deliverable completion in the form `X/Y (Z%)`.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0007: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

The change is `git diff origin/<base>...<commit>`, or with `layer_prs` each layer PR's own base...head range (never a diff against a moving base); read content at `<commit>`.


### Rationale

The qa-template stack-discipline text freezes the branch at the reviewed commit; reviewing against a moving base or branch tip would judge changes that are not the layer under review.

### Success Criteria

**Acceptance Criteria:**

- [ ] The reviewed change is `git diff origin/<base>...<commit>`, or, when `layer_prs` is set, each layer PR's own base...head range, with no diff taken against a moving base.
- [ ] File content cited in findings is read with `git show <commit>:<path>`, not from the branch tip or worktree.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0008: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Round 1: run `reviewers_round1` plus conditional reviewers `policy_path` requires. Fix round: only each carried finding's filing reviewer (`fix-round-scope owned`, confirmed by `check`), each locked to its own `finding_ref` ids, its result reduced with `filter`.


### Rationale

Round 1 uses the repository's configured reviewer set; later rounds use only the filing reviewers because re-running a panel on a fix reopens the whole sprint review (CHANGELOG: filing-reviewer-only fix verification, ruling 2026-10-03).

### Success Criteria

**Acceptance Criteria:**

- [ ] In round 1 the reviewers dispatched are exactly `reviewers_round1` plus any conditional reviewer the policy at `policy_path` requires.
- [ ] In a fix round, `fix-round-scope owned` lists each carried finding's filing reviewer, `fix-round-scope check` exits 0 for the dispatched set, and no other reviewer runs.
- [ ] Each fix-round reviewer receives only its own `finding_ref` ids, and its result is reduced with `fix-round-scope filter`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_dispatch_set_is_the_filing_reviewers`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_check_exit_codes`

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0009: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Spawn every reviewer in the background; never run tests, linters or broad analysis in the foreground.


### Rationale

The role says every reviewer is a background agent so that long test and lint runs never block the quality-mgr or its other concurrent tasks (role Reviewers section).

### Success Criteria

**Acceptance Criteria:**

- [ ] Each reviewer is started as a background agent, and the quality-mgr's own shell runs no tests, linters or broad analysis in the foreground during the round.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0010: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Re-verify every cited file:line at `<commit>`; stale or missing evidence is a finding (fix round: fails that carried finding).


### Rationale

Reviewer citations drift when the branch moves; qa-template step e re-verifies each file:line at the pinned commit, and in a fix round stale or missing evidence fails the carried finding.

### Success Criteria

**Acceptance Criteria:**

- [ ] For every file:line cited by a reviewer, `git show <commit>:<path>` was used to confirm the cited content before the finding is kept.
- [ ] A citation that is stale or missing at `<commit>` is recorded as a finding; in a fix round the carried finding is recorded as not fixed.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0011: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Round 1: sweep the whole commit for every repeatable pattern.


### Rationale

A single occurrence reported by a reviewer usually has siblings; the round-1 text asks for a sweep for every repeatable pattern so one fix round fixes the class and not only the instance.

### Success Criteria

**Acceptance Criteria:**

- [ ] In round 1 the review covers the whole commit, each repeatable pattern found is searched across the full commit, and every occurrence is reported.
- [ ] A fix round performs no sweep.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0012: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Round 1: screen every finding with `ceremony-finding-screen` (background); normalize severity (`critical`/`Blocking`/`BLOCKING` → blocking, `Important` → important, `Minor`/`low` → minor).


### Rationale

Reviewers spell severity differently, and severity sets priority and the PASS/FAIL verdict, so the role requires the ceremony screen and a fixed severity normalization before finding beads are rendered.

### Success Criteria

**Acceptance Criteria:**

- [ ] In round 1, `ceremony-finding-screen` is run as a background agent over every finding of the round.
- [ ] Severity values `critical`, `Blocking` and `BLOCKING` are recorded as `blocking`, `Important` as `important`, and `Minor` and `low` as `minor` in the rendered finding data.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0013: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Round 1: pour each blocking finding the screen keeps as a fix ← sanity ← qa group under the sprint (quick-fix QA: pour nothing; list the blocking findings in the close's `findings_md` for the lead to file); file every other finding as one finding bead under the phase or feature bead, copying `requirements`, `adrs`, `sprint_bead` and `difficulty` from the checked bead, never defaulting `difficulty`; `blocked_by` only to another finding of this round. Never skip a finding whose render fails: fix its vars.


### Rationale

Blocking findings must come up ahead of the next planned dev bead, so they are poured as fix groups under the sprint while other findings are backlog beads; the role forbids defaulting `difficulty` and requires fixing the vars of a failed render because a skipped finding silently disappears.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each blocking finding kept by the screen exists as a poured fix <- sanity <- qa group under the sprint; for a quick-fix QA nothing is poured and the blocking findings appear in the close's `findings_md`.
- [ ] Every other finding exists as one finding bead under the phase or feature bead, with `requirements`, `adrs`, `sprint_bead` and `difficulty` copied from the checked bead and `difficulty` never defaulted.
- [ ] A finding bead's `blocked_by` lists only another finding of the same round.
- [ ] A finding whose render fails is rendered again with corrected vars; the number of filed finding beads equals the number of findings reported.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0014: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Apply the screen: `keep`/`not_applicable` open; `concern_valid_remedy_ceremony` open with remedy rewritten to the named mechanism; `ceremony` filed then closed with `ceremony: <reason>`.


### Rationale

The role's screen-verdict table defines what is filed for each verdict, so ceremony-only remedies are closed at once with a reason rather than assigned to a dev.

### Success Criteria

**Acceptance Criteria:**

- [ ] A finding with screen verdict `keep` or `not_applicable` is filed open as reported.
- [ ] A finding with verdict `concern_valid_remedy_ceremony` is filed open with its `remedy` rewritten to the mechanism the screen names.
- [ ] A finding with verdict `ceremony` is filed and then closed with a close reason starting `ceremony: `.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0015: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Verify the import added only poured fix groups, finding beads and inter-finding edges; never add a finding edge to a planned sprint.


### Rationale

Step g1 verifies the import so that a finding never adds a dependency edge to a planned sprint; the role states the plan file holds the minimum sprint edges and only the lead adds one.

### Success Criteria

**Acceptance Criteria:**

- [ ] After the import, the beads added are only poured fix groups, finding beads and edges between findings of the same round.
- [ ] No dependency edge from a finding to a planned sprint bead was added; a needed edge is recommended in the report instead.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0016: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Fix round: file nothing; note each confirmed fix; for each regressed or open carried fix bead pour round n+1; never reopen.


### Rationale

A fix round verifies existing fix beads; filing new beads there would reopen sprint scope, and reopening a fix bead would hide its history, so the role has the next round poured as a new bead.

### Success Criteria

**Acceptance Criteria:**

- [ ] In a fix round no finding bead is created.
- [ ] Each confirmed fix has a note `QA round <n>: fixed, verified at <commit>` on its fix bead.
- [ ] For each carried fix that regressed or is still open, a round n+1 fix bead is poured, and no closed fix bead is reopened.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0017: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Never assign findings.


### Rationale

The role ends its Findings section with this rule and says the lead picks the member for each finding, so assignment stays a lead decision (CHANGELOG #98: the lead, not a script, decides who takes a bead).

### Success Criteria

**Acceptance Criteria:**

- [ ] After a QA round, no finding or fix bead filed by quality-mgr has an assignee set by quality-mgr, and quality-mgr assigns no ATM task for a finding.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0018: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Verdict: only-minor is PASS; blocking or important is FAIL with one fix round; a second FAIL is `ROUND_CAP`, stop dispatch, record root cause.


### Rationale

A verdict rule with a round cap stops endless QA loops; the role defines only-minor as PASS, blocking or important as FAIL with a fix round, and `ROUND_CAP` once round n+1 would exceed `max_rounds`.

### Success Criteria

**Acceptance Criteria:**

- [ ] A round whose findings are all minor closes with verdict PASS.
- [ ] A round with any blocking or important finding closes with verdict FAIL and one fix round poured.
- [ ] When a further fix round would exceed `max_rounds`, the close reports `ROUND_CAP`, no further fix round is dispatched, and the root cause is recorded.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0019: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

With a PR: post `qa-complete.md.j2` as a PR comment and check stack and CI state (never `--watch`). No PR: say so in notes.


### Rationale

The PR comment is the visible QA record for the layer, and the template forbids `--watch` so a QA task is never blocked waiting for CI.

### Success Criteria

**Acceptance Criteria:**

- [ ] When `pr_number` is set, the `qa-complete.md.j2` rendering is posted as a comment on that PR before the close, and the stack and CI state are read with a one-shot command without `--watch`.
- [ ] When there is no PR, the close notes state that there is no PR.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0020: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

Close bead and task together whatever the verdict, `bd close` first and the task only if it succeeded.


### Rationale

QA never holds dev back, so the bead and task are closed together whatever the verdict; closing the bead first guarantees the task is not closed over a bead left open (role Tasks section, qa-template step i).

### Success Criteria

**Acceptance Criteria:**

- [ ] After a PASS or a FAIL, both the QA bead and its ATM task are closed.
- [ ] The task close is issued only after `bd close` of the bead succeeded.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0021: QA round (`qa-template`)

**Status:** Draft  
### Requirement Statement

After the closes (never on refusal), append one row each to the phase QA log and stats log, computed fresh; never hand-edit; correct with a workflow-issue bead plus a correcting row; never commit the logs.


### Rationale

The QA metrics logs feed velocity and closure estimates and must tie out at phase end; computing each row fresh and fixing errors by correcting rows avoids drifting counters (role QA Metrics Log; CHANGELOG: one printf append per row).

### Success Criteria

**Acceptance Criteria:**

- [ ] After a successful close, exactly one new row is appended to `.sc/qa-log/phase-<p>.jsonl` and one to `.sc/qa-log/phase-<p>-stats.jsonl`, with values computed at close time from `bd`.
- [ ] No row is appended when the task was closed `refused`.
- [ ] A wrong row is corrected by a workflow-issue bead and an appended correcting row, and neither log file is committed from a QA worktree.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_log_paths_and_fields_are_unchanged`

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0022: Plan review (`plan-review-template`)

**Status:** Draft  
### Requirement Statement

Check readiness, claim, start; blocked: close the task `refused` (`bead_state` open) naming the blocker and the dependency to add; a blocker met mid-task: return the bead open, unassigned, blocker in notes, close the task `refused` the same way; never wait.


### Rationale

A plan review of an unready bead or a blocked task would sit idle; the plan-review template and the CHANGELOG (blocked-task refusal review) require a refusal that names the blocker and the dependency to add, never a wait.

### Success Criteria

**Acceptance Criteria:**

- [ ] Readiness is checked, the bead claimed and the task started in that order.
- [ ] A bead that is not ready gets a task close `refused` with `bead_state` `open`, naming the blocker and the dependency to add.
- [ ] A blocker met mid-task returns the bead open and unassigned with the blocker in its notes and closes the task `refused` in the same form; no waiting occurs.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0023: Plan review (`plan-review-template`)

**Status:** Draft  
### Requirement Statement

Run `validate-plan --root <root>`: exit 5 every line blocking; exit 2 cannot-run (`PLAN_REVIEW_CANNOT_RUN`); a missing plan file and `bd doctor` errors are blocking.


### Rationale

Plan problems found by `validate-plan` and `bd doctor` are binding because a malformed plan misdirects every dev; the role states every problem it prints is a blocking finding and exit 2 is cannot-run.

### Success Criteria

**Acceptance Criteria:**

- [ ] `validate-plan --root <root>` is run before the reviewers.
- [ ] With exit 5, each printed line is recorded as a blocking finding; with exit 2 the review is reported `PLAN_REVIEW_CANNOT_RUN`.
- [ ] A missing plan file and each `bd doctor` error are recorded as blocking findings.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0024: Plan review (`plan-review-template`)

**Status:** Draft  
### Requirement Statement

Pin reviewers to `integration_branch` at `origin/<integration_branch>`.


### Rationale

Plan reviewers must read the same plan content; pinning to `origin/<integration_branch>` avoids reviewing a stale or local checkout (CHANGELOG: plan-review-template 3.10.0 requires a worktree of `integration_branch`).

### Success Criteria

**Acceptance Criteria:**

- [ ] Each plan reviewer's assignment names the branch `<integration_branch>` and reads the plan at `origin/<integration_branch>`.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0025: Plan review (`plan-review-template`)

**Status:** Draft  
### Requirement Statement

Round 1: missing/empty/mixed, unknown (outside New Ids), non-governing or unlisted touched requirement/ADR ids are blocking; never downgraded or screened out.


### Rationale

Wrong governing ids make a dev build against the wrong contract and QA check against the same wrong list, so the role states these findings are always blocking and never screened out.

### Success Criteria

**Acceptance Criteria:**

- [ ] A bead whose requirement or ADR ids are missing, empty or mixed, are unknown (outside New Ids), do not govern the work, or omit a requirement or ADR the work touches (including `NONE`) is reported as a blocking finding.
- [ ] Such a finding is not downgraded and is kept after the ceremony screen.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0026: Plan review (`plan-review-template`)

**Status:** Draft  
### Requirement Statement

Round 1: run `req-qa` and `arch-qa` per sprint container, `plan-scope-reviewer` in full over all of them (report its `parallelism`), plus the other plan reviewers; screen findings except validate-plan and REQ/ADR ones, list each drop with reason.


### Rationale

The plan review needs per-sprint requirement and architecture checks and one scope review over all sprints; findings other than validate-plan and REQ/ADR ones are screened, with each drop listed so nothing disappears silently.

### Success Criteria

**Acceptance Criteria:**

- [ ] In round 1, `req-qa` and `arch-qa` each run once per sprint container, `plan-scope-reviewer` runs once over all containers, and its `parallelism` is in the report.
- [ ] The other plan reviewers named by the assignment also run in round 1.
- [ ] `validate-plan` findings and REQ/ADR findings are not screened; every other dropped finding is listed with its reason.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_round_one_is_the_full_plan_review`

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0027: Plan review (`plan-review-template`)

**Status:** Draft  
### Requirement Statement

Fix round: only filing reviewers, locked; `validate-plan` still runs; no screen, no new findings.


### Rationale

CHANGELOG (ruling 2026-10-03): plan fix rounds are filing-reviewer-only, with `validate-plan` still run like required CI, so a fix round cannot grow into a new full review.

### Success Criteria

**Acceptance Criteria:**

- [ ] In a plan fix round only the filing reviewer of each carried finding runs, locked to its own ids; `req-qa` and `arch-qa` are not re-run and `plan-scope-reviewer` does not run in full.
- [ ] `validate-plan` runs in the fix round.
- [ ] No ceremony screen runs and no new finding is recorded.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_validate_plan_is_never_dispatched`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_plan_mode`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_fix_round_dispatches_only_filing_reviewers`

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0028: Plan review (`plan-review-template`)

**Status:** Draft  
### Requirement Statement

Report findings one line each: `<bead> <severity> <reviewer> <field>: ...`; file no finding beads.


### Rationale

Plan findings are report lines naming their filing reviewer so that a fix round can find the reviewer to re-run (CHANGELOG: plan finding lines name their reviewer and `fix-round-scope --plan` reads them).

### Success Criteria

**Acceptance Criteria:**

- [ ] Each plan finding appears in the report as one line in the form `<bead> <severity> <reviewer> <field>: ...`.
- [ ] No finding bead is created by a plan review.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_lines_name_their_filing_reviewer`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_a_line_without_a_reviewer_is_an_error`

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0029: Plan review (`plan-review-template`)

**Status:** Draft  
### Requirement Statement

PASS (no blocking/important open): no findings → close bead; minor → assign bead to the task assigner with notes, leave open. FAIL → bead open, unassigned, notes. Fix-round PASS: every carried finding fixed and validate-plan clean. Either way close the task with `plan-review-complete.md.j2`.


### Rationale

The plan-review bead stays open until a round passes so the lead sees unresolved plan problems, while a clean plan closes at once; the completion is the task close using `plan-review-complete.md.j2`.

### Success Criteria

**Acceptance Criteria:**

- [ ] With no blocking or important finding open and no findings at all, the bead is closed.
- [ ] With no blocking or important finding open and minor findings present, the bead is assigned to the task assigner with notes and left open.
- [ ] With a blocking or important finding, the bead is left open and unassigned with notes.
- [ ] A fix-round PASS requires every carried finding fixed and a clean `validate-plan`.
- [ ] In each case the task is closed with the `plan-review-complete.md.j2` rendering.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0030: Phase-end review (`review-template`)

**Status:** Draft  
### Requirement Statement

Check readiness, claim, start; not ready or a blocker met mid-task: refuse as in 22.


### Rationale

The phase-end review uses the same readiness and refusal discipline as plan review; the requirement points to the refusal form of REQ-QM-0022 so a not-ready review is refused, not waited on.

### Success Criteria

**Acceptance Criteria:**

- [ ] Readiness is checked, the bead claimed and the task started in that order.
- [ ] A bead that is not ready, or a blocker met mid-task, results in the bead returned open and the task closed `refused` in the form required by REQ-QM-0022.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0031: Phase-end review (`review-template`)

**Status:** Draft  
### Requirement Statement

Require branch = root `integration_branch`, worktree HEAD = `<commit>`; read at `<commit>`; plan = the phase feature bead and its children.


### Rationale

The integration review must examine the exact integration head; reading a moving branch or a different commit would certify content that was not reviewed (review-template).

### Success Criteria

**Acceptance Criteria:**

- [ ] The checked-out branch equals the root's `integration_branch` and `git rev-parse HEAD` in the worktree equals `<commit>` before review starts.
- [ ] File content is read at `<commit>`, and the plan reviewed is the phase feature bead and its children.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0032: Phase-end review (`review-template`)

**Status:** Draft  
### Requirement Statement

JEV post-mortem per `post-mortem.md`: inventory every phase finding (closed, nested); investigate every flagged result; dedupe; report them to the task assigner, who files them as finding beads; append raw evaluations to the phase JSONL.


### Rationale

The role makes quality-mgr own the JEV post-mortem so that fixes merged without verification of current behavior are found before phase closure (`roles/quality-mgr.md` Phase-ending post-mortem; `references/post-mortem.md`).

### Success Criteria

**Acceptance Criteria:**

- [ ] The inventory lists every phase finding, including closed and nested ones.
- [ ] Every flagged or uncertain result is investigated before it is accepted, and confirmed defects are deduplicated and reported to the task assigner, who files them as finding beads.
- [ ] Raw evaluations are appended to the phase JSONL with UTC timestamps, pinned SHA and run IDs, keeping earlier attempts.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0033: Phase-end review (`review-template`)

**Status:** Draft  
### Requirement Statement

Record `post_mortem_jev`; model error is not PASS; no code findings: `not_applicable`; JEV unavailable: `unavailable`, review stays pending: bead returned open, task refused `REVIEW_PENDING_JEV` with the code findings and `post_mortem_jev` in the refusal notes, which the lead files; never a completion.


### Rationale

A phase must not close on an unverified post-mortem, so the role defines how JEV status is recorded and says an unavailable JEV leaves the review pending with a `REVIEW_PENDING_JEV` refusal instead of a completion.

### Success Criteria

**Acceptance Criteria:**

- [ ] The review completion records `post_mortem_jev`, and a model error is not recorded as PASS.
- [ ] With no code findings, `post_mortem_jev.status` is `not_applicable` with the inventory reason.
- [ ] With JEV unavailable, the bead is returned open and the task is closed `refused` with `REVIEW_PENDING_JEV`, with the code findings and `post_mortem_jev` (status `unavailable`) in the refusal notes, and no completion is produced.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_integration_completion_requires_audit_evidence`

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0034: Phase-end review (`review-template`)

**Status:** Draft  
### Requirement Statement

Make no code changes.


### Rationale

The review-template describes the phase-ending review as read-only analysis ("no code changes") so the audited head does not move under the review.

### Success Criteria

**Acceptance Criteria:**

- [ ] The review worktree's `git status` shows no modified file and its HEAD still equals `<commit>` at the close.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0035: Phase-end review (`review-template`)

**Status:** Draft  
### Requirement Statement

Re-verify every file:line at `<commit>`; report SUMMARY, FINDINGS, EXTRACTION-READINESS, RECOMMENDED-NEXT-SPRINTS, INTEGRATION POST-MORTEM.


### Rationale

A fixed report shape lets the lead and `check-review-completion.py` consume the result, and file:line re-verification at the pinned commit matches the QA rule.

### Success Criteria

**Acceptance Criteria:**

- [ ] Every cited file:line was confirmed with content read at `<commit>`.
- [ ] The report contains the sections SUMMARY, FINDINGS, EXTRACTION-READINESS, RECOMMENDED-NEXT-SPRINTS and INTEGRATION POST-MORTEM.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0036: Phase-end review (`review-template`)

**Status:** Draft  
### Requirement Statement

Write to no bead except claiming, closing or returning the review bead. `check-review-completion.py` must exit 0 before closing bead and task with `review-complete.md.j2`.


### Rationale

The review-template step c limits bead writes to the review bead itself, and `check-review-completion.py` gates the completion contract so a certified phase cannot carry a wrong count or commit.

### Success Criteria

**Acceptance Criteria:**

- [ ] During the review the only beads written are the review bead's claim, close or return.
- [ ] `check-review-completion.py` exits 0 on the completion variables before the bead and task are closed with the `review-complete.md.j2` rendering.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_integration_completion_requires_audit_evidence`

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0037: Subagents

**Status:** Draft  
### Requirement Statement

Reviewers: background; pinned `branch`, `commit`, `worktree_path`, `sprint_doc` where the template takes it; never run `bd` or write ATM.


### Rationale

Reviewers report to quality-mgr only: the role says a reviewer never runs `bd` or writes ATM, so concurrent tasks cannot interleave bead writes, and each reviewer sees the same pinned checkout.

### Success Criteria

**Acceptance Criteria:**

- [ ] Each reviewer runs in the background with the pinned `branch`, `commit` and `worktree_path` in its assignment, and `sprint_doc` where its template takes it.
- [ ] No reviewer result shows a `bd` command or an ATM write; bead and task updates are made by quality-mgr.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0038: Subagents

**Status:** Draft  
### Requirement Statement

Each reviewer gets its assignment rendered from its assignment template as fenced JSON; no free-form prompts.


### Rationale

The role requires assignments rendered from the `<reviewer>-assignment.json.j2` templates and gated with `jq`, so malformed or free-form input is stopped before a reviewer runs (CHANGELOG: every handoff that sends fenced JSON matches its receiver).

### Success Criteria

**Acceptance Criteria:**

- [ ] Each reviewer's input is a fenced ```json block rendered by `sc-compose render --strict` from its assignment template and accepted by `jq -e .`.
- [ ] No reviewer receives a free-form prompt in place of the rendered assignment.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0039: Subagents

**Status:** Draft  
### Requirement Statement

In a fix round, a reviewer's carried ids are its own `finding_ref` ids; with ids, `req-qa`, `arch-qa`, `flaky-test-qa` and `ruthless-boundary-qa` carry the scope lock (a disposition for each id, no new findings).


### Rationale

Scope-locked verification stops fix rounds from finding new issues: each reviewer gets only its own `finding_ref` ids and must give a disposition for each (CHANGELOG: reviewer assignments carry `carry_forward_findings` and `findings_scope_locked`).

### Success Criteria

**Acceptance Criteria:**

- [ ] In a fix round each reviewer's `carry_forward_findings_json` is a JSON array of its own `finding_ref` ids and never an empty string.
- [ ] For `req-qa`, `arch-qa`, `flaky-test-qa` and `ruthless-boundary-qa` the assignment carries the scope lock, and the result gives a disposition for each carried id and no new findings.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_out_of_scope_findings_never_survive`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_another_reviewers_ids_are_not_in_scope`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_every_supported_filing_reviewer_can_run_locked_verification`

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0040: Subagents

**Status:** Draft  
### Requirement Statement

`ceremony-finding-screen` returns `keep`, `not_applicable`, `concern_valid_remedy_ceremony` or `ceremony` per finding.


### Rationale

The role's screen-verdict table needs a closed set of verdicts so every finding maps to a defined filing action.

### Success Criteria

**Acceptance Criteria:**

- [ ] `ceremony-finding-screen` returns, for each finding, exactly one of `keep`, `not_applicable`, `concern_valid_remedy_ceremony` or `ceremony`.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0041: Scripts

**Status:** Draft  
### Requirement Statement

`fix-round-scope owned|check|filter`: filing-reviewer map; check exit 5 `FIX_ROUND_DISPATCH_MISMATCH`; filter keeps only dispositions on own ids, unreported = `open`.


### Rationale

The script enforces the filing-reviewer-only rule mechanically, so a dispatch mistake is refused with exit 5 and a missing reviewer result cannot count as a fix (CHANGELOG: `fix-round-scope` checks; an unreported carried finding stays open).

### Success Criteria

**Acceptance Criteria:**

- [ ] `fix-round-scope owned` prints a map from each filing reviewer to its carried ids.
- [ ] `fix-round-scope check` exits 5 and prints `FIX_ROUND_DISPATCH_MISMATCH` when the dispatched reviewers differ from the filing reviewers.
- [ ] `fix-round-scope filter` keeps only dispositions for the reviewer's own ids and reports a carried id the reviewer did not report as `open`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_dispatch_set_is_the_filing_reviewers`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_check_exit_codes`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_unreported_carried_finding_stays_open`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_fix_round_scope.py::test_out_of_scope_findings_never_survive`

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0042: Scripts

**Status:** Draft  
### Requirement Statement

`check-review-completion.py`: verdict PASS/FAIL agrees with `integration_review`; PASS needs zero blocking, important, unresolved; `integration_commit` = `commit`; post-mortem counts sum to total; `post_mortem_jev.status` is `completed` or `not_applicable`; `post_mortem_md` non-empty.


### Rationale

The script gates the phase-end completion so a PASS that disagrees with its counts, a wrong commit or an unavailable JEV cannot be recorded (CHANGELOG: `check-review-completion.py` ships with the post-mortem).

### Success Criteria

**Acceptance Criteria:**

- [ ] `check-review-completion.py` exits non-zero when `verdict` PASS/FAIL disagrees with `integration_review`, or when a PASS has any blocking, important or unresolved count above zero.
- [ ] It exits non-zero when `integration_commit` differs from `commit`, or when the `post_mortem_counts` do not sum to the total.
- [ ] It exits non-zero unless `post_mortem_jev.status` is `completed` or `not_applicable`, and when `post_mortem_md` is empty.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_templates.py::test_integration_completion_requires_audit_evidence`

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0043: Scripts

**Status:** Draft  
### Requirement Statement

`assignment-gates.py qa`: `READY`, `PR_REQUIRED`, `PR_TARGET_MISMATCH`, `SANITY_STALE`, `QA_HEAD_MISMATCH`, `GATE_CANNOT_RUN`; exit 0/5/2.


### Rationale

The QA gate script turns the pre-claim checks of REQ-QM-0004 into one typed result so dispatch and refusal use the same codes.

### Success Criteria

**Acceptance Criteria:**

- [ ] `assignment-gates.py qa` prints exactly one of `READY`, `PR_REQUIRED`, `PR_TARGET_MISMATCH`, `SANITY_STALE`, `QA_HEAD_MISMATCH` or `GATE_CANNOT_RUN`.
- [ ] It exits 0 for `READY`, 5 for a refusal and 2 for `GATE_CANNOT_RUN`.

**Test Evidence:**

- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::test_qa_refusals_and_ready`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::test_a_quick_fix_qa_skips_only_the_sanity_pass_check`
- `plugins/atm-bd-orchestration/skills/atm-bd-orchestration/scripts/tests/test_assignment_gates.py::test_qa_base_check_that_cannot_run_is_not_a_refusal`

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## REQ-QM-0044: Scripts

**Status:** Draft  
### Requirement Statement

Upstream-owned installed `.claude/` skill, agent and template content is out of QA reviewer scope; the lead accepts such changes by diff review and the package's template tests.


### Rationale

CHANGELOG records this rule (#5): installed upstream content is owned upstream, so QA reviewers do not file findings against it and the lead accepts changes by diff review and template tests.

### Success Criteria

**Acceptance Criteria:**

- [ ] The reviewers' scope excludes upstream-owned installed `.claude/` skill, agent and template content, and no finding is filed against that content.
- [ ] A change to that content is accepted by the lead through diff review and the package's template tests.

### Implementation Notes

Sources: `skills/atm-bd-orchestration/`: `roles/quality-mgr.md`, `SKILL.md`, templates `qa-template`, `plan-review-template`, `review-template`, `*-assignment.json.j2`, `finding-bead`, `qa-complete`, `review-complete`, `formulas/README.md`, scripts `fix-round-scope`, `check-review-completion.py`, `assignment-gates.py qa`.

## Unresolved

1. QA refusal codes: `qa-template.xml.j2` step a refuses every mismatch as `SANITY_STALE`; `assignment-gates.py qa` returns `PR_REQUIRED`/`PR_TARGET_MISMATCH`/`QA_HEAD_MISMATCH`, and no template invokes the `qa` subcommand.
2. Phase-end reviewer: `roles/quality-mgr.md`/`SKILL.md` say quality-mgr owns it; `SKILL.md` assigns `<reviewer>` and `review-template.xml.j2` is a single read-only reviewer with no reviewer set.
3. `qa-template.xml.j2` and `plan-review-template.xml.j2` pass `qa_round` to every reviewer; only `ruthless-boundary-qa-assignment.json.j2` declares it (`plan-scope-reviewer` takes `round_index`).
