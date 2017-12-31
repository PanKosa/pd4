import os
from os.path import dirname, join
import sqlite3
#conn = sqlite3.connect(str(os.path.dirname(os.path.abspath(__file__))) + "/map.sql")
conn           = sqlite3.connect("/home/pkosewski/python/pd4/databases/flights_full.sql")

import numpy as np
import pandas.io.sql as psql
import sqlite3 as sql
import pandas as pd
from numpy import histogram, linspace
from collections import OrderedDict
from bokeh.plotting import figure
from bokeh.layouts import layout, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, Div, CustomJS, Legend, LegendItem
from bokeh.models.widgets import Slider, Select, TextInput, CheckboxButtonGroup
from bokeh.io import curdoc
from bokeh.sampledata.movies_data import movie_path
from bokeh.io import output_file, show
from bokeh.models import (
  ColumnDataSource, Line, MultiLine, Circle, Range1d, PanTool, WheelZoomTool, BoxSelectTool, DatetimeTickFormatter
)

p = figure(plot_width=700, plot_height=400)

p.xaxis.formatter=DatetimeTickFormatter(
         hourmin = ['%H:%M']
    )

#flights = psql.read_sql("SELECT * FROM Arr_Delays_vs_time_h", conn)
flights = psql.read_sql("SELECT * FROM Arr_Delays_vs_time_h24102007", conn)

flights["time"] = "0000" + flights["time"].astype(str)
flights["time"] = flights.time.str[-4:]
flights["time"] = flights.time.str[0:2] + ":" + flights.time.str[2:4]
flights["time"] = pd.to_datetime(flights.time, format='%H:%M').dt.time

# Create Input controls
genre = Select(title="Airport", value="CO",options=open('/home/pkosewski/python/pd4/carriers.txt').read().split())
box_size = Slider(title="Box size", start=3, end=100, value=15, step=1)

# Create Column Data Source that will be used by the plot
source = ColumnDataSource(data=dict(dep=[], delay_smooth=[],  delay=[], name=[]))


#ML = Line(x="dep", y="delay", line_color="color", line_width=2)

ML = Line(x="dep", y="delay", line_width=2)
Smooth = Line(x="dep", y="delay_smooth", line_width=2, line_color="red")

g1 = p.add_glyph(source, ML)
g2 = p.add_glyph(source, Smooth)

legend = Legend(legends=[("curve1", [g1]), ("curve2", [g2])])
p.legend.location = "top_left"
p.legend.click_policy="hide"

#p.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool())


def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth

def select_movies():
    selected = flights[
        flights.UniqueCarrier == genre.value
    ]   
    return selected

def update():
    df = select_movies()

    source.data = dict(
        dep=df["time"],
        delay=df["ArrDelay"],
	delay_smooth=smooth(df["ArrDelay"],box_size.value),
#        delay=df["number_of_flights"],
        name=df["UniqueCarrier"],
    )

    p.update()


genre.on_change('value', lambda attr, old, new: update())
box_size.on_change('value', lambda attr, old, new: update())

sizing_mode = 'fixed' 

controls = [genre, box_size]

inputs = widgetbox(*controls, sizing_mode=sizing_mode)
l = layout([
    [inputs, p],
    legend

], sizing_mode=sizing_mode)

update()  # initial load of the data

curdoc().add_root(l)
curdoc().title = "Flights"

