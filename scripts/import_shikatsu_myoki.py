#!/usr/bin/env python3
"""Import the non-variation Shikatsu Myoki positions from archived Sensei's SGFs."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import replace
from pathlib import Path

from problems import Problem, _SgfParser, _sgf_setup_points, normalize, write_ascii

SECTIONS = (
    ("Killing", 1, 73, 48),
    ("Living", 74, 117, 30),
    ("Ko", 118, 155, 32),
    ("Capturing Races", 156, 168, 10),
)
SERIES_URL = "https://senseis.xmp.net/?ShikatsuMyokiTsumegoSeries"


def selected_sources(source: Path) -> list[tuple[int, str, str]]:
    """Return (source number, chapter-problem ID, section) in index order."""
    index = (source / "series-index.html").read_text(encoding="latin-1")
    links = re.findall(
        r'<a href="/\?ShikatsuMyokiTsumegoSeries(\d+)">(\d+)(v?)</a>',
        index,
    )
    if [(int(number), int(label)) for number, label, _ in links] != [
        (number, number) for number in range(1, 169)
    ]:
        raise ValueError("expected index entries 1–168 in source order")
    selected = [int(number) for number, _, variation in links if not variation]
    result = []
    for chapter, (title, start, end, count) in enumerate(SECTIONS, 1):
        numbers = [number for number in selected if start <= number <= end]
        if len(numbers) != count:
            raise ValueError(f"{title}: expected {count} non-variation problems")
        result.extend(
            (number, f"{chapter}-{position}", title)
            for position, number in enumerate(numbers, 1)
        )
    return result


def _play(
    point: tuple[int, int], own: set[tuple[int, int]], other: set[tuple[int, int]]
) -> None:
    """Apply a numbered stone in a displayed diagram, including any captures."""
    if point in own | other:
        raise ValueError(f"diagram move overlaps a stone at {point}")
    own.add(point)

    def neighbors(point: tuple[int, int]) -> set[tuple[int, int]]:
        x, y = point
        return {(a, b) for a, b in ((x-1, y), (x+1, y), (x, y-1), (x, y+1))
                if 0 <= a < 19 and 0 <= b < 19}

    def captured(start: tuple[int, int], stones: set[tuple[int, int]]) -> set[tuple[int, int]]:
        group, pending = set(), {start}
        liberties = set()
        while pending:
            current = pending.pop()
            group.add(current)
            adjacent = neighbors(current)
            liberties.update(adjacent - (own | other))
            pending.update((adjacent & stones) - group)
        return set() if liberties else group

    for adjacent in neighbors(point) & other:
        if adjacent in other:
            other.difference_update(captured(adjacent, other))
    if captured(point, own):
        raise ValueError(f"suicidal diagram move at {point}")


def read_diagram(path: Path) -> Problem:
    """Sensei's diagram SGFs describe displayed moves, not solution trees.

    GoWiki's PL is the player of the first displayed numbered move. The caption
    names the player who must solve the problem *after* those moves are played.
    """
    games = _SgfParser(path.read_text(encoding="utf-8"), path).sequences()
    if len(games) != 1:
        raise ValueError(f"{path}: expected one SGF diagram")
    nodes, _ = games[0]
    root = nodes[0]
    if root.get("GM", ["1"]) != ["1"] or root.get("SZ", ["19"]) != ["19"]:
        raise ValueError(f"{path}: expected a 19x19 Go diagram")
    caption = root.get("GN", [""])[0]
    player = re.match(r"(Black|White)\b", caption, re.IGNORECASE)
    if player is None:
        raise ValueError(f"{path}: caption does not name the player to play")
    black = _sgf_setup_points(root.get("AB", []), path)
    white = _sgf_setup_points(root.get("AW", []), path)
    for node in nodes:
        if node is not root and any(key in node for key in ("AB", "AW", "AE")):
            raise ValueError(f"{path}: unexpected setup after diagram root")
        for color in ("B", "W"):
            for value in node.get(color, []):
                if value:  # An empty SGF move is a pass.
                    point, = _sgf_setup_points([value], path)
                    own, other = (black, white) if color == "B" else (white, black)
                    _play(point, own, other)
    if player[1].lower() == "white":
        black, white = white, black
    return normalize(Problem(path.stem, frozenset(black), frozenset(white)))


def read_collection(source: Path) -> list[Problem]:
    return [
        replace(read_diagram(source / f"{number}.sgf"), identifier=identifier)
        for number, identifier, _ in selected_sources(source)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="archived index and numbered SGFs")
    parser.add_argument("destination", type=Path, help="canonical ASCII collection")
    args = parser.parse_args()
    try:
        collection = read_collection(args.source)
        write_ascii(collection, args.destination)
        with (args.source / "source-map.csv").open(
            "w", encoding="utf-8", newline=""
        ) as output:
            writer = csv.writer(output, lineterminator="\n")
            writer.writerow(["source_problem", "book_problem", "section", "page_url"])
            for number, identifier, title in selected_sources(args.source):
                writer.writerow([number, identifier, title, f"{SERIES_URL}{number}"])
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(f"wrote {len(collection)} problems to {args.destination}")


if __name__ == "__main__":
    main()
