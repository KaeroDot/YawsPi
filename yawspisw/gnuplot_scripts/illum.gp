# requires inputs as, xmin and xmax, e.g.:
# gnuplot -e "as=0; xmin='2021-03-30T19:11:01'; xmax='2021-04-01T15:28:17'" illum.gp
# if as is > 0, autoscale of x axis is used
load 'gnuplot_scripts/common.gp'

set ylabel 'Ambient light (lux)'
set logscale y
set yrange [10:*]
set format y "10^{%T}"

set output 'static/data/illum.png'
plot "data/illum.csv" using 1:2 with lines lw 2 lc "orange"
