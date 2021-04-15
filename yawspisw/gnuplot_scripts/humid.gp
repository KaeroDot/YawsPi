# requires inputs as, xmin and xmax, e.g.:
# gnuplot -e "as=0; xmin='2021-03-30T19:11:01'; xmax='2021-04-01T15:28:17'" humid.gp
# if as is > 0, autoscale of x axis is used
load 'gnuplot_scripts/common.gp'

set ylabel 'Ambient humidity (% R.H.)'
set format y "%.0f"

set output 'static/data/humid.png'
plot "data/humid.csv" using 1:2 with lines lw 2 lc "blue"
