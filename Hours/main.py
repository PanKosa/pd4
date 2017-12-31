from os.path import dirname, abspath

import sqlite3
import numpy as np
import pandas.io.sql as psql
import pandas as pd

from collections import OrderedDict
from bokeh.plotting import figure
from bokeh.layouts import layout, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, Div, Paragraph, CustomJS
from bokeh.models.widgets import Slider, Select, TextInput, CheckboxButtonGroup
from bokeh.io import curdoc
from bokeh.models import (
  ColumnDataSource, Line, Range1d, PanTool, WheelZoomTool, BoxSelectTool, DatetimeTickFormatter
)
from bokeh.models.widgets import Paragraph, Div

conn = sqlite3.connect(str(dirname(abspath(__file__))) + "/hours.sql")

p = figure(plot_width=700, plot_height=400)

p.xaxis.formatter=DatetimeTickFormatter(
         hourmin = ['%H:%M']
    )

#flights = psql.read_sql("SELECT * FROM Arr_Delays_vs_time_h", conn)
flights = psql.read_sql("SELECT * FROM Arr_Delays_vs_time_h24102007", conn)

flights["time_str"] = "0000" + flights["time"].astype(str)
flights["time_str"] = flights.time_str.str[-4:]
flights["time_str"] = flights.time_str.str[0:2] + ":" + flights.time_str.str[2:4]
flights["time"] = pd.to_datetime(flights.time_str, format='%H:%M').dt.time

# Create Input controls
carrier = Select(title="Carrier", value="CO",options=open(str(dirname(abspath(__file__))) + "/carriers.txt").read().split())
box_size = Slider(title="Box size", start=3, end=100, value=15, step=1)

# Create Column Data Source that will be used by the plot
source = ColumnDataSource(data=dict(dep=[], delay_smooth=[],  delay=[], name=[], time_str=[], num_of_flights=[], num_of_flights_smooth=[]))

p.scatter(x="dep", y="delay", line_width=2, source = source, legend="Raw Data")
g1 = p.line(x="dep", y="delay_smooth", line_width=2, line_color="red", source = source, legend="Smooth")

tooltips = OrderedDict([
    ('Dep.: ', '@time_str'),
    ('Est. Arr. Delay: ', '@delay_smooth'),
])
p.add_tools( HoverTool(tooltips=tooltips, renderers=[g1]))

p.title.text = 'Predicted Delays'
p.legend.location = "top_left"
p.legend.click_policy="hide"

# Histogram ilosci lotow

p2 = figure(plot_width=700, plot_height=400)

p2.xaxis.formatter=DatetimeTickFormatter(
         hourmin = ['%H:%M']
    )

p2.scatter(x="dep", y="num_of_flights", line_width=2, source = source, legend="Raw Data")
g2 = p2.line(x="dep", y="num_of_flights_smooth", line_width=2, line_color="red", source = source, legend="Smooth")

tooltips_num = OrderedDict([
    ('Dep.: ', '@time_str'),
    ('Num. of flights: ', '@num_of_flights_smooth'),
])
p2.add_tools( HoverTool(tooltips=tooltips_num, renderers=[g2]))


p2.title.text = 'Number of flights'
p2.legend.location = "top_left"
p2.legend.click_policy="hide"


def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth

def select_movies():
    selected = flights[
        flights.UniqueCarrier == carrier.value
    ]   
    return selected

def update():
    df = select_movies()

    source.data = dict(
        dep=df["time"],
        delay=df["ArrDelay"],
	delay_smooth=smooth(df["ArrDelay"],box_size.value),
	num_of_flights_smooth=smooth(df["number_of_flights"],box_size.value),
        num_of_flights=df["number_of_flights"],
        name=df["UniqueCarrier"],
        time_str=df["time_str"],
    )
    
    p.update()

# Text

t1 = Paragraph(text="""
From above plots we can see...
""", width=500, height=200)

t2 = Div(text="""
Plots
""",width=800, height=200)


carrier.on_change('value', lambda attr, old, new: update())
box_size.on_change('value', lambda attr, old, new: update())

sizing_mode = 'fixed' 

controls = [carrier, box_size]

inputs = widgetbox(*controls, sizing_mode=sizing_mode)
l = layout([
    [t2],
    [inputs, p, p2],
    [t1]

], sizing_mode=sizing_mode)

update()  # initial load of the data


curdoc().add_root(l)
curdoc().title = "Flights"

