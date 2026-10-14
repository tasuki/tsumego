# Guanzi Pu source SGFs

These are the three Guanzi Pu (Kanzufu / Gwan Ja Bo) collections published by
Ulrich Goertz at <https://www.u-go.net/classic/index.html#guan-zi-pu>:

| File | Problems | Upstream archive |
| --- | ---: | --- |
| `gzp1.sgf` | 539 | <https://dl.u-go.net/problems/gzp1.sgf.gz> |
| `gzp2.sgf` | 557 | <https://dl.u-go.net/problems/gzp2.sgf.gz> |
| `gzp3.sgf` | 381 | <https://dl.u-go.net/problems/gzp3.sgf.gz> |

The files are the verbatim decompressed upstream downloads. Each starts with a
short plain-text provenance note before its sequence of SGF game trees. The
collection has 1,477 problems in total. All but one include a solution; that
solution's first move establishes which player is to play. The sole position
without a solution (volume 1, problem 424) is treated as White to play, matching
the rest of the collection. The upstream page credits Flygo for the original
files and records permission to redistribute them.

The original global source numbers are 1--539 from volume 1, 540--1096 from
volume 2, and 1097--1477 from volume 3. The canonical collection removes 370
exact duplicate positions (355 identical normalized diagrams plus 15 rotated
or reflected copies), keeping the first occurrence, and numbers the remaining
1,107 problems consecutively.

Equality compares Black and White stones and labels under all eight board
rotations/reflections. It ignores diagram margins and solution moves. No
translations, colour reversals, or near-duplicate matching are performed.

`source-map.csv` maps every original global source number to its book number
and the original number of the first occurrence kept. A row is a removed
duplicate when `source_problem` differs from `kept_source_problem`. The upstream
SGFs remain unmodified, preserving all solution records.

Regenerate the canonical problem data from the repository root with:

```sh
python3 scripts/problems.py import-sgf --default-player W --deduplicate-symmetries \
    --source-map books/sources/guanzi-pu/source-map.csv \
    books/sources/guanzi-pu/gzp{1,2,3}.sgf \
    books/problems/guanzi-pu.txt
```

Verify the imported files with:

```sh
(cd books/sources/guanzi-pu && sha256sum -c SHA256SUMS)
```
