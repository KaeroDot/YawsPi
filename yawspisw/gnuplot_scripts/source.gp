# requires inputs as, xmin and xmax, e.g.:
# gnuplot -e "as=0; xmin='2021-03-30T19:11:01'; xmax='2021-04-01T15:28:17'" source.gp
# if as is > 0, autoscale of x axis is used
load 'gnuplot_scripts/common.gp'

set ylabel 'Source water level (a. u.)'
set format y "%.2g"

set output 'static/data/source.png'
plot "data/source.csv" using 1:2 with lines lw 2 lc "blue"
