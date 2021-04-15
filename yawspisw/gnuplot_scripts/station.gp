# requires inputs staion_index, as, xmin and xmax, e.g.:
# gnuplot -e "station_index='0'; as=0; xmin='2021-03-30T19:11:01'; xmax='2021-04-01T15:28:17'" station.gp
# if as is > 0, autoscale of x axis is used
load 'gnuplot_scripts/common.gp'

set key on
set ylabel 'Water level (a.u.), Soil humidity (a.u.)'
set y2label 'Fill volume (l)'
set ytics nomirror
set y2tics
set format y "%.2f"
set format y2 "%.2f"

# set yrange [0:1]
set y2range [0:1]

set output 'static/data/0.png'
plot '< grep -E "level" data/'.station_index.'.csv' using 1:2 axis x1y1 title 'Water l.' with lines lw 2 lc "blue", \
     '< grep -E "soil"  data/'.station_index.'.csv' using 1:2 axis x1y1 title 'Soil h.'  with lines lw 2 lc "green", \
     '< grep -E "fill"  data/'.station_index.'.csv' using 1:2 axis x1y2 title 'Fill v.'  with points ps 2 pt 7 lc "black"
