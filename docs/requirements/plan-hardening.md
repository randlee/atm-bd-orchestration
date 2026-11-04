# plan-hardening

Sources: `plugins/atm-bd-orchestration/skills/plan-hardening/` (SKILL.md,
references/adversarial-plan-hardening.md, formulas/*.j2, templates/*.j2,
examples/*.json), `agents/plan-scope-reviewer.md`,
`agents/critical-plan-reviewer.md`, and the existing ceremony-qa agent.
Contract: atm-core `develop`, `docs/plans/phase-bp/contract/README.md`.

## Requirements

1. The planner, lead and reviewers use the phase root and sprint-container
   beads and `atm-beads-plan-guidelines.md` as their planning input and rules.
2. Choose among planner with subagents, planner with teammates and lead
   adversarial modes. An otherwise unassigned team uses lead adversarial;
   interrupt a teammate for a hard plan when justified, otherwise use
   planner subagents during ongoing work.
3. Select tiers through the dev-dispatch difficulty rule; scope and critical
   use frontier. Prefer mixed foundries and change each pass's foundry for
   iteration 2 wherever possible.
4. Default to two iterations, overridable by the planner or lead. Scope,
   critical and all adversaries run in parallel within an iteration.
5. Each iteration's fix waits for scope and critical and, in lead mode, all
   adversary steps. The next iteration waits for the preceding fix to close.
6. A final critical FAIL does not add an iteration: fix its findings and run
   the final ceremony, fix and verify sequence.
7. Render the shipped formulas with `sc-compose bead render`; create vapor
   wisps with `bd mol wisp`, and dispatch only their ready steps. Keep the
   ephemeral steps out of ordinary ready queues.
8. Every runner receives the same shipped step template rendered with its
   real step, phase, root, planner, actor and runner variables. Reject any
   runner except teammate or subagent.
9. A teammate's assignment uses `atm task assign --template --vars`. A
   background general-purpose subagent receives the exact rendered prompt.
   The reviewer agent file supplies rules rather than the subagent type.
10. Both runners claim and close their step bead. Only teammates start and
    close ATM tasks. Preserve the template's typed task lifecycle (ADR-062).
11. Each finding carries title, description, severity and plan_bead. The
    runner creates a stage:plan-fix bead under the phase root assigned to
    the planner and records its filing pass.
12. The planner changes the plan, records fixed or cited rebutted notes and
    validates the changed plan. The filing pass verifies and closes fix
    beads; the planner never closes them.
13. The final verify pass files no new findings and leaves unresolved ones
    for the existing Plan Gate.
14. Squash every wisp after the final sequence. Record verdict and filed and
    verified fix ids in close reasons, which survive squash; metadata does not.
15. Planner-with-subagents mode runs every pass, including final critical
    and ceremony reviews, without waiting for the phase lead; notify the
    lead only at the Plan Gate handoff.
16. Planner-with-teammates mode assigns review and verify steps to teammates
    and has the planner perform fix steps.
17. In lead adversarial mode, research each cross-repository or external API
    integration through an adversary wisp with its own area and task.
18. Review related existing and new requirements and ADRs. Propose revisions
    for contradictions, missing detail and sharpened contracts through a
    req-adr adversary and planner fix beads.
19. The lead files its own findings through area=lead. Its iteration-2 pass
    first verifies carried lead and adversary findings.
20. Use multiple fast researchers for broad shallow work and frontier
    models for difficult code and integrations, preferring mixed foundries.
    Give iteration-2 adversaries different tasks targeted at discovered
    weaknesses or previously uncovered areas; record each area in the title.
21. Preserve all six proven contract files byte for byte. Ship the skill,
    rules, requirements and tests through the generated package manifest;
    orchestration hooks, scripts and Plan Gate remain outside this skill.

## Unresolved

None within this package boundary. Live execution and the eval matrix are
owned by bp-2.
