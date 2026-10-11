# Problem data

Problem collections use a small, editable ASCII format as their source of
truth. The books generate their Plain TeX diagrams from the `.txt` files.

## Format

Each problem starts with `problem ID` and is followed by a rectangular diagram:

```text
problem 12
..x...
.xoo..
......
```

The symbols are:

- `.` — empty intersection
- `x` — black stone
- `o` — white stone
- `A` through `Z` — a labelled empty intersection

Blank lines and lines starting with `#` are ignored. Omitted intersections to
the right and below are empty; the underlying board is always 19 by 19. The
last row and column in the ASCII diagram provide one empty line of context when
possible. They are not necessarily board edges.

All positions are normalized to **Black to play**. Positions are transformed by
one of the eight symmetries of the square to minimize their height and then
their width, placing local problems toward the top-left. This is the same rule
used by the historical `scripts/rotate.pl`.

## Tooling

From the `books` directory:

```sh
# Validate canonical data
../scripts/problems.py check problems/xxqj.txt

# Import positions, remove duplicates under board symmetry, and renumber
../scripts/problems.py import-sgf --default-player W --deduplicate-symmetries \
    --source-map sources/guan-zi-pu/source-map.csv \
    sources/guan-zi-pu/gzp{1,2,3}.sgf problems/guan-zi-pu.txt

# Run the validation and round-trip regression tests
make test

# Generate input for the existing Plain TeX books
../scripts/problems.py render-tex --profile a5 \
    problems/xxqj.txt generated/a5-xxqj.tex

# Export a standard SGF collection
../scripts/problems.py export-sgf problems/xxqj.txt /tmp/xxqj.sgf
```

Generated TeX is a build artifact. A5 and A6 are separately paginated so their
diagram sizing and layout can diverge without changing problem data. A5 columns
are padded to the same total height. Full-height columns and matching bottoms
come first; when several layouts are otherwise equivalent, neighboring problem
tops and captions are aligned, then matching heights are preferred. Diagrams
always retain an empty row after the
stones; heights 15 through 18 are avoided by expanding such diagrams to the
full 19 rows.
