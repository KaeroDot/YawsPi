# requires inputs as, xmin and xmax, e.g.:
# gnuplot -e "as=0; xmin='2021-03-30T19:11:01'; xmax='2021-04-01T15:28:17'" press.gp
# if as is > 0, autoscale of x axis is used
load 'gnuplot_scripts/common.gp'

set ylabel 'Ambient pressure (kPa)'
set format y "%.1f"

set output 'static/data/press.png'
plot "data/press.csv" using 1:($2/1000) with lines lw 2 lc "green"
