#!/usr/bin/env python3
"""Regression tests for scripts/problems.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import problems


ROOT = Path(__file__).resolve().parent.parent
BOOKS = ROOT / "books"


class ProblemDataTests(unittest.TestCase):
    def test_canonical_collection_counts(self) -> None:
        expected = {
            "cho-1.txt": (900, 0),
            "cho-2.txt": (861, 0),
            "cho-3.txt": (792, 0),
            "gokyoshumyo.txt": (520, 8),
            "hatsuyoron.txt": (183, 0),
            "xxqj.txt": (347, 0),
        }
        for filename, (problem_count, label_count) in expected.items():
            with self.subTest(filename=filename):
                collection = problems.read_ascii(BOOKS / "problems" / filename)
                self.assertEqual(problem_count, len(collection))
                self.assertEqual(
                    label_count, sum(len(problem.labels) for problem in collection)
                )

    def test_ascii_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for source_path in sorted((BOOKS / "problems").glob("*.txt")):
                with self.subTest(collection=source_path.stem):
                    source = problems.read_ascii(source_path)
                    destination = Path(directory) / source_path.name
                    problems.write_ascii(source, destination)
                    self.assertEqual(source, problems.read_ascii(destination))

    def test_page_layouts_are_valid(self) -> None:
        for profile in ("a5", "a6"):
            row_unit, overhead, budget = problems._PROFILE_METRICS[profile]
            for source_path in sorted((BOOKS / "problems").glob("*.txt")):
                with self.subTest(profile=profile, collection=source_path.stem):
                    collection = problems.read_ascii(source_path)
                    columns = problems.plan_layout(collection, profile)
                    self.assertEqual(len(collection), sum(len(column) for column in columns))
                    for column in columns:
                        used = sum(
                            (problems._render_height(problem) + padding) * row_unit
                            + overhead
                            for problem, padding in column
                        ) + max(0, len(column) - 1) * problems._INTER_PROBLEM_ROWS
                        self.assertLessEqual(used, budget)
                        for problem, padding in column:
                            height = problems._render_height(problem) + padding
                            self.assertLessEqual(height, problems.BOARD_SIZE)
                            self.assertFalse(15 <= height <= 18)
                            if height < problems.BOARD_SIZE:
                                occupied_rows = [
                                    y
                                    for _, y in problem.black | problem.white
                                ] + [y for _, y, _ in problem.labels]
                                self.assertLess(max(occupied_rows), height - 1)

    def test_outputs_preserve_labels(self) -> None:
        source = problems.read_ascii(BOOKS / "problems" / "gokyoshumyo.txt")
        with tempfile.TemporaryDirectory() as directory:
            tex_path = Path(directory) / "problems.tex"
            sgf_path = Path(directory) / "problems.sgf"
            problems.render_tex(source, tex_path, "a5")
            problems.write_sgf(source, sgf_path)
            self.assertEqual(8, tex_path.read_text().count(r"\!  A"))
            self.assertEqual(8, sgf_path.read_text().count(":A]"))

    def test_normalization_prefers_short_then_narrow(self) -> None:
        original = problems.Problem(
            identifier="example",
            black=frozenset({(16, 14), (17, 14), (17, 18)}),
            white=frozenset({(16, 15)}),
        )
        normalized = problems.normalize(original)
        occupied = normalized.black | normalized.white
        self.assertEqual(4, normalized.height)
        self.assertEqual(6, normalized.width)
        self.assertEqual(2, max(y for _, y in occupied))
        self.assertEqual(4, max(x for x, _ in occupied))


if __name__ == "__main__":
    unittest.main()
