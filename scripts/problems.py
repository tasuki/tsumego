#!/usr/bin/env python3
"""Convert, validate, and render the book's tsumego problem data.

The canonical format is documented in problems/README.md.  This module has no
third-party dependencies so that building the books only requires Python and
TeX.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, replace
from functools import cache
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


class _SgfParser:
    """Small FF[4] parser sufficient for importing problem positions."""

    def __init__(self, text: str, path: Path) -> None:
        self.text = text
        self.path = path
        self.position = 0

    def _error(self, message: str) -> ValueError:
        line = self.text.count("\n", 0, self.position) + 1
        return ValueError(f"{self.path}:{line}: {message}")

    def _skip_whitespace(self) -> None:
        while self.position < len(self.text) and self.text[self.position].isspace():
            self.position += 1

    def _expect(self, value: str) -> None:
        self._skip_whitespace()
        if not self.text.startswith(value, self.position):
            raise self._error(f"expected {value!r}")
        self.position += len(value)

    def _value(self) -> str:
        self._expect("[")
        value: list[str] = []
        while self.position < len(self.text):
            character = self.text[self.position]
            self.position += 1
            if character == "]":
                return "".join(value)
            if character == "\\":
                if self.position == len(self.text):
                    raise self._error("unfinished escape in property value")
                character = self.text[self.position]
                self.position += 1
                if character == "\r":
                    if self.position < len(self.text) and self.text[self.position] == "\n":
                        self.position += 1
                    continue
                if character == "\n":
                    continue
            value.append(character)
        raise self._error("unterminated property value")

    def _node(self) -> dict[str, list[str]]:
        self._expect(";")
        properties: dict[str, list[str]] = {}
        while True:
            self._skip_whitespace()
            start = self.position
            while (
                self.position < len(self.text)
                and "A" <= self.text[self.position] <= "Z"
            ):
                self.position += 1
            if self.position == start:
                return properties
            identifier = self.text[start : self.position]
            self._skip_whitespace()
            values: list[str] = []
            while self.position < len(self.text) and self.text[self.position] == "[":
                values.append(self._value())
                self._skip_whitespace()
            if not values:
                raise self._error(f"property {identifier} has no value")
            properties.setdefault(identifier, []).extend(values)

    def _game_tree(self) -> tuple[list[dict[str, list[str]]], str | None]:
        self._expect("(")
        self._skip_whitespace()
        nodes: list[dict[str, list[str]]] = []
        while self.position < len(self.text) and self.text[self.position] == ";":
            nodes.append(self._node())
            self._skip_whitespace()
        if not nodes:
            raise self._error("game tree has no nodes")

        first_player: str | None = None
        for node in nodes:
            players = [player for player in ("B", "W") if player in node]
            if len(players) > 1:
                raise self._error("node contains both a Black and White move")
            if players and first_player is None:
                first_player = players[0]

        while self.position < len(self.text) and self.text[self.position] == "(":
            _, variation_player = self._game_tree()
            if first_player is None:
                first_player = variation_player
            self._skip_whitespace()
        self._expect(")")
        return nodes, first_player

    def sequences(self) -> list[tuple[list[dict[str, list[str]]], str | None]]:
        """Read each game's main sequence, keeping variations out of the position."""
        # The u-go.net collections have a plain-text provenance paragraph before
        # the first tree. SGF itself starts at the first opening parenthesis.
        match = re.search(r"\(\s*;", self.text)
        if match is None:
            raise self._error("no SGF game trees found")
        self.position = match.start()

        trees: list[tuple[list[dict[str, list[str]]], str | None]] = []
        while self.position < len(self.text):
            self._skip_whitespace()
            if self.position == len(self.text):
                break
            if self.text[self.position] != "(":
                raise self._error("unexpected text between game trees")
            trees.append(self._game_tree())
        return trees

    def collection(self) -> list[tuple[dict[str, list[str]], str | None]]:
        return [(nodes[0], player) for nodes, player in self.sequences()]


