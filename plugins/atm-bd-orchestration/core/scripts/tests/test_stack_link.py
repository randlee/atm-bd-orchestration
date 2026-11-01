# pyright: strict
"""Provider stack-link argv remains an argument vector."""
from __future__ import annotations

from pathlib import Path
import subprocess
from atm_bd_types import PrOp
from providers import execute, load_provider
from result import Ok


def test_link_splices_ordered_argument_list_without_shell(tmp_path: Path) -> None:
    provider = load_provider({})
    assert isinstance(provider, Ok)
    observed: list[list[str]] = []
    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed.append(argv)
        return subprocess.CompletedProcess(argv, 0, 'Added 2 PRs to stack #7', '')
    result = execute(provider.value, PrOp.STACK_LINK,
                     {'number': ['--base', 'main', '12', '13']}, cwd=tmp_path, runner=run)
    assert isinstance(result, Ok)
    assert result.value == 'Added 2 PRs to stack #7'
    assert observed == [['gh', 'stack', 'link', '--base', 'main', '12', '13']]


def test_production_scripts_do_not_spell_hosted_stack_commands() -> None:
    plugin = Path(__file__).resolve().parents[3]
    forbidden = ('gh' + ' stack', '/' + 'stacks')
    violations: list[str] = []
    for root in (plugin / 'core', plugin / 'skills'):
        for path in root.rglob('*'):
            if not path.is_file() or 'tests' in path.parts:
                continue
            if path.suffix not in ('.py', '.j2') and path.name != 'sanity-stack-link':
                continue
            if any(token in path.read_text(encoding='utf-8') for token in forbidden):
                violations.append(str(path.relative_to(plugin)))
    assert not violations, violations


def test_both_provider_lookups_report_draft_state(tmp_path: Path) -> None:
    import json
    from atm_bd_types import PrRef
    cases = [
        ({'provider': 'github'}, {'number': 12, 'html_url': 'https://example.test/12',
          'base': {'ref': 'main'}, 'head': {'sha': 'a' * 40}, 'draft': True}),
        ({'provider': 'azure', 'azure': {'organization': 'o', 'project': 'p', 'repository': 'r'}},
         {'pullRequestId': 12, 'url': 'https://example.test/12', 'targetRefName': 'refs/heads/main',
          'lastMergeSourceCommit': {'commitId': 'a' * 40}, 'isDraft': True}),
    ]
    for config, payload in cases:
        loaded = load_provider(config)
        assert isinstance(loaded, Ok)
        def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(argv, 0, json.dumps([payload]), '')
        found = execute(loaded.value, PrOp.LOOKUP_BY_HEAD,
                        {'head': 'topic', 'organization': 'o', 'project': 'p', 'repository': 'r'},
                        cwd=tmp_path, runner=run)
        assert isinstance(found, Ok) and isinstance(found.value, PrRef)
        assert found.value.draft and found.value.base == 'main'
