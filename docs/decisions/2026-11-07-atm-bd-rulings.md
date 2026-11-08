# atm-bd rulings, 2026-11-07 / 2026-11-08

Records cite rulings by quote, not by number.

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
   REQ-CORE-0006, REQ-CORE-0038.
6. **Bead assignee.** "In planning assignee should be fast/normal/frontier so
   exact dev is not locked in. At task assign, assignee should be set by
   phase-lead to agent-name." Records: REQ-CORE-0007, REQ-CORE-0008.
7. **Sanity/QA assigner = dev task's assigner, set by ATM task hooks.** "For
   sanity and qa task assign, the assigner must be set based from what is read
   from the dev task assigner. This can occur at 'atm task assign <dev>' in an
   assign hook, AND it can also occur at the 'atm task close <dev-task>' hook
   ... doing it in both places would be prudent ... the 2nd close-hook
   assignment should do a write IF NOT correct. No need to actually write a
   bead to db w/ redundant data." Records: REQ-CORE-0009 (the reviewing ATM task's assigner field), REQ-CORE-0010.
8. **Messages go to the task's assigner.** "This is even more important,
   because sometimes lead transitions mid phase (i.e. out of tokens)."
   Supersedes phase-bj ANC-051/052/053 (messages to `<phase-lead>`) and the
   parallax per-wave lead ("parallax is ONLY lead for a wave, NOT lead for the
   phase"). Records: REQ-CORE-0011, REQ-PLX-0009.

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
    REQ-DSAN-0061, REQ-CORE-0028 (phase-lead close where a package grants it).
12. **Jev sanity.** "The strategy for how to prompt jev sanity needs to get
    reviewed and tightened. For now we need documentation and code in sync."
    Records: REQ-DSAN-0051..0057 describe today's `jev_client.py`.

## Tooling

13. **bd-cache everywhere.** "Everything in atm-bd (including agent 'bd'
    instructions) need to use bd-cache." Record: REQ-CORE-0034.
14a. **bd-cache is the phase's source of truth.** "I expect that the cache
    matches the bd api as closely as possible (json)." "I would expect changes
    'from upstream' to be rare. The bd-cache should be the source of truth for
    the phase." "beads-cache (rust daemon using tokio) is already in
    development based on requirements coming from atm-bd, and changes must
    align w/ beads-cache api." So atm-bd needs (bead create, write semantics)
    are filed as beads-cache requirements and consumed through its API; atm-bd
    never adds its own bead layer. Journaled create is beads-cache #104.
    Records: REQ-CORE-0034, REQ-CORE-0039, ADR-CORE-0006.

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
    Records: REQ-CORE-0040, ADR-CORE-0007.
16. **Plan.** "The goal is to get atm-bd-lite locked down w/ requirements,
    then rewrite atm-bd-orch and remove 90% of needless code."
    Record: ADR-CORE-0002.
17. **Raptor import is schema compliance.** "Importing is part of complying to
    the schema. The raptor cli must return helpful error messages (compiler
    grade or better)." "Missing text should warn/error on import so the team
    managing the req/adr fix/close the gap." Raptor REQ-RAP-0012.
18. **judge-jev per location.** "A single requirement mapped to multiple
    places in prompts/skills/agents/code: I would expect a separate jev query
    for each location it is satisfied. We may be able to fan out a single jev
    call w/ <location> - <question-1-req-1> | <question-2-req-1> |
    <question-3-req-2> | ... depending on how we can fit items in context."
    Record: judge-jev REQ-JEV-0206 (randlee/judge-jev #4); the batching
    option conflicts with REQ-JEV-0202 and is open.

19. **Rulebook location.** "All of the REQ/ADR are to be on
    atm-bd-orchestration repo, not on atm-core." Record: ADR-CORE-0001.
20. **Simple, isolated entry points.** "The complexity of atm-bd is FAR too
    large for us to make these changes reliably. This is why I keep pushing
    for a simple implementation that isolates every hook/command against
    requirements. Trying to apply 100's of requirements against 10000+ lines
    of code is not going to be easy." Record: ADR-CORE-0003.
21. **Order of work.** "First priority is making sure our rulebook is
    written." "Mis-recording these rulings is the biggest risk." Rulings are
    written first, then duplication is removed, all on one gh stack against
    atm-bd-orchestration.

22. **Review beads carry the assigner.** "I thought qa+sanity beads were
    poured before planning is complete. They should be around for a long
    time before dev task assignment." The dev assign hook records the dev
    task's assigner on them; the close hook rewrites it only if wrong.
    Records: REQ-CORE-0009, REQ-CORE-0010, REQ-CORE-0029 (one-write limit
    removed).
23. **Checks: bd-cache, local git, gh before assign.** "I already told you
    that bd-cache should be used for all read/writes. Yes, local git to be
    used. gh checks must be done before task.assign and passed to
    task-assign w/ evidence." Records: REQ-CORE-0012, REQ-CORE-0041.
24. **Hooks return ATM commands.** "The atm-core hooks return an array of
    atm commands that atm will run post-hook. (no atm-core change
    necessary)" Record: REQ-CORE-0013.
25. **Fewer checks.** "You are getting too aggressive on checks." "You are
    continually trying to check everything, this is why the simple 100 line
    solution continuously gets 1000's of lines of code." Records:
    REQ-LITE-0003 retired, REQ-CORE-0029.
26. **No dev auto-assign in lite.** "I don't know when the decision for dev
    to auto assign in atm-bd-lite was made. This makes atm-bd-lite more
    complicated than necessary for mvp." It came from aec7860b4
    (2026-11-02) with no recorded ruling. Record: REQ-LITE-0014 retired.
27. **Lead sanity close confirmed.** "confirm. verify that this unlocks qa
    and qa bead has necessary info." Verified: a close with reason
    `PASS at <PR head sha>` unlocks QA; any other reason leaves QA refused
    `SANITY_STALE`. Record: REQ-DSAN-0061 notes.
28. **Who acts.** "task assignment are made by tool using phase-lead
    identity (or assigner in the case of sanity/qa). reports/notices always
    come from tool_identity." Records: REQ-CORE-0001, REQ-CORE-0018.

29. **Purpose: take load off the phase lead.** "This process works w/ NO
    automation and has for weeks. The problem is at scale, there are way too
    many messages/responsibilities for phase-lead and getting 5+ messages in
    10 seconds overwhelms his context. The atm-task hook performing
    validation and auto assignment makes this manageable. However by adding
    code that is too strict/fails and sends errors to phase-lead directly
    impacts the usability. i.e. it defeats that entire reason we created
    atm-bd in the first place." Record: ADR-CORE-0008.

## Open

- judge-jev: whether one Jev call may carry several records for one
  location (REQ-JEV-0202 vs ruling 18).
- atm-bd-types crate: keep or drop (no ruling yet).
- D8 batch of small orchestration-record rulings (Rand's cut-off item 8).
