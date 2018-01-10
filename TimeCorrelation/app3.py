# In[]:
# Import required libraries
import os
import pickle
import copy
import datetime as dt
import sqlite3
import pandas.io.sql as psql

import pandas as pd
from flask import Flask
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import numpy as np
from datetime import datetime


# In[]:
# Setup app
server = Flask(__name__)
server.secret_key = os.environ.get('secret_key', 'secret')

app = dash.Dash(__name__, server=server, url_base_pathname='/time-dep/', csrf_protect=False)  # noqa: E501

app.css.append_css({'external_url': 'https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css'})  # noqa: E501#

#if 'DYNO' in os.environ:
#    app.scripts.append_script({
#        'external_url': 'https://cdn.rawgit.com/chriddyp/ca0d8f02a1659981a0ea7f013a378bbd/raw/e79f3f789517deec58f41251f7dbb6bee72c44ab/plotly_ga.js'  # noqa: E501
#    })

#a
#app.css.config.serve_locally = True
app.scripts.config.serve_locally = True


# Create controls

carriers = open("data/origin.txt").read().split()

carrier_options = [{'label': carrier, 'value': carrier}
for carrier in carriers]


### Load data
# flights
conn = sqlite3.connect("data/time_dep.sql")

flights = psql.read_sql("SELECT * FROM timeDep", conn)

flights["date"] = pd.to_datetime(flights.date)

data = flights[flights.year == 2008]

data = data.drop(['date', 'month', 'dayofmonth', 'year'], axis=1)

corr_df = data.corr(method='pearson')

corr = pd.DataFrame(corr_df.stack(), columns=['Rate']).reset_index()

corr.columns = ["Origin1", "Origin2",'Rate']

# Maps

conn = sqlite3.connect("data/map.sql")

flights_map = psql.read_sql("SELECT * FROM US_filghts_dep_delay_Y", conn)

flights_map["prec_delayed"] = flights_map["delay_over_15"]/flights_map["number_of_flights"]*100

flights_map["color"] = np.where(flights_map["prec_delayed"] < 10, 0,
                               np.where((flights_map["prec_delayed"] >= 10) & (flights_map["prec_delayed"] < 15), 1,
                               np.where((flights_map["prec_delayed"] >= 15) & (flights_map["prec_delayed"] < 20), 2, 
                               np.where((flights_map["prec_delayed"] >= 20) & (flights_map["prec_delayed"] < 25), 3, 4))))

colors_map = ["green", "#b10fc6", "blue", "orange", "red"]

# Periodic time dep
conn = sqlite3.connect("data/hours.sql")
#flights_week = psql.read_sql("SELECT * FROM Arr_Delays_vs_time_h24102007", conn)
flights_week = psql.read_sql("SELECT * FROM Arr_Delays_vs_time_h", conn)

flights_week["time_str"] = "0000" + flights_week["time"].astype(str)
flights_week["time_str"] = flights_week.time_str.str[-4:]
flights_week["time_str"] = flights_week.time_str.str[0:2] + ":" + flights_week.time_str.str[2:4]
flights_week["time"] = pd.to_datetime(flights_week.time_str, format='%H:%M').dt.time
flights_week["time_date"] = pd.to_datetime(flights_week.time_str, format='%H:%M')

carriers_periodic = open("data/carriers.txt").read().split()

carrier_priodic_options = [{'label': carrier, 'value': carrier} for carrier in carriers_periodic]

carriers_big = open("data/carriers_big.txt").read().split()

data_day_options = [{'label': "Arrival Delay", 'value': "ArrDelay"}, {'label': "Departure Delay", 'value': "DepDelay"}]

flights_dof = psql.read_sql("SELECT * FROM Arr_Delays_vs_DayOfWeek", conn)

dof = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

data_week_options = [{'label': "Arrival Delay", 'value': "ArrDelay"}, {'label': "Departure Delay", 'value': "DepDelay"}]


flights_date = psql.read_sql("SELECT * FROM Delays_vs_Date", conn)

data_year_options = [{'label': 'Number of flights', 'value': 'number_of_flights'}, {'label': 'Number of delayed departures', 'value': 'delay_over_15'},
                     {'label': 'Number of delayed arrivals', 'value': 'arrival_over_15'}, {'label': 'Mean departure delay', 'value': 'depDelay'},
                     {'label': 'Mean arrival delay', 'value': 'arrDelay'}]

# models of planes

conn = sqlite3.connect("data/processed.sql")

manufacturer_names_dt = psql.read_sql("SELECT * FROM Manufacturer_Names", conn)

manufacturer_names = manufacturer_names_dt["manufacturer"]

