#!/bin/sh

# This script requires sgfutils (https://homepages.cwi.nl/~aeb/go/sgfutils/html/sgfutils.html)
# and pup (https://github.com/ericchiang/pup) on your PATH.

seq -f "%04g" 123 > "/tmp/123"
# Ids of the 6 volumes of Lee Chang-ho's Selected Life and Death Go Problems on goproblems.com
for collection in 186 187 188 190 193 194; do
  mkdir -p "$collection"
  problem=1
  curl -s "http://www.goproblems.com/group/usergroup.php?id=$collection" | pup "table table td a attr{href}" | uniq | grep -o "/.*?" | rev | cut -c2- | rev | cut -c2- | while read i; do
    number=$(printf "%04d" $problem)
    test -f "$collection/$number.sgf" || curl -s "http://www.goproblems.com/$i" | pup "#player-container text{}" | tee -a "$collection/$number.sgf"
    problem=$(expr $problem + 1)
  done

  rm -rf 190/0041.sgf # Remove duplicate problem
  rm -rf tmp1; mkdir -p tmp1
  rm -rf tmp2; mkdir -p tmp2

  # The .sgf files from goproblems contains variations for the solutions and
  # annotations, so we get rid of that first...
  (cd "$collection"; ls *.sgf | while read p; do
    cat "$p" | sgf $p -c | sgfstrip AN AP BR BT CP DT EV FF GM GN HA KM ON OT PB PC PL PW RE RO RU SO SZ TM US WR WT GE DI DP CO CA ST TR MA MN > "../tmp1/problem-$collection-$p"
  done)

  # Reordered problems
  paste -d " " "$collection/order.txt" "/tmp/123" | while read old new; do
    test "$old" != "0000" &&
      mv "tmp1/problem-$collection-$old.sgf" \
         "tmp2/problem-$collection-$new.sgf"
  done

  # Sanity check
  test -z "$(ls -A tmp1)" ||\
    echo "Some problems in $collection have not been reordered"

  (cd "tmp2"; ls *.sgf | while read p; do
    # Here we `swapcolors` if white plays first in the solutions variations,
    # then delete all the moves on the variation to only keep problems.
    if cat "$p" | tail -n1 | grep -q -e '^;B'; then
      cat "$p" | sed '/^;B/d' > "../zal/$p"
      echo ")" >> "../zal/$p"
    elif cat "$p" | tail -n1 | grep -q -e '^;W'; then
      cat "$p" | sgftf -swapcolors | sed '/^;B/d' > "../zal/$p"
      echo ")" >> "../zal/$p"
    else
      echo "$p"
      cat "$p" | tail -n2
      echo
    fi
  done)

  # Sanity check
  cat "/tmp/123" | while read i; do
    test -f "zal/problem-$collection-$i.sgf" ||\
      echo "Missing problem $collection-$i.sgf"
  done
done
