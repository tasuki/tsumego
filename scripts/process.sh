#/!bin/bash

cd zal

for i in `ls prob*.sgf`; do
  ../rotate.pl $i > zz$i
  sgf2dg -b `head -n 1 zz$i` -twoColumn zz$i
done

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
  s/to 42/to 30/
  s/to 52/to 40/
  s/to 62/to 50/
  s/to 72/to 60/
  s/to 82/to 70/
  s/to 92/to 80/
  s/to 102/to 90/
  s/to 112/to 100/
  s/to 122/to 110/
  s/to 132/to 120/
  s/to 142/to 130/
  s/to 152/to 140/
  s/to 162/to 150/
  s/to 172/to 160/
  s/to 182/to 170/
  s/to 192/to 180/
  s/to 202/to 190/
  s/.tex//
  s/problem zzprob000/problem /
  s/problem zzprob00/problem /
  s/problem zzprob0/problem /
  s/\\\bye//
  " $i >> collection
done

echo '\bye' >> collection

rm zz*

mv collection ../collection.tex
