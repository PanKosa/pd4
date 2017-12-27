import os
from os.path import dirname, join
import sqlite3
conn = sqlite3.connect(str(os.path.dirname(os.path.abspath(__file__))) + "/map.sql")

import numpy as np
import pandas.io.sql as psql
import sqlite3 as sql

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
  GMapPlot, GMapOptions, ColumnDataSource, Line, MultiLine, Circle, Range1d, PanTool, WheelZoomTool, BoxSelectTool
)

map_options = GMapOptions(lat=39.83, lng=-98.58, map_type="roadmap", zoom=3)

p = GMapPlot(x_range=Range1d(), y_range=Range1d(), map_options=map_options)

# Replace the value below with your personal API key:
p.api_key = "AIzaSyC0M_jwOmZkBEErr960yN6_imbueC6he0k"

movies = psql.read_sql("SELECT * FROM US_filghts_dep_delay_Y", conn)

movies["prec_delayed"] = movies["delay_over_15"]/movies["number_of_flights"]*100

movies["color"] = np.where(movies["prec_delayed"] < 10, "green",
                               np.where((movies["prec_delayed"] >= 10) & (movies["prec_delayed"] < 15), "#b10fc6",
                               np.where((movies["prec_delayed"] >= 15) & (movies["prec_delayed"] < 20), "blue", 
                               np.where((movies["prec_delayed"] >= 20) & (movies["prec_delayed"] < 25), "orange", "red"))))


# Create Input controls
reviews = Slider(title="Minimum number of flights", value=100, start=0, end=1000, step=100)
min_year = Slider(title="Year", start=1989, end=2008, value=2000, step=1)
genre = Select(title="Airport", value="CHS",options=open(str(os.path.dirname(os.path.abspath(__file__))) + '/airports_chose.txt').read().split())
cb_group_le10  = CheckboxButtonGroup(labels=[' <= 10%']  ,active=[0,1], button_type="success")
cb_group_10_15 = CheckboxButtonGroup(labels=['10% - 15%'],active=[0,1], button_type="success")
cb_group_15_20 = CheckboxButtonGroup(labels=['15% - 20%'],active=[0,1], button_type="success")
cb_group_20_25 = CheckboxButtonGroup(labels=['20% - 25%'],active=[0,1], button_type="success")
cb_group_ge25  = CheckboxButtonGroup(labels=[' >25%']    ,active=[0,1], button_type="success")

alpha = Slider(title="Number of bins", start=1, end=25, value=8, step=1)

# Create Column Data Source that will be used by the plot
source = ColumnDataSource(data=dict(lat=[], lon=[], name=[], color=[]))
source_selected = ColumnDataSource(data=dict(lat=[], lon=[], name=[]))
sourceML = ColumnDataSource(data=dict(lat=[], lon=[]))


invisible_circle  = Circle(x="lon", y="lat", size=15, fill_color="color", fill_alpha=0.8, line_color=None) 
invisible_circle2 = Circle(x="lon", y="lat", size=15, fill_color="black", fill_alpha=0.8, line_color=None)
circle_renderer = p.add_glyph(source, invisible_circle, selection_glyph=invisible_circle, nonselection_glyph=invisible_circle)
circle_renderer_selected = p.add_glyph(source_selected, invisible_circle2, selection_glyph=invisible_circle2, nonselection_glyph=invisible_circle2)
ML = MultiLine(xs="lon", ys="lat", line_color="color", line_width=2)
p.add_glyph(sourceML, ML)

p.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool())

def select_movies():
    selected = movies[
        (movies.number_of_flights >= reviews.value) &
        (movies.year == min_year.value) &
        (movies.origin_id == genre.value)
    ]   
    if 0 not in cb_group_le10.active:
        selected = selected[selected["prec_delayed"] > 10]
    if 0 not in cb_group_10_15.active:
        selected = selected[(selected["prec_delayed"] <= 10) | (selected["prec_delayed"] > 15)]
    if 0 not in cb_group_15_20.active:
        selected = selected[(selected["prec_delayed"] <= 15) | (selected["prec_delayed"] > 20)]
    if 0 not in cb_group_20_25.active:
        selected = selected[(selected["prec_delayed"] <= 20) | (selected["prec_delayed"] > 25)]
    if 0 not in cb_group_ge25.active:
        selected = selected[selected["prec_delayed"] <= 25]


    return selected

def selected_flight():
    selected = origin = psql.read_sql("SELECT * FROM airports where iata == '%s'" % genre.value, conn)
    return selected

def histogram_data(data):
    selected = data("SELECT * FROM airports where iata == '%s'" % genre.value, conn)
    return selected


def update():
    df = select_movies()
    origin = selected_flight()
    source.data = dict(
        lat=df["dest_lat"],
        lon=df["dest_lon"],
        name=df["dest_name"],
        DepDelay=df["DepDelay"],
        number_of_flights=df["number_of_flights"],
        color=df["color"],
    )

    source_selected.data = dict(
        lat=origin["latitude_deg"],
        lon=origin["longitude_deg"],
        name=origin["name"],
    )
    lats = [] 
    lons = []
    for lat in df["dest_lat"]:
        lats.append([lat, origin.loc[0,"latitude_deg"]])
    for lon in df["dest_lon"]:
        lons.append([lon, origin.loc[0,"longitude_deg"]])

    sourceML.data = dict(
        lat=lats,
        lon=lons,
        color=df["color"],
    )

    hist, edges = histogram(df["dest_lat"], density=True, bins=alpha.value)
    source_hist.data = {'top': hist, 'left': edges[:-1], 'right': edges[1:]}
    p.update()


tooltips = OrderedDict([
    ('Name', '@name'),
    ('Avg delay: ', '@DepDelay'),
    ('Num.of.flights: ', '@number_of_flights'),
])

tooltips_selected = OrderedDict([
    ('Name', '@name'),
])

p.add_tools( HoverTool(tooltips=tooltips, renderers=[circle_renderer]))
p.add_tools( HoverTool(tooltips=tooltips_selected, renderers=[circle_renderer_selected]))


controls = [reviews, genre, min_year, alpha]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())

cb_group_le10.on_change('active', lambda attr, old, new: update())
cb_group_10_15.on_change('active', lambda attr, old, new: update())
cb_group_15_20.on_change('active', lambda attr, old, new: update())
cb_group_20_25.on_change('active', lambda attr, old, new: update())
cb_group_ge25.on_change('active', lambda attr, old, new: update())
controls.append(cb_group_le10)
controls.append(cb_group_10_15)
controls.append(cb_group_15_20)
controls.append(cb_group_20_25)
controls.append(cb_group_ge25)

source_hist = ColumnDataSource({'top': [], 'left': [], 'right': []})
p2 = figure(plot_width=800, plot_height=350)
p2.title.text = 'Histogram'
p2.quad(top='top', bottom=0, left='left', right='right', alpha=0.4, source=source_hist)



sizing_mode = 'fixed' 

inputs = widgetbox(*controls, sizing_mode=sizing_mode)
#inputs = widgetbox(*controls, width=300)
l = layout([
    [inputs, p],
    p2

], sizing_mode=sizing_mode)



#l = layout([
#    [inputs, p],
#     p2
#])

update()  # initial load of the data

curdoc().add_root(l)
curdoc().title = "Flights"
