# atm-bd bootstrap prompt

Paste the prompt below as the first message to Claude Code or Codex, opened at the root of the repo you want to set up. It checks the machine and the repo, proposes a plan, and stops for your approval before writing anything. It ends with the console running in dry-run.

For background, see [Getting going with atm-bd](getting-started.md).

````text
You are setting up this repository to use the atm-bd workflow. In that workflow, an ATM agent team works through a planned phase tracked in beads, and the `atm-bd` console shows it and sends out QA work once sanity passes. Sanity work is sent by the dev's own close, not by the console. Get the repo to the point where the console starts cleanly in dry-run mode. Report to me at each stop point below.

Ground rules
- Work from the repo root and run every command there. The console doesn't look in parent folders.
- Check before you change. Don't create or overwrite any config file until I've approved the plan in step 3.
- If a tool is missing, an identity is wrong, or `bd doctor` reports an error, stop and report it. Never work around it.
- Treat the docs as the source of truth, and read them before acting. Where this prompt names a section, it means a section of getting-started.md; follow it there rather than from memory:
  - https://github.com/randlee/atm-bd-orchestration/blob/main/docs/getting-started.md
  - https://github.com/randlee/atm-bd-orchestration/blob/main/apps/atm-bd-console/README.md
  - https://github.com/randlee/atm-bd-orchestration/blob/main/plugins/atm-bd-orchestration/README.md

Step 1: check the machine (read-only)
Report one line per item with its version, or MISSING, against the table in "One-time machine setup":
- `atm-bd`. These steps need 0.19.2, the first release that adds the dev-sanity member and lists its changes when it installs. If it's missing, the fix is `uv tool install atm-bd`; if it's older, `uv tool upgrade atm-bd`.
- `atm` must be 1.6.3 or newer, and `atm hook --help` must work. 1.6.3 is currently a GitHub prerelease from randlee/atm-core; until a stable release has `atm hook`, install that prerelease. `brew install randlee/tap/atm` gives 1.6.1, which lacks `atm hook` and `atm cron`.
- `python3`, `bd`, `dolt`, `git`, `jq`, `gh` and the `gh stack` extension must be on PATH, at the versions in the table. `gh auth status` must show a logged-in account.
- The `sc-compose` CLI must be 1.7.0 or newer, below 2. If it's older, run `brew update` first, because a stale tap shows an old version; the fix is then `brew upgrade randlee/tap/sc-compose`.
- `python3 -c "import pydantic, yaml, sc_compose"` must succeed, and the `sc-compose` Python package must be the same version as the CLI. If the import fails, report the full error. If it is simply missing, the fix is `python3 -m pip install pydantic pyyaml 'sc-compose==<CLI version>'`. The copy of the wheel inside `atm-bd`'s uv tool environment must match the CLI too; the guide gives the reinstall command.
- `$ATM_IDENTITY` and `$ATM_TEAM`: report their values, or note that they aren't set.
- `$TYPESAFE_API_KEY`: report only whether it is set, never its value. The dev-sanity and quality-mgr agents need it for Jev.
STOP. Show me the list and the fixes. Install only what I approve.

Step 2: check the repo (read-only)
Report each item as present, missing or wrong, quoting the evidence:
- `git remote get-url origin` is a GitHub URL in owner/name form.
- `.beads/` exists, and `.beads/metadata.json` has `"dolt_mode": "server"`.
- `.atm.toml` exists at the root and contains `[atm] default_team`.
- `.claude/agents/registry.yaml` exists. List which of the plugin README's required variables it has and which it lacks, and whether `roles:` names a lead, a quality-mgr and a dev-sanity member.
- The file `policy_path` names exists.
- The agents and skills atm-bd does not ship, as listed in "One-time repo setup": `.claude/agents/quality-mgr.md`, an agent file for every name in `reviewers_round1`, `req-qa`, `arch-qa`, `plan-scope-reviewer` and `ceremony-finding-screen`, and the `sc-gh-stack` and `sc-gh-stack-view` skills.
- These may already exist from an earlier install. Note any that do, and whether they're in the current format:
  - `.claude/skills/atm-bd-orchestration/`
  - `.claude/project/atm-bd-orchestration.yaml`
  - the install records `.claude/project/atm-bd-orchestration.lock.json` and `.claude/atm-bd-install.json`
  - `.atm-bd/phase-*.toml`. The current format needs nonempty `plan`, `root`, `integration_branch` and `lead`, and a `[templates]` table with dev, fix, sanity, qa, plan_review and review, each an existing file under `.claude/skills/atm-bd-orchestration/templates/`. A legacy `dev_fix` entry is tolerated; any other key is an error. `code_checkout` is optional.
- `.gitignore` has these three lines: `.atm-bd/sanity-close/`, `.atm-bd/*.bd-cache.sqlite3*`, `.atm-bd/*.bd-cache.drain.*`.
- The team's members: `atm members --team <default_team>`, with each member's alias from its `[[rmux.windows.panes]]` entry in `.atm.toml`, if any.

