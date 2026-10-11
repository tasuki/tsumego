#!/usr/bin/env python3
"""Regression tests for scripts/problems.py."""

from __future__ import annotations

import csv
import io
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
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
            "guan-zi-pu.txt": (1107, 0),
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

    def test_guan_zi_pu_sgf_import(self) -> None:
        source_directory = BOOKS / "sources" / "guan-zi-pu"
        imported: list[problems.Problem] = []
        for volume in range(1, 4):
            imported.extend(
                problems.read_sgf(
                    source_directory / f"gzp{volume}.sgf",
                    start_number=len(imported) + 1,
                    default_player="W",
                )
            )
        self.assertEqual(
            [str(number) for number in range(1, 1478)],
            [problem.identifier for problem in imported],
        )
        exact, _ = problems.deduplicate(imported)
        self.assertEqual(355, len(imported) - len(exact))
        unique, source_to_retained = problems.deduplicate(imported, symmetries=True)
        self.assertEqual(15, len(exact) - len(unique))
        self.assertEqual(370, len(imported) - len(unique))
        retained_to_book = {
            problem.identifier: str(number)
            for number, problem in enumerate(unique, 1)
        }
        expected = [
            replace(problem, identifier=retained_to_book[problem.identifier])
            for problem in unique
        ]
        self.assertEqual(
            problems.read_ascii(BOOKS / "problems" / "guan-zi-pu.txt"),
            expected,
        )
        self.assertEqual(
            len(unique), len(problems.deduplicate(expected, symmetries=True)[0])
        )
        with (source_directory / "source-map.csv").open(newline="") as source_map:
            rows = list(csv.DictReader(source_map))
        self.assertEqual(
            [
                {
                    "source_problem": source_id,
                    "book_problem": retained_to_book[retained_id],
                    "kept_source_problem": retained_id,
                }
                for source_id, retained_id in source_to_retained.items()
            ],
            rows,
        )

    def test_deduplication_only_removes_exact_positions(self) -> None:
        first = problems.Problem(
            identifier="first",
            black=frozenset({(0, 0), (2, 0)}),
            white=frozenset({(1, 1)}),
            labels=((3, 2, "A"), (4, 2, "B")),
            width=6,
            height=4,
        )
        duplicate = replace(
            first, identifier="duplicate", width=19, height=19,
            labels=tuple(reversed(first.labels)),
        )
        near = replace(first, identifier="near", black=first.black | {(2, 1)})
        reflected = replace(
            first, identifier="reflected", width=19, height=19,
            black=frozenset((18 - x, y) for x, y in first.black),
            white=frozenset((18 - x, y) for x, y in first.white),
            labels=tuple((18 - x, y, label) for x, y, label in first.labels),
        )
        swapped = replace(
            first, identifier="swapped", black=first.white, white=first.black,
        )
        relabelled = replace(
            first, identifier="relabelled", labels=((3, 2, "B"), (4, 2, "A")),
        )
        unique, mapping = problems.deduplicate(
            [first, duplicate, near, reflected, swapped, relabelled]
        )
        self.assertEqual([first, near, reflected, swapped, relabelled], unique)
        self.assertEqual("first", mapping["duplicate"])
        self.assertEqual("first", mapping["first"])
        self.assertEqual(([], {}), problems.deduplicate([]))
        self.assertEqual(unique, problems.deduplicate(unique)[0])

    def test_deduplication_under_all_board_symmetries(self) -> None:
        first = problems.Problem(
            identifier="0",
            black=frozenset({(0, 0), (2, 0)}),
            white=frozenset({(1, 1)}),
            labels=((3, 2, "A"), (4, 2, "B")),
        )
        variants = [
            replace(
                first, identifier=str(index),
                black=frozenset(
                    problems._transform_point(index, x, y) for x, y in first.black
                ),
                white=frozenset(
                    problems._transform_point(index, x, y) for x, y in first.white
                ),
                labels=tuple(
                    (*problems._transform_point(index, x, y), label)
                    for x, y, label in first.labels
                ),
            )
            for index in range(8)
        ]
        near = replace(first, identifier="near", black=first.black | {(2, 1)})
        swapped = replace(
            first, identifier="swapped", black=first.white, white=first.black,
        )
        shifted = replace(
            first, identifier="shifted",
            black=frozenset((x + 1, y) for x, y in first.black),
            white=frozenset((x + 1, y) for x, y in first.white),
            labels=tuple((x + 1, y, label) for x, y, label in first.labels),
        )
        relabelled = replace(
            first, identifier="relabelled", labels=((3, 2, "B"), (4, 2, "A")),
        )
        unique, mapping = problems.deduplicate(
            [*variants, near, swapped, shifted, relabelled], symmetries=True
        )
        self.assertEqual([first, near, swapped, shifted, relabelled], unique)
        for index in range(8):
            self.assertEqual("0", mapping[str(index)])
        self.assertEqual(unique, problems.deduplicate(unique, symmetries=True)[0])

    def test_sgf_import_symmetry_deduplication_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.sgf"
            destination = Path(directory) / "book.txt"
            source_map = Path(directory) / "source-map.csv"
            source.write_text(
                "(;AB[aa][ba]AW[ab];W[bb])"
                "(;AB[aa][ab]AW[ba];W[bb])"
                "(;AB[aa][ba][bb]AW[ab];W[cc])",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                result = problems.main([
                    "import-sgf", "--deduplicate-symmetries",
                    "--source-map", str(source_map), str(source), str(destination),
                ])
            self.assertEqual(0, result)
            self.assertEqual(2, len(problems.read_ascii(destination)))
            self.assertEqual(
                "source_problem,book_problem,kept_source_problem\n"
                "1,1,1\n2,1,1\n3,2,3\n",
                source_map.read_text(),
            )

    def test_sgf_import_deduplication_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.sgf"
            second = Path(directory) / "second.sgf"
            destination = Path(directory) / "book.txt"
            source_map = Path(directory) / "source-map.csv"
            first.write_text("(;AB[aa]AW[ba];W[ab])", encoding="utf-8")
            second.write_text(
                "(;AB[aa]AW[ba];W[ac])(;AB[aa][bb]AW[ba];W[ab])",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                result = problems.main([
                    "import-sgf", "--deduplicate", "--source-map", str(source_map),
                    str(first), str(second), str(destination),
                ])
            self.assertEqual(0, result)
            self.assertEqual(
                ["1", "2"],
                [problem.identifier for problem in problems.read_ascii(destination)],
            )
            self.assertEqual(
                "source_problem,book_problem,kept_source_problem\n"
                "1,1,1\n2,1,1\n3,2,3\n",
                source_map.read_text(),
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
            tex = tex_path.read_text()
            self.assertEqual(8, tex.count(r"\!  A"))
            self.assertEqual(8, sgf_path.read_text().count(":A]"))
            for chapter in range(1, 8):
                self.assertIn(
                    rf"\pdfdest name {{problem-{chapter}-1}} xyz", tex
                )

    def test_gokyo_contents_pages_match_layouts(self) -> None:
        source = problems.read_ascii(BOOKS / "problems" / "gokyoshumyo.txt")
        for profile in ("a5", "a6"):
            columns = problems.plan_layout(source, profile)
            actual: list[int] = []
            for column_index, column in enumerate(columns):
                page = column_index // 2 + 1 if profile == "a5" else column_index + 1
                for problem, _ in column:
                    if re.fullmatch(r"\d+-1", problem.identifier):
                        actual.append(page)

            wrapper = (BOOKS / f"{profile}-gokyoshumyo.tex").read_text()
            match = re.search(
                r"\\def\\chapterpage#1\{\\ifcase#1((?:\\or\d+)+)\\fi\}",
                wrapper,
            )
            self.assertIsNotNone(match)
            listed = [
                int(page)
                for page in match.group(1).split(r"\or")
                if page
            ]
            self.assertEqual(actual, listed)

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
