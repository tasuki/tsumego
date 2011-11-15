#!/usr/bin/perl -w
use strict;

my @abeceda=("a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s");
my @ABECEDA=("A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S");
my @rotation; my $rot;
my $fname;
my $i; my $j;
my $maxstr; my @height; my @width; my $minheight=20; my $minwidth=20;
my $line;

sub extreme {
  my $max; my $len; my $charr; my $i; my $j;
  $max=0;
  $len=length($maxstr);                # count the length of the string
  for ($i=0; $i<$len; $i++) {
    $charr=substr($maxstr,$i,1);       # take next char
    for ($j=0; $j<19; $j++) {          # cycle alphabet to find our char
      if ($charr eq $abeceda[$j]) {    # found it?
        if ($j>$max) {                 # how far is it? further than furthest?
          $max=$j;
        }
      }
    }
  }
  return($max);
}

foreach $fname (@ARGV) {
  open(FILE, $fname) or die("Could not open $fname\n");
  $rotation[0]="";
  while($line = <FILE>) {
    $rotation[0]=$rotation[0].$line;   # append lines
    #if ($line=~ /^A[BW]/) {            # read only lines starting with AB or AW
    #  $rotation[0]=$rotation[0].$line; # append them
    #}
  }
  #$rotation[0]=~ s/PL/\nPL/g;          # this part is getting a bit dirty...
  $rotation[0]=~ s/\(;GM\[1\]FF\[3\]SZ\[19\]//g;
  $rotation[0]=~ s/PL.*//sg;

  #print "$rotation[0]\n";

  for ($rot=1; $rot<8; $rot++) {       # do the 7 rotations, leave the first one be
    if ($rot<4) {                      # first 4 rotations
      $rotation[$rot]=$rotation[0];    # copy the original to make changes to
      for ($i=0; $i<19;$i++) {
        $j=18-$i;
        if ($rot==1 || $rot==3) {      # switch the first chars for 1, 3
          $rotation[$rot]=~ s/\[$abeceda[$i]/\[$ABECEDA[$j]/g;
        }
        if ($rot==2 || $rot==3) {      # switch the second chars for 2, 3
          $rotation[$rot]=~ s/$abeceda[$i]\]/$ABECEDA[$j]\]/g;
        }
      }
    }
    else {                             # mirror rotations for 4, 5, 6, 7
      $rotation[$rot]=$rotation[$rot-4];
      $rotation[$rot]=~ s/\[(.)(.)\]/\[$2$1\]/g;
    }

    for ($i=0; $i<19;$i++) {           # clean of uppercase
      $rotation[$rot]=~ s/\[$ABECEDA[$i]/\[$abeceda[$i]/g;
      $rotation[$rot]=~ s/$ABECEDA[$i]\]/$abeceda[$i]\]/g;
    }
  }

  for ($rot=0; $rot<8; $rot++) {       # for all rotations

    $maxstr=$rotation[$rot];
    $maxstr=~ s/\[.//g;                # get rid of first letters
    $height[$rot]=extreme;             # get height

    $maxstr=$rotation[$rot];
    $maxstr=~ s/.\]//g;                # get rid of second letters
    $width[$rot]=extreme;              # get width

    if ($height[$rot]<$minheight) {
      $minheight=$height[$rot];        # compute height of all 8
    }
  }

  for ($rot=0; $rot<8; $rot++) {
    if ($height[$rot]==$minheight) {
      if ($width[$rot]<$minwidth) {
        $minwidth=$width[$rot];        # compute minimal width of the ones with min height
      }
    }
  }

  for ($rot=0; $rot<8; $rot++) {       # print the min height + min possible width one
    if ($height[$rot]==$minheight && $width[$rot]==$minwidth) {
      $minheight+=2;
      $minwidth+=2;
      print "$minheight\n$minwidth\n(;$rotation[$rot])\n";
    }
  }

  close(FILE);
}
