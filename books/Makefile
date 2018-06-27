default: book-cho-1-elementary.pdf book-cho-2-intermediate.pdf book-cho-3-advanced.pdf

book-cho-1-elementary.pdf: include-a5.tex include-a5-gotc.tex include-motto.tex book-cho-1-elementary.tex
	pdftex book-cho-1-elementary.tex

book-cho-2-intermediate.pdf: include-a5.tex include-a5-gotc.tex include-motto.tex book-cho-2-intermediate.tex
	pdftex book-cho-2-intermediate.tex

book-cho-3-advanced.pdf: include-a5.tex include-a5-gotc.tex include-motto.tex book-cho-3-advanced.tex
	pdftex book-cho-3-advanced.tex

clean:
	rm *.log
	rm book*.pdf