manufacturer_names = [{'label': mn, 'value': mn} for mn in manufacturer_names]

model_names_dt = psql.read_sql("SELECT * FROM Model_Names", conn)

model_names = ["ALL"]

model_names = [{'label': mn, 'value': mn} for mn in model_names]

features_planes = ["dep_delay", "perc_delayed", "number_of_flights"]

features_planes_names_l = ["Average departure delay", "Percentage delayed (>15 min)", "Number of flights"]

features_planes_names = [{'label': features_planes_names_l[i], 'value': i} for i in range(len(features_planes_names_l))]

planes = psql.read_sql("SELECT * from Model_Performance", conn)

planes["perc_delayed"] = planes["delay_over_15"]/planes["number_of_flights"]

# Create global chart template
mapbox_access_token = 'pk.eyJ1IjoiamFja2x1byIsImEiOiJjajNlcnh3MzEwMHZtMzNueGw3NWw5ZXF5In0.fk8k06T96Ml9CLGgKmk81w'  # noqa: E501

layout = dict(
    autosize=True,
    height=500,
    font=dict(color='#CCCCCC'),
    titlefont=dict(color='#CCCCCC', size='14'),
    margin=dict(
        l=35,
        r=35,
        b=35,
        t=45
    ),
    hovermode="closest",
    plot_bgcolor="#191A1A",
    paper_bgcolor="#020202",
    legend=dict(font=dict(size=10), orientation='h'),
    title='Satellite Overview',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="dark",
        center=dict(
            lon=-78.05,
            lat=42.54
        ),
        zoom=7,
    ),
    geo = dict(
            scope='north america',
            projection=dict( type='azimuthal equal area' ),
            showland = True,
            landcolor = 'rgb(243, 243, 243)',
            countrycolor = 'rgb(204, 204, 204)',
        ),
)


# In[]:
# Create app layout
tab1 = html.Div([
	html.Div(
	    [
		html.Div(
		    [
		        html.H1(
		            'Time dependencies in year 2008',
		            className='eight columns',
		        ),
		    ],
		    className='row'
		),
		html.Div(
		    [
		        html.H5(
		            '',
		            id='well_text',
		            className='two columns'
		        ),
		        html.H5(
		            '',
		            id='production_text',
		            className='eight columns',
		            style={'text-align': 'center'}
		        ),
		        html.H5(
		            '',
		            id='year_text',
		            className='two columns',
		            style={'text-align': 'right'}
		        ),
		    ],
		    className='row'
		),
		html.Div(
		    [
			html.Div([
		        html.Div(
		            [
		                dcc.Graph(id = "heatmap")
		            ],
		            className='ten columns',
		            style={'margin-top': '20'}
		        ),
			]),
		        html.Div(
		            [
				html.P('Number of corelated plots:'),  # noqa: E501
				dcc.Slider(
				    id='nn_slider',
				    min=1,
				    max=3,
				    value=3
		        ),
		            ],
		            className='six columns'
		        ),
		    ],
		    style={'margin-top': '20'},
		    className='row'
		),
		html.Div(
		    [
		        html.Div(
		            [
		                html.P('Carrier:'),
		                dcc.Dropdown(
		                    id='carrier_iata',
		                    options=carrier_options,
		                    multi=False,
		                    value="JFK"
		                ),
		            ],
		            className='six columns'
		        ),
		    ],
		    className='row'
		),
		html.Div(
		    [
		        html.Div(
		            [
		                dcc.Graph(id='individual_graph')
		            ],
		            className='ten columns',
		            style={'margin-top': '20'}
		        ),
		    ],
		    className='row'
		),
	    ],
	    className='twelwe columns offset-by-one',
            id = 'tab1'
	)
        ])

tab2 = html.Div([
	html.Div(
	    [
		html.Div(
		    [
		        html.H1(
		            'Geo Data',
		            className='eight columns',
		        ),
		    ],
		    className='row'
		),
		html.Div(
		    [
		        html.Div(
		            [
				html.P('Year:'),  # noqa: E501
				dcc.Slider(
				    id='year_map',
				    min=1987,
				    max=2008,
				    value=2008
		        ),
		            ],
		            className='six columns'
		        ),
		    ],
		    style={'margin-top': '20'},
		    className='row'
		),
		html.Div(
		    [
		        html.Div(
		            [
		                html.P('Carrier:'),
		                dcc.Dropdown(
		                    id='iata_map',
		                    options=carrier_options,
		                    multi=False,
		                    value="JFK"
		                ),
		            ],
		            className='six columns'
		        ),
		    ],
		    className='row'
		),
                html.Div(
		    [
		        html.Div(
		            [
		                dcc.Graph(id='map')
		            ],
		            className='ten columns',
		            style={'margin-top': '20'}
		        ),
		    ],
		    className='row'
		),
                html.Div(
		    [
		        html.Div(
		            [
		                dcc.Graph(id='histogram_map')
		            ],
		            className='ten columns',
		            style={'margin-top': '20'}
		        ),
		    ],
		    className='row'
		),
	    ],
	    className='twelwe columns offset-by-one',
            id = 'tab2'
	)
        ])

