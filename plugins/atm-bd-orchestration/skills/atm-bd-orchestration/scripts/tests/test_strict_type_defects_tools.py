"""Regressions for runtime defects exposed while making the tools strict."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

JUDGE_PATH = Path(__file__).parents[3] / "prompt-rewrite-judge/scripts/judge.py"
SPEC = importlib.util.spec_from_file_location("prompt_rewrite_judge", JUDGE_PATH)
assert SPEC is not None and SPEC.loader is not None
judge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(judge)


class StrictTypeDefectTests(unittest.TestCase):
    def run_client(self, output: str) -> tuple[object, object]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client = root / "client.py"
            client.write_text(f"print({output!r})\n")
            request = root / "request.json"
            request.write_text("{}\n")
            return judge.run(client, request)

    def test_non_object_jev_response_is_a_failure_record(self):
        answers, error = self.run_client("[]\n")

        self.assertIsNone(answers)
        self.assertIsNotNone(error)
        self.assertIn("response must be a JSON object", str(error))
        self.assertIn("[]", str(error))

    def test_selected_choice_without_probability_is_a_failure_record(self):
        response = (
            '{"success":true,"data":{"answers":{"question":'
            '{"choice":"yes","probabilities":{"no":1.0}}}},"error":null}'
        )
        answers, error = self.run_client(response)

        self.assertIsNone(answers)
        self.assertIsNotNone(error)
        self.assertIn("success response has invalid answers", str(error))


if __name__ == "__main__":
    unittest.main()
