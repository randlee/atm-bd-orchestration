"""Regression tests for concrete type defects found by the BN-2 lane."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "sanity-split"


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