def _sgf_setup_points(values: Iterable[str], path: Path) -> set[tuple[int, int]]:
    points: set[tuple[int, int]] = set()

    def point(value: str) -> tuple[int, int]:
        if len(value) != 2 or any(not ("a" <= item <= "s") for item in value):
            raise ValueError(f"{path}: unsupported SGF point {value!r}")
        return ord(value[0]) - ord("a"), ord(value[1]) - ord("a")

    for value in values:
        if ":" not in value:
            points.add(point(value))
            continue
        start, end = value.split(":", 1)
        start_x, start_y = point(start)
        end_x, end_y = point(end)
        for x in range(min(start_x, end_x), max(start_x, end_x) + 1):
            for y in range(min(start_y, end_y), max(start_y, end_y) + 1):
                points.add((x, y))
    return points


def read_sgf(
    path: Path,
    *,
    start_number: int = 1,
    default_player: str | None = None,
) -> list[Problem]:
    """Read initial positions from an SGF collection, ignoring solution moves."""
    parser = _SgfParser(path.read_text(encoding="utf-8"), path)
    problems: list[Problem] = []
    for number, (root, first_player) in enumerate(parser.collection(), 1):
        if root.get("GM", ["1"]) != ["1"]:
            raise ValueError(f"{path}: game {number} is not Go")
        if root.get("SZ", [str(BOARD_SIZE)]) != [str(BOARD_SIZE)]:
            raise ValueError(f"{path}: game {number} is not on a 19x19 board")

        identifier = str(start_number + number - 1)
        black = _sgf_setup_points(root.get("AB", []), path)
        white = _sgf_setup_points(root.get("AW", []), path)
        player_values = root.get("PL", [])
        if len(player_values) > 1 or (
            player_values and player_values[0] not in ("B", "W")
        ):
            raise ValueError(f"{path}: game {number} has invalid PL")
        player = (
            player_values[0] if player_values else first_player or default_player
        )
        if player is None:
            raise ValueError(
                f"{path}: game {number} does not specify which player moves first"
            )
        if player == "W":
            black, white = white, black

        problems.append(
            normalize(
                Problem(
                    identifier=identifier,
                    black=frozenset(black),
                    white=frozenset(white),
                )
            )
        )
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


def deduplicate(
    problems: Sequence[Problem],
    *,
    symmetries: bool = False,
) -> tuple[list[Problem], dict[str, str]]:
    """Keep the first exact position; map every source ID to its retained ID.

    Compare stones and labels, ignoring identifiers and diagram margins.
    Optionally allow all eight board symmetries, but never translations,
    colour reversal, or near-matches. Solution moves are ignored.
    """
    unique: list[Problem] = []
    first_by_position = {}
    source_to_retained: dict[str, str] = {}
    for problem in problems:
        key = min(
            (
                tuple(sorted(_transform_point(index, x, y) for x, y in problem.black)),
                tuple(sorted(_transform_point(index, x, y) for x, y in problem.white)),
                tuple(sorted(
                    (*_transform_point(index, x, y), label)
                    for x, y, label in problem.labels
                )),
            )
            for index in range(8 if symmetries else 1)
        )
        if key not in first_by_position:
            first_by_position[key] = problem.identifier
            unique.append(problem)
        source_to_retained[problem.identifier] = first_by_position[key]
    return unique, source_to_retained


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


# Every vertical unit is exactly one board row.  A problem's caption and the
# space around it occupy exactly two such rows, giving both formats a regular
# baseline grid. These budgets define the usable height of a generated column.
_PROFILE_METRICS = {
    "a5": (1, 2, 56),   # board row, caption area, column height
    "a6": (1, 2, 30),
}
_INTER_PROBLEM_ROWS = 1


@cache
def _render_height(problem: Problem) -> int:
    """Return an allowed height while preserving an empty row after stones."""
    if 15 <= problem.height <= 18:
        return BOARD_SIZE
    return problem.height


def _column_natural_units(group: Sequence[Problem], profile: str) -> int:
    row_unit, caption_rows, _ = _PROFILE_METRICS[profile]
    problem_units = sum(
        _render_height(problem) * row_unit + caption_rows for problem in group
    )
    gaps = max(0, len(group) - 1) * _INTER_PROBLEM_ROWS
    return problem_units + gaps


