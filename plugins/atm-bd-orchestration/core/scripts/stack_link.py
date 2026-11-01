#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.12"
# dependencies = ["pydantic>=2", "pyyaml", "sc-compose>=1.7.0,<2", "atm-bd-types==0.20.0"]
# ///
"""Append one PR under a bead claim, keeping bd's TTL alive with 120 s heartbeats."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
import tempfile
import time

import json as _core_json
import sys as _core_sys
from pathlib import Path as _CorePath
_core = next((candidate for parent in _CorePath(__file__).resolve().parents
              for candidate in (parent / ".atm-bd/scripts", parent / "plugins/atm-bd-orchestration/core/scripts")
              if (candidate / "core_paths.py").is_file()), None)
if _core is None:
    print(_core_json.dumps({"err": {"code": "CORE.NOT_FOUND", "fix": "run atm-bd skill --dest <repository>"}}), file=_core_sys.stderr)
    raise SystemExit(3)
_core_sys.path.insert(0, str(_core))
import core_paths as _core_paths  # noqa: E402
from result import Err as _CoreErr  # noqa: E402
_core_resolved = _core_paths.core_scripts_dir(_CorePath(__file__))
if isinstance(_core_resolved, _CoreErr):
    print(_core_json.dumps({"err": {"code": "CORE.NOT_FOUND", "fix": _core_resolved.error.fix}}), file=_core_sys.stderr)
    raise SystemExit(3)

from stack_top import select_stack_top
from atm_bd_types import PrOp, PrRef
import pr_lookup
import providers
import stack_link_ops


COMMAND_TIMEOUT = 120
HEARTBEAT_INTERVAL = 120


class StackError(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise StackError(message)


def rows(output):
    try:
        value = json.loads(output)
        return value if isinstance(value, list) else [value]
    except json.JSONDecodeError:
        try:
            return [json.loads(line) for line in output.splitlines() if line.strip()]
        except json.JSONDecodeError as error:
            raise StackError(f"invalid JSON from command: {error}") from error


class Linker:
    def __init__(self, values, runner, clock, actor):
        self.values = values
        self.runner = runner
        self.clock = clock
        self.actor = actor
        self.held = False
        self.heartbeat_at = 0
        self.mode = None
        self.lean_reason = None

    def command(self, argv, *, check=True, allow_transport_failure=False):
        if self.held and argv[:2] != ['bd', 'heartbeat'] and self.clock() - self.heartbeat_at >= HEARTBEAT_INTERVAL:
            self.heartbeat()
        # git and gh act on the checked layer's repository; bd and atm stay in the caller's checkout.
        options = {'cwd': self.values['worktree_path']} if argv[0] not in ('bd', 'atm') and self.values.get('worktree_path') else {}
        try:
            result = self.runner(argv, capture_output=True, text=True, timeout=COMMAND_TIMEOUT, **options)
        except (OSError, subprocess.TimeoutExpired) as error:
            if allow_transport_failure:
                return subprocess.CompletedProcess(argv, 1, '', str(error))
            raise StackError(f"{' '.join(argv)}: {error}") from error
        if check and result.returncode:
            detail = (result.stderr or '').strip().splitlines()
            raise StackError(f"{' '.join(argv)} [{result.returncode}] {detail[0] if detail else 'command failed'}")
        return result

    def heartbeat(self):
        self.command(['bd', 'heartbeat', self.values['stack_bead'], '--actor', self.actor])
        self.heartbeat_at = self.clock()

    def bead(self):
        result = self.command(['bd', 'show', self.values['stack_bead'], '--json'])
        found = rows(result.stdout)
        if len(found) != 1 or not isinstance(found[0], dict):
            raise StackError('bd show returned an invalid stack bead')
        return found[0]

    def acquire(self):
        result = self.command(['bd', 'update', self.values['stack_bead'], '--claim', '--actor', self.actor], check=False)
        if result.returncode == 0:
            self.held = True
            self.heartbeat_at = self.clock()
            return None
        bead = self.bead()
        if not bead.get('assignee') or bead.get('assignee') == self.actor:
            detail = (result.stderr or '').strip().splitlines()
            raise StackError(f"bd update --claim [{result.returncode}] {detail[0] if detail else 'claim failed'}")
        return {'result': 'lock_timeout', 'holder': bead.get('assignee'), 'claimed_at': bead.get('started_at')}

    def release(self):
        if self.held:
            self.held = False
            self.command(['bd', 'update', self.values['stack_bead'], '--if-assignee', self.actor,
                          '--status', 'open', '--assignee', '', '--actor', self.actor])

    def write(self, metadata):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', encoding='utf-8') as stream:
            json.dump(metadata, stream)
            stream.flush()
            self.command(['bd', 'update', self.values['stack_bead'], '--if-assignee', self.actor,
                          '--metadata', '@' + stream.name, '--actor', self.actor])

    def execute(self):
        result = stack_link_ops.execute(self)
        if isinstance(result, _CoreErr):
            raise StackError(f"{result.error.message}; fix: {result.error.fix}")
        return result.value


def rebase_steps(values, top, metadata, contained):
    return [{'option': 'rebase', 'steps': [f"git rebase origin/{top}", 'git push --force-with-lease',
                                           'Request a new sanity check at the pushed head.']}]


def main(argv=None, runner=subprocess.run, clock=time.time):
    parser = Parser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--notify-lead')
    linker = None
    args = None
    values = {}
    result: dict[str, Any] | None = None
    try:
        args = parser.parse_args(argv)
        values = json.loads(args.input.read_text(encoding='utf-8'))
        if not isinstance(values, dict) or any(not isinstance(values.get(key), str) or not values[key] for key in ('checked_bead', 'branch', 'commit', 'stack_bead')):
            raise StackError('input requires checked_bead, branch, commit and stack_bead strings')
        if type(values.get('pr_number')) is not int or values['pr_number'] <= 0 or values.get('budget') not in ('full', 'lean'):
            raise StackError('input requires a positive pr_number and budget full or lean')
        if not re.fullmatch(r'[0-9a-fA-F]{7,64}', values['commit']):
            raise StackError('commit must be a hexadecimal Git object ID')
        if not isinstance(values.get('worktree_path', ''), str):
            raise StackError('worktree_path must be a string')
        actor = os.environ.get('ATM_IDENTITY')
        if not actor:
            raise StackError('ATM_IDENTITY is required')
        linker = Linker(values, runner, clock, actor)
        try:
            try:
                result = linker.execute()
            except (StackError, OSError, ValueError, TypeError, KeyError) as error:
                result = {'result': 'stack_failed', 'evidence': str(error)}
        finally:
            try:
                linker.release()
            except StackError as error:
                if result is None:
                    raise
                if result['result'] == 'stacked':
                    result['release_warning'] = str(error)
                elif result['result'] == 'stack_failed':
                    result['evidence'] += f'; release failed: {error}'
                else:
                    result = {'result': 'stack_failed', 'evidence': f'release failed after {result["result"]}: {error}'}
    except (StackError, OSError, ValueError, TypeError, KeyError) as error:
        result = {'result': 'stack_failed', 'evidence': str(error)}
    assert result is not None
    if linker is not None and linker.mode is not None:
        result.update(mode=linker.mode, lean_reason=linker.lean_reason)
    lead = (args.notify_lead if args is not None else None) or (values.get('lead') if isinstance(values, dict) else None)
    if lead and result['result'] != 'stacked':
        try:
            notice = runner(['atm', 'send', lead,
                             'Sanity task already closed; stack handoff needs lead action: ' + json.dumps(result)],
                            capture_output=True, text=True, timeout=30)
            if notice.returncode:
                result['notification_error'] = notice.stderr or notice.stdout
        except (OSError, subprocess.TimeoutExpired) as error:
            result['notification_error'] = str(error)
    print(json.dumps(result))
    return int(result['result'] == 'stack_failed')


if __name__ == '__main__':
    sys.exit(main())
