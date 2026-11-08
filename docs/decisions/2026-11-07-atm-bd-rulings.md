# atm-bd rulings, 2026-11-07 / 2026-11-08

Rand's rulings from the session that converted atm-bd's requirements to Raptor
records. Quotes are verbatim (spelling fixed). Each ruling names the records
that carry it in `docs/requirements/`. Shared rulings live in `core.md`
(REQ-CORE-*), package rulings in the package file.

## Identity, team and context

1. **Never from the environment.** "atm-bd should not get team or identity
   from environment. It should come from folder where phase config is loaded."
   "When omega-prime@hermes runs `atm-bd query` for atm-dev, I do not want
   team hermes leaking in. Every ingress into the system MUST assess the risk
   of environment var being used." "The original 'use ATM_TEAM' became a
   problem when orchestrator omega-prime@hermes became involved. All atm-bd
   cli tools should get all info from repo/folder it was launched from."
   Reverses ADR-066 and phase-bi ANC-042/043 (2026-10-18), which let
   `ATM_TEAM` select the team. Records: REQ-CORE-0001..0004, REQ-CORE-0036.
2. **Phase lead.** "phase-lead is defined in the phase-file (it should NOT
   default to team-lead)." Records: REQ-CORE-0005, REQ-LITE-0017.
3. **ATM task first, config second.** "I would like all of atm-bd to move
   toward getting information from existing 'atm task' queries w/ fallback of
   atm-bd config." Record: REQ-CORE-0035.
4. **Mid-phase lead change.** "There should be a note in the skills that the
   atm-bd config file naming phase-lead MUST be updated if there is a change
   mid-sprint." Record: REQ-CORE-0037.

## Assignment and routing

5. **Claim actor.** "`--actor $ATM_IDENTITY` is correct." An agent's own
   session identity is its claim actor. Rendering the assignee identity into an
   assignment "is fine for quality-mgr/sanity, NOT ok for dev". Record:
   REQ-CORE-0006.
6. **Bead assignee.** "In planning assignee should be fast/normal/frontier so
   exact dev is not locked in. At task assign, assignee should be set by
   phase-lead to agent-name." Records: REQ-CORE-0007, REQ-CORE-0008.
7. **Sanity/QA assigner = dev task's assigner, set by ATM task hooks.** "For
   sanity and qa task assign, the assigner must be set based from what is read
   from the dev task assigner. This can occur at 'atm task assign <dev>' in an
   assign hook, AND it can also occur at the 'atm task close <dev-task>' hook
   ... doing it in both places would be prudent ... the 2nd close-hook
   assignment should do a write IF NOT correct. No need to actually write a
   bead to db w/ redundant data." Records: REQ-CORE-0009, REQ-CORE-0010.
8. **Messages go to the task's assigner.** "This is even more important,
   because sometimes lead transitions mid phase (i.e. out of tokens)."
   Supersedes phase-bj ANC-051/052/053 (messages to `<phase-lead>`) and the
   parallax per-wave lead ("parallax is ONLY lead for a wave, NOT lead for the
   phase"). Record: REQ-CORE-0011.

## Gates, rounds and sanity

9. **Pre-claim checks in the task.start hook.** "Shouldn't all of this occur
   in the 'atm-task-open' hook? (check bd ready -> git checks -> returns true,
   otherwise returns false and lead is notified)". Replaces
   `assignment-gates.py` template steps. Constraint from history: the 2.5 s
   hook limit (ADR-068) behind phase-bo ANC-066. Records: REQ-CORE-0012,
   REQ-CORE-0013.
10. **Round cap escalates, findings always created.** "I do NOT want any
    language to the effect STOP EVERYTHING AND NOTIFY USER ... More than 3
    rounds should escalate to lead w/ a message having the lead deploy an
    architect to see why this isn't converging." "Refusing to create findings
    does NOT sound like a useful thing to do." Cause observed: adversarial
    reviewers redeployed every round. Records: REQ-CORE-0014..0016.
11. **Sanity close path.** "Typical sanity close path is 'sanity pass'
    condition in atm-task-close-sanity-hook (which would close sanity task +
    sanity bead). phase-lead must also be able to close/bypass sanity with
    clear instructions (so he doesn't guess)." Records: REQ-DSAN-0060,
    REQ-DSAN-0061.
12. **Jev sanity.** "The strategy for how to prompt jev sanity needs to get
    reviewed and tightened. For now we need documentation and code in sync."
    Records: REQ-DSAN-0051..0057 describe today's `jev_client.py`.

## Tooling

13. **bd-cache everywhere.** "Everything in atm-bd (including agent 'bd'
    instructions) need to use bd-cache." Record: REQ-CORE-0034.
14. **One evaluate/notify path per package.** "There is ONE evaluate notify
    path PER package (orch/lite) regardless of whether it is called by cron or
    console." Sender is the configured `tool_identity`. Records:
    REQ-CORE-0017, REQ-CORE-0018.

## Requirements process

15. **Shared or package, never hybrid.** "Make sure the requirements/ADR are
    partitioned so common requirements are in one place, specific req/adr in
    package-specific location. Do NOT write requirements with IF orch ELSE lite
    in them. I expect we will write dozens of packages and they should have
    shared or individual req/adr, not hybrid."
16. **Plan.** "The goal is to get atm-bd-lite locked down w/ requirements,
    then rewrite atm-bd-orch and remove 90% of needless code."
17. **Raptor import is schema compliance.** "Importing is part of complying to
    the schema. The raptor cli must return helpful error messages (compiler
    grade or better)." "Missing text should warn/error on import so the team
    managing the req/adr fix/close the gap." Raptor REQ-RAP-0012.
18. **judge-jev per location.** "A single requirement mapped to multiple
    places in prompts/skills/agents/code: I would expect a separate jev query
    for each location it is satisfied. We may be able to fan out a single jev
    call w/ <location> - <question-1-req-1> | <question-2-req-1> |
    <question-3-req-2> | ... depending on how we can fit items in context."
    Pending a judge-jev record.

## Open

- Whether phase-bo ANC-064 ("close hook does not assign") is lifted for the
  write-if-wrong assigner fix (ruling 7).
- How task.start git checks fit the 2.5 s hook limit (ruling 9).
- Lite's "caller must be the phase lead" assign check after a lead change.
