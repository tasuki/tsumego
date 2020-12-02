default: a5-cho-1-elementary.pdf a5-cho-2-intermediate.pdf a5-cho-3-advanced.pdf a5-gokyoshumyo.pdf a5-xxqj.pdf a5-hatsuyoron.pdf \
	     a6-cho-1-elementary.pdf a6-cho-2-intermediate.pdf a6-cho-3-advanced.pdf a6-gokyoshumyo.pdf a6-xxqj.pdf a6-hatsuyoron.pdf a5-lee-chang-ho.pdf a6-lee-chang-ho.pdf

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

a5-lee-chang-ho.pdf: includes/a5*.tex a5-lee-chang-ho.tex content/lee-chang-ho.tex problems/lee-chang-ho.tex
	pdftex a5-lee-chang-ho.tex


a6-cho-1-elementary.pdf: includes/a6*.tex a6-cho-1-elementary.tex content/cho-1-elementary.tex problems/cho-1.tex
	pdftex a6-cho-1-elementary.tex

a6-cho-2-intermediate.pdf: includes/a6*.tex a6-cho-2-intermediate.tex content/cho-2-intermediate.tex problems/cho-2.tex
	pdftex a6-cho-2-intermediate.tex

a6-cho-3-advanced.pdf: includes/a6*.tex a6-cho-3-advanced.tex content/cho-3-advanced.tex problems/cho-3.tex
	pdftex a6-cho-3-advanced.tex

a6-gokyoshumyo.pdf: includes/a6*.tex a6-gokyoshumyo.tex content/gokyoshumyo.tex problems/gokyoshumyo.tex
	pdftex a6-gokyoshumyo.tex

a6-xxqj.pdf: includes/a6*.tex a6-xxqj.tex content/xxqj.tex problems/xxqj.tex
	pdftex a6-xxqj.tex

a6-hatsuyoron.pdf: includes/a6*.tex a6-hatsuyoron.tex content/hatsuyoron.tex problems/hatsuyoron.tex
	pdftex a6-hatsuyoron.tex

a6-lee-chang-ho.pdf: includes/a6*.tex a6-lee-chang-ho.tex content/lee-chang-ho.tex problems/lee-chang-ho.tex
	pdftex a6-lee-chang-ho.tex


pub: default
	mkdir -p pub
	cp a5-cho-1-elementary.pdf pub/cho-1-elementary.pdf
	cp a6-cho-1-elementary.pdf pub/cho-1-elementary-mobile.pdf
	cp a5-cho-2-intermediate.pdf pub/cho-2-intermediate.pdf
	cp a6-cho-2-intermediate.pdf pub/cho-2-intermediate-mobile.pdf
	cp a5-cho-3-advanced.pdf pub/cho-3-advanced.pdf
	cp a6-cho-3-advanced.pdf pub/cho-3-advanced-mobile.pdf
	cp a5-gokyoshumyo.pdf pub/gokyoshumyo.pdf
	cp a6-gokyoshumyo.pdf pub/gokyoshumyo-mobile.pdf
	cp a5-xxqj.pdf pub/xxqj.pdf
	cp a6-xxqj.pdf pub/xxqj-mobile.pdf
	cp a5-hatsuyoron.pdf pub/hatsuyoron.pdf
	cp a6-hatsuyoron.pdf pub/hatsuyoron-mobile.pdf
	cp a5-lee-chang-ho.pdf pub/lee-chang-ho.pdf
	cp a6-lee-chang-ho.pdf pub/lee-chang-ho-mobile.pdf

clean:
	rm -rf *.log *.pdf
