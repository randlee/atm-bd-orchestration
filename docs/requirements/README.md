# Role Requirements

One file per agent, with its subagents and scripts: what it does, when, in what order. Each file has `Requirements` (checked against the package sources) and `Unresolved` (package sources that contradict each other). A prompt line that maps to no requirement goes to review: the requirement may be missing.

| File | Agent |
| --- | --- |
| [dev.md](dev.md) | dev, dev-fix, fix; `assignment-gates.py` |
| [dev-sanity.md](dev-sanity.md) | dev-sanity with sc-sanity-llm, sc-sanity-jev; sanity scripts |
| [quality-mgr.md](quality-mgr.md) | QA, plan review, phase-end review; reviewers, ceremony screen |
| [planner.md](planner.md) | design to beads; `validate-plan` |
| [team-lead.md](team-lead.md) | sequencer; swarm-master (none in the package) |
| [parallax.md](parallax.md) | work-orchestrator teammate (optional) |
