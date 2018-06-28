default: a5-cho-1-elementary.pdf a5-cho-2-intermediate.pdf a5-cho-3-advanced.pdf a5-gokyoshumyo.pdf a5-xxqj.pdf a5-hatsuyoron.pdf

a5-cho-1-elementary.pdf: includes/a5*.tex a5-cho-1-elementary.tex content/cho-1-elementary.tex problems/cho-1.tex
	pdftex a5-cho-1-elementary.tex

a5-cho-2-intermediate.pdf: includes/a5*.tex a5-cho-2-intermediate.tex content/cho-2-intermediate.tex problems/cho-2.tex
	pdftex a5-cho-2-intermediate.tex

a5-cho-3-advanced.pdf: includes/a5*.tex a5-cho-3-advanced.tex content/cho-3-advanced.tex problems/cho-3.tex
	pdftex a5-cho-3-advanced.tex

a5-gokyoshumyo.pdf: includes/a5*.tex a5-gokyoshumyo.tex content/gokyoshumyo.tex problems/gokyoshumyo.tex
	pdftex a5-gokyoshumyo.tex

a5-xxqj.pdf: includes/a5*.tex a5-xxqj.tex content/xxqj.tex problems/xxqj.tex
	pdftex a5-xxqj.tex

a5-hatsuyoron.pdf: includes/a5*.tex a5-hatsuyoron.tex content/hatsuyoron.tex problems/hatsuyoron.tex
	pdftex a5-hatsuyoron.tex

clean:
	rm -rf *.log *.pdf