tab3 = html.Div([
	html.Div(
	    [
		html.Div(
		    [
		        html.H1(
		            'Daily dependencies',
		            className='eight columns',
		        ),
		    ],
		    className='row'
		),
		html.Div(
		    [
		        html.Div(
		            [
                                html.P('Min number of flights:'), # dodac ruchoma srednia a potem smotha dac -> czyli te biny z bokeh
								dcc.Slider(
									id='numb_flights',
									min=1,
									max=100,
								    step=1,
									value=100
										),   
                                html.P('Data:'), # dodac ruchoma srednia a potem smotha dac -> czyli te biny z bokeh
						        dcc.Dropdown(
						            id='data_day',
						            options=data_day_options,
						            multi=False,
						            value="ArrDelay",
						        ),
                                html.P('Box Size:'), # dodac ruchoma srednia a potem smotha dac -> czyli te biny z bokeh
								dcc.Slider(
									id='box_size',
									min=1,
									max=100,
								                    step=1,
									value=80
										),
								                html.P('Carriers:'),
						        dcc.Dropdown(
						            id='carries_included',
						            options=carrier_priodic_options,
						            multi=True,
						            value=carriers_big,
						        ),
	                    ],
		            className='two columns',
		            style={'margin-top': '20'}
		        ),
		        html.Div(
		            [
		                dcc.Graph(id='predicted_delays_daily')
		            ],
		            className='eight columns',
		            style={'margin-top': '20'}
		        ),
		    ],
		    className='row'
		    ),
			html.Div(
				[
		                    html.Div(
				        [
				            dcc.Graph(id = "number_of_flights_daily")
				        ],
				        className='eight columns  offset-by-two',
				        style={'margin-top': '20'}
				    ),
				],
				className='row'
			),
            html.Div(
				[
				    html.H1(
				        'Weekly dependencies',
				        className='eight columns',
				    ),
				],
				className='row'
		    ),
		    html.Div(
		        [
		        html.Div(
		                [
                            html.P('Data:'), # dodac ruchoma srednia a potem smotha dac -> czyli te biny z bokeh
					        dcc.Dropdown(
					            id='data_week',
					            options=data_week_options,
					            multi=False,
					            value="ArrDelay",
					        ),
							html.P('Carriers:'),
					        dcc.Dropdown(
					            id='carries_included_weekly',
					            options=carrier_priodic_options,
					            multi=True,
					            value=carriers_big,
					        ),
	                    ],
		            className='two columns',
		            style={'margin-top': '20'}
		        ),
		        html.Div(
		            [
		                dcc.Graph(id='predicted_delays_weekly')
		            ],
		            className='eight columns',
		            style={'margin-top': '20'}
		        ),
		    ],
		    className='row'
		    ),
			html.Div(
				[
		            html.Div(
				        [
				            dcc.Graph(id = "number_of_flights_weekly")
				        ],
				        className='eight columns  offset-by-two',
				        style={'margin-top': '20'}
				    ),
				],
				className='row'
			),
            html.Div(
				[
				    html.H1(
				        'Yearly dependencies',
				        className='eight columns',
				    ),
				],
				className='row'
		    ),
		    html.Div(
		        [
		        html.Div(
		                [
                            html.P('Data:'), # dodac ruchoma srednia a potem smotha dac -> czyli te biny z bokeh
					        dcc.Dropdown(
					            id='data_type_year',
					            options=data_year_options,
					            multi=False,
					            value="delay_over_15",
					        ),
							html.P('Year:'),
							dcc.Slider(
								id='year_data',
								min=1987,
								max=2008,
								value=2008
							),
	                    ],
		            className='two columns',
		            style={'margin-top': '20'}
		        ),
		        html.Div(
		            [
		                dcc.Graph(id='predicted_delays_yearly')
		            ],
		            className='eight columns',
		            style={'margin-top': '20'}
		        ),
		    ],
		    className='row'
		    ),
			],
			className='twelwe columns offset-by-one',
		        id = 'tab3'
		)
        ])

