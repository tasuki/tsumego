What the hell?
==============

First, I am sorry. This project is the biggest mess. If you want to learn best
practices, just look here and do everything differently!

A bit of history
----------------

When I created [Tsumego Collections](http://tsumego.tasuki.org/) in 2004, I was
young and naive. Also didn't understand the importance of writing maintainable
code. As a result, this was mostly created by copying few scripts around and
modifying each of them to fit the particular sgf/tex files.

Get it running
---------------------

As of 2018 I can get it running on Ubuntu with `texlive` and Kashomon's [go-type1](https://github.com/otrego/go-type1).

	cd books
	make

CJK titles
----------

Books use plain LuaTeX (`luatex`, not `lualatex`), with `luaotfload` for OpenType
fonts and `luatex85` for compatibility with the existing PDF primitives. On
Debian/Ubuntu install `texlive-luatex` alongside the existing TeX dependencies.
The Palatino text and Type 1 Go-diagram fonts are unchanged.

Noto Serif CJK TC Regular is bundled in `books/fonts/`, with its SIL Open Font
License and pinned download instructions in `books/fonts/README.md`. No system
font installation is needed. Japanese titles select the font's Japanese glyph
forms; traditional Chinese titles select its Traditional Chinese forms.

Each title is ordinary Unicode text in its book's content `.tex` file, e.g.:

```tex
\centerline{\cjktitle 管子譜}
\centerline{\japanesetitle 碁経衆妙}
```

The A5/A6 styles set the title font sizes. `make -C books` builds the books in
one step, embedding only the glyphs used. There are no separate title PDFs,
SVGs, or title-generation rules.

Thanks
------

I would never get anywhere without Toxygen's immense help with converting the
original Metafont fonts into Type1. For that I am eternally grateful!
