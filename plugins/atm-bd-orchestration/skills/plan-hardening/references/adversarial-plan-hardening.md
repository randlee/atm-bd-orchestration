# Lead Adversarial Plan Hardening

The planner is a teammate. Follow the shared iteration and final-wisp loop in
[SKILL.md](../SKILL.md), using the same rendered step template for every runner.
The lead, scope and critical passes and all adversaries run in parallel.

For each iteration:

1. List every integration with another repository or an external API (CLI,
   schema, service). Assign a researcher to each integration to find detail
   missing from the plan. Render `plan-hardening-adversary.formula.toml.j2`
   with the shared variables plus `area` naming that integration and `task`
   giving its research instruction, then create it with `bd mol wisp`.
   Require source citations for research claims.
   Follow the contract's quoting constraint for `task`. Before creation,
   constrain `area` to a lower-case hyphenated slug and parse the rendered
   TOML: render success alone does not establish TOML validity. Set `request`
   and `rendered_formula` to the scratch request and output paths, then run
   this block with `set -euo pipefail`; a failed guard stops before `bd`:

   ```bash
   set -euo pipefail
   jq -e '.compose_variables.area | type == "string" and test("^[a-z0-9]+(-[a-z0-9]+)*$")' "$request" >/dev/null
   sc-compose bead render --request "$request" --json
   uv run --no-project --python '>=3.11' python -c 'import sys,tomllib; tomllib.load(open(sys.argv[1], "rb"))' "$rendered_formula"
   bd mol wisp "$rendered_formula" --json
   ```
2. Review every existing and new requirement and ADR the plan relates to.
   Look for inconsistency, gaps and vague language. When the plan outgrows,
   contradicts or sharpens an existing requirement or ADR, file a planner
   fix bead proposing its revision through an adversary wisp with
   `area=req-adr`.
3. Review the plan yourself through an adversary wisp with `area=lead` and
   file your own findings as plan-fix beads. In iteration 2, first verify open fix beads filed by
   the `lead` and `adversary:*` passes; close resolved or cited rebutted
   findings and leave the rest open with precise remaining work.
4. Select researcher tiers using the dev-dispatch `difficulty` rule: several
   fast agents can cover broad, shallow ground in parallel; difficult code
   and integrations use frontier models, preferably different foundries.
   Background subagents are allowed and receive the rendered step prompt.
5. Never give an adversary the same task in iteration 2 as in iteration 1.
   Target a weakness iteration 1 found or an area nobody has covered.
   Record every adversary's area per iteration in its wisp title.
6. When the scope and critical passes and all adversary wisps close, assign
   the iteration's fix step to the planner. This work runs alongside the
   standard passes, rather than replacing them.

Every lead and adversary finding must record a `Verification:` section in
its `description`: name the affected plan bead and field, the concrete check
to run or source to compare, and the expected result. The lead includes this
instruction in every adversary task. This is the check the final formula
means when it says lead and adversary findings name their own check.

The final verifier reads that recorded check and compares it with the current
plan. Close the finding only when the stated check passes or a cited design
rebuttal resolves the original issue. If the check is absent or the result
does not match, leave the finding open with a note naming the missing check
or remaining mismatch; do not invent a verification rule.

Retain all adversary wisp ids for the final squash. The final ceremony, fix,
and verification sequence remains the shared loop's sequence.