tab4 = html.Div([
	html.Div(
	    [
		html.Div(
		    [
		        html.H1(
		            'Plane performance by manufacturer and model',
		            className='eight columns',
		        ),
		    ],
		    className='row'
		),
		html.Div(
		    [
		        html.Div(
		            [
		                html.P('Manufacturer:'),
		                dcc.Dropdown(
		                    id='manufacturer1',
		                    options=manufacturer_names,
		                    multi=False,
		                    value="ALL"
		                ),
		            ],
		            className='five columns'
		        ),
		        html.Div(
		            [
		                html.P('Model:'),
		                dcc.Dropdown(
		                    id='model1',
		                    options=model_names,
		                    multi=False,
		                    value="ALL"
		                ),
		            ],
		            className='five columns'
		        ),
		    ],
		    className='row'
		),
		html.Div(
		    [
		        html.Div(
		            [
		                html.P('Manufacturer:'),
		                dcc.Dropdown(
		                    id='manufacturer2',
		                    options=manufacturer_names,
		                    multi=False,
		                    value="ALL"
		                ),
		            ],
		            className='five columns'
		        ),
		        html.Div(
		            [
		                html.P('Model:'),
		                dcc.Dropdown(
		                    id='model2',
		                    options=model_names,
		                    multi=False,
		                    value="ALL"
		                ),
		            ],
		            className='five columns'
		        ),
		    ],
		    className='row'
		),
		html.Div(
		    [
		        html.Div(
		            [
		                html.P('Metric:'),
		                dcc.Dropdown(
		                    id='feature_plane',
		                    options=features_planes_names,
		                    multi=False,
		                    value=0
		                ),
		            ],
		            className='five columns'
		        ),
		    ],
		    className='row'
		),
		html.Div(
		    [
		        html.Div(
		            [
		                dcc.Graph(id='performance')
		            ],
		            className='ten columns',
		            style={'margin-top': '20'}
		        ),
		    ],
		    className='row'
		),
	    ],
	    className='twelwe columns offset-by-one',
            id = 'tab4'
	)
        ])

tabs=dcc.Tabs(
        tabs=[
            {'label': 'Time Dependencies', 'value': 'tab1'},
            {'label': 'Geo Dependencies', 'value': 'tab2'},
            {'label': 'Periodic Dependencies', 'value': 'tab3'},
            {'label': 'Plane Dependencies', 'value': 'tab4'}
        ],
        value='tab1',
        id='tabs',
        style={
	    'width': '80%',
	    'fontFamily': 'Sans-Serif',
	    'margin-left': 'auto',
	    'margin-right': 'auto'
        }
)


app.layout = html.Div([
	tabs,
	tab1,
        tab2,
        tab3,
        tab4
	])


# In[]:
# Helper functions

