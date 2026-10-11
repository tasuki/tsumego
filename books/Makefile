.PHONY: default pub clean test

LUATEX ?= luatex
TEX = $(LUATEX) -no-shell-escape -interaction=nonstopmode -halt-on-error

default: a5-cho-1-elementary.pdf a5-cho-2-intermediate.pdf a5-cho-3-advanced.pdf a5-gokyoshumyo.pdf a5-guan-zi-pu.pdf a5-xxqj.pdf a5-hatsuyoron.pdf \
	     a6-cho-1-elementary.pdf a6-cho-2-intermediate.pdf a6-cho-3-advanced.pdf a6-gokyoshumyo.pdf a6-guan-zi-pu.pdf a6-xxqj.pdf a6-hatsuyoron.pdf

a5-cho-1-elementary.pdf: includes/a5*.tex a5-cho-1-elementary.tex content/cho-1-elementary.tex generated/a5-cho-1.tex
	$(TEX) a5-cho-1-elementary.tex

a5-cho-2-intermediate.pdf: includes/a5*.tex a5-cho-2-intermediate.tex content/cho-2-intermediate.tex generated/a5-cho-2.tex
	$(TEX) a5-cho-2-intermediate.tex

a5-cho-3-advanced.pdf: includes/a5*.tex a5-cho-3-advanced.tex content/cho-3-advanced.tex generated/a5-cho-3.tex
	$(TEX) a5-cho-3-advanced.tex

a5-gokyoshumyo.pdf: includes/a5*.tex a5-gokyoshumyo.tex content/gokyoshumyo.tex generated/a5-gokyoshumyo.tex
	$(TEX) a5-gokyoshumyo.tex

a5-guan-zi-pu.pdf: includes/a5*.tex a5-guan-zi-pu.tex content/guan-zi-pu.tex generated/a5-guan-zi-pu.tex
	$(TEX) a5-guan-zi-pu.tex

a5-xxqj.pdf: includes/a5*.tex a5-xxqj.tex content/xxqj.tex generated/a5-xxqj.tex
	$(TEX) a5-xxqj.tex

a5-hatsuyoron.pdf: includes/a5*.tex a5-hatsuyoron.tex content/hatsuyoron.tex generated/a5-hatsuyoron.tex
	$(TEX) a5-hatsuyoron.tex


a6-cho-1-elementary.pdf: includes/a6*.tex a6-cho-1-elementary.tex content/cho-1-elementary.tex generated/a6-cho-1.tex
	$(TEX) a6-cho-1-elementary.tex

a6-cho-2-intermediate.pdf: includes/a6*.tex a6-cho-2-intermediate.tex content/cho-2-intermediate.tex generated/a6-cho-2.tex
	$(TEX) a6-cho-2-intermediate.tex

a6-cho-3-advanced.pdf: includes/a6*.tex a6-cho-3-advanced.tex content/cho-3-advanced.tex generated/a6-cho-3.tex
	$(TEX) a6-cho-3-advanced.tex

a6-gokyoshumyo.pdf: includes/a6*.tex a6-gokyoshumyo.tex content/gokyoshumyo.tex generated/a6-gokyoshumyo.tex
	$(TEX) a6-gokyoshumyo.tex

a6-guan-zi-pu.pdf: includes/a6*.tex a6-guan-zi-pu.tex content/guan-zi-pu.tex generated/a6-guan-zi-pu.tex
	$(TEX) a6-guan-zi-pu.tex

a6-xxqj.pdf: includes/a6*.tex a6-xxqj.tex content/xxqj.tex generated/a6-xxqj.tex
	$(TEX) a6-xxqj.tex

a6-hatsuyoron.pdf: includes/a6*.tex a6-hatsuyoron.tex content/hatsuyoron.tex generated/a6-hatsuyoron.tex
	$(TEX) a6-hatsuyoron.tex


# Both shared styles load the bundled font, including for Latin-only books.
$(patsubst %.tex,%.pdf,$(wildcard a5-*.tex a6-*.tex)): fonts/NotoSerifCJKtc-Regular.otf


generated/a5-%.tex: problems/%.txt ../scripts/problems.py
	mkdir -p generated
	../scripts/problems.py render-tex --profile a5 $< $@

generated/a6-%.tex: problems/%.txt ../scripts/problems.py
	mkdir -p generated
	../scripts/problems.py render-tex --profile a6 $< $@

test:
	python3 ../scripts/test_problems.py

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
	cp a5-guan-zi-pu.pdf pub/guan-zi-pu.pdf
	cp a6-guan-zi-pu.pdf pub/guan-zi-pu-mobile.pdf
	cp a5-xxqj.pdf pub/xxqj.pdf
	cp a6-xxqj.pdf pub/xxqj-mobile.pdf
	cp a5-hatsuyoron.pdf pub/hatsuyoron.pdf
	cp a6-hatsuyoron.pdf pub/hatsuyoron-mobile.pdf

clean:
	rm -rf *.log *.pdf generated
