---
name: plan-hardening
version: 0.19.12
description: Harden a phase plan in bd before the Plan Gate, using parallel scope and critical reviews, planner fixes, and final ceremony review. Use for new plans or replans; the Plan Gate remains a separate review.
requires:
  cli:
    - name: bd
      minimum_version: 1.3.0
    - name: atm
    - name: sc-compose
      minimum_version: 1.7.0
    - name: jq
    - name: uv
---

# Plan Hardening

The plan is the phase root and its sprint-container beads. Read
`.claude/skills/atm-beads/resources/atm-beads-plan-guidelines.md` for planning
rules. This skill changes plan beads through `bd`; it adds no script or hook.
After hardening, hand the plan to the existing [Plan Gate](../atm-bd-orchestration/SKILL.md#plan-gate) unchanged.

## Step 1 — Verify CLI Installation

Run this before anything else in the skill:

```bash
for c in bd atm sc-compose jq uv; do command -v "$c" >/dev/null && echo "ok $c" || echo "MISSING $c"; done
bd version          # 1.3.0 or newer
sc-compose --version # 1.7.0 or newer
uv --version
```

If anything is missing or too old, **read
[`../atm-beads/references/installation-and-troubleshooting.md`](../atm-beads/references/installation-and-troubleshooting.md)
before proceeding.**

## Run modes

- **Planner with subagents**: the planner runs the entire loop with background
  `general-purpose` subagents, including final critical and ceremony reviews.
- **Planner with teammates**: teammates review; the planner takes fix steps.
- **Lead adversarial**: the phase lead runs hardening against a teammate
  planner, with integration researchers and its own adversarial review.

## Mode selection

When the team is idle (has no assigned work), choose lead adversarial. Otherwise choose
planner with teammates when the plan is hard enough to justify interrupting
another frontier model, preferably from a different foundry. Otherwise choose
planner with subagents; this is the usual mid-phase replan while teammates
are busy.

## Reviewer selection

Use the dev-dispatch `difficulty` rule in [the orchestration skill](../atm-bd-orchestration/SKILL.md#plan-gate) for
fast, normal and frontier tiers. Scope and critical passes run at frontier.
Prefer different foundries (Anthropic, OpenAI, xAI). In iteration 2, run each
pass on a different foundry than in iteration 1 wherever possible. Record the
chosen runner and foundry with the step's evidence.

For general-purpose subagents use the harness-native model mapping: fast =
haiku (Anthropic) or gpt-6-luna (OpenAI), normal = sonnet or gpt-6.1-terra,
frontier = opus or gpt-6-astra. If a named tier is unavailable, report it; do
not silently substitute a more expensive tier. An evaluation may explicitly
override all tiers to its specified model.

The runner is the teammate or background `general-purpose` agent taking the
step. It reads the reviewer agent file named by the step description as its
review rules. Those files remain read-only: the runner executes the template's
`bd` and `atm` commands and files the findings.

The runner's `bd` writes are limited to the step template's commands: claim
and close the step, create `stage:plan-fix` beads under the root, and close
verified fix beads or update their notes. In planner fix steps, the planner
may also update plan beads and, only through the add-sprint path below, render
and import a sprint container, update its plan index, and add or remove only
the corresponding container-to-container `blocks` edges. Do not pour or
modify sprint groups during hardening. A direct
`bd create` of a sprint or any other `bd` write fails the step. The planner
adds a `fixed:` or `rebutted:` note to each fix bead and never closes it. The
only permitted `git` write is after the plan changes and
the final formula passes: pour groups, render the DAG, and commit and push it
to the plan PR unless the dispatch template specifies no PR. Reviewer agents remain read-only.

## Iterations

Default to **2 iterations**; the lead or planner may set another number.
Within each iteration, scope and critical passes and adversaries run in
parallel, with at most four adversary subagents active at once; queue the
rest. The planner's fix step waits for all of them. Create the final
formula only after the last iteration's fix step closes: ceremony-qa reviews
the plan after the final critical pass.

A FAIL from the final critical pass is normal because it is adversarial.
Fix the findings and proceed to the final formula; never add an iteration
because of that FAIL.

## Loop

Use the current repository's bd database and repository configuration.
`skill-root` below is this skill's directory: in the package it is
`plugins/atm-bd-orchestration/skills/plan-hardening`, and after installation
it is `.claude/skills/plan-hardening`. Keep requests, renders and results in
scratch outside the tracked tree. `sprint-review` is an exception: it writes
the phase DAG under `docs/plans/phase-<p>/` and, by default,
`scratchpad/phase-<p>-dag/` in the worktree. Both are expected clone writes;
inspect the output and include it when the plan requires it.

When validating a local, unpushed plan, set the dispatch `plan_index` to
its absolute path; each step passes it to both validate-plan and sprint-review.
For the integration-branch index use the literal `integration`.

For each iteration `i` from 1 through `N`:

1. Copy the selected shipped formula byte for byte into scratch. The bead
   renderer requires the template inside its working directory. Write a
   request for `sc-compose bead render --request <req.json> --json`:

   ```json
   {
     "schema": "sc-compose/beads/v1",
     "operation": "render",
     "working_directory": "<absolute scratch directory>",
     "template": "plan-hardening-iteration.formula.toml.j2",
     "rendered_formula": "iteration.formula.toml",
     "bead_variables": {},
     "compose_variables": {
       "root": "<phase root>", "phase": "<phase>",
       "iteration": "<i>", "iterations": "<N>", "planner": "<planner>"
     }
   }
   ```

   Require a successful render before using its output.
2. Run `bd mol wisp <rendered file> --json`; retain the returned wisp id.
   The formula has `phase = "vapor"`, so its steps are ephemeral and stay
   out of ordinary ready queues.
3. List steps with `bd ready --mol <wisp> --include-ephemeral --json`.
4. Dispatch ready scope and critical steps at the same time using two distinct
   available teammates when a teammate has max_tasks=1. If only one teammate
   is available, run the two passes serially and record that limitation. In lead
   mode, also dispatch the iteration's adversary wisps in parallel, at most four
   adversary subagents at a time.
5. Once those steps have all closed, dispatch the ready fix step to the
   planner. In lead mode, the lead first confirms every adversary closed.
6. After the fix step closes, create the next iteration's wisp.

In either planner mode, the planner is the phase lead for hardening and owns
rulings on every finding. If a proposed change is unsupported by the plan or
its governing requirements, record a rebuttal citing that evidence; otherwise
apply the fix. Never invent a ruling or leave a finding without a fixed or
cited rebuttal note. In lead-adversarial mode the phase lead makes the ruling.
For every applied fix, cite both its finding and a REQ, ADR, or existing plan
source. Never add or remove scope without a source; rebut an unsupported
finding with `rebutted: unsupported by <source>`.
For structural findings, prefer editing an existing sprint; otherwise rebut
with a citation if the request is unsupported; add a sprint only when neither
resolves it. When a ruling adds a sprint, render the container with
`.claude/skills/atm-beads/templates/sprint-bead.json.j2`, using
[the sprint vars example](examples/sprint-bead-vars.json) as a field shape;
replace every example value with facts supported by the plan. Add its sprint and
prerequisites to the selected plan index and import it. Do not pour its dev,
sanity or QA beads during hardening; the final step pours all groups once. Choose the added sprint's `pr_target` using
`atm-beads-plan-guidelines.md` and `resources/planning.md` (nearest
`must_follow` prerequisite, highest planned layer if there are several; trunk
when none). Its own layer is above that prerequisite.

When changing an existing sprint's prerequisites, update `depends_on` in the
plan index, then use `bd dep add <sprint> --blocked-by <prerequisite>` for
each new container edge and `bd dep remove <sprint> <prerequisite>` for each
stale container edge. Limit writes to planned sprint containers, inspect the
graph, and validate the updated index. If an edge operation or validation
fails, leave the step open and return the failure envelope; refuse its ATM
task if it has one.


After the last fix step closes, copy into scratch, render and wisp
`formulas/plan-hardening-final.formula.toml.j2` using `root`, `phase`, and
`planner`. Dispatch ceremony, then fix, then verify as their dependencies
release them. The final fix includes unresolved final-critical findings.
For each carried finding, verification re-applies its filing pass's rule to
the current plan state, records the evidence path, and closes it if resolved
or reopens it if unresolved. Verification files no new findings. For `lead` and `adversary:*` findings, use the
`Verification:` check recorded in the finding's `description`, as defined in
[the adversarial reference](references/adversarial-plan-hardening.md). Confirm
its expected result against the current plan or a cited design rebuttal;
leave a missing check or unresolved result open with a note.

After the final formula passes, run `bead-groups --phase <p>` once to pour
all groups, then run `sprint-review --root <root> --index <index>`. Save both
outputs and exit codes. Commit and push the DAG to the plan PR only when the
dispatch template specifies a PR; for `plan_pr=none`, keep the DAG in the
clone and scratch. A failed pour or render fails the run.

Finally run `bd mol squash <wisp>` on each iteration, adversary and final
wisp. Close reasons retain verdicts and filed/verified fix-bead ids; wisp
metadata is not retained in the digest. Hand the plan and remaining findings
to the existing Plan Gate, without changing that gate's workflow.

## Resume

Recover iteration, adversary and final wisp and step ids after an interruption
from `bd list -l phase-<p>,stage:plan-hardening --include-ephemeral --all --json`,
filtered on `metadata.root` for the phase root. Retain the parent wisp ids for
the final squash. Retry a step only while its bead is open; ensure the previous
runner has stopped before reopening or dispatching it, and never run two copies
of a step concurrently. A closed step is not retried. The filing block reuses
an existing finding with the same step, title, description, severity and plan
bead, including closed findings, and files only missing entries from a partial
batch. Preserve the same finding input when retrying.

For a recoverable fix-step execution failure, stop the failed runner, leave
or reopen its bead, and dispatch the same step once to a fresh runner with
the failed return and evidence attached. If the retry fails, stop the run with
`EXECUTION.STEP_FAILED`; never start two copies concurrently.

## Dispatch

For each background step, use a bounded wait (30 minutes by default; the
dispatcher may set another limit). For a subagent tool without a deadline
parameter, impose the bound in the dispatcher wait; if bounded waiting or
stopping the agent is unavailable, stop the run with `EXECUTION.TIMEOUT`
instead of waiting or starting a duplicate. If a step has not closed by
its deadline, stop its agent, leave the bead open (reopen it if needed), and
re-dispatch it once. Ensure the previous agent has stopped before retrying. If
the retry also times out, stop the run and return `EXECUTION.TIMEOUT` naming
the step to the caller. A timed-out review is incomplete: never close it with
a review verdict or release the fix step. If the agent cannot be stopped,
stop the run instead of dispatching another copy.

Use `templates/plan-hardening-step.xml.j2` for every step and the shipped
`examples/plan-hardening-step-{teammate,subagent}-vars.json` as input shapes.
Set `step`, `runner`, `actor`, `phase`, `root`, `planner`, `plan_index`,
`beads_dir`, `workdir`, `plan_pr`, `scratch_dir`, and `cache_path` for the
real run. `plan_pr=none` means no push; any other value identifies the plan PR. Use absolute paths for the last
two, and an absolute index path or `integration` for `plan_index`; every step
runs with the supplied working directory and BEADS_DIR.
Never hand-write a step prompt.

For a teammate, set `runner=teammate`, `actor=<agent>`, and deliver with:

```bash
atm task assign <agent> --task-id <step> --template <skill-root>/templates/plan-hardening-step.xml.j2 --vars <vars.json>
```

For a subagent, set `runner=subagent`. For a fix step set `actor=<planner>`
because the formula assigns that step to the planner; for review steps use
`actor=<dispatcher>`. Render:

```bash
sc-compose render --root <absolute-skill-root>/templates --strict --file plan-hardening-step.xml.j2 --var-file <vars.json> --output <scratch>/step.xml
```

Give the exact contents of that rendered file as the prompt to one background
`general-purpose` agent at the chosen tier. Its fenced JSON is the return:
`success`, `data` (`step`, `verdict`, `findings`), and `error`. A completed
review returns `success:true` and `error:null`, including when its review
verdict is FAIL. An execution failure returns `success:false` with error
`code`, `message`, `recoverable`, and `suggested_action`.

Require one fenced JSON object. An unfenced, missing or malformed return,
`success:false`, or a returned verdict differing from the step bead's
`close_reason` (`VERDICT=PASS` or `VERDICT=FAIL`) is a failed step. Read the
recorded reason with `bd show <step> --json`; do not trust the return alone.
Surface a concise error and its recovery action. A failed step does not
release the fix step: never dispatch the fix merely because `bd ready`
lists it. Leave the failed step open, or reopen it with
`bd update <step> --status open` if the runner already closed it. Recover
that step and accept its return before releasing the planner's fix.

The teammate starts and closes its ATM task; the subagent runs no ATM command.
Both claim and close their step bead through the rendered instructions.

Each finding has `title`, `description`, `severity` (Blocking, Important or
Minor), and `plan_bead`. The finding block creates a `stage:plan-fix` bead
under the phase root assigned to the planner, preserving the filing pass.
The planner fixes or rebuts it; the filing pass verifies and closes it.
Temporarily omit the `phase-<x>` label from plan-fix beads: the current phase
validator has no model for that stage (atm-bd-orchestration#788). Keep the
parent and `stage:plan-fix` label, and query them with `--all`. Restore the
phase label when that model ships.

## Filing reviewer output

For scope and critical, before applying the step description's finding-based PASS rule, inspect the
reviewer's envelope. `success: false` or any non-empty `errors` array means
the review did not complete. Leave the step open (reopen it if closed), file
nothing, and return the step's `success: false` envelope with the reviewer's
error as the message. Never close `VERDICT=FAIL` for an incomplete review:
that would release the next step. For a successful envelope, use `data`; a
legacy top-level `errors` array also triggers this error. The following maps
the reviewer JSON in `$REVIEW` to its outcome, error and filing array:

```bash
jq -c 'if (.success == false or ((.data.errors // []) | length > 0) or ((.errors // []) | length > 0)) then {verdict:"ERROR", error:([.error, (.data.errors // [])[], (.errors // [])[]] | map(select(. != null)) | if length == 0 then ["reviewer returned success:false without an error"] else . end), findings:[]} else {verdict:"FINDINGS", error:null, findings:([(.data.findings // [])[], (.data.minor_wording // [])[]] | map({title, description, severity, plan_bead}))} end' "$REVIEW"
```

For `FINDINGS`, apply the step's normal finding-based verdict after filing;
`FINDINGS` is not a close verdict. For `ERROR`, use the mapped `error` in the
failure envelope and follow the step template's execution-error path.

For scope and critical, the runner converts successful reviewer JSON to the step template's filing array in
one way: concatenate `findings` and `minor_wording`, then copy only `title`,
`description`, `severity` and `plan_bead` from every entry. File both arrays,
including Minor wording findings; do not drop `minor_wording`. The canonical
`description` already states the problem and exact correction. Additional
`issue`, `required_correction` and `target_refs` fields are diagnostic context,
not alternative filing fields. The runner does not infer canonical fields
from those extras. Both reviewer agents use this mapping.

### Ceremony output

For ceremony-qa's `doc_review` input, capture each plan bead with
`bd show <id> --json > <scratch>/<id>.json`. Set `worktree_path` to the
checkout and `review_targets` to those capture paths. Findings cite a capture
in `file`; its `[0].id` is the cited bead id. Do not infer ids from filenames.
Apply any ceremony-finding screen required by the consuming repository before
filing and computing the ceremony-qa verdict. Record each dropped finding and
the screen decision in the step notes. `review_output` below is the resulting
screened reviewer output, retaining the reviewer envelope and status.

| Reviewer | Source findings | Filing mapping | Step verdict |
| --- | --- | --- | --- |
| ceremony-qa | `data.findings` | `title=issue`; `description=issue + " " + recommendation`; capitalize `severity`; `plan_bead` is the cited capture's bead id | FAIL when `data.status=findings` has an `important` finding; otherwise PASS |

Set `review_output` to the reviewer's JSON file and `findings_file` to the
step template's findings-array path. Run this adapter before the filing
block. A reviewer error (`success:false`) stops the step; propagate its error.
An empty converted array needs no filing block. Use the printed verdict for
the step close.

```bash
# Ceremony filing adapter
set -euo pipefail
jq -e '.success == true' "$review_output" >/dev/null
jq -c '.data.findings[]' "$review_output" | while IFS= read -r finding; do
  capture=$(jq -er '.file' <<<"$finding")
  plan_bead=$(jq -er '.[0].id' "$capture")
  jq -c --arg bead "$plan_bead" '{title:.issue, description:(.issue + " " + .recommendation), severity:(.severity | (.[0:1] | ascii_upcase) + .[1:]), plan_bead:$bead}' <<<"$finding"
done | jq -s '.' >"$findings_file"
jq -r 'if .data.status == "findings" and any(.data.findings[]; .severity == "important") then "FAIL" else "PASS" end' "$review_output"
```

## Planner with subagents

The planner creates every iteration and the final wisp and runs every pass
with its own background subagents, including final critical and ceremony
passes. No step waits on the phase lead. Tell the lead only when handing the
plan to the Plan Gate.

## Planner with teammates

The planner assigns scope, critical and verify steps to teammates and takes
the fix steps itself. Dispatch the final ceremony review to a teammate too.
Use the same formula dependencies and rendered step template in every case.
A single identity may hold planner, dispatcher, and step teammate roles; it
assigns each step to itself using the rendered ATM assignment, then starts and
closes its own task. Record verification by that same identity as not independent.

## Lead adversarial

Read [references/adversarial-plan-hardening.md](references/adversarial-plan-hardening.md)
for the lead's integration, requirement/ADR and own-review work. It runs
alongside each iteration's scope and critical reviews.
