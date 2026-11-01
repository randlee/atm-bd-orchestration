# Phase bo — triaging-gh-issues

Phase `bo`. The latest integration branch on this repo is `integrate/phase-bn`,
so this plan is the next phase.

The skill is `triaging-gh-issues`. It follows the skills and agents
guidelines: the skill discovers and deploys, each agent does one thing, and
each agent returns fenced JSON.

```json
{ "success": true, "data": { "determination": "kind/bug" }, "error": null }
```

`data.determination` is one label. The skill writes that label on the bead
and the same label on the linked GitHub issue or pull request. The labels on
the bead are the state. The skill deploys an agent when the label that agent
owns is missing.

Plugin path: `plugins/triaging-gh-issues`.

## Difficulty

| Difficulty | Models |
| --- | --- |
| fast | luna, haiku |
| normal | terra, opus, sol, sonnet |
| hard | fable, opus, sol, astra |

`sol` is the same class as `opus`. No agent writes `p0`. A person sets `p0`
on one `p1` bead to schedule it ahead of the other `p1` beads.

## Config

Global logins:

```toml
# ~/.atm-bd/config.toml
[contributor]
logins = []

[approver]
logins = []
```

Repo file. Gate holds and any extra contributors for this repo:

```toml
# .atm-bd/triage.toml
[contributor]
logins = []

pr_target = ""

[gates.whitelist]
holds = ["pr"]

[gates.approver]
holds = []

[gates.priority]
blocks_above = 1
holds = ["publish"]

[gates.risk]
labels = ["arch/impact", "security/review"]
holds = ["pr", "publish"]
```

| Source | Label |
| --- | --- |
| `~/.atm-bd/config.toml` `approver.logins` | `approver` and `contributor` |
| `~/.atm-bd/config.toml` `contributor.logins` | `contributor` |
| `.atm-bd/triage.toml` `contributor.logins` | `contributor` |
| neither | blank |

The skill reads the home file first, then the repo file. `approver` is not a
key in the repo file. Home-file logins are not copied into the repo.
Acceptance criteria are not an input to either label.

`contributor` on the bead is what accepts an existing `p1` claim in
`issue-priority-classify`. `approver` is not required for that. The report
is still verified by `issue-report-verify`.

## Gates

Permanent gate beads. A match adds a `blocks` edge from the work bead to the
gate. The gate stays open. A person lets one bead through by removing that
edge and recording the agreement on the bead.

| Gate | Holds when |
| --- | --- |
| `<prefix>-gate-whitelist` | `contributor` is absent, at `gates.whitelist.holds` |
| `<prefix>-gate-approver` | `approver` is absent and `gates.approver.holds` is non-empty |
| `<prefix>-gate-priority` | priority number > `blocks_above` |
| `<prefix>-gate-risk` | any label in `gates.risk.labels` |

`p1` is priority number 1. `blocks_above = 1` holds `p2`, `p3`, and `p4`.
A manual `p0` is number 0, so the priority gate does not hold it.

With the toml above, a blank login stops before a pull request, priority
above 1 stops before publish, and `arch/impact` or `security/review` stops
before a pull request. Empty `gates.approver.holds` leaves `approver` as a
tag.

The incoming triage gate still holds the incoming epic. Triage steps link to
the incoming bead with `discovered-from`. They are not children of incoming.

## Before triage

The skill stops this list when the bead is closed or `phase-done/yes` is set.

| Missing | Agent | Difficulty | Determination | State change |
| --- | --- | --- | --- | --- |
| no bead | `issue-import` | skill, at cron | bead id | Bead in incoming, `status/needs-triage`, `contributor` and maybe `approver`. GitHub labels copied onto the bead. |
| no `dup/` | `issue-duplicate-judge` | fast | `dup/none` or `dup/#N` | `dup/#N` closes the bead and the issue with `Duplicate of #N`. |
| no `phase/` | `issue-phase-match` | fast | `phase/none` or `phase/<bead>` | Records the matching phase bead. |
| `phase/<bead>`, no `phase-done/` | `issue-phase-done` | fast | `phase-done/no` or `phase-done/yes` | `yes` stores the pull request number and full commit sha, and adds the next patch release label. |
| no `overlap/` | `issue-overlap-judge` | fast | `overlap/none` or `overlap/<bead>` | `overlap/<bead>` adds a `parent-child` edge. The incoming bead is the child. |
| no `prpair/` | `issue-prpair-judge` | fast | `prpair/none` or `prpair/#N` | Records the other open pull request. Both stay open. |

An active phase is a `.atm-bd/phase-<x>.toml` whose root bead is open. The
duplicate judge and the phase agents look at:

