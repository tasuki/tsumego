#!/usr/bin/env python3
"""Import Volume 3 of Gokyo Seimyo from archived Sensei's Library diagrams."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from problems import Problem, _SgfParser, _sgf_setup_points, normalize, write_ascii

INDEX_URL = "https://senseis.xmp.net/?GokyoSeimyoTsumegoSeries"
PROBLEM_URL = "https://senseis.xmp.net/?GokyoSeimyoVolume3Problem"
REFERENCE_TITLES = {
    66: "hanezeki",
    68: "eternal life (chosei)",
    69: "double-ko seki",
}
SECTIONS = (
    ("Tesuji inside territories", 1, 44, 44),
    ("Other problems", 45, 118, 74),
    ("Connect underneath", 119, 128, 10),
    ("Cut/connect groups", 129, 136, 8),
    ("Ladder", 137, 145, 9),  # 146 links to the same diagram as 145.
)
# 37's caption reads "hite to move"; 62 has no caption, but its page explicitly
# says White to play. 55's caption correctly says White despite its PL[B].
PLAYER_OVERRIDES = {37: "W", 62: "W"}


def selected_sources(source: Path) -> list[tuple[int, str, str]]:
    index = (source / "series-index.html").read_text(encoding="latin-1")
    links = re.findall(
        r'<a href="/\?GokyoSeimyoVolume3Problem(\d+)">(\d+)</a>', index
    )
    if [(int(number), int(label)) for number, label in links] != [
        (number, number) for number in range(1, 147)
    ]:
        raise ValueError("expected index entries 1–146 in source order")
    result = []
    for chapter, (title, start, end, count) in enumerate(SECTIONS, 1):
        numbers = list(range(start, end + 1))
        if len(numbers) != count:
            raise ValueError(f"{title}: expected {count} problems")
        result.extend((number, f"{chapter}-{position}", title)
                      for position, number in enumerate(numbers, 1))
    return result


def read_diagram(path: Path, number: int, identifier: str) -> Problem:
    games = _SgfParser(path.read_text(encoding="utf-8"), path).sequences()
    if len(games) != 1:
        raise ValueError(f"{path}: expected one SGF diagram")
    nodes, _ = games[0]
    root = nodes[0]
    if root.get("GM", ["1"]) != ["1"] or root.get("SZ", ["19"]) != ["19"]:
        raise ValueError(f"{path}: expected a 19x19 Go diagram")
    if any(key in node for node in nodes[1:] for key in ("B", "W", "AB", "AW", "AE")):
        raise ValueError(f"{path}: unexpected moves or setup after diagram root")
    caption = root.get("GN", [""])[0].strip().strip("()")
    match = re.match(r"(Black|White)\b", caption, re.IGNORECASE)
    player = PLAYER_OVERRIDES.get(number)
    if number in REFERENCE_TITLES:
        # Nothing to solve: preserve source colours rather than infer a turn.
        player = "B"
    if player is None:
        if match is None:
            raise ValueError(f"{path}: caption does not name the player to play")
        player = match[1][0].upper()
    black = _sgf_setup_points(root.get("AB", []), path)
    white = _sgf_setup_points(root.get("AW", []), path)
    labels = []
    # These labels only refer to alternative positions discussed below the diagram.
    if number not in (72, 84):
        for value in root.get("LB", []):
            coordinate, separator, label = value.partition(":")
            if not separator:
                raise ValueError(f"{path}: invalid LB {value!r}")
            point, = _sgf_setup_points([coordinate], path)
            labels.append((*point, label.upper()))
    if player == "W":
        black, white = white, black
    return normalize(Problem(
        identifier=identifier, black=frozenset(black), white=frozenset(white),
        labels=tuple(labels), title=REFERENCE_TITLES.get(number, ""),
    ))


def read_collection(source: Path) -> list[Problem]:
    selected = selected_sources(source)
    if {path.stem for path in source.glob("*.sgf")} != {str(n) for n in range(1, 147)}:
        raise ValueError("expected exactly the 146 archived diagram SGFs")
    if (source / "145.sgf").read_bytes() != (source / "146.sgf").read_bytes():
        raise ValueError("expected source 146 to duplicate source 145")
    return [read_diagram(source / f"{number}.sgf", number, identifier)
            for number, identifier, _ in selected]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="archived index and numbered SGFs")
    parser.add_argument("destination", type=Path, help="canonical ASCII collection")
    args = parser.parse_args()
    try:
        collection = read_collection(args.source)
        write_ascii(collection, args.destination)
        with (args.source / "source-map.csv").open("w", encoding="utf-8", newline="") as output:
            writer = csv.writer(output, lineterminator="\n")
            writer.writerow(["source_problem", "book_problem", "section", "page_url"])
            for number, identifier, title in selected_sources(args.source):
                writer.writerow([number, identifier, title, f"{PROBLEM_URL}{number}"])
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(f"wrote {len(collection)} problems to {args.destination}")


if __name__ == "__main__":
    main()