Step 3: propose a plan
List exactly which files you'll create or edit, with their proposed contents. For each registry variable and each role (lead, dev-sanity member, QA member, round-1 reviewers), say what value you propose and why. Ask me for anything you can't infer, especially the team name, which member leads, and the plans folder.
- The dev-sanity member's name, or its alias, must be unique on this computer, not only in the team, because herdr finds an agent by its alias, else its member name. Propose one like `<3-letter repo prefix>-sanity` (`rap-sanity` for raptor) as `roles.dev-sanity`, and check it against the members of every team on this computer. Propose the same host-unique aliases for the lead, quality-mgr and devs, as "Setting up the team" describes.
- Propose the `.atm.toml` startup blocks and launch environment (`ATM_IDENTITY`, `ATM_TEAM`, `BEADS_ACTOR`) from "Setting up the team", including the recommended `[startup.<dev-sanity-member>]` block from "One-time repo setup". The installer prints that block but never writes `.atm.toml`; it is added only if I approve.
- For anything in step 2 that atm-bd doesn't ship, say where it comes from. The two stack skills install in Claude Code with `/sc-manage --install sc-gh-stack --local`. The quality-mgr and reviewer agents are not shipped by any package yet; the repo must supply them, so ask me for them.
STOP and wait for my approval.

Step 4: install (only after I approve)
1. Create or fix `.atm.toml` (including the approved startup blocks), `.claude/agents/registry.yaml` and the beads server mode, as approved.
2. Run `atm-bd skill` from the repo root. Add `--set name=value` for anything approved but missing from the registry. Use `--codex` only if I asked for a Codex install.
3. If it fails, report the exact error and stop. Don't retry with different flags unless I say so.
4. Show me the list of changes it prints, every `NOT DONE:` line, and the recommended `.atm.toml` block. Confirm that `.claude/project/atm-bd-orchestration.yaml` was written, that `atm-bd` is a member of the `tool` team (`atm members --team tool`), and that the dev-sanity member is on our team. If `tool_identity` is set in that file, confirm that identity exists instead of `atm-bd`. For a `NOT DONE:` line, run the command it gives only after I approve.
5. Add the remaining team members (lead, quality-mgr, each dev) as approved, with the `atm teams add-member` command in "Setting up the team".
6. Add the three `.gitignore` lines from step 2 if any are missing.
7. If a phase file already existed, this is an upgrade: follow the upgrade paragraph in "One-time repo setup". Ask me before the step 7 hook and crons for each active phase (see step 5 below). Run `.claude/skills/atm-bd-orchestration/scripts/close_fields_backfill.py --phase <x>` once for each active phase and show me the plan it prints; add `--apply --actor <identity>` only after I approve.

Step 5: set up the first phase (only if I've given you a phase id and a lead)
1. Run `.claude/skills/atm-beads/scripts/phase-config init --phase <x> --lead <member>`.
2. If I gave you a design document, follow steps 2 to 6 of "Starting a phase", in order: the integration branch, `bd doctor --json`, the plan written as `.claude/skills/atm-beads/resources/planning.md` says, `validate-plan` before import, then import, `bead-groups`, the plan-review bead, the commit and push, and `validate-plan --phase <x>` on the live beads. Never edit the plan or the script just to make validation pass.
3. If I didn't give you a design, stop after `phase-config init` and tell me what the plan needs.
4. Ask me before switching on the sanity close hook, the bd-cache cron and the `atm-bd cron --phase <x>` schedule. Run them exactly as step 7 of "Starting a phase" gives them (https://github.com/randlee/atm-bd-orchestration/blob/main/docs/getting-started.md#starting-a-phase). They change local ATM daemon state, or add a schedule, but commit nothing and dispatch nothing.

Step 6: verify without dispatching anything
Run these and report what each one prints:
- `atm-bd queues --phase <x> --all`
- `atm-bd snapshot --phase <x> --github off --no-fetch`
- `atm-bd console --phase <x> --dry-run`: start it, confirm it renders, then quit.

Finish with a short report:
- what was installed or changed, with file paths;
- what's still missing, and who has to provide it;
- the exact command to start the console for real, and the `atm-bd cron --phase <x>` schedule from the plugin README's "Phase cron" section;
- who sends which work, from "Who sends which work": the lead sends plan review, dev and fix work and writes each dev's close vars file; the dev's close sends sanity; the console sends QA;
- the first three prompts I should send to the lead session, taken from the "Day to day" table in getting-started.md.
````

The installer and host `python3` require Python 3.11 or newer: above the 3.11 floor the installer probes that the interpreter can import the sc-compose wheel (1.7.0 ships cp311 wheels only, so newer interpreters build it from source). [CPython 3.14 wheel request](https://github.com/randlee/sc-compose/issues/819).