def _available_padding(group: Sequence[Problem], profile: str) -> int:
    _, _, budget = _PROFILE_METRICS[profile]
    natural = _column_natural_units(group, profile)
    if natural > budget:
        raise ValueError(
            f"{profile} layout column is too tall ({natural} > {budget} lines)"
        )
    return budget - natural


def _allowed_paddings(problem: Problem, maximum: int) -> tuple[int, ...]:
    """Return padding values that never produce a 15--18-row diagram."""
    height = _render_height(problem)
    if height == BOARD_SIZE:
        return (0,)
    values = list(range(min(14 - height, maximum) + 1))
    full_board_padding = BOARD_SIZE - height
    if full_board_padding <= maximum:
        values.append(full_board_padding)
    return tuple(values)


def _waterfill_padding(group: Sequence[Problem], available: int) -> list[int]:
    """Use as many whole rows as possible, then favor even diagram heights."""
    # used rows -> (negative sum of squared heights, padding)
    states: dict[int, tuple[int, tuple[int, ...]]] = {0: (0, ())}
    for problem in group:
        next_states: dict[int, tuple[int, tuple[int, ...]]] = {}
        for used, (balance, padding) in states.items():
            for add in _allowed_paddings(problem, available - used):
                new_used = used + add
                candidate = (
                    balance - (_render_height(problem) + add) ** 2,
                    padding + (add,),
                )
                previous = next_states.get(new_used)
                if previous is None or candidate[0] > previous[0]:
                    next_states[new_used] = candidate
        states = next_states
    _, result = max(states.items(), key=lambda item: (item[0], item[1][0]))
    return list(result[1])


def _balanced_padding(
    left: Sequence[Problem], right: Sequence[Problem]
) -> tuple[list[int], list[int]]:
    """Fill both A5 columns, preferring matching bottoms and neighbor heights."""
    available_left = _available_padding(left, "a5")
    available_right = _available_padding(right, "a5")
    count = max(len(left), len(right))

    row_unit, caption_rows, _ = _PROFILE_METRICS["a5"]
    base_left = [0]
    for index, problem in enumerate(left):
        gap = _INTER_PROBLEM_ROWS if index < len(left) - 1 else 0
        base_left.append(
            base_left[-1] + _render_height(problem) * row_unit + caption_rows + gap
        )
    base_right = [0]
    for index, problem in enumerate(right):
        gap = _INTER_PROBLEM_ROWS if index < len(right) - 1 else 0
        base_right.append(
            base_right[-1] + _render_height(problem) * row_unit + caption_rows + gap
        )

    # State score: aligned tops/captions, proximity, equal heights, balance.
    states: dict[
        tuple[int, int],
        tuple[int, int, int, int, tuple[int, ...], tuple[int, ...]],
    ] = {(0, 0): (0, 0, 0, 0, (), ())}
    for index in range(count):
        next_states: dict[
            tuple[int, int],
            tuple[int, int, int, int, tuple[int, ...], tuple[int, ...]],
        ] = {}
        has_left = index < len(left)
        has_right = index < len(right)
        for (used_left, used_right), state in states.items():
            aligned, distance, equal, balance, pads_left, pads_right = state
            left_values = (
                _allowed_paddings(left[index], available_left - used_left)
                if has_left
                else (0,)
            )
            right_values = (
                _allowed_paddings(right[index], available_right - used_right)
                if has_right
                else (0,)
            )
            start_left = base_left[index] + used_left if has_left else 0
            start_right = base_right[index] + used_right if has_right else 0
            for add_left in left_values:
                for add_right in right_values:
                    new_aligned = aligned
                    new_distance = distance
                    new_equal = equal
                    new_balance = balance
                    if has_left:
                        height_left = _render_height(left[index]) + add_left
                        new_balance -= height_left**2
                    if has_right:
                        height_right = _render_height(right[index]) + add_right
                        new_balance -= height_right**2
                    if has_left and has_right:
                        caption_left = start_left + height_left
                        caption_right = start_right + height_right
                        new_aligned += int(start_left == start_right) + int(
                            caption_left == caption_right
                        )
                        new_distance -= abs(start_left - start_right) + abs(
                            caption_left - caption_right
                        )
                        new_equal += int(height_left == height_right)
                    key = (used_left + add_left, used_right + add_right)
                    candidate = (
                        new_aligned,
                        new_distance,
                        new_equal,
                        new_balance,
                        pads_left + ((add_left,) if has_left else ()),
                        pads_right + ((add_right,) if has_right else ()),
                    )
                    previous = next_states.get(key)
                    if previous is None or candidate[:4] > previous[:4]:
                        next_states[key] = candidate
        states = next_states

    natural_left = _column_natural_units(left, "a5")
    natural_right = _column_natural_units(right, "a5")
    _, result = max(
        states.items(),
        key=lambda item: (
            -abs(
                natural_left + item[0][0] - natural_right - item[0][1]
            ),
            min(natural_left + item[0][0], natural_right + item[0][1]),
            item[1][0],
            item[1][1],
            item[1][2],
            item[1][3],
        ),
    )
    return list(result[4]), list(result[5])