| Where | Match |
| --- | --- |
| Other open GitHub issues | The same request is already filed |
| Open pull requests | A pull request already does this work |
| Active phase sprint index | `phase-<x>.jsonl` already plans it |
| Open beads on that phase | The work is in progress |
| Closed beads on that phase | The work is already complete there |
| Merged pull requests on its integration branch | The work has landed on the phase |

| Scan result | What the skill does |
| --- | --- |
| `dup/#N` | Close both sides with `Duplicate of #N`. Deploy nothing further. |
| `phase-done/yes` | Store `pr` and `commit`. Add the next patch release label. Leave the issue open. |
| `overlap/<bead>` | Parent-child under the bead that owns the shared work. Triage the remainder. |
| `prpair/#N` | Leave both pull requests open. Continue triage. |
| `dup/none` and `phase/none` or `phase-done/no` | Continue triage. |

The next patch label is the patch component of `release-version.toml` plus
one. Version `0.19.12` writes the label `0.19.13`.

A matching pull request or issue with no bead is recorded on the incoming
bead. The skill does not invent a parent.

Two open pull requests for the same work stay in triage. A replacement pull
request credits the original submitter:

- Body line: `Credits: @login in #<original>`
- Replacement commits: `Co-authored-by` from the original author

`pr-author-credit` writes that credit. It is deployed when `prpair/#N` is set
and a replacement pull request is opened.

## Triage labels

Deployed only after `dup/none`, and after `phase-done/no` or `phase/none`.
The skill deploys whichever of these labels is missing.

| Missing | Agent | Difficulty | Determination |
| --- | --- | --- | --- |
| no `kind/` | `issue-kind-classify` | fast | `kind/bug`, `kind/feature`, `kind/docs`, or `kind/question` |
| no `area/` | `issue-area-classify` | fast | `area/product`, `area/skills`, or `area/workflows` |
| no `size/` | `issue-size-classify` | fast | `size/s`, `size/m`, `size/l`, or `size/xl` |
| no `priority/` | `issue-priority-classify` | fast | `priority/p1`, `priority/p2`, `priority/p3`, or `priority/p4` |
| `status/needs-triage` | `issue-report-verify` | normal | `status/verified` or `status/unverified` |
| `status/unverified`, no gap label | `issue-gap-classify` | normal | `status/needs-info`, `status/needs-repro`, or `status/needs-design` |
| no `arch/` | `issue-arch-classify` | normal | `arch/none`, `arch/impact`, or `arch/already-exists` |
| no `security/` | `issue-security-classify` | normal | `security/none` or `security/review` |

`status/verified` replaces `status/needs-triage`. An issue is triaged when
the bead exists and `status/verified` is set.

## Plan and delivery

The skill checks the gates before these deployments. A holding gate deploys
no agent.

| Missing | Agent | Difficulty | Determination |
| --- | --- | --- | --- |
| `arch/` and `security/` set, no `status/planned` | `issue-plan-write` | hard | `status/planned`, with the new plan bead id |
| `status/planned`, no plan decision | `plan-accept` | quality-mgr | `status/plan-accepted` or `status/plan-rejected` |
| `status/plan-accepted`, no pull request | cron | skill | pull request number, against `pr_target` |
| work just finished, no `pr` and `commit` | `issue-landed-record` | the close path | pull request number and full commit sha |

`issue-plan-write` puts the plan bead in `backlog-product`,
`backlog-skills`, or `backlog-workflows` from the `area/` label.

When work finishes, the close path writes this line on the issue and stores
both values on the bead:

```text
LANDED: pr=#<n> commit=<full-sha>
```

Phase work that is done also gets the next patch release label at that
moment.

## triage-close

A separate cron. Each agent still returns one determination.

| Missing | Agent | Difficulty | Determination |
| --- | --- | --- | --- |
| open issue, no `pr` and `commit` | `issue-landed-record` | fast | pull request number and full sha, or `landed/none` |
| `LANDED` and `QA-APPROVED` with `items=all`, no `status/close` | `issue-close-mark` | fast | `status/close` |
| release label and `status/close`, release published | `issue-release-close` | quality-mgr | closed, after `FIXED-RELEASED` matches the commit |

`issue-close-mark` is deployed only when both lines are present and
`items=all`. Otherwise `status/close` stays absent.

`issue-release-close` runs when that patch release is published. It closes
the issue when both of these hold:

- `QA-APPROVED` with `items=all` and the pull request merged
- `FIXED-RELEASED` showing that commit is in the release

If either is missing, the issue stays open and the agent reports which check
failed.

```text
QA-APPROVED: pr=#<n> commit=<full-sha> qa=<id> items=<all|list>
FIXED-RELEASED: release=v<x.y.z> commit=<full-sha> verified=<date> by=<model>
```

## Label mirror

At intake, labels on the GitHub issue are copied onto the bead. After that, a
label added to the bead is added to the linked issue or pull request under
the same name. Closing the bead as `dup/#N` closes that issue with
`Duplicate of #N`.
