# atm-bd-orchestration

ATM + Beads orchestration skill pack, published as a Claude Code plugin
marketplace and as a synaptic-canvas style package for `sc-install`
(`.claude` and `.codex` targets).

```
.claude-plugin/marketplace.json          the marketplace manifest
plugins/
  atm-bd-orchestration/                  one package: skills + agents + installer
    .claude-plugin/plugin.json           Claude Code plugin manifest
    manifest.yaml                        sc-install package manifest (artifacts, requires)
    registry.yaml                        repository values rendered at install time
    install.py                           sc-install hook (prepare/complete/cleanup) and standalone installer
    skills/{atm-beads,atm-bd-orchestration,sprint-report,sprint-review}/
    agents/{dev-sanity,dev-sanity-llm,sc-sanity-llm,dev-sanity-jev,sc-sanity-jev}.md
    assets/scripts/jev_client.py         Jev transport, placed at <repo>/scripts/jev_client.py
    tests/                               package consistency and install tests
```

## Use it

Claude Code marketplace:

```
/plugin marketplace add randlee/atm-bd-orchestration
/plugin install atm-bd-orchestration@atm-bd-orchestration
```

Then install the package into the repository where the agents run, because the
skills execute repository-relative scripts and dispatch templates:

```bash
python3 plugins/atm-bd-orchestration/install.py --dest /path/to/repo/.claude
python3 plugins/atm-bd-orchestration/install.py --dest /path/to/repo/.codex
```

`skills/atm-bd-orchestration/references/bv.md` tells the lead how to use BV
graph analysis (`scripts/bv-analyze`) to optimize work in progress and plan
continuing work. BV is optional.

`install.py` reads the team from `.atm.toml` and the repo slug from git origin.
Pass lead/sanity member names with `--set` when using `.atm.toml` agent
configuration; the installer also supports legacy agent-registry defaults.
Repository values are rendered into the installed copy with `sc-compose`.
Details, variables and overrides: [plugins/atm-bd-orchestration/README.md](plugins/atm-bd-orchestration/README.md).

synaptic-canvas will reference this repository's package with a `git-subdir`
marketplace entry and list it in its `sc-install` registry at release time;
nothing is copied.

## Develop

```bash
cd plugins/atm-bd-orchestration
python3 -m pytest -q tests assets/scripts/tests
python3 tests/gen_manifest.py   # after adding or removing a skill or agent file
```

No repository- or team-specific string may appear in `skills/` or `agents/`;
`tests/test_install.py` fails on the known ones. A value that differs per
repository becomes a variable in `registry.yaml`, never an edit.