def paginate(problems: Sequence[Problem], profile: str) -> list[tuple[int, ...]]:
    """Choose fresh page boundaries; preserving historical pages is not a goal."""
    _, _, budget = _PROFILE_METRICS[profile]
    pages: list[tuple[int, ...]] = []
    offset = 0

    if profile == "a6":
        while offset < len(problems):
            count = 1
            while (
                offset + count < len(problems)
                and _column_natural_units(
                    problems[offset : offset + count + 1], profile
                )
                <= budget
            ):
                count += 1
            pages.append((count,))
            offset += count
        return pages

    while offset < len(problems):
        remaining = len(problems) - offset
        candidates: list[tuple[tuple[int, int, int, int], int, int]] = []
        for left_count in range(1, remaining + 1):
            left = problems[offset : offset + left_count]
            left_height = _column_natural_units(left, profile)
            if left_height > budget:
                break
            right_limit = remaining - left_count
            if right_limit == 0:
                candidates.append(
                    ((left_count, -left_count, -left_height, 0), left_count, 0)
                )
                continue
            for right_count in range(1, right_limit + 1):
                right = problems[
                    offset + left_count : offset + left_count + right_count
                ]
                right_height = _column_natural_units(right, profile)
                if right_height > budget:
                    break
                score = (
                    left_count + right_count,
                    -abs(left_count - right_count),
                    -abs(left_height - right_height),
                    left_height + right_height,
                )
                candidates.append((score, left_count, right_count))
        if not candidates:
            raise ValueError(f"could not paginate {problems[offset].identifier}")
        _, left_count, right_count = max(candidates)
        pages.append((left_count, right_count))
        offset += left_count + right_count
    return pages


def plan_layout(
    problems: Sequence[Problem], profile: str
) -> list[list[tuple[Problem, int]]]:
    pages = paginate(problems, profile)
    columns: list[list[tuple[Problem, int]]] = []
    offset = 0
    for page in pages:
        groups: list[Sequence[Problem]] = []
        for count in page:
            groups.append(problems[offset : offset + count])
            offset += count
        if profile == "a5":
            paddings = _balanced_padding(groups[0], groups[1])
        else:
            paddings = (
                _waterfill_padding(groups[0], _available_padding(groups[0], profile)),
            )
        for group, padding in zip(groups, paddings):
            columns.append(list(zip(group, padding)))
    return columns


