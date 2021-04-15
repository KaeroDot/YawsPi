set encoding utf8
set term png size 800, 500
set datafile separator ";"
set xtics rotate
# 2021-03-26T19:11:01.257006+01:00; 22.912368157125332
set timefmt "%Y-%m-%dT%H:%M:%S"
set format x "%Y-%m-%d"
set xdata time
if (as > 0) set autoscale x; else set xrange [xmin: xmax]

unset key
