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
- `atm-bd`. It needs 0.19.0 or newer, because `atm-bd skill` installs the skills bundled in that version. If it's missing, the fix is `uv tool install atm-bd`; if it's older, `uv tool upgrade atm-bd`.
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
  - an install record: `.claude/atm-bd-install.json` (written by `atm-bd skill`) or `.claude/project/atm-bd-orchestration.lock.json` (written by `install.py`)
  - `.atm-bd/phase-*.toml`. The current format needs nonempty `plan`, `root`, `integration_branch` and `lead`, and a `[templates]` table with dev, fix, sanity, qa, plan_review and review, each an existing file under `.claude/skills/atm-bd-orchestration/templates/`. A legacy `dev_fix` entry is tolerated; any other key is an error. `code_checkout` is optional.
- `.gitignore` has these three lines: `.atm-bd/sanity-close/`, `.atm-bd/*.bd-cache.sqlite3*`, `.atm-bd/*.bd-cache.drain.*`.
- The team's members: `atm members --team <default_team>`.

Step 3: propose a plan
List exactly which files you'll create or edit, with their proposed contents. For each registry variable and each role (lead, dev-sanity member, QA member, round-1 reviewers), say what value you propose and why. Ask me for anything you can't infer, especially the team name, which member leads, and the plans folder.
STOP and wait for my approval.

Step 4: install (only after I approve)
1. Create or fix `.atm.toml`, `.claude/agents/registry.yaml` and the beads server mode, as approved.
2. Run `atm-bd skill` from the repo root. Add `--set name=value` for anything approved but missing from the registry. Use `--codex` only if I asked for a Codex install.
3. If it fails, report the exact error and stop. Don't retry with different flags unless I say so.
4. Confirm that `.claude/project/atm-bd-orchestration.yaml` was written and that `atm-bd` is a member of the `tool` team (`atm members --team tool`). If `tool_identity` is set in that file, confirm that identity exists instead.
5. Add the three `.gitignore` lines from step 2 if any are missing.
6. If a phase file already existed, run `.claude/skills/atm-bd-orchestration/scripts/close_fields_backfill.py --phase <x>` once for each active phase. Show me the plan it prints; add `--apply` only after I approve.

Step 5: set up the first phase (only if I've given you a phase id and a lead)
1. Run `.claude/skills/atm-beads/scripts/phase-config init --phase <x> --lead <member>`.
2. If I gave you a design document, follow `.claude/skills/atm-beads/resources/planning.md`. Render the beads into `<scratch>/plan.jsonl`, with `<scratch>` outside the repo. Write the plan file `<plans_dir>/phase-<x>.jsonl` (one line per sprint). Then, in this order:
   - `.claude/skills/atm-beads/scripts/validate-plan --file <scratch>/plan.jsonl --phase <x> --index <plans_dir>/phase-<x>.jsonl`
   - `bd import --dry-run -i <scratch>/plan.jsonl`, then `bd import -i <scratch>/plan.jsonl`
   - `.claude/skills/atm-bd-orchestration/scripts/bead-groups --phase <x>`
   - commit the plan file and the phase file, and push them to the phase's `integration_branch`
   - `.claude/skills/atm-beads/scripts/validate-plan --phase <x>`, which checks the imported beads against the plan file on that branch.
   Never edit the plan or the script just to make validation pass.
3. If I didn't give you a design, stop after `phase-config init` and tell me what the plan needs.
4. Ask me before each of these. They change local ATM daemon state but dispatch nothing.
   - Register the sanity close hook (`.claude/skills/atm-bd-orchestration/scripts/SANITY-CLOSE-HOOK.md`). Run it from the repo root, with the `dev_sanity_member` from `.claude/project/atm-bd-orchestration.yaml`:
     `atm hook register task.close --phase <x> --cwd . --module .claude/skills/atm-bd-orchestration/scripts/sanity_task_close_hook.py --custom '{"task_prefix":"<bead_prefix>-<x>-","sanity_agents":["<dev_sanity_member>"]}'`
   - Start the bd-cache cron once for the repo (`.claude/skills/atm-bd-orchestration/scripts/BD-CACHE.md`):
     `atm cron start bd-cache --phase <x> --cron "*/30 * * * * *" --until-hook --module .claude/skills/atm-bd-orchestration/scripts/bd_cache_cron.py --cwd . --custom '{"team":"<default_team>"}'`

Step 6: verify without dispatching anything
Run these and report what each one prints:
- `atm-bd queues --phase <x> --all`
- `atm-bd snapshot --phase <x> --github off --no-fetch`
- `atm-bd console --phase <x> --dry-run`: start it, confirm it renders, then quit.

Finish with a short report:
- what was installed or changed, with file paths;
- what's still missing, and who has to provide it;
- the exact command to start the console for real, and the `atm-bd cron --phase <x>` schedule from the plugin README's "Phase cron" section;
- the first three prompts I should send to the lead session, taken from the "Day to day" table in getting-started.md.
````
