# Wangyou Qingle Ji source SGFs

These 37 files were copied verbatim from the supplied sibling repository
`../wangyou-qingle-ji/`, keeping its filenames `01.sgf` through `37.sgf`.
`SHA256SUMS` pins the copies. Their SGF metadata identifies the exporter as
`puzzle2sgf:0.1`; each file contains one problem, its English name, a starting
position, a player-to-play property, comments, and solution branches.

The book includes all 37 positions in filename order, numbered 1–37, without
deduplication. Only the root setup is imported: solution moves, later labels,
and later triangle marks are not part of the starting diagram. White-to-play
positions are colour-reversed, and all positions are normalized to the top-left
using the standard book importer.

The English names are printed with each diagram, alongside its number. The
book's presentation differs from the unmodified source files as follows:

- Problem 3's obvious target group is left unmarked.
- Problem 7's five corner target stones are marked with triangles (original SGF
  points `op`, `pp`, `qp`, `rp`, and `or`; White stones in the printed book).
- Problem 13 omits the title suffix `(revised)` and the A mark identifying the
  older stone location. Its supplied stone position is unchanged.
- The Alcatraz problems (25 and 33) omit their starting-move A marks.

The printed collection has no letter labels and 23 triangle marks. There are
no separate problem notes. Original names, comments, marks, and solutions remain
in the archived SGFs.

Regenerate the canonical problem data from the repository root:

```sh
python3 scripts/import_wangyou_qingle_ji.py \
    books/sources/wangyou-qingle-ji books/problems/wangyou-qingle-ji.txt
(cd books/sources/wangyou-qingle-ji && sha256sum -c SHA256SUMS)
```

The zero-padded filenames ensure numerical ordering. No default player is
needed: every root specifies `PL`. Build both books with:

```sh
make -C books a5-wangyou-qingle-ji.pdf a6-wangyou-qingle-ji.pdf
```

`make -C books test` checks the source import, numbering, colour normalization,
titles, label and triangle adjustments, ASCII and SGF round trips, and both page
layouts.