def smooth_avg(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth


# In[]:
# Create callbacks

@app.callback(
    Output('model1', 'options'),
    [Input('tabs','value'),Input('manufacturer1', 'value')])
def update_date_dropdown(x, name):
    models = model_names_dt.loc[model_names_dt["manufacturer"] == name]
    models = list(models["model"])
    return [{'label': i, 'value': i} for i in models]

@app.callback(
    Output('model1', 'value'),
    [Input('tabs','value'),Input('manufacturer1', 'value')])
def update_date_dropdown(x, name):
    return "ALL"

@app.callback(
    Output('model2', 'options'),
    [Input('tabs','value'),Input('manufacturer2', 'value')])
def update_date_dropdown(x, name):
    models = model_names_dt.loc[model_names_dt["manufacturer"] == name]
    models = list(models["model"])
    return [{'label': i, 'value': i} for i in models]

@app.callback(
    Output('model2', 'value'),
    [Input('tabs','value'),Input('manufacturer2', 'value')])
def update_date_dropdown(x, name):
    return "ALL"

# individual graph
@app.callback(Output('individual_graph', 'figure'),
              [Input('nn_slider', 'value'),
               Input('carrier_iata', 'value')])
def make_individual_figure(nn_slider, carrier_iata):
    layout_individual = copy.deepcopy(layout)

    nn = nn_slider
    origin=carrier_iata
    #origin="JFK"
    kk = corr_df.sort_values(by=[origin], ascending=False).loc[:,origin].nlargest(nn).index.values
    kols = ["date", *kk]
    data_f = flights.loc[flights["year"] == 2008, kols]
    kolor = ['#fac1b7', '#a9bb95', '#92d8d8']
    data = []
    it = 0
    for k in kk:
        d = dict(
		type='scatter',
		mode='lines+markers',
		name=k,
		x=data_f["date"],
		y=data_f[k],
		line=dict(
		    shape="spline",
		    smoothing=2,
		    width=1,
		    color=kolor[it]
		    ),
        marker=dict(symbol='diamond-open')
        )
        data.append(d)
        it+=1

    layout_individual['title'] = 'Most corerlated time serries: '  # noqa: E501

    figure = dict(data=data, layout=layout_individual)
    return figure

# heatmap graph
@app.callback(Output('heatmap', 'figure'),
              [Input('nn_slider', 'value'),
               Input('carrier_iata', 'value')])
def make_heatmap(nn_slider, carrier_iata):
    layout_individual = copy.deepcopy(layout)

    layout_individual['title'] = 'Airport correlation'  # noqa: E501
    figure = go.Figure( data = [go.Heatmap(z=corr["Rate"],
                                           x=corr["Origin1"],
                                           y=corr["Origin2"],
                                           colorscale='Viridis',)],
                       layout=layout_individual) 
    return figure

# map 
@app.callback(Output('map', 'figure'),
              [Input('tabs','value'), Input('year_map', 'value'), Input('iata_map', 'value')])
def make_individual_figure(x, year_map, iata_map):
    layout_individual = copy.deepcopy(layout)

    selected = flights_map[
        (flights_map.number_of_flights >= 0) &
        (flights_map.year == year_map) &
        (flights_map.origin_id == iata_map)
    ] 
    conn = sqlite3.connect("data/map.sql")
    origin = psql.read_sql("SELECT * FROM airports where iata == '%s'" % iata_map, conn)
    lats = list(selected['dest_lat'])
    lons = list(selected['dest_lon'])
    kolor = list(selected['color'])
    number_of_flights = selected['number_of_flights']

    inlegend = [True, True, True, True, True]
    groups = [' <= 10%', '10% - 15%', '15% - 20%', '20% - 25%', ' >25%']

    flight_paths = []
    for i in range( len( selected["dest_lat"] ) ):
        flight_paths.append(
            dict(
                type = 'scattergeo',
                locationmode = 'USA-states',
                legendgroup =  groups[kolor[i]],
                showlegend = inlegend[kolor[i]],
                name =  groups[kolor[i]],
                lon = [ origin.loc[0,"longitude_deg"], lons[i] ],
                lat = [ origin.loc[0,"latitude_deg"] , lats[i] ],
                mode = 'lines',
                line = dict(
                    width = 1,
                    color = colors_map[kolor[i]]
                ),
#               opacity = float(number_of_flights[i])/float(number_of_flights.max()),
            )
        )
        inlegend[kolor[i]] = False
    layout_individual['title'] = 'Most corerlated time serries: '  # noqa: E501
    layout_individual["legend"] = dict(traceorder =  'reversed')
    

    groups = [' <= 10% (pkt)', '10% - 15% (pkt)', '15% - 20% (pkt)', '20% - 25% (pkt)', ' >25% (pkt)']

    selected_prec = selected[(selected["prec_delayed"]<10)]
    hover_m = ['Airport: ' + list(selected_prec["dest_name"])[i] + '<br>' +
               'Average Delay: ' + str(round(list(selected_prec["DepDelay"])[i]))  + '<br>' +
               'Number of flights: ' + str(round(list(selected_prec["number_of_flights"])[i],1))  + '<br> ' +
               'Percentage of flights del. > 15 min: ' + str(round(list(selected_prec["prec_delayed"])[i],1)) + '%'  for i in range(len(selected_prec["dest_name"]))]
    airports10 = [ dict(
        type = 'scattergeo',
        locationmode = 'USA-states',
        lon = selected_prec['dest_lon'],
        lat = selected_prec['dest_lat'],
        hoverinfo = 'text',
        showlegend = True,
        name = groups[0],
        text = hover_m,
        mode = 'markers',
        marker = dict( 
            size=2, 
            color=colors_map[0],
        ))]
    selected_prec = selected[(selected["prec_delayed"]>=10) & (selected["prec_delayed"]<15)]
    hover_m = ['Airport: ' + list(selected_prec["dest_name"])[i] + '<br>' +
               'Average Delay: ' + str(round(list(selected_prec["DepDelay"])[i]))  + '<br>' +
               'Number of flights: ' + str(round(list(selected_prec["number_of_flights"])[i],1))  + '<br> ' +
               'Percentage of flights del. > 15 min: ' + str(round(list(selected_prec["prec_delayed"])[i],1)) + '%'  for i in range(len(selected_prec["dest_name"]))]
    airports1015 = [ dict(
        type = 'scattergeo',
        locationmode = 'USA-states',
        lon = selected_prec['dest_lon'],
        lat = selected_prec['dest_lat'],
        hoverinfo = 'text',
        showlegend = True,
        name = groups[1],
        text = hover_m,
        mode = 'markers',
        marker = dict( 
            size=2, 
            color=colors_map[1],
        ))]

    selected_prec = selected[(selected["prec_delayed"]>=15) & (selected["prec_delayed"]<20)]
    hover_m = ['Airport: ' + list(selected_prec["dest_name"])[i] + '<br>' +
               'Average Delay: ' + str(round(list(selected_prec["DepDelay"])[i]))  + '<br>' +
               'Number of flights: ' + str(round(list(selected_prec["number_of_flights"])[i],1))  + '<br> ' +
               'Percentage of flights del. > 15 min: ' + str(round(list(selected_prec["prec_delayed"])[i],1)) + '%'  for i in range(len(selected_prec["dest_name"]))]
    airports1520 = [ dict(
        type = 'scattergeo',
        locationmode = 'USA-states',
        lon = selected_prec['dest_lon'],
        lat = selected_prec['dest_lat'],
        hoverinfo = 'text',
        showlegend = True,
        name = groups[2],
        text = hover_m,
        mode = 'markers',
        marker = dict( 
            size=2, 
            color=colors_map[2],
        ))]

    selected_prec = selected[(selected["prec_delayed"]>=20) & (selected["prec_delayed"]<25)]
    hover_m = ['Airport: ' + list(selected_prec["dest_name"])[i] + '<br>' +
               'Average Delay: ' + str(round(list(selected_prec["DepDelay"])[i]))  + '<br>' +
               'Number of flights: ' + str(round(list(selected_prec["number_of_flights"])[i],1))  + '<br> ' +
               'Percentage of flights del. > 15 min: ' + str(round(list(selected_prec["prec_delayed"])[i],1)) + '%'  for i in range(len(selected_prec["dest_name"]))]
    airports2025 = [ dict(
        type = 'scattergeo',
        locationmode = 'USA-states',
        lon = selected_prec['dest_lon'],
        lat = selected_prec['dest_lat'],
        hoverinfo = 'text',
        showlegend = True,
        name = groups[3],
        text = hover_m,
        mode = 'markers',
        marker = dict( 
            size=2, 
            color=colors_map[3],
        ))]
    ('Avg delay: ', '@DepDelay'),
    ('Num.of.flights: ', '@number_of_flights'),
    selected_prec = selected[(selected["prec_delayed"]>=25)]
    hover_m = ['Airport: ' + list(selected_prec["dest_name"])[i] + '<br>' +
               'Average Delay: ' + str(round(list(selected_prec["DepDelay"])[i]))  + '<br>' +
               'Number of flights: ' + str(round(list(selected_prec["number_of_flights"])[i],1))  + '<br> ' +
               'Percentage of flights del. > 15 min: ' + str(round(list(selected_prec["prec_delayed"])[i],1)) + '%'  for i in range(len(selected_prec["dest_name"]))]
    airports25 = [ dict(
        type = 'scattergeo',
        locationmode = 'USA-states',
        lon = selected_prec['dest_lon'],
        lat = selected_prec['dest_lat'],
        hoverinfo = 'text',
        showlegend = True,
        name = groups[4],
        text = hover_m,
        mode = 'markers',
        marker = dict( 
            size=2, 
            color=colors_map[4],
        ))]

    origin_map = [ dict(
        type = 'scattergeo',
        locationmode = 'USA-states',
        lon = origin['longitude_deg'],
        lat = origin['latitude_deg'],
        hoverinfo = 'text',
        showlegend = True,
        name = "origin",
        text = origin["name"],
        mode = 'markers',
        marker = dict( 
            size=2, 
            color="black",
        ))]

    figure = dict(data=flight_paths+airports10+airports1015+airports1520+airports2025+airports25+origin_map, layout=layout_individual, barmode = "stack")
    return figure

# histogram graph
@app.callback(Output('histogram_map', 'figure'),
              [Input('tabs','value'), Input('year_map', 'value'), Input('iata_map', 'value')])
def make_heatmap(x, year_map, iata_map):
    layout_individual = copy.deepcopy(layout)
    
    selected = flights_map[
        (flights_map.number_of_flights >= 0) &
        (flights_map.year == year_map) &
        (flights_map.origin_id == iata_map)
    ] 

    layout_individual['title'] = 'Histogram rozkladu procentu lotow spoznionych z lotniska %s' % iata_map
    x = np.random.randn(500)

    figure = go.Figure( data = [go.Histogram(x=selected["prec_delayed"],histnorm='probability')],
                        layout=layout_individual) 

    return figure

# daily delays graph
@app.callback(Output('predicted_delays_daily', 'figure'),
              [Input('tabs','value'), Input('carries_included','value'), Input('data_day','value'), Input('box_size','value'), Input('numb_flights','value')])
def make_delay_daily(x, carries_included, data_day, box_size, numb_flights):
    layout_individual = copy.deepcopy(layout)
    all_x = pd.date_range("00:00", "23:59", freq="1min").time

    data = []
    data.append(
            go.Scatter(
                 x = all_x,
                 y = [0]*len(all_x),
                 mode = 'lines',
                 name = 'null',
                 showlegend = False
            )
    )

    for carrier in carries_included:
        selected = flights_week[
            (flights_week.UniqueCarrier == carrier) & (flights_week.number_of_flights >= numb_flights)
        ]
        if not selected.empty:
            ts = pd.Series(list(smooth_avg(selected[data_day],box_size)), index=selected["time_date"])
            ts = ts.resample('T', how='mean')
            ts = ts.interpolate(method='cubic')
            data.append(
		    go.Scatter(
               x = ts.index.time,
               y = ts.values,
#		        x = selected["time"],
#		        y = smooth_avg(selected["DepDelay"],box_size),
		        mode = 'lines',
		        name = carrier,
		        line=dict(
		              shape='spline',
		              smoothing=1.3
		        )
		    )
	    )

    data_day_str = "Departure Delay"
    if data_day == "ArrDelay":
        data_day_str = "Arrival Delay"

    layout_individual['title'] = 'Mean %s by time of planned departure' % data_day_str  # noqa: E501
    layout_individual['legend'] = dict(orientation="v") # noqa: E501
    layout_individual['xaxis']  = dict(type='hours', range = ['00:00','23:59'])

    figure = go.Figure( data = data,
                       layout=layout_individual) 
    return figure

# daily delays graph
@app.callback(Output('number_of_flights_daily', 'figure'),
              [Input('tabs','value'), Input('carries_included','value')])
def make_number_daily(x, carries_included):
    layout_individual = copy.deepcopy(layout)
    
    all_x = pd.date_range("00:00", "23:59", freq="1min").time

    data = []
    data.append(
            go.Scatter(
                 x = all_x,
                 y = [0]*len(all_x),
                 mode = 'lines',
                 name = 'null',
                 showlegend = False
            )
    )

    for carrier in carries_included:
        selected = flights_week[
            flights_week.UniqueCarrier == carrier
        ]
        data.append(
            go.Scatter(
                 x = selected["time"],
                 y = selected["number_of_flights"],
                 mode = 'lines',
                 name = carrier
            )
        )

    layout_individual['title'] = 'Number of flights'  # noqa: E501
    layout_individual['legend'] = dict(orientation="v") # noqa: E501
    layout_individual['xaxis']  = dict(type='hours', range = ['00:00','23:59'])
    figure = go.Figure( data = data,
                       layout=layout_individual) 
    return figure

# weekly delays graph
@app.callback(Output('predicted_delays_weekly', 'figure'),
              [Input('tabs','value'), Input('carries_included_weekly','value'), Input('data_week','value')])
def make_delay_weekly(x, carries_included_weekly, data_week):
    layout_individual = copy.deepcopy(layout)

    data = []
    for carrier in carries_included_weekly:
        selected = flights_dof[
            flights_dof.UniqueCarrier == carrier
        ]

        if not selected.empty:
            data.append(
		    go.Scatter(
               x = selected["day"],
               y = selected[data_week],
		       mode = 'lines',
		       name = carrier
		    )
			)

    bandxaxis = go.XAxis(
		title="Day of week",
		range=[1, 7],
		showgrid=True,
		showline=True,
		ticks="", 
		showticklabels=True,
		mirror=True,
		linewidth=2,
		ticktext=dof,
		tickvals=[i + 1 for i in range(len(dof))]
	)

    data_day_str = "Departure Delay"
    if data_week == "ArrDelay":
        data_day_str = "Arrival Delay"


    layout_individual['title'] = 'Mean %s by time of planned departure' % data_day_str  # noqa: E501
    layout_individual['legend'] = dict(orientation="v") # noqa: E501
    layout_individual['xaxis'] = bandxaxis


    figure = go.Figure( data = data,
                       layout=layout_individual) 
    return figure

# weekly number graph
@app.callback(Output('number_of_flights_weekly', 'figure'),
              [Input('tabs','value'), Input('carries_included_weekly','value')])
def make_number_weekly(x, carries_included_weekly):
    layout_individual = copy.deepcopy(layout)

    data = []
    for carrier in carries_included_weekly:
        selected = flights_dof[
            flights_dof.UniqueCarrier == carrier
        ]

        if not selected.empty:
            data.append(
		    go.Scatter(
               x = selected["day"],
               y = selected["number_of_flights"],
		       mode = 'lines',
		       name = carrier
		    )
			)

    bandxaxis = go.XAxis(
		title="Day of week",
		range=[1, 7],
		showgrid=True,
		showline=True,
		ticks="", 
		showticklabels=True,
		mirror=True,
		linewidth=2,
		ticktext=dof,
		tickvals=[i + 1 for i in range(len(dof))]
	)


    layout_individual['title'] = 'Number of departures by the day of week'  # noqa: E501
    layout_individual['legend'] = dict(orientation="v") # noqa: E501
    layout_individual['xaxis'] = bandxaxis


    figure = go.Figure( data = data,
                       layout=layout_individual) 
    return figure

# yearly delays graph
@app.callback(Output('predicted_delays_yearly', 'figure'),
              [Input('tabs','value'), Input('data_type_year','value'), Input('year_data','value')])
def make_delay_yearly(x, data_type_year, year_date):
    layout_individual = copy.deepcopy(layout)

    selected = flights_date[
        flights_date.year == year_date
    ]

    data = []
    data.append(
		go.Scatter(
		   x = selected["date"],
		   y = selected[data_type_year],
		   mode = 'lines',
		   name = "Plot"
		)
	)



    data_day_str = "Number of flights"
    if data_type_year == "delay_over_15":
        data_day_str = "Number of delayed departures"
    if data_type_year == "arrival_over_15":
        data_day_str = "Number of delayed arrivals"
    if data_type_year == "depDelay":
        data_day_str = "Mean departure delay"
    if data_type_year == "arrDelay":
        data_day_str = "Mean arrival delay"

    layout_individual['title'] = ' %s by time of planned departure in year %s ' % (data_day_str, str(year_date))  # noqa: E501
    layout_individual['legend'] = dict(orientation="v") # noqa: E501
    layout_individual['xaxis']  = dict(type='date')

    figure = go.Figure( data = data,
                       layout=layout_individual) 
    return figure

# yearly delays graph
@app.callback(Output('performance', 'figure'),
              [Input('tabs','value'),
               Input('manufacturer1','value'),
               Input('model1','value'),
               Input('manufacturer2','value'),
               Input('model2','value'),
               Input('feature_plane','value')])
def planes_comp(x, manufacturer1, model1, manufacturer2, model2, feature_plane):
    layout_individual = copy.deepcopy(layout)

    plane1 = planes[
        (planes.manufacturer == manufacturer1) & (planes.model == model1) 
    ]

    plane2 = planes[
        (planes.manufacturer == manufacturer2) & (planes.model == model2) 
    ]

    year = list(plane1["year"])
    month = list(plane1["month"])

    x1 = [datetime(year[i], month[i], 1) for i in range(len(year))]

    year = list(plane2["year"])
    month = list(plane2["month"])

    x2 = [datetime(year[i], month[i], 1) for i in range(len(year))]

    feature = features_planes[feature_plane]

    trace0 = go.Scatter(
        x = x1,
        y=plane1[feature],
        name = str(manufacturer1) + ' ' + str(model1)
    )
    trace1 = go.Scatter(
        x=x2,
        y=plane2[feature],
        name = str(manufacturer2) + ' ' + str(model2)
    )
    data = [trace0, trace1]

    layout_individual = dict(
        title='Time Series for '+ features_planes_names_l[feature_plane],
        xaxis=dict(
            type='date',
            title='Date',
        ),
        yaxis=dict(
            title=features_planes_names_l[feature_plane],
        )
    )

    figure = go.Figure(data = data, layout=layout_individual) 

    return figure

# changing tabs
@app.callback(
    Output('tab1','style'),
    [Input('tabs','value'),
    ])
def update_div1_visible(tab_val):
    if tab_val=='tab1':
        return {'display':'block'}
    else:
        return {'display':'none'}
    
@app.callback(
    Output('tab2','style'),
    [Input('tabs','value'),
    ])
def update_div2_visible(tab_val):
    if tab_val=='tab2':
        return {'display':'block'}
    else:
        return {'display':'none'}

@app.callback(
    Output('tab3','style'),
    [Input('tabs','value'),
    ])
def update_div3_visible(tab_val):
    if tab_val=='tab3':
        return {'display':'block'}
    else:
        return {'display':'none'}

@app.callback(
    Output('tab4','style'),
    [Input('tabs','value'),
    ])
def update_div4_visible(tab_val):
    if tab_val=='tab4':
        return {'display':'block'}
    else:
        return {'display':'none'}


# In[]:
# Main
if __name__ == '__main__':
    app.server.run(debug=True, threaded=True)
