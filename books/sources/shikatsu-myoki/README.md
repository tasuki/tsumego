# Shikatsu Myoki source positions

Source: [Shikatsu Myoki Tsumego Series at Sensei's Library](https://senseis.xmp.net/?ShikatsuMyokiTsumegoSeries),
retrieved October 12, 2026. `series-index.html` is the unmodified series index.
The numbered `.sgf` files are verbatim downloads of the **first problem diagram**
from each selected problem page, not its solution page or diagrams in comments.
Each SGF records its source page in `PC` and `C`; filenames retain the series
numbers. `SHA256SUMS` pins the archived index and SGFs.

The later-edition series has 168 entries, including 48 variations marked `v`.
Only the 120 entries **without** `v` are included, in source order:

| Section | Series range | Main problems | Book identifiers |
| --- | --- | ---: | --- |
| Killing | 1–73 | 48 | 1-1 through 1-48 |
| Living | 74–117 | 30 | 2-1 through 2-30 |
| Ko | 118–155 | 32 | 3-1 through 3-32 |
| Capturing Races | 156–168 | 10 | 4-1 through 4-10 |

`source-map.csv` maps the retained series numbers to chapter-problem identifiers
and links back to their source pages. No deduplication is performed.

The problem caption (`GN`) specifies the player to play. Some diagram SGFs
also contain already-played numbered stones as move nodes (for example, series
74 and 80). Those stones are included in the position: GoWiki's `PL` identifies
the first *displayed move*, which need not be the player who solves the problem.
White-to-play positions are colour-reversed to Black to play, then
rotated/reflected and cropped using the same normalization as the other
collections. Diagram markup such as a circle highlighting a setup stone is not
printed. The archived originals preserve that markup.

Regenerate the canonical problem data and source map from the repository root,
without network access:

```sh
python3 scripts/import_shikatsu_myoki.py \
    books/sources/shikatsu-myoki books/problems/shikatsu-myoki.txt
(cd books/sources/shikatsu-myoki && sha256sum -c SHA256SUMS)
```

Build both books with:

```sh
make -C books a5-shikatsu-myoki.pdf a6-shikatsu-myoki.pdf
```

The preface lists clickable sections, using the same chapter destinations and
content-relative page numbering as Gokyo Shumyo. `make -C books test` checks the
import, exclusion of variations, section counts, link targets, and page numbers.
