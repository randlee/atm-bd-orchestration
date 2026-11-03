"""A lite-shaped profile on disk (the contract's profile.toml and cron script, verbatim), a recording runner and a
fake collector, so a tick runs end to end with controlled inputs and no ATM, bd or network."""
from __future__ import annotations

import shutil
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from atm_bd_core.profile import CronScript, LoadedProfile
from atm_bd_core.reported import reported_keys
from atm_bd_types import (
    Bead,
    ErrorId,
    PhaseFacts,
    PhaseFile,
    Refusal,
    StackFact,
    Stage,
    Status,
)
from atm_bd_types._core import CommandResult, Ports
from atm_bd_types._native import _bead, _layer, _stack

SHIPPED = Path(__file__).resolve().parents[3] / "skills" / "atm-bd-lite"
LEAD = "lead-agent"
QA = "qa-agent"
STARTUP_PARAMS = 'dev_agent = "dev-agent"\nlead = "lead-agent"\ndev_startup = "dev instructions"\nqa_startup = "qa instructions"\nlead_startup = "lead instructions"\n'
POLICY = '[params]\nqa_agent = "qa-agent"\nqa_template = "templates/qa.xml.j2"\n' + STARTUP_PARAMS
HOOK_FILES = ["scripts/atm-bd-task-assign-hook.py", "scripts/atm-bd-task-start-hook.py",
              "scripts/atm-bd-task-hook.py"]
TEMPLATE_FILES = ["templates/refuse.md.j2", "templates/dev-close.md.j2", "templates/qa-pass.md.j2",
                  "templates/qa-findings.md.j2", "templates/land-close.md.j2", "templates/qa.xml.j2"]


def make_profile(root: Path, policy: str | None = POLICY) -> Path:
    """Write the contract profile.toml, its named files and `policy` (None: no policy.toml)."""
    skill = root / "skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "templates").mkdir()
    shutil.copy(SHIPPED / "profile.toml", skill / "profile.toml")
    shutil.copy(SHIPPED / "scripts" / "atm-bd-cron.py", skill / "scripts" / "atm-bd-cron.py")
    for name in [*HOOK_FILES, *TEMPLATE_FILES]:
        (skill / name).write_text("x\n", encoding="utf-8")
    if policy is not None:
        (skill / "policy.toml").write_text(policy, encoding="utf-8")
    return skill / "profile.toml"


def make_primary(root: Path, profile: str = "lite") -> Path:
    """A primary checkout with .atm-bd/phase-bo.toml naming `profile`."""
    primary = root / "primary"
    (primary / ".atm-bd").mkdir(parents=True)
    lines = [f'profile = "{profile}"', f'profile_path = "{root / "skill" / "profile.toml"}"',
             f'lead = "{LEAD}"', 'root = "atm-phase-bo"', 'repo = "owner/repo"']
    (primary / ".atm-bd" / "phase-bo.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return primary


def qa_bead(bead_id: str = "tst-1.qa", assignee: str | None = None) -> Bead:
    return _bead(bead_id, Status.OPEN, Stage.QA, assignee, sprint="tst-1", phase="bo",
                 checked_bead=f"dev-{bead_id}")


@dataclass
class Runner:
    """Records every command; answers from `codes` in order (0 when exhausted)."""

    codes: deque[tuple[int, str]] = field(default_factory=deque)
    calls: list[tuple[list[str], str | None]] = field(default_factory=list)

    def run(self, argv: list[str], stdin: str | None) -> CommandResult:
        self.calls.append((list(argv), stdin))
        code, stderr = self.codes.popleft() if self.codes else (0, "")
        return CommandResult(code, "", stderr)


@dataclass
class Collector:
    """A fake collect(): the given ready beads; REPORTED_KEYS read from the real state file."""

    ready: list[Bead] = field(default_factory=list)
    calls: int = 0
    tasks: list = field(default_factory=list)

    def __call__(self, phase: str, phase_file: PhaseFile, ports: Ports, now: int, state_dir: Path) -> PhaseFacts:
        self.calls += 1
        keys, _ = reported_keys(state_dir)
        devs = [_bead(f"dev-{b.id}", Status.CLOSED, Stage.DEV, None, branch=f"branch-{b.id}") for b in self.ready]
        layers = [_layer(f"branch-{b.id}", "a" * 40, 42, "main") for b in self.ready]
        stack = _stack(layers)
        stack_bead = _bead("stack", Status.OPEN, Stage.STACK, None, stack=stack)
        return PhaseFacts(phase, now, phase_file, self.tasks, [], keys, None, None, [*self.ready, *devs],
                          list(self.ready), StackFact(stack_bead, stack, "main", None), None, None, [])


def refusal_id(value: LoadedProfile | CronScript | Refusal | None) -> ErrorId | None:
    """The ErrorId of a loader refusal; None when the loader returned a value."""
    if value is None or isinstance(value, (LoadedProfile, CronScript)):
        return None
    return value.id


def ports(runner: Runner) -> Ports:
    return Ports(runner, object())
