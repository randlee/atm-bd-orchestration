# pyright: strict
"""Provider-independent stack checks using only Git and typed results."""
from __future__ import annotations

import re
import shlex
import subprocess
from collections.abc import Callable
from pathlib import Path

from atm_bd_types import Error, ErrorDetail, ErrorKind, StackGateResult
from result import Err, Ok, Result


class GitStackGate:
    """Check the PR base, pushed branch head and local remote-tracking ancestry."""

    def __init__(self, cwd: Path, *, runner: Callable[..., subprocess.CompletedProcess[str]] | None = None) -> None:
        self.cwd = cwd
        self.runner = runner or subprocess.run

    def _git(self, *args: str) -> Result[subprocess.CompletedProcess[str]]:
        argv = ["git", *args]
        try:
            return Ok(self.runner(argv, cwd=self.cwd, capture_output=True, text=True, check=False, timeout=180))
        except (OSError, subprocess.TimeoutExpired) as exc:
            return Err(Error(ErrorKind.UNREACHABLE, str(exc), f"Restore Git access and retry `{shlex.join(argv)}`."))

    def _failure(self, command: list[str], completed: subprocess.CompletedProcess[str]) -> Err:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        return Err(Error(ErrorKind.COMMAND_FAILED, detail, f"Repair and retry `{shlex.join(command)}`.",
                         ErrorDetail.CommandFailed(command, completed.returncode, detail)))

    def check(self, pr_base_ref: str, head_branch: str, head_sha: str,
              stack_top_branch: str, remote: str = "origin") -> Result[StackGateResult]:
        """Return repository facts only; operational failures remain typed errors."""
        base = pr_base_ref.removeprefix("refs/heads/")
        top = stack_top_branch.removeprefix("refs/heads/")
        if base != top:
            return Ok(StackGateResult.NotStacked(top, base))
        if not all(value and not value.startswith("-") and not any(c.isspace() for c in value)
                   for value in (head_branch, top, remote)) or not re.fullmatch(r"[0-9a-fA-F]{7,64}", head_sha):
            return Err(Error(ErrorKind.CONFIG_INVALID, "invalid branch, remote or head SHA", "Supply valid Git references and a hexadecimal commit SHA."))
        refs = ["git", "ls-remote", "--exit-code", "--", remote, f"refs/heads/{head_branch}"]
        pushed = self._git(*refs[1:])
        if isinstance(pushed, Err):
            return pushed
        if pushed.value.returncode == 2 and not pushed.value.stderr.strip():
            return Ok(StackGateResult.NotPushed(head_branch, head_sha))
        if pushed.value.returncode:
            return self._failure(refs, pushed.value)
        rows = [line.split() for line in pushed.value.stdout.splitlines() if line.strip()]
        if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != f"refs/heads/{head_branch}":
            return Err(Error(ErrorKind.PARSE_FAILED, "invalid git ls-remote output", "Inspect the remote branch and retry."))
        if rows[0][0].lower() != head_sha.lower():
            return Ok(StackGateResult.NotPushed(head_branch, head_sha))
        rev = ["git", "rev-parse", "--verify", f"refs/remotes/{remote}/{top}^{{commit}}"]
        resolved = self._git(*rev[1:])
        if isinstance(resolved, Err):
            return resolved
        if resolved.value.returncode:
            return self._failure(rev, resolved.value)
        base_sha = resolved.value.stdout.strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", base_sha):
            return Err(Error(ErrorKind.PARSE_FAILED, "invalid remote base commit", "Fetch the remote base and retry."))
        ancestry = ["git", "merge-base", "--is-ancestor", base_sha, head_sha]
        checked = self._git(*ancestry[1:])
        if isinstance(checked, Err):
            return checked
        if checked.value.returncode == 1:
            return Ok(StackGateResult.NotAncestor(base_sha, head_sha))
        if checked.value.returncode:
            return self._failure(ancestry, checked.value)
        return Ok(StackGateResult.Stacked())
