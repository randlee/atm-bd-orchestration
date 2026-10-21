# atm-bd bootstrap prompt

Paste the prompt below as the first message to Claude Code or Codex, opened at the root of the repo you want to set up. It checks the machine and the repo, proposes a plan, and stops for your approval before writing anything. It ends with the console running in dry-run.

For background, see [Getting going with atm-bd](getting-started.md).

````text
You are setting up this repository to use the atm-bd workflow. In that workflow, an ATM agent team works through a planned phase tracked in beads, and the `atm-bd` console shows it and sends out sanity and QA work. Get the repo to the point where the console starts cleanly in dry-run mode. Report to me at each stop point below.

Ground rules
- Work from the repo root and run every command there. The console doesn't look in parent folders.
- Check before you change. Don't create or overwrite any config file until I've approved the plan in step 3.
- If a tool is missing, an identity is wrong, or `bd doctor` reports an error, stop and report it. Never work around it.
- Treat the docs as the source of truth, and read them before acting:
  - https://github.com/randlee/atm-bd-orchestration/blob/main/docs/getting-started.md
  - https://github.com/randlee/atm-bd-orchestration/blob/main/apps/atm-bd-console/README.md
  - https://github.com/randlee/atm-bd-orchestration/blob/main/plugins/atm-bd-orchestration/README.md
  If PR #510 hasn't merged yet, read those files from the `docs/atm-bd-readme-launch-prereqs` branch instead.

Step 1: check the machine (read-only)
Report one line per item with its version, or MISSING:
- `atm-bd`. It needs 0.18.2 or newer. If it's missing, the fix is `uv tool install atm-bd`; if it's older, `uv tool upgrade atm-bd`.
- `atm`, `bd`, `dolt`, `git`, `jq` and `gh` must be on PATH. `gh auth status` must show a logged-in account.
- The `sc-compose` CLI must be 1.7.0 or newer. If it's older, run `brew update` first, because a stale tap shows an old version; the fix is then `brew upgrade randlee/tap/sc-compose`.
- `python3 -c "import pydantic, yaml, sc_compose"` must succeed, and the `sc-compose` Python package must be the same version as the CLI. If the import fails, report the full error. If it is simply missing, the fix is `python3 -m pip install pydantic pyyaml 'sc-compose==<CLI version>'`.
- `$ATM_IDENTITY` and `$ATM_TEAM`: report their values, or note that they aren't set.
STOP. Show me the list and the fixes. Install only what I approve.

Step 2: check the repo (read-only)
Report each item as present, missing or wrong, quoting the evidence:
- `git remote get-url origin` is a GitHub URL in owner/name form.
- `.beads/` exists, and `.beads/metadata.json` has `"dolt_mode": "server"`.
- `.atm.toml` exists at the root and contains `[atm] default_team`.
- `.claude/agents/registry.yaml` exists. List which of the plugin README's required variables it has and which it lacks.
- These may already exist from an earlier install. Note any that do, and whether they're in the current format:
  - `.claude/skills/atm-bd-orchestration/`
  - `.claude/project/atm-bd-orchestration.yaml`
  - an install record named `atm-bd-install.json`
  - `.atm-bd/phase-*.toml`. The current format needs `lead` and a `[templates]` table with exactly six entries: dev, fix, sanity, qa, plan_review, review.
- The team's members: `atm members --team <default_team>`.

Step 3: propose a plan
List exactly which files you'll create or edit, with their proposed contents. For each registry variable and each role (lead, dev-sanity member, QA member, round-1 reviewers), say what value you propose and why. Ask me for anything you can't infer, especially the team name, which member leads, and the plans folder.
STOP and wait for my approval.

Step 4: install (only after I approve)
1. Create or fix `.atm.toml`, `.claude/agents/registry.yaml` and the beads server mode, as approved.
2. Run `atm-bd skill` from the repo root. Add `--set name=value` for anything approved but missing from the registry. Use `--codex` only if I asked for a Codex install.
3. If it fails, report the exact error and stop. Don't retry with different flags unless I say so.
4. Confirm that `.claude/project/atm-bd-orchestration.yaml` was written and that `atm-bd@tool` (or the configured `tool_identity`) is now a team member.

Step 5: set up the first phase (only if I've given you a phase id and a lead)
1. Run `.claude/skills/atm-beads/scripts/phase-config init --phase <x> --lead <member>`.
2. If I gave you a design document, use the atm-beads skill to turn it into `<plans_dir>/phase-<x>.jsonl`. Run `validate-plan --phase <x>`, then `bd import` and `bead-groups --phase <x>`. Never edit the plan or the script just to make validation pass.
3. If I didn't give you a design, stop after `phase-config init` and tell me what the plan needs.

Step 6: verify without dispatching anything
Run these and report what each one prints:
- `atm-bd queues --phase <x> --all`
- `atm-bd snapshot --phase <x> --github off --no-fetch`
- `atm-bd console --phase <x> --dry-run`: start it, confirm it renders, then quit.

Finish with a short report:
- what was installed or changed, with file paths;
- what's still missing, and who has to provide it;
- the exact command to start the console for real;
- the first three prompts I should send to the lead session, taken from the "Day to day" table in getting-started.md.
````
