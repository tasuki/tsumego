#!/bin/bash

cd zal

ls prob*.sgf | tac | xargs -P8 -i sh -c '../rotate.pl {} > zz{}'
ls prob*.sgf | tac | xargs -P8 -i sh -c 'sgf2dg -b `head -n 1 zz{}` -twoColumn zz{}'

echo '
\magnification=800
\input cpalatin.tex
\raggedbottom
\nopagenumbers
\tolerance=10000
\baselineskip=6pt
\font\tenrm=pplr8z at 14 pt
\font\tenbf=pplb8z at 14 pt
\font\tenit=pplri8z at 14 pt
\font\label=pplri8z at 10 pt
\font\biggest=pplr8z at 28 pt
\font\big=pplr8z at 20 pt
\tenrm

\hoffset=-3.5mm
\voffset=-5mm
\hsize=115 true mm
\vsize=170 true mm
\pdfpagewidth=148 true mm
\pdfpageheight=210 true mm
\baselineskip=6mm

\pdfinfo{
   /Title (Igo Hatsuyoron)
   /Creator (TeX)
   /Author (Vit Brunner)
   /CreationDate (20061127233500)
}

\label

\pageno=1
\footline={\hss\folio\hss}
\input gotcmacs
\parindent=0pt

' > collection

for i in `ls zz*.tex`; do
  sed "
  1,23d
  s/{\\\bf Diagram 1}/\\\hfil problem $i/
  s/^\\\vbox.*$/\\\vbox{\\\vbox{\\\goo/
  s/.tex//
  s/problem zzproblem-186-/volume 1, problem zzprob/g
  s/problem zzproblem-187-/volume 2, problem zzprob/g
  s/problem zzproblem-188-/volume 3, problem zzprob/g
  s/problem zzproblem-190-/volume 4, problem zzprob/g
  s/problem zzproblem-193-/volume 5, problem zzprob/g
  s/problem zzproblem-194-/volume 6, problem zzprob/g
  s/problem zzprob000/problem /
  s/problem zzprob00/problem /
  s/problem zzprob0/problem /
  s/\\\bye//
  " $i >> collection
done

echo '\bye' >> collection

rm zz*

mv collection ../collection.tex
