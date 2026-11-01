# pyright: strict
"""Read-only full-profile close preflight, with actionable typed refusals."""
from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable
from pathlib import Path

from atm_bd_types import Error, ErrorKind, PrRef, StackGateResult
import pr_lookup
import providers
import repo_config
from result import Err, Ok, Result
from stack_gate import GitStackGate
from stack_top import JsonObject, is_json_object, select_stack_top


def preflight(root: Path, worktree: Path, branch: str, head: str, bead: JsonObject,
              fallback: str, runner: Callable[..., subprocess.CompletedProcess[str]]) -> Result[tuple[PrRef, str]]:
    def failure(message: str, fix: str) -> Err:
        return Err(Error(ErrorKind.REJECTED, message, fix))
    try:
        dirty = runner(['git', 'status', '--porcelain'], cwd=worktree, capture_output=True, text=True, check=False, timeout=180)
        if dirty.returncode or dirty.stdout.strip():
            return failure('worktree is dirty or inaccessible', 'Commit changes and retry git status.')
        fetched = runner(['git', 'fetch', 'origin'], cwd=worktree, capture_output=True, text=True, check=False, timeout=180)
        if fetched.returncode:
            return failure(fetched.stderr, 'Repair origin access and retry git fetch origin.')
        def resolve(name: str) -> str:
            result = runner(['git', 'rev-parse', f'origin/{name}'], cwd=worktree, capture_output=True, text=True, check=False, timeout=180)
            return result.stdout.strip() if result.returncode == 0 else ''
        try:
            top, top_head = select_stack_top(bead, fallback, resolve)
        except ValueError as exc:
            producer = f"bd show {bead.get('id', 'stack bead')} --json"
            return Err(Error(ErrorKind.CONFIG_INVALID, f"{producer}: {exc}", f"Repair {exc} in `{producer}` and retry."))
        if resolve(top) != top_head:
            return failure(f"origin/{top} differs from the stack ledger", "Refresh or repair the stack ledger, then retry.")
        found = pr_lookup.find_pr_by_head(branch, root, expected_head=head, runner=runner)
        if isinstance(found, Err):
            return found
        pr = found.value
        metadata = bead.get('metadata')
        layers = metadata.get('layers', []) if is_json_object(metadata) else []
        if isinstance(layers, list):
            for layer in layers:
                if not is_json_object(layer) or layer.get('branch') != branch:
                    continue
                if layer.get('head') != head or str(layer.get('pr')) != pr.number:
                    return failure(f'recorded layer {branch} has a different head or PR',
                                   'Keep the recorded layer frozen and open a fix bead for changes.')
                recorded_base = layer.get('base')
                if not isinstance(recorded_base, str) or not recorded_base:
                    return failure(f'recorded layer {branch} has no base', 'Repair the stack ledger and retry.')
                top = recorded_base
                top_head = resolve(top)
                if not top_head:
                    return failure(f'cannot resolve origin/{top}', 'Fetch origin and repair the recorded base.')
                break
        checked = GitStackGate(worktree, runner=runner).check(pr.base, branch, head, top)
        if isinstance(checked, Err):
            return checked
        fact = checked.value
        if isinstance(fact, StackGateResult.NotStacked):
            try:
                config = repo_config.load(root)
            except repo_config.ConfigNotFound:
                config = {'provider': 'github'}
            loaded = providers.load_provider(config)
            if isinstance(loaded, Err):
                return loaded
            operation = loaded.value.command('edit_base')
            if operation is None:
                return failure('missing edit_base provider operation', 'Repair the provider configuration.')
            context = {'number': pr.number, 'base': top}
            azure = config.get('azure')
            if isinstance(azure, dict):
                context.update({str(key): value for key, value in azure.items() if isinstance(value, str)})
            command = shlex.join([part.format_map(context) for part in operation.argv])
            return failure(f'PR base {pr.base} differs from {top}', f'Run `{command}`, then retry.')
        if isinstance(fact, StackGateResult.NotPushed):
            return failure(f'branch {branch} is not pushed at {head}', f'Run `git push origin {shlex.quote(branch)}`, then retry.')
        if isinstance(fact, StackGateResult.NotAncestor):
            return failure(f'origin/{top} is not an ancestor of {head}', f'Run `git rebase origin/{shlex.quote(top)}` and `git push --force-with-lease`, then retry.')
        if isinstance(fact, StackGateResult.Stacked):
            return Ok((pr, top_head))
        return failure('unknown stack gate result', 'Repair the stack gate and retry.')
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, repo_config.ConfigError) as exc:
        return Err(Error(ErrorKind.COMMAND_FAILED, str(exc), 'Repair Git, provider, or stack ledger configuration and retry.'))
