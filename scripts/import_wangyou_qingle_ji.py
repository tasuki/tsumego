#!/usr/bin/env python3
"""Import Wangyou Qingle Ji with diagram titles and without the revision marker."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from problems import Problem, _sgf_setup_points, read_sgf, write_ascii


def read_collection(source: Path) -> list[Problem]:
    paths = sorted(source.glob("*.sgf"))
    if [path.name for path in paths] != [f"{number:02}.sgf" for number in range(1, 38)]:
        raise ValueError("expected source files 01.sgf through 37.sgf")
    collection = []
    for number, path in enumerate(paths, 1):
        positions = read_sgf(path, start_number=number, include_titles=True)
        if len(positions) != 1 or not positions[0].title:
            raise ValueError(f"{path}: expected one named problem")
        problem = positions[0]
        if number == 3:
            problem = replace(problem, triangles=frozenset())
        elif number == 7:
            # This full-board position retains its source orientation. Mark the
            # five original Black corner stones, now White after colour reversal.
            targets = frozenset(_sgf_setup_points(["op", "pp", "qp", "rp", "or"], path))
            if not targets <= problem.white:
                raise ValueError(f"{path}: expected the five White corner target stones")
            problem = replace(problem, triangles=targets)
        elif number == 13:
            problem = replace(problem, title=problem.title.removesuffix(" (revised)"))
        if number in (13, 25, 33):
            problem = replace(problem, labels=tuple(label for label in problem.labels if label[2] != "A"))
        collection.append(problem)
    return collection


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        collection = read_collection(args.source)
        write_ascii(collection, args.destination)
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(f"wrote {len(collection)} problems to {args.destination}")


if __name__ == "__main__":
    main()
