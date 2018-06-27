default: book-cho-1-elementary.pdf book-cho-2-intermediate.pdf book-cho-3-advanced.pdf book-gokyoshumyo.pdf book-xxqj.pdf book-hatsuyoron.pdf

book-cho-1-elementary.pdf: include-a5.tex include-a5-gotc.tex include-motto.tex book-cho-1-elementary.tex problems-cho-1.tex
	pdftex book-cho-1-elementary.tex

book-cho-2-intermediate.pdf: include-a5.tex include-a5-gotc.tex include-motto.tex book-cho-2-intermediate.tex problems-cho-2.tex
	pdftex book-cho-2-intermediate.tex

book-cho-3-advanced.pdf: include-a5.tex include-a5-gotc.tex include-motto.tex book-cho-3-advanced.tex problems-cho-3.tex
	pdftex book-cho-3-advanced.tex

book-gokyoshumyo.pdf: include-a5.tex include-a5-gotc.tex include-motto.tex book-gokyoshumyo.tex problems-gokyoshumyo.tex
	pdftex book-gokyoshumyo.tex

book-xxqj.pdf: include-a5.tex include-a5-gotc.tex include-motto.tex book-xxqj.tex problems-xxqj.tex
	pdftex book-xxqj.tex

book-hatsuyoron.pdf: include-a5.tex include-a5-gotc.tex include-motto.tex book-hatsuyoron.tex problems-hatsuyoron.tex
	pdftex book-hatsuyoron.tex

clean:
	rm *.log
	rm book*.pdf
