# Gokyo Seimyo source positions

Source: [Gokyo Seimyo Tsumego Series at Sensei's Library](https://senseis.xmp.net/?GokyoSeimyoTsumegoSeries),
retrieved October 13, 2026. `series-index.html` is the unmodified index. The
numbered `.sgf` files are verbatim downloads of the **first problem diagram**
on each selected page, not solution diagrams or diagrams in comments. Their
`PC` and `C` properties record the source pages; filenames retain the source
numbers. `SHA256SUMS` pins the index, SGFs, and supplementary page snapshots.

This is **Volume 3**, not the joseki, invasion/endgame, or games volumes. The
series has 146 entries, including **66, 68, and 69 as reference diagrams rather
than problems**. The book includes 145 diagrams in source order: source 146
is omitted because pages 145 and 146 link to the exact same SGF. Both originals
remain archived (the shared SGF names page 146 in its provenance). Source 145
is retained as **5-9**; there is no **5-10**. No other deduplication is performed,
even when positions also occur in another collection. The three references illustrate
hanezeki, eternal life (chosei), and double-ko seki, respectively; they have
nothing to solve and retain their original stone colours.

| Section | Series range | Diagrams | Book identifiers |
| --- | --- | ---: | --- |
| Tesuji inside territories | 1–44 | 44 | 1-1 through 1-44 |
| Other problems | 45–118 | 74 | 2-1 through 2-74 |
| Connect underneath | 119–128 | 10 | 3-1 through 3-10 |
| Cut/connect groups | 129–136 | 8 | 4-1 through 4-8 |
| Ladder | 137–145 (146 duplicates 145) | 9 | 5-1 through 5-9 |

`source-map.csv` links each book identifier to its original number and page.
The reference diagrams are book entries **2-22, 2-24, and 2-25**. Their unmodified
`66-page.html`, `68-page.html`, and `69-page.html` snapshots document their purpose.
The diagram caption (`GN`) determines the player, with these corrections:

- 37's caption has the typo `hite to move`; its `PL[W]` confirms White.
- 55 says `(White to play)` despite `PL[B]`; the caption takes precedence.
- 62 has no caption and `PL[B]`, but the page explicitly says White to play.
- 134 and 135 have cached SGF captions `Black to move`, while their current
  page captions say `Black to connect`; the snapshots retain this distinction.

The unmodified `55-page.html`, `62-page.html`, `134-page.html`, and
`135-page.html` snapshots document these decisions. All downloaded SGFs have
only setup stones and empty/markup-only trailing nodes; no solution moves are
added to the positions. Reference diagrams have no player to move; their empty
captions and placeholder `PL[B]` do not supply an objective. White-to-play problems
are colour-reversed to Black,
then normalized using the same rotation/reflection and cropping as other books.
Full-board ladder problems retain their full extent.

All stone marks, including circles identifying target groups, are omitted from
the book. Special objective captions are also omitted. Only the three reference
diagrams have descriptive captions: **2-22 hanezeki**, **2-24 eternal life
(chosei)**, and **2-25 double-ko seki**. Other diagrams use only their problem
numbers. Source captions are still used to determine the player to play. Labels in 72 and 84 annotate alternative positions discussed in the
source commentary, so they are omitted. The archived SGFs retain all original
markup.

Regenerate data and source mapping offline, from the repository root:

```sh
python3 scripts/import_gokyo_seimyo.py \
    books/sources/gokyo-seimyo books/problems/gokyo-seimyo.txt
(cd books/sources/gokyo-seimyo && sha256sum -c SHA256SUMS)
make -C books a5-gokyo-seimyo.pdf a6-gokyo-seimyo.pdf
make -C books test
```

Both books have clickable section lists with content-relative page numbers.
`make -C books pub` also publishes `pub/gokyo-seimyo.pdf` and
`pub/gokyo-seimyo-mobile.pdf` alongside the existing collections.
