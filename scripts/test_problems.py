#!/usr/bin/env python3
"""Regression tests for scripts/problems.py."""

from __future__ import annotations

import csv
import hashlib
import io
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path

import problems
import import_gokyo_seimyo
import import_shikatsu_myoki
import import_wangyou_qingle_ji


ROOT = Path(__file__).resolve().parent.parent
BOOKS = ROOT / "books"


class ProblemDataTests(unittest.TestCase):
    def test_canonical_collection_counts(self) -> None:
        expected = {
            "cho-1.txt": (900, 0),
            "cho-2.txt": (861, 0),
            "cho-3.txt": (792, 0),
            "gokyoshumyo.txt": (520, 8),
            "gokyo-seimyo.txt": (145, 0),
            "guanzi-pu.txt": (1107, 0),
            "hatsuyoron.txt": (183, 0),
            "shikatsu-myoki.txt": (120, 0),
            "wangyou-qingle-ji.txt": (37, 0),
            "xxqj.txt": (347, 0),
        }
        for filename, (problem_count, label_count) in expected.items():
            with self.subTest(filename=filename):
                collection = problems.read_ascii(BOOKS / "problems" / filename)
                self.assertEqual(problem_count, len(collection))
                self.assertEqual(
                    label_count, sum(len(problem.labels) for problem in collection)
                )

    def test_guanzi_pu_sgf_import(self) -> None:
        source_directory = BOOKS / "sources" / "guanzi-pu"
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
            problems.read_ascii(BOOKS / "problems" / "guanzi-pu.txt"),
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

    def test_wangyou_qingle_ji_import(self) -> None:
        source = BOOKS / "sources" / "wangyou-qingle-ji"
        paths = sorted(source.glob("*.sgf"))
        self.assertEqual([f"{number:02}.sgf" for number in range(1, 38)],
                         [path.name for path in paths])
        imported = import_wangyou_qingle_ji.read_collection(source)
        for number, path in enumerate(paths, 1):
            root, _ = problems._SgfParser(path.read_text(), path).collection()[0]
            self.assertTrue(root["GN"][0].startswith(f"{number}. "))
            position = imported[number - 1]
            title = root["GN"][0].removeprefix(f"{number}. ")
            self.assertEqual(title.removesuffix(" (revised)"), position.title)
            original, = problems.read_sgf(path, start_number=number)
            self.assertEqual(original.black, position.black)
            self.assertEqual(original.white, position.white)
            if number == 3:
                self.assertFalse(position.triangles)
            elif number == 7:
                self.assertEqual(
                    frozenset({(14, 15), (15, 15), (16, 15), (17, 15), (14, 17)}),
                    position.triangles,
                )
                self.assertTrue(position.triangles <= position.white)
            else:
                self.assertEqual(original.triangles, position.triangles)
            self.assertEqual(original.labels if number not in (13, 25, 33) else (), position.labels)
            black_key, white_key = ("AB", "AW") if root["PL"] == ["B"] else ("AW", "AB")
            self.assertEqual(len(root[black_key]), len(position.black))
            self.assertEqual(len(root[white_key]), len(position.white))
        self.assertEqual(
            problems.read_ascii(BOOKS / "problems" / "wangyou-qingle-ji.txt"), imported
        )
        self.assertEqual(23, sum(len(problem.triangles) for problem in imported))
        self.assertEqual(
            {"7": 5, "9": 1, "13": 1, "23": 8, "26": 8},
            {problem.identifier: len(problem.triangles)
             for problem in imported if problem.triangles},
        )
        self.assertEqual([],
                         [problem.identifier for problem in imported if problem.labels])
        for profile in ("a5", "a6"):
            with tempfile.TemporaryDirectory() as directory:
                tex_path = Path(directory) / "problems.tex"
                sgf_path = Path(directory) / "problems.sgf"
                problems.render_tex(imported, tex_path, profile)
                tex = tex_path.read_text()
                self.assertEqual(0, tex.count(r"\!  A"))
                for problem in imported:
                    self.assertIn(f"{problem.identifier}. {problem.title}", tex)
                self.assertNotIn("revised", tex)
                content = (BOOKS / "content" / "wangyou-qingle-ji.tex").read_text()
                self.assertNotIn("Problem notes", content)
                self.assertEqual(1, tex.count(r"\- :"))
                self.assertEqual(22, tex.count(r"\- ;"))
                problems.write_sgf(imported, sgf_path)
                self.assertEqual(imported, problems.read_sgf(sgf_path, include_titles=True))

    def test_titles_round_trip_and_escape_tex(self) -> None:
        position = problems.Problem(
            identifier="1", black=frozenset({(0, 0)}), white=frozenset({(1, 0)}),
            title="A & B: 50% #1 {test}", width=3, height=2,
        )
        with tempfile.TemporaryDirectory() as directory:
            ascii_path = Path(directory) / "problems.txt"
            sgf_path = Path(directory) / "problems.sgf"
            tex_path = Path(directory) / "problems.tex"
            problems.write_ascii([position], ascii_path)
            self.assertEqual([position], problems.read_ascii(ascii_path))
            problems.write_sgf([position], sgf_path)
            self.assertEqual([position], problems.read_sgf(sgf_path, include_titles=True))
            self.assertEqual("", problems.read_sgf(sgf_path)[0].title)
            for profile in ("a5", "a6"):
                problems.render_tex([position], tex_path, profile)
                tex = tex_path.read_text()
                self.assertIn(r"\label 1. A {\char38} B: 50{\char37} {\char35}1 {\char123}test{\char125}", tex)
                self.assertNotIn(r"\problemtitle", tex)
                self.assertEqual(0, problems.main([
                    "render-tex", "--profile", profile, "--title-separator", " ",
                    str(ascii_path), str(tex_path),
                ]))
                tex = tex_path.read_text()
                self.assertIn(r"\label 1 A {\char38} B: 50{\char37} {\char35}1 {\char123}test{\char125}", tex)
                self.assertNotIn(r"\label 1.", tex)
            ascii_path.write_text("problem 1\nx.\n..\ntitle Too late\n")
            with self.assertRaisesRegex(ValueError, "title must occur once before"):
                problems.read_ascii(ascii_path)

    def test_sgf_import_preserves_only_root_marks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "marked.sgf"
            source.write_text(
                "(;SZ[19]PL[W]AB[ss]AW[rs]LB[qr:A]TR[ss][rs]"
                ";W[qs]LB[ps:B]TR[qs])"
            )
            expected = problems.normalize(problems.Problem(
                identifier="1", black=frozenset({(17, 18)}),
                white=frozenset({(18, 18)}), labels=((16, 17, "A"),),
                triangles=frozenset({(17, 18), (18, 18)}),
            ))
            self.assertEqual([expected], problems.read_sgf(source))

    def test_triangles_are_validated_and_part_of_deduplication(self) -> None:
        first = problems.Problem(
            identifier="first", black=frozenset({(0, 0), (1, 0)}),
            white=frozenset({(0, 1)}), triangles=frozenset({(0, 0)}),
        )
        variants = [
            replace(
                first, identifier=str(index),
                black=frozenset(problems._transform_point(index, x, y) for x, y in first.black),
                white=frozenset(problems._transform_point(index, x, y) for x, y in first.white),
                triangles=frozenset(problems._transform_point(index, x, y) for x, y in first.triangles),
            )
            for index in range(8)
        ]
        different = replace(first, identifier="different", triangles=frozenset({(1, 0)}))
        unmarked = replace(first, identifier="unmarked", triangles=frozenset())
        unique, _ = problems.deduplicate([*variants, different, unmarked], symmetries=True)
        self.assertEqual([variants[0], different, unmarked], unique)
        with self.assertRaisesRegex(ValueError, "triangle is not on a stone"):
            replace(first, triangles=frozenset({(2, 2)}))

    def test_gokyo_seimyo_import(self) -> None:
        source = BOOKS / "sources" / "gokyo-seimyo"
        selected = import_gokyo_seimyo.selected_sources(source)
        self.assertEqual(145, len(selected))
        self.assertEqual(
            [(1, "1-1", "Tesuji inside territories"),
             (45, "2-1", "Other problems"), (119, "3-1", "Connect underneath"),
             (129, "4-1", "Cut/connect groups"), (137, "5-1", "Ladder")],
            [entry for entry in selected if entry[1].endswith("-1")],
        )
        self.assertEqual(list(range(1, 146)), [n for n, _, _ in selected])
        self.assertEqual((145, "5-9", "Ladder"), selected[-1])
        self.assertEqual((source / "145.sgf").read_bytes(),
                         (source / "146.sgf").read_bytes())
        self.assertEqual(
            [(66, "2-22", "Other problems"), (68, "2-24", "Other problems"),
             (69, "2-25", "Other problems")],
            [entry for entry in selected if entry[0] in (66, 68, 69)],
        )
        imported = import_gokyo_seimyo.read_collection(source)
        self.assertEqual(
            problems.read_ascii(BOOKS / "problems" / "gokyo-seimyo.txt"), imported
        )
        self.assertEqual("5-9", imported[-1].identifier)
        self.assertNotIn("5-10", [p.identifier for p in imported])
        self.assertFalse(any(p.triangles for p in imported))
        self.assertEqual(
            {"2-22": "hanezeki", "2-24": "eternal life (chosei)",
             "2-25": "double-ko seki"},
            {p.identifier: p.title for p in imported if p.title},
        )
        for (number, identifier, _), position in zip(selected, imported):
            path = source / f"{number}.sgf"
            root, _ = problems._SgfParser(path.read_text(), path).collection()[0]
            caption = root["GN"][0].strip("()")
            white_to_play = number in (37, 62) or caption.startswith("White")
            black_key, white_key = ("AW", "AB") if white_to_play else ("AB", "AW")
            # Compare independently normalized stones, including the two PL[B]
            # diagrams whose captions/page actually say White (55 and 62).
            expected = problems.normalize(problems.Problem(
                identifier=identifier,
                black=frozenset(problems._sgf_setup_points(root[black_key], path)),
                white=frozenset(problems._sgf_setup_points(root[white_key], path)),
            ))
            self.assertEqual(expected.black, position.black)
            self.assertEqual(expected.white, position.white)
            self.assertFalse(position.labels)
            if number >= 137:
                self.assertEqual(19, position.width)
                self.assertEqual(19, position.height)
        with (source / "source-map.csv").open(newline="") as source_map:
            self.assertEqual(
                [{"source_problem": str(number), "book_problem": identifier,
                  "section": title,
                  "page_url": f"{import_gokyo_seimyo.PROBLEM_URL}{number}"}
                 for number, identifier, title in selected],
                list(csv.DictReader(source_map)),
            )
        for line in (source / "SHA256SUMS").read_text().splitlines():
            digest, filename = line.split("  ")
            self.assertEqual(digest, hashlib.sha256((source / filename).read_bytes()).hexdigest())
        with tempfile.TemporaryDirectory() as directory:
            for profile in ("a5", "a6"):
                tex_path = Path(directory) / f"{profile}.tex"
                problems.render_tex(imported, tex_path, profile, title_separator=" ")
                tex = tex_path.read_text()
                for position in imported:
                    if position.title:
                        self.assertIn(f"{position.identifier} {position.title}", tex)
                        self.assertNotIn(f"{position.identifier}. {position.title}", tex)
                self.assertNotIn("Cut off", tex)
            sgf_path = Path(directory) / "gokyo-seimyo.sgf"
            # The generic SGF importer assigns sequential identifiers.
            sequential = [replace(p, identifier=str(n)) for n, p in enumerate(imported, 1)]
            problems.write_sgf(sequential, sgf_path)
            self.assertEqual(
                [replace(p, title=p.title or p.identifier) for p in sequential],
                problems.read_sgf(sgf_path, include_titles=True),
            )

    def test_gokyo_seimyo_rejects_incomplete_index_and_diagram_moves(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "series-index.html").write_text(
                '<a href="/?GokyoSeimyoVolume3Problem1">1</a>'
            )
            with self.assertRaisesRegex(ValueError, "expected index entries"):
                import_gokyo_seimyo.selected_sources(source)
            sgf = source / "1.sgf"
            sgf.write_text("(;SZ[19]GN[Black to move]AB[aa]AW[ba];B[ab])")
            with self.assertRaisesRegex(ValueError, "unexpected moves"):
                import_gokyo_seimyo.read_diagram(sgf, 1, "1-1")
            sgf.write_text("(;SZ[19]GN[]PL[B]AB[aa]AW[ba])")
            with self.assertRaisesRegex(ValueError, "caption does not name"):
                import_gokyo_seimyo.read_diagram(sgf, 1, "1-1")

    def test_shikatsu_myoki_import(self) -> None:
        source = BOOKS / "sources" / "shikatsu-myoki"
        selected = import_shikatsu_myoki.selected_sources(source)
        self.assertEqual(120, len(selected))
        self.assertEqual(
            [(1, "1-1", "Killing"), (74, "2-1", "Living"),
             (118, "3-1", "Ko"), (156, "4-1", "Capturing Races")],
            [entry for entry in selected if entry[1].endswith("-1")],
        )
        self.assertEqual(
            {str(number) for number, _, _ in selected},
            {path.stem for path in source.glob("*.sgf")},
        )
        self.assertEqual(
            problems.read_ascii(BOOKS / "problems" / "shikatsu-myoki.txt"),
            import_shikatsu_myoki.read_collection(source),
        )
        with (source / "source-map.csv").open(newline="") as source_map:
            self.assertEqual(
                [
                    {"source_problem": str(number), "book_problem": identifier,
                     "section": title,
                     "page_url": f"{import_shikatsu_myoki.SERIES_URL}{number}"}
                    for number, identifier, title in selected
                ],
                list(csv.DictReader(source_map)),
            )

    def test_senseis_numbered_stones_are_part_of_the_problem(self) -> None:
        source = BOOKS / "sources" / "shikatsu-myoki" / "74.sgf"
        root, _ = problems._SgfParser(source.read_text(), source).collection()[0]
        expected = problems.normalize(problems.Problem(
            identifier="74",
            black=frozenset(problems._sgf_setup_points(root["AB"], source)),
            white=frozenset(problems._sgf_setup_points(root["AW"], source) | {(18, 3)}),
        ))
        self.assertEqual(expected, import_shikatsu_myoki.read_diagram(source))
        # The generic collection importer must still ignore solution moves.
        self.assertEqual(
            len(root["AB"]), len(problems.read_sgf(source)[0].white)
        )
        self.assertEqual(
            len(root["AW"]), len(problems.read_sgf(source)[0].black)
        )

    def test_senseis_diagram_moves_capture_and_follow_caption_player(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "capture.sgf"
            source.write_text(
                "(;GM[1]SZ[19]GN[White to play]PL[B]AB[ba]AW[aa];B[ab])"
            )
            self.assertEqual(
                problems.normalize(problems.Problem(
                    identifier="capture", black=frozenset(),
                    white=frozenset({(1, 0), (0, 1)}),
                )),
                import_shikatsu_myoki.read_diagram(source),
            )

    def test_shikatsu_index_requires_complete_source_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "series-index.html").write_text(
                '<a href="/?ShikatsuMyokiTsumegoSeries1">1</a>'
            )
            with self.assertRaisesRegex(ValueError, "expected index entries"):
                import_shikatsu_myoki.selected_sources(source)

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

    def test_contents_pages_and_links_match_layouts(self) -> None:
        for collection in ("gokyoshumyo", "shikatsu-myoki", "gokyo-seimyo"):
            source = problems.read_ascii(BOOKS / "problems" / f"{collection}.txt")
            content = (BOOKS / "content" / f"{collection}.tex").read_text()
            entries = re.findall(r"\\chapterentry\{(\d+)\}\{[^}]+\}\{(\d+)\}", content)
            for chapter, count in entries:
                self.assertEqual(
                    int(count),
                    sum(problem.identifier.startswith(f"{chapter}-") for problem in source),
                )
            self.assertIn("goto name {problem-#1-1}", content)
            for profile in ("a5", "a6"):
                with self.subTest(collection=collection, profile=profile):
                    columns = problems.plan_layout(source, profile)
                    actual: list[int] = []
                    for column_index, column in enumerate(columns):
                        page = column_index // 2 + 1 if profile == "a5" else column_index + 1
                        for problem, _ in column:
                            if re.fullmatch(r"\d+-1", problem.identifier):
                                actual.append(page)

                    wrapper = (BOOKS / f"{profile}-{collection}.tex").read_text()
                    match = re.search(
                        r"\\def\\chapterpage#1\{\\ifcase#1((?:\\or\d+)+)\\fi\}",
                        wrapper,
                    )
                    self.assertIsNotNone(match)
                    listed = [int(page) for page in match.group(1).split(r"\or") if page]
                    self.assertEqual(actual, listed)
                    self.assertEqual(len(entries), len(listed))
                    with tempfile.TemporaryDirectory() as directory:
                        output = Path(directory) / "problems.tex"
                        problems.render_tex(source, output, profile)
                        targets = re.findall(r"\\pdfdest name \{([^}]+)\} xyz", output.read_text())
                        self.assertEqual(
                            [f"problem-{chapter}-1" for chapter, _ in entries], targets
                        )

    def test_gokyo_seimyo_sections_and_signature_share_a_box(self) -> None:
        content = (BOOKS / "content" / "gokyo-seimyo.tex").read_text()
        start = content.index(r"\vbox{") + len(r"\vbox{")
        depth = 1
        for end in range(start, len(content)):
            if content[end] == "{":
                depth += 1
            elif content[end] == "}":
                depth -= 1
            if depth == 0:
                break
        self.assertEqual(0, depth)
        block = content[start:end]
        self.assertIn(r"\header Sections", block)
        self.assertEqual(5, block.count(r"\chapterentry{"))
        self.assertIn(r"\rightline{\it\me}", block)
        self.assertIn(r"\rightline{\it November 2026}", block)
        self.assertNotIn(r"\baselineskip", block)

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
