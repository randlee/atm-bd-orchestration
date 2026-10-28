import importlib.machinery
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

SKILLS = Path(__file__).resolve().parents[2]
BEADS_SCRIPTS = SKILLS / 'atm-beads/scripts'
REPORT_SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path[:0] = [str(BEADS_SCRIPTS), str(REPORT_SCRIPTS),
                str(SKILLS / 'atm-bd-orchestration/scripts')]
import bead_formulas
import operation_models as models

loader = importlib.machinery.SourceFileLoader('sprint_report_models', str(REPORT_SCRIPTS / 'sprint-report'))
spec = importlib.util.spec_from_loader(loader.name, loader)
assert spec is not None
report = importlib.util.module_from_spec(spec)
loader.exec_module(report)


class OperationModelTests(unittest.TestCase):
    def test_bead_metadata_guard_checks_every_declared_field(self):
        string_fields = (
            'branch', 'checked_bead', 'difficulty', 'integration_branch', 'phase',
            'severity', 'stack', 'sprint', 'verdict', 'worktree', 'pr_target',
        )
        metadata: dict[str, str | int] = {field: f'{field}-value' for field in string_fields}
        metadata.update({'layer': 1, 'round': 2})
        self.assertTrue(models.is_bead_metadata(metadata))
        self.assertTrue(models.is_bead_records([{
            'id': 'atm-x-1', 'status': 'open', 'metadata': metadata,
        }]))

        for field in string_fields:
            with self.subTest(field=field):
                malformed = {**metadata, field: 7}
                self.assertFalse(models.is_bead_metadata(malformed))
                self.assertFalse(models.is_bead_records([{
                    'id': 'atm-x-1', 'status': 'open', 'metadata': malformed,
                }]))

        for field in ('layer', 'round'):
            for malformed_value in ([], {}):
                with self.subTest(field=field, value=malformed_value):
                    self.assertFalse(models.is_bead_metadata({**metadata, field: malformed_value}))
        for field in ('layer', 'round'):
            for valid_value in (None, '2', 2, 2.5, True):
                with self.subTest(field=field, value=valid_value):
                    self.assertTrue(models.is_bead_metadata({**metadata, field: valid_value}))

    def test_bd_records_validate_operation_fields_and_dependencies(self):
        rows = [{
            'id': 'atm-x-1.group-dev',
            'status': 'open',
            'labels': ['phase-x', 'stage:dev'],
            'dependencies': [{'type': 'blocks', 'depends_on_id': 'atm-x-1'}],
            'metadata': {'branch': 'sprint/x-1', 'layer': 1},
        }]
        self.assertTrue(models.is_bead_records(rows))
        self.assertFalse(models.is_bead_records([{'id': 'atm-x-1', 'status': 3}]))
        self.assertFalse(models.is_bead_records([{
            'id': 'atm-x-1', 'dependencies': [{'type': 4, 'depends_on_id': 'atm-x-2'}],
        }]))
        self.assertTrue(models.is_bead_records([{
            'id': 'atm-x-1', 'status': 'open',
            'dependencies': [{'dependency_type': 'blocks', 'id': 'atm-x-2'}],
        }]))
        self.assertFalse(models.is_bead_records([{
            'id': 'atm-x-1', 'status': 'open', 'dependencies': [{'type': 'blocks'}],
        }]))
        self.assertFalse(models.is_bead_records([{'id': 'atm-x-1', 'metadata': {'branch': 8}}]))

    def test_bd_show_returns_a_validated_record(self):
        process = subprocess.CompletedProcess([], 0, stdout='[{"id":"atm-x-1","status":"open"}]', stderr='')
        with mock.patch.object(bead_formulas.Bd, 'run', return_value=process):
            record = bead_formulas.Bd().show('atm-x-1')
        self.assertEqual(record, {'id': 'atm-x-1', 'status': 'open'})

        malformed = subprocess.CompletedProcess([], 0, stdout='[{"status":"open"}]', stderr='')
        with mock.patch.object(bead_formulas.Bd, 'run', return_value=malformed):
            with self.assertRaisesRegex(ValueError, 'invalid bead records'):
                bead_formulas.Bd().show('atm-x-1')

    def test_report_adapters_reject_mismatched_operation_records(self):
        bead = {'id': 'atm-x-1', 'status': 'open', 'metadata': {'sprint': 'x-1'}}
        with mock.patch.object(report, 'run_json', return_value={'beads': [bead]}):
            self.assertEqual(report.run_bead_records(Path('/repo'), 'beads', 'bd', 'show', 'atm-x-1', '--json'), [bead])
        with mock.patch.object(report, 'run_json', return_value={'tasks': [{'task_id': 'task-1', 'state': 'active'}]}):
            self.assertEqual(report.run_atm_tasks(Path('/repo'), 'atm', 'task', 'list', '--json'),
                             [{'task_id': 'task-1', 'state': 'active'}])
        with mock.patch.object(report, 'run_json', return_value={'events': [{'event': 'completed', 'at': '2026-10-28T00:00:00Z'}]}):
            self.assertEqual(report.run_atm_task_events(Path('/repo'), 'atm', 'task', 'events', 'task-1', '--json'),
                             [{'event': 'completed', 'at': '2026-10-28T00:00:00Z'}])
        pull_request = {'number': 7, 'state': 'OPEN', 'head': {'ref': 'fix/example'}, 'base': {'ref': 'main'}}
        with mock.patch.object(report, 'run_json', return_value=[[pull_request]]):
            self.assertEqual(report.run_pull_request_pages(Path('/repo'), 'gh', 'api', '--paginate'), [[pull_request]])

        with mock.patch.object(report, 'run_json', return_value={'members': [{'name': 'dev', 'agent_type': 5}]}):
            with self.assertRaisesRegex(RuntimeError, 'ATM member records'):
                report.run_atm_members(Path('/repo'), 'atm', 'members', '--json')
        with mock.patch.object(report, 'run_json', return_value={'events': [{'event': 2}]}):
            with self.assertRaisesRegex(RuntimeError, 'ATM task-event records'):
                report.run_atm_task_events(Path('/repo'), 'atm', 'task', 'events', 'task-1', '--json')
        with mock.patch.object(report, 'run_json', return_value=[[{'number': 7, 'state': 'OPEN', 'head': {'ref': 9}}]]):
            with self.assertRaisesRegex(RuntimeError, 'pull-request pages'):
                report.run_pull_request_pages(Path('/repo'), 'gh', 'api', '--paginate')

    def test_atm_and_github_operation_models_check_required_identity_and_nested_shapes(self):
        self.assertTrue(models.is_atm_tasks([{'task_id': 'atm-x-1', 'state': 'active'}]))
        self.assertFalse(models.is_atm_tasks([{'state': 'active'}]))
        self.assertTrue(models.is_atm_task_events([{'event': 'completed', 'at': '2026-10-28T00:00:00Z'}]))
        self.assertFalse(models.is_atm_task_events([{'to_state': 'completed'}]))
        self.assertTrue(models.is_pull_requests([{
            'number': 9, 'state': 'OPEN', 'head': {'ref': 'fix/example'},
            'base': {'ref': 'main'}, 'merged_at': None,
        }]))
        self.assertFalse(models.is_pull_requests([{
            'number': 9, 'state': 'OPEN', 'head': {'ref': 1}, 'base': {'ref': 'main'},
        }]))


if __name__ == '__main__':
    unittest.main()
