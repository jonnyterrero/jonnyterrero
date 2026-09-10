"""Unit tests for the profile coding-statistics updater."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("update_coding_stats.py")
SPEC = importlib.util.spec_from_file_location("update_coding_stats", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CountNeetCodeSolutionsTests(unittest.TestCase):
    def test_counts_unique_problem_folders_and_submission_files(self) -> None:
        tree = [
            {
                "type": "blob",
                "path": "Data Structures & Algorithms/binary-search/submission-0.py",
            },
            {
                "type": "blob",
                "path": "Data Structures & Algorithms/binary-search/submission-1.cpp",
            },
            {
                "type": "blob",
                "path": "Python For Beginners/two-sum/submission-0.kt",
            },
            {"type": "blob", "path": "src/algorithms/search.py"},
            {"type": "blob", "path": "Data Structures & Algorithms/README.md"},
        ]

        self.assertEqual(MODULE.count_neetcode_solutions(tree), (2, 3))


class RenderStatsTests(unittest.TestCase):
    def test_renders_counts_and_recent_accepts(self) -> None:
        leetcode = MODULE.LeetCodeStats(
            total=32,
            easy=11,
            medium=17,
            hard=4,
            recent_accepts=(("Two Sum", "two-sum"),),
        )
        neetcode = MODULE.NeetCodeStats(
            problems=25,
            submissions=30,
            latest_message="Add: eating-bananas - submission-0",
            latest_date="2026-09-06",
        )

        rendered = MODULE.render_stats(
            leetcode,
            neetcode,
            leetcode_username="jterrero16",
            github_user="jonnyterrero",
            neetcode_repository="Neetcode-Problems",
        )

        self.assertIn("**32 solved** · 11 Easy · 17 Medium · 4 Hard", rendered)
        self.assertIn("**25 problems** · 30 synchronized submissions", rendered)
        self.assertIn("https://leetcode.com/problems/two-sum/", rendered)


if __name__ == "__main__":
    unittest.main()
