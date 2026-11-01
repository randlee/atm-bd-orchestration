# pyright: strict
"""Provider-backed stack-link decisions; legacy lock and CLI remain in stack_link."""
from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, cast

from atm_bd_types import Error, ErrorKind, PrOp, PrRef, ProviderCommands
import repo_config
from sprint_index_common import is_json_object
import providers
from result import Err, Ok, Result
from stack_top import select_stack_top


def problem(message: str) -> Err:
    return Err(Error(ErrorKind.REJECTED, message, "Repair the stack ledger or provider operation and retry."))


def provider_call(linker: Any, commands: ProviderCommands, context: dict[str, str], op: PrOp,
                  values: dict[str, str | list[str]]) -> Result[PrRef | providers.MergedPrRef | providers.JsonValue]:
    def run(argv: list[str], **kwargs: Any) -> Any:
        return linker.command(argv, check=False)
    return providers.execute(commands, op, {**context, **values},
                             cwd=Path(linker.values.get('worktree_path') or '.'), runner=run)


def execute(self: Any) -> Result[dict[str, Any]]:
    timeout = self.acquire()
    if timeout:
        return Ok(timeout)
    bead: dict[str, Any] = self.bead()
    raw: Any = copy.deepcopy(bead.get('metadata'))
    if not isinstance(raw, dict):
        return problem("stack bead metadata is invalid")
    metadata = cast(dict[str, Any], raw)
    if (not isinstance(metadata.get('trunk'), str) or not metadata['trunk'] or
            not isinstance(metadata.get('layers'), list) or
            (metadata.get('stack_number') is not None and (type(metadata['stack_number']) is not int or metadata['stack_number'] <= 0))):
        return problem('stack bead metadata is invalid')
    layers = cast(list[dict[str, Any]], metadata['layers'])
    previous: str = metadata['trunk']
    branches: set[str] = set()
    numbers: set[int] = set()
    for layer in layers:
        if (not isinstance(cast(object, layer), dict) or not isinstance(layer.get('branch'), str) or not layer['branch'] or
                type(layer.get('pr')) is not int or layer['pr'] <= 0 or not isinstance(layer.get('head'), str) or
                not re.fullmatch(r'[0-9a-fA-F]{7,64}', layer['head']) or
                not isinstance(layer.get('linked', True), bool) or layer.get('base') != previous or
                layer['branch'] in branches or layer['pr'] in numbers):
            return problem('stack bead has an invalid layer')
        previous = layer['branch']
        branches.add(layer['branch'])
        numbers.add(layer['pr'])
    original = copy.deepcopy(metadata)
    root = Path(self.values.get('worktree_path') or '.')
    try:
        config = repo_config.load(root)
    except repo_config.ConfigNotFound:
        config = {"provider": "github"}
    except (repo_config.ConfigError, OSError) as exc:
        return Err(Error(ErrorKind.CONFIG_INVALID, str(exc), "Repair the repository configuration."))
    loaded = providers.load_provider(config)
    if isinstance(loaded, Err):
        return loaded
    commands = loaded.value
    context: dict[str, str] = {}
    azure = config.get("azure")
    if is_json_object(azure):
        for name in ("organization", "project", "repository"):
            value = azure.get(name)
            if isinstance(value, str):
                context[name] = value
    candidate_result = provider_call(self, commands, context, PrOp.LOOKUP_BY_HEAD,
                                     {'head': self.values['branch'], 'state': 'open', 'head_sha': self.values['commit']})
    if isinstance(candidate_result, Err):
        return candidate_result
    candidate = candidate_result.value
    if (not isinstance(candidate, PrRef) or candidate.number != str(self.values['pr_number']) or
            candidate.head_sha != self.values['commit'] or candidate.draft):
        return problem('checked pull request is missing, draft, or differs from the pinned branch and commit')
    refreshed = self.bead()
    if refreshed.get('assignee') != self.actor or refreshed.get('metadata') != original:
        return problem('stack claim or ledger changed during reconciliation')
    self.command(['git', 'fetch', 'origin'])
    def resolve_head(branch: str) -> str:
        return cast(str, self.command(['git', 'rev-parse', 'refs/remotes/origin/' + branch]).stdout.strip())
    recorded = next((layer for layer in layers if layer['pr'] == self.values['pr_number'] or layer['branch'] == self.values['branch']), None)
    if recorded is not None:
        selected, selected_head = select_stack_top({'metadata': metadata}, metadata['trunk'], resolve_head)
        if resolve_head(selected) != selected_head:
            return problem('recorded stack top differs from the fetched branch head')
        if (recorded['pr'] != self.values['pr_number'] or recorded['branch'] != self.values['branch'] or
                recorded['head'] != self.values['commit'] or candidate.base != recorded['base'] or
                resolve_head(recorded['branch']) != self.values['commit']):
            return problem('checked layer conflicts with its recorded pinned commit')
        if recorded.get('linked', True):
            top, top_head = select_stack_top({'metadata': metadata}, metadata['trunk'], resolve_head)
            if resolve_head(top) != top_head:
                return problem('recorded stack top differs from the fetched branch head')
            return Ok({'result': 'stacked', 'top': layers[-1], 'stack_number': metadata.get('stack_number')})
        if recorded is not layers[-1]:
            return problem('checked unlinked layer is not the next stack layer')
        base = recorded['base']
        recorded_head = resolve_head(base)
    else:
        base, recorded_head = select_stack_top({'metadata': metadata}, metadata['trunk'], resolve_head)
    actual = resolve_head(base)
    if actual != recorded_head:
        return problem('fetched stack top differs from its recorded head')
    ancestor = self.command(['git', 'merge-base', '--is-ancestor', 'origin/' + base, self.values['commit']], check=False)
    if ancestor.returncode == 1:
        contained = self.command(['git', 'merge-base', '--is-ancestor', self.values['commit'], 'origin/' + base], check=False)
        if contained.returncode not in (0, 1):
            return problem(f'git ancestry check failed: {contained.stderr}')
        steps = ([{'option': 'relink_in_git_order', 'steps': [f"do not rebase {self.values['branch']}", 'Ask the stack owner to repair the ledger in Git order.']}]
                 if contained.returncode == 0 else
                 [{'option': 'rebase', 'steps': [f'git rebase origin/{base}', 'git push --force-with-lease', 'Request a new sanity check.']}])
        return Ok({'result': 'rebase_required', 'top': {'branch': base, 'head': actual},
                   'evidence': f"origin/{base} is not an ancestor of {self.values['commit']}", 'next_steps': steps})
    if ancestor.returncode:
        return problem(f"git merge-base --is-ancestor [{ancestor.returncode}] {(ancestor.stderr or '').strip()}")
    if candidate.base != base:
        intervening = self.command(['git', 'merge-base', '--is-ancestor', 'origin/' + base, 'origin/' + candidate.base], check=False)
        if intervening.returncode == 0:
            return problem(f'PR base {candidate.base} descends from the recorded top {base}; repair the missing ledger layer before retargeting')
        if intervening.returncode != 1:
            return problem(f'cannot verify PR base ancestry: {intervening.stderr}')
        edited = provider_call(self, commands, context, PrOp.EDIT_BASE, {'number': candidate.number, 'base': base})
        if isinstance(edited, Err):
            return edited
    new = recorded or {'branch': self.values['branch'], 'pr': self.values['pr_number'], 'head': self.values['commit'], 'base': base, 'linked': False}
    if recorded is None:
        layers.append(new)
    link_command = commands.command('stack_link')
    if link_command is None:
        return problem('provider has no stack link operation')
    if not link_command.argv:
        new['linked'] = True
    else:
        pending = [layer for layer in layers if not layer.get('linked', True)]
        number = metadata.get('stack_number')
        if number is not None or len(pending) >= 2:
            arguments = ([str(number), *[str(layer['pr']) for layer in pending]] if number is not None else
                         ['--base', metadata['trunk'], *[str(layer['pr']) for layer in pending]])
            linked = provider_call(self, commands, context, PrOp.STACK_LINK, {'number': arguments})
            if isinstance(linked, Err):
                if number is None:
                    checkout = ' '.join(('gh', 'stack', 'checkout', str(new['pr'])))
                    return Err(Error(linked.error.kind, linked.error.message,
                                     f'Run `{checkout}` in a worktree with no stale tracking, repair the stack ledger, then retry.'))
                return linked
            output = linked.value
            pattern = link_command.result.get('stack_number', '')
            match = re.search(pattern, output) if pattern and isinstance(output, str) else None
            if not match or not match.group(1).isdigit():
                checkout = ' '.join(('gh', 'stack', 'checkout', str(new['pr'])))
                return Err(Error(ErrorKind.PARSE_FAILED, 'stack number missing from provider output',
                                 f'Run `{checkout}` in a worktree with no stale tracking, repair the stack ledger, then retry.'))
            metadata['stack_number'] = int(match.group(1))
            for layer in pending:
                layer['linked'] = True
    self.write(metadata)
    return Ok({'result': 'stacked', 'top': new, 'stack_number': metadata.get('stack_number')})
