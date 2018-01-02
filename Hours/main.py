from os.path import dirname, abspath

import sqlite3
import numpy as np
import pandas.io.sql as psql
import pandas as pd

from collections import OrderedDict
from bokeh.plotting import figure
from bokeh.layouts import layout, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, Div, Paragraph, CustomJS, FuncTickFormatter
from bokeh.models.widgets import Slider, Select, TextInput, CheckboxButtonGroup
from bokeh.io import curdoc
from bokeh.models import (
  ColumnDataSource, Line, Range1d, PanTool, WheelZoomTool, BoxSelectTool, DatetimeTickFormatter
)
from bokeh.models.widgets import Paragraph, Div
from bokeh.models.tickers import FixedTicker

conn = sqlite3.connect(str(dirname(abspath(__file__))) + "/hours.sql")


########################################
## Delays

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


##############################
## Number of flights

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

################################
## Delays by day of week


p3 = figure(plot_width=700, plot_height=400)

flights_dof = psql.read_sql("SELECT * FROM Arr_Delays_vs_DayOfWeek", conn)

carrier_dof = Select(title="Carrier", value="CO",options=open(str(dirname(abspath(__file__))) + "/carriers.txt").read().split())

source_dof = ColumnDataSource(data=dict(day=[], UniqueCarrier=[],  number_of_flights=[], ArrDelay=[]))

p3.line(x="day", y="ArrDelay", line_width=2, source=source_dof, legend="Raw Data")

p3.title.text = 'Predicted Delays by day of week'
p3.legend.location = "top_left"
p3.legend.click_policy="hide"

dof = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
p3.xaxis.formatter = FuncTickFormatter(code="""
    var labels = %s;
    return labels[tick-1];
""" % dof)

## Delays by day of week 

p4 = figure(plot_width=700, plot_height=400)

p4.line(x="day", y="number_of_flights", line_width=2, source=source_dof, legend="Raw Data")

p4.title.text = 'Number of flights by day of week'
p4.legend.location = "top_left"
p4.legend.click_policy="hide"

p4.xaxis.formatter = FuncTickFormatter(code="""
    var labels = %s;
    return labels[tick-1];
""" % dof)

################################
## Delays by day of year


p5 = figure(plot_width=700, plot_height=400, x_axis_type='datetime')


flights_date = psql.read_sql("SELECT * FROM Delays_vs_Date", conn)

flights_date["date_tooltip"] = flights_date["date"]
flights_date["date"] = pd.to_datetime(flights_date.date)

axis_map = {
    "Number of flights":            "number_of_flights",
    "Number of delayed departures": "delay_over_15",
    "Number of delayed arrivals":   "arrival_over_15",
    "Mean departure delay":         "depDelay",
    "Mean arrival delay":           "arrDelay",
}
year_date = Slider(title="Year", start=1987, end=2008, value=2008, step=1)
y_axis = Select(title="Y Axis", options=sorted(axis_map.keys()), value="Number of flights")

source_date = ColumnDataSource(data=dict(date=[], y=[], date_tooltip=[]))

g5 = p5.line(x="date", y="y", line_width=2, source=source_date, legend="Raw Data")

tooltips_date = OrderedDict([
    ('Dep.: ', '@date_tooltip'),
])
p5.add_tools( HoverTool(tooltips=tooltips_date, renderers=[g5]))

p5.title.text = 'Yearlly Patterns'
p5.legend.location = "bottom_left"
p5.legend.click_policy="hide"
p5.xaxis.axis_label = "Date"

p5.y_range.start = 0



################################
## Update

def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth

def select_flights():
    selected = flights[
        flights.UniqueCarrier == carrier.value
    ]   
    return selected

def select_flights_dof():
    selected = flights_dof[
        flights_dof.UniqueCarrier == carrier_dof.value
    ]   
    return selected

def select_flights_date():
    selected = flights_date[
        flights_date.year == year_date.value
    ]   
    return selected

def update():
    
    #load data
    df = select_flights()

    df_dof = select_flights_dof()

    df_date = select_flights_date()
    
    # update hours
    source.data = dict(
        dep=df["time"],
        delay=df["ArrDelay"],
	delay_smooth=smooth(df["ArrDelay"],box_size.value),
	num_of_flights_smooth=smooth(df["number_of_flights"],box_size.value),
        num_of_flights=df["number_of_flights"],
        name=df["UniqueCarrier"],
        time_str=df["time_str"],
    )
    # update weak
    source_dof.data = dict(
        day=df_dof["day"],
        UniqueCarrier=df_dof["UniqueCarrier"],
	number_of_flights=df_dof["number_of_flights"],
	ArrDelay=df_dof["ArrDelay"],
    )
    # update year

    p5.yaxis.axis_label = y_axis.value

    source_date.data = dict(
        date=df_date["date"],
        y=df_date[axis_map[y_axis.value]],
        date_tooltip=df_date["date_tooltip"],
    )


##################################################################
## Texts

title = Div(text="""
<h1>Time Dependencies</h1>
""",width=800, height=70)

daily_txt = Div(text="""
<h2>
 <ul>
  <li>Daily patterns</li>
</ul> 
</h2>
""",width=800, height=70)

week_txt = Div(text="""
<h2>
 <ul>
  <li>Weekly patterns</li>
</ul> 
</h2>
""",width=800, height=70)

year_txt = Div(text="""
<h2>
 <ul>
  <li>Yearly patterns</li>
</ul> 
</h2>
""",width=800, height=70)


day_concl = Paragraph(text="""
From above plots we can see...
""", width=500, height=50)

week_concl = Paragraph(text="""
From above plots we can see...
""", width=500, height=50)

year_concl = Paragraph(text="""
From above plots we can see...
""", width=500, height=50)


carrier.on_change('value', lambda attr, old, new: update())
box_size.on_change('value', lambda attr, old, new: update())

carrier_dof.on_change('value', lambda attr, old, new: update())

year_date.on_change('value', lambda attr, old, new: update())
y_axis.on_change('value', lambda attr, old, new: update())

sizing_mode = 'fixed' 

controls = [carrier, box_size]

inputs = widgetbox(*controls, sizing_mode=sizing_mode)


controls_dof = [carrier_dof]

inputs_dof = widgetbox(*controls_dof, sizing_mode=sizing_mode)

controls_date = [year_date, y_axis]

inputs_date = widgetbox(*controls_date, sizing_mode=sizing_mode)

l = layout([
    [title],
    [daily_txt],
    [inputs, p, p2],
    [day_concl],
    [week_txt],
    [inputs_dof, p3, p4],
    [week_concl],
    [year_txt],
    [inputs_date, p5],
    [year_concl],

], sizing_mode=sizing_mode)

update()  # initial load of the data


curdoc().add_root(l)
curdoc().title = "Flights"

