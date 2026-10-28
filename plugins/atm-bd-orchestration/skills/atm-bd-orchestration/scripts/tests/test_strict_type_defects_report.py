"""Regression coverage for concrete post-mortem/report type defects."""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_post_mortem_jev import response
import post_mortem_jev as m


class PostMortemProbabilityTypeTests(unittest.TestCase):
    def test_integer_zero_and_one_are_valid_but_bool_is_not(self):
        reply = response()
        for answer in reply["answers"].values():
            answer["probabilities"] = {
                choice: 1 if choice == answer["choice"] else 0
                for choice in answer["probabilities"]
            }

        coverage = {"scope": "whole_finding", "limitations": [], "obligation_ids": ["o1"]}
        self.assertEqual(m.route(reply, coverage), "screened_present")

        reply["answers"]["fix_presence"]["probabilities"]["fully_present"] = True
        self.assertEqual(m.route(reply, coverage), "evaluation_error")
