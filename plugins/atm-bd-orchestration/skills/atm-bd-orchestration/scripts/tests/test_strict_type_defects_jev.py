"""Regression tests for concrete type defects found by the BN-2 lane."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "sanity-split"
WRAPPER = SCRIPT.parent / "wrap_jev_receipt.py"


class MalformedBeadTests(unittest.TestCase):
    def test_non_object_metadata_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            bead = Path(directory) / "bead.json"
            bead.write_text(json.dumps({"id": "x-1", "metadata": ["invalid"]}))
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--task", "x-1-sanity", "--bead", "x-1",
                 "--worktree", directory, "--branch", "fixture", "--commit", "abc",
                 "--base", "base", "--lint-command", "true", "--scratch", directory,
                 "--bead-json", str(bead), "--split-only"],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 3)
        self.assertIn("metadata must be an object", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_receipt_assignment_rejects_non_string_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assignment = root / "assignment.json"
            assignment.write_text(json.dumps({
                "sanity_bead": "s", "dev_bead": {"id": "d"},
                "deliverable": {"number": 1}, "deliverables_total": 1, "commit": 42,
            }))
            client = root / "client.json"
            client.write_text(json.dumps({"success": False, "data": None,
                                          "error": {"message": "TYPESAFE_API_KEY is missing; no Jev evaluation ran"}}))
            result = subprocess.run(
                [sys.executable, str(WRAPPER), "--assignment", str(assignment), "--client-output", str(client)],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("assignment_fields", result.stderr)
        self.assertIn("commit must be strings", result.stderr)
