#!/usr/bin/env python3
"""Convert, validate, and render the book's tsumego problem data.

The canonical format is documented in problems/README.md.  This module has no
third-party dependencies so that building the books only requires Python and
TeX.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

BOARD_SIZE = 19
GRID_CHARACTERS = frozenset(".xoABCDEFGHIJKLMNOPQRSTUVWXYZ")


@dataclass(frozen=True)
class Problem:
    identifier: str
    black: frozenset[tuple[int, int]]
    white: frozenset[tuple[int, int]]
    labels: tuple[tuple[int, int, str], ...] = ()
    width: int = BOARD_SIZE
    height: int = BOARD_SIZE

    def __post_init__(self) -> None:
        points = set(self.black) | set(self.white)
        label_points = {(x, y) for x, y, _ in self.labels}
        if self.black & self.white:
            raise ValueError(f"problem {self.identifier}: black and white overlap")
        if points & label_points:
            raise ValueError(f"problem {self.identifier}: a label overlaps a stone")
        if not points and not label_points:
            raise ValueError(f"problem {self.identifier}: empty diagram")
        for x, y in points | label_points:
            if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
                raise ValueError(
                    f"problem {self.identifier}: point {(x, y)} is outside the board"
                )
        if not (1 <= self.width <= BOARD_SIZE and 1 <= self.height <= BOARD_SIZE):
            raise ValueError(f"problem {self.identifier}: invalid diagram dimensions")
        if any(x >= self.width or y >= self.height for x, y in points | label_points):
            raise ValueError(
                f"problem {self.identifier}: diagram dimensions omit occupied points"
            )
        for _, _, label in self.labels:
            if len(label) != 1 or not label.isupper() or not label.isascii():
                raise ValueError(
                    f"problem {self.identifier}: unsupported label {label!r}"
                )


# A cell is an empty intersection, a setup stone, or an empty labelled point.
# The final character of an old cell selects the go-font background glyph; it
# is presentation rather than problem data.
_LEGACY_CELL_RE = re.compile(
    r"\\0\?\?.|\\-\s*(?P<stone>[@!]).|\\!\s+(?P<label>[A-Z])"
)
_LEGACY_BLOCK_RE = re.compile(
    r"^\\vbox\{\\vbox\{\\goo\n"
    r"(?P<board>.*?)"
    r"^\}\n\\hfil problem (?P<caption>[^\\]+)\\hfil\\break\n\}",
    re.MULTILINE | re.DOTALL,
)


def read_legacy_tex(path: Path) -> list[Problem]:
    """Read active sgf2tex-style diagrams from a legacy TeX collection."""
    text = path.read_text(encoding="utf-8")
    problems: list[Problem] = []

    for match in _LEGACY_BLOCK_RE.finditer(text):
        caption = match.group("caption").strip()
        identifier, separator, player_text = caption.partition(",")
        player = "white" if "white to play" in player_text.lower() else "black"
        black: set[tuple[int, int]] = set()
        white: set[tuple[int, int]] = set()
        labels: list[tuple[int, int, str]] = []
        rows = match.group("board").splitlines()

        for y, row in enumerate(rows):
            cells = list(_LEGACY_CELL_RE.finditer(row))
            if len(cells) != BOARD_SIZE:
                raise ValueError(
                    f"{path}: problem {identifier}, row {y + 1}: "
                    f"expected {BOARD_SIZE} cells, found {len(cells)}"
                )
            for x, cell in enumerate(cells):
                stone = cell.group("stone")
                label = cell.group("label")
                if stone == "@":
                    black.add((x, y))
                elif stone == "!":
                    white.add((x, y))
                elif label:
                    labels.append((x, y, label))

        # Canonical diagrams always have Black to play.  Colour reversal does
        # not change the problem, and lets the books use one instruction.
        if player == "white":
            black, white = white, black

        problem = Problem(
            identifier=identifier.strip(),
            black=frozenset(black),
            white=frozenset(white),
            labels=tuple(labels),
            width=BOARD_SIZE,
            height=len(rows),
        )
        problems.append(normalize(problem))

    if not problems:
        raise ValueError(f"{path}: no active problem diagrams found")
    return problems


def _transform_point(index: int, x: int, y: int) -> tuple[int, int]:
    """Apply one of the eight square symmetries, preserving identity on ties."""
    last = BOARD_SIZE - 1
    transforms = (
        (x, y),
        (last - x, y),
        (x, last - y),
        (last - x, last - y),
        (y, x),
        (y, last - x),
        (last - y, x),
        (last - y, last - x),
    )
    return transforms[index]


def normalize(problem: Problem) -> Problem:
    """Put a position at top-left, minimizing height and then width.

    This is the rule used by the historical scripts/rotate.pl.  One empty row
    and column are retained after the last occupied point, except at a board
    edge.  Labels count as occupied points and are transformed with stones.
    """
    occupied = (
        set(problem.black)
        | set(problem.white)
        | {(x, y) for x, y, _ in problem.labels}
    )

    candidates: list[tuple[tuple[int, int, int], int]] = []
    for index in range(8):
        transformed = [_transform_point(index, x, y) for x, y in occupied]
        max_x = max(x for x, _ in transformed)
        max_y = max(y for _, y in transformed)
        candidates.append(((max_y, max_x, index), index))
    _, transform = min(candidates)

    def points(values: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
        return frozenset(_transform_point(transform, x, y) for x, y in values)

    black = points(problem.black)
    white = points(problem.white)
    labels = tuple(
        (*_transform_point(transform, x, y), label)
        for x, y, label in problem.labels
    )
    normalized_occupied = set(black) | set(white) | {
        (x, y) for x, y, _ in labels
    }
    width = min(BOARD_SIZE, max(x for x, _ in normalized_occupied) + 2)
    height = min(BOARD_SIZE, max(y for _, y in normalized_occupied) + 2)

    return Problem(
        identifier=problem.identifier,
        black=black,
        white=white,
        labels=labels,
        width=width,
        height=height,
    )


def read_ascii(path: Path) -> list[Problem]:
    problems: list[Problem] = []
    identifier: str | None = None
    rows: list[str] = []

    def finish() -> None:
        nonlocal identifier, rows
        if identifier is None:
            return
        if not rows:
            raise ValueError(f"{path}: problem {identifier} has no diagram")
        width = len(rows[0])
        if width == 0 or any(len(row) != width for row in rows):
            raise ValueError(f"{path}: problem {identifier} is not rectangular")
        if width > BOARD_SIZE or len(rows) > BOARD_SIZE:
            raise ValueError(f"{path}: problem {identifier} exceeds 19x19")

        black: set[tuple[int, int]] = set()
        white: set[tuple[int, int]] = set()
        labels: list[tuple[int, int, str]] = []
        for y, row in enumerate(rows):
            invalid = set(row) - GRID_CHARACTERS
            if invalid:
                raise ValueError(
                    f"{path}: problem {identifier} contains {sorted(invalid)!r}"
                )
            for x, value in enumerate(row):
                if value == "x":
                    black.add((x, y))
                elif value == "o":
                    white.add((x, y))
                elif value != ".":
                    labels.append((x, y, value))

        problems.append(
            Problem(
                identifier=identifier,
                black=frozenset(black),
                white=frozenset(white),
                labels=tuple(labels),
                width=width,
                height=len(rows),
            )
        )
        identifier = None
        rows = []

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("problem "):
            finish()
            identifier = line.removeprefix("problem ").strip()
            if not identifier:
                raise ValueError(f"{path}:{line_number}: missing problem identifier")
        elif identifier is None:
            raise ValueError(f"{path}:{line_number}: expected 'problem ID'")
        else:
            rows.append(line)
    finish()

    if not problems:
        raise ValueError(f"{path}: no problems found")
    identifiers = [problem.identifier for problem in problems]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{path}: duplicate problem identifier")
    return problems


def write_ascii(problems: Sequence[Problem], path: Path) -> None:
    chunks = [
        "# tsumego-ascii 1",
        "# All positions are normalized to the top-left with Black to play.",
        "# . empty, x black, o white, A-Z labelled empty point",
        "",
    ]
    for problem in problems:
        labels = {(x, y): label for x, y, label in problem.labels}
        chunks.append(f"problem {problem.identifier}")
        for y in range(problem.height):
            row: list[str] = []
            for x in range(problem.width):
                point = (x, y)
                if point in problem.black:
                    row.append("x")
                elif point in problem.white:
                    row.append("o")
                elif point in labels:
                    row.append(labels[point])
                else:
                    row.append(".")
            chunks.append("".join(row))
        chunks.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(chunks), encoding="utf-8")


def _background(x: int, y: int) -> str:
    last = BOARD_SIZE - 1
    if y == 0:
        return "<" if x == 0 else ">" if x == last else "("
    if y == last:
        return "," if x == 0 else "." if x == last else ")"
    if x == 0:
        return "["
    if x == last:
        return "]"
    return "*" if x in (3, 9, 15) and y in (3, 9, 15) else "+"


def render_tex(problems: Sequence[Problem], path: Path, profile: str) -> None:
    """Render generated input for the existing go fonts and Plain TeX layout."""
    if profile not in {"a5", "a6"}:
        raise ValueError(f"unknown output profile {profile!r}")

    # Keep the historical full board width during the initial migration.  The
    # separate profile argument deliberately makes later A5/A6 sizing changes
    # independent of the canonical problem data.
    width = BOARD_SIZE
    chunks = ["% Generated by tools/problems.py; do not edit.", ""]
    for problem in problems:
        chunks.append(r"\vbox{\vbox{\goo")
        label_at = {(x, y): label for x, y, label in problem.labels}
        for y in range(problem.height):
            cells: list[str] = []
            for x in range(width):
                point = (x, y)
                background = _background(x, y)
                if point in problem.black:
                    cells.append(r"\- @" + background)
                elif point in problem.white:
                    cells.append(r"\- !" + background)
                elif point in label_at:
                    cells.append(r"\!  " + label_at[point])
                else:
                    cells.append(r"\0??" + background)
            chunks.append("".join(cells))
        chunks.extend(
            [
                "}",
                rf"\hfil problem {problem.identifier}\hfil\break",
                "}",
                "",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(chunks), encoding="utf-8")


def _sgf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("]", r"\]")


def _sgf_point(x: int, y: int) -> str:
    return chr(ord("a") + x) + chr(ord("a") + y)


def write_sgf(problems: Sequence[Problem], path: Path) -> None:
    trees: list[str] = []
    for problem in problems:
        properties = [
            "GM[1]FF[4]CA[UTF-8]SZ[19]",
            f"GN[{_sgf_escape(problem.identifier)}]PL[B]",
        ]
        if problem.black:
            properties.append("AB" + "".join(f"[{_sgf_point(x, y)}]" for x, y in sorted(problem.black)))
        if problem.white:
            properties.append("AW" + "".join(f"[{_sgf_point(x, y)}]" for x, y in sorted(problem.white)))
        if problem.labels:
            properties.append(
                "LB"
                + "".join(
                    f"[{_sgf_point(x, y)}:{_sgf_escape(label)}]"
                    for x, y, label in sorted(problem.labels)
                )
            )
        properties.append(f"VW[aa:{_sgf_point(problem.width - 1, problem.height - 1)}]")
        trees.append("(;" + "\n".join(properties) + ")")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(trees) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    importer = commands.add_parser("import-legacy", help="convert legacy TeX to ASCII")
    importer.add_argument("source", type=Path)
    importer.add_argument("destination", type=Path)

    checker = commands.add_parser("check", help="validate an ASCII collection")
    checker.add_argument("source", type=Path)

    renderer = commands.add_parser("render-tex", help="generate Plain TeX diagrams")
    renderer.add_argument("--profile", choices=("a5", "a6"), required=True)
    renderer.add_argument("source", type=Path)
    renderer.add_argument("destination", type=Path)

    exporter = commands.add_parser("export-sgf", help="export an SGF collection")
    exporter.add_argument("source", type=Path)
    exporter.add_argument("destination", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "import-legacy":
            problems = read_legacy_tex(args.source)
            write_ascii(problems, args.destination)
            print(f"wrote {len(problems)} problems to {args.destination}")
        elif args.command == "check":
            problems = read_ascii(args.source)
            labels = sum(len(problem.labels) for problem in problems)
            print(f"{args.source}: {len(problems)} problems, {labels} labels")
        elif args.command == "render-tex":
            render_tex(read_ascii(args.source), args.destination, args.profile)
        elif args.command == "export-sgf":
            write_sgf(read_ascii(args.source), args.destination)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