def render_tex(
    problems: Sequence[Problem], path: Path, profile: str
) -> None:
    """Render generated input for the existing go fonts and Plain TeX layout."""
    if profile not in _PROFILE_METRICS:
        raise ValueError(f"unknown output profile {profile!r}")

    width = BOARD_SIZE
    columns = plan_layout(problems, profile)

    _, caption_rows, column_rows = _PROFILE_METRICS[profile]
    used_rows = [
        sum(
            _render_height(problem) + padding + caption_rows
            for problem, padding in column
        )
        + max(0, len(column) - 1) * _INTER_PROBLEM_ROWS
        for column in columns
    ]
    leading_rows = [0] * len(columns)
    trailing_rows = [column_rows - used for used in used_rows]
    if profile == "a5":
        for index in range(0, len(columns), 2):
            common_end = max(used_rows[index : index + 2])
            for column_index in range(index, min(index + 2, len(columns))):
                leading_rows[column_index] = common_end - used_rows[column_index]
                trailing_rows[column_index] = column_rows - common_end

    chunks = [
        "% Generated by scripts/problems.py; do not edit.",
        r"\offinterlineskip",
        r"\setbox0\hbox{\gooegb +}\global\goIntHt=\ht0",
        "",
    ]
    for column_index, column in enumerate(columns):
        if leading_rows[column_index]:
            chunks.extend(
                [rf"\vskip {leading_rows[column_index]}\goIntHt", ""]
            )
        for problem_index, (problem, padding) in enumerate(column):
            # Sectioned collections use chapter-problem identifiers. Give
            # each chapter's first problem a stable target for its contents.
            if re.fullmatch(r"\d+-1", problem.identifier):
                chunks.extend(
                    [rf"\pdfdest name {{problem-{problem.identifier}}} xyz", ""]
                )
            chunks.append(r"\vbox{\vbox{\goo")
            label_at = {(x, y): label for x, y, label in problem.labels}
            for y in range(_render_height(problem) + padding):
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
                    r"\vbox to 2\goIntHt{\vfil"
                    + rf"\hbox to \hsize{{\hfil problem {problem.identifier}\hfil}}"
                    + r"\vfil}",
                    "}",
                    "",
                ]
            )
            if problem_index < len(column) - 1:
                chunks.extend([r"\vskip \goIntHt", ""])
        if trailing_rows[column_index]:
            chunks.append(rf"\vskip {trailing_rows[column_index]}\goIntHt")
        chunks.extend([r"\eject", ""])
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

    sgf_importer = commands.add_parser("import-sgf", help="convert SGF positions to ASCII")
    sgf_importer.add_argument(
        "--default-player",
        choices=("B", "W"),
        help="player to use when neither PL nor a solution move specifies one",
    )
    sgf_importer.add_argument(
        "--deduplicate",
        action="store_true",
        help="keep the first exact normalized position and renumber consecutively",
    )
    sgf_importer.add_argument(
        "--deduplicate-symmetries",
        action="store_true",
        help="deduplicate including board rotations/reflections and renumber",
    )
    sgf_importer.add_argument(
        "--source-map",
        type=Path,
        help="write a CSV mapping original global source numbers to book numbers",
    )
    sgf_importer.add_argument("sources", type=Path, nargs="+")
    sgf_importer.add_argument("destination", type=Path)

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
        elif args.command == "import-sgf":
            problems = []
            for source in args.sources:
                problems.extend(
                    read_sgf(
                        source,
                        start_number=len(problems) + 1,
                        default_player=args.default_player,
                    )
                )
            source_count = len(problems)
            if args.deduplicate or args.deduplicate_symmetries:
                problems, source_to_retained = deduplicate(
                    problems, symmetries=args.deduplicate_symmetries
                )
            else:
                source_to_retained = {
                    problem.identifier: problem.identifier for problem in problems
                }
            retained_to_book = {
                problem.identifier: str(number)
                for number, problem in enumerate(problems, 1)
            }
            problems = [
                replace(problem, identifier=retained_to_book[problem.identifier])
                for problem in problems
            ]
            write_ascii(problems, args.destination)
            if args.source_map:
                args.source_map.parent.mkdir(parents=True, exist_ok=True)
                with args.source_map.open("w", encoding="utf-8", newline="") as output:
                    writer = csv.writer(output, lineterminator="\n")
                    writer.writerow(
                        ["source_problem", "book_problem", "kept_source_problem"]
                    )
                    for source_id, retained_id in source_to_retained.items():
                        writer.writerow(
                            [source_id, retained_to_book[retained_id], retained_id]
                        )
            print(f"wrote {len(problems)} problems to {args.destination}")
            if args.deduplicate or args.deduplicate_symmetries:
                print(f"removed {source_count - len(problems)} exact duplicates")
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
