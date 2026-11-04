---
name: plan-hardening
version: 0.19.12
description: Harden a phase plan in bd before the Plan Gate, using parallel scope and critical reviews, planner fixes, and final ceremony review. Use for new plans or replans; the Plan Gate remains a separate review.
---

# Plan Hardening

The plan is the phase root and its sprint-container beads. Read
`.claude/skills/atm-beads/resources/atm-beads-plan-guidelines.md` for planning
rules. This skill changes plan beads through `bd`; it adds no script or hook.
After hardening, hand the plan to the existing Plan Gate in
`atm-bd-orchestration/SKILL.md` unchanged.

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

Use the dev-dispatch `difficulty` rule in `atm-bd-orchestration/SKILL.md` for
fast, normal and frontier tiers. Scope and critical passes run at frontier.
Prefer different foundries (Anthropic, OpenAI, xAI). In iteration 2, run each
pass on a different foundry than in iteration 1 wherever possible. Record the
chosen runner and foundry with the step's evidence.

The runner is the teammate or background `general-purpose` agent taking the
step. It reads the reviewer agent file named by the step description as its
review rules. Those files remain read-only: the runner executes the template's
`bd` and `atm` commands and files the findings.

## Iterations

Default to **2 iterations**; the lead or planner may set another number.
Within each iteration, scope and critical passes and every adversary run in
parallel. The planner's fix step waits for all of them. Create the final
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
scratch outside the tracked tree.

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
4. Dispatch ready scope and critical steps at the same time. In lead mode,
   also dispatch the iteration's adversary wisps in parallel.
5. Once those steps have all closed, dispatch the ready fix step to the
   planner. In lead mode, the lead first confirms every adversary closed.
6. After the fix step closes, create the next iteration's wisp.

After the last fix step closes, copy into scratch, render and wisp
`formulas/plan-hardening-final.formula.toml.j2` using `root`, `phase`, and
`planner`. Dispatch ceremony, then fix, then verify as their dependencies
release them. The final fix includes unresolved final-critical findings.
Verification checks each carried finding with its filing pass's rules and
files no new findings.

Finally run `bd mol squash <wisp>` on each iteration, adversary and final
wisp. Close reasons retain verdicts and filed/verified fix-bead ids; wisp
metadata is not retained in the digest. Hand the plan and remaining findings
to the existing Plan Gate, without changing that gate's workflow.

## Dispatch

Use `templates/plan-hardening-step.xml.j2` for every step and the shipped
`examples/plan-hardening-step-{teammate,subagent}-vars.json` as input shapes.
Set `step`, `runner`, `actor`, `phase`, `root`, and `planner` for the real run.
Never hand-write a step prompt.

For a teammate, set `runner=teammate`, `actor=<agent>`, and deliver with:

```bash
atm task assign <agent> --task-id <step> --template <skill-root>/templates/plan-hardening-step.xml.j2 --vars <vars.json>
```

For a subagent, set `runner=subagent`, `actor=<dispatcher>`, and render:

```bash
sc-compose render --strict --file <skill-root>/templates/plan-hardening-step.xml.j2 --var-file <vars.json> --output <scratch>/step.xml
```

Give that exact rendered file as the prompt to one background
`general-purpose` agent at the chosen tier. Its fenced JSON is the return.
The teammate starts and closes its ATM task; the subagent runs no ATM command.
Both claim and close their step bead through the rendered instructions.

Each finding has `title`, `description`, `severity` (Blocking, Important or
Minor), and `plan_bead`. The finding block creates a `stage:plan-fix` bead
under the phase root assigned to the planner, preserving the filing pass.
The planner fixes or rebuts it; the filing pass verifies and closes it.

## Planner with subagents

The planner creates every iteration and the final wisp and runs every pass
with its own background subagents, including final critical and ceremony
passes. No step waits on the phase lead. Tell the lead only when handing the
plan to the Plan Gate.

## Planner with teammates

The planner assigns scope, critical and verify steps to teammates and takes
the fix steps itself. Dispatch the final ceremony review to a teammate too.
Use the same formula dependencies and rendered step template in every case.

## Lead adversarial

Read [references/adversarial-plan-hardening.md](references/adversarial-plan-hardening.md)
for the lead's integration, requirement/ADR and own-review work. It runs
alongside each iteration's scope and critical reviews.
