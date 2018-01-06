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
		            'New tab',
		            className='eight columns',
		        ),
		    ],
		    className='row'
		),
		html.Div(
		    [
		        html.Div(
		            [
				html.P('Number of corelated plots:'),  # noqa: E501
				dcc.Slider(
				    id='nn2_slider',
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
		                dcc.Graph(id='map')
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

tabs=dcc.Tabs(
        tabs=[
            {'label': 'Time Dependencies', 'value': 'tab1'},
            {'label': 'New Tab', 'value': 'tab2'},
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
        tab2
	])


# In[]:
# Helper functions



# In[]:
# Create callbacks

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
              [Input('nn2_slider', 'value')])
def make_individual_figure(nn_slider):
    layout_individual = copy.deepcopy(layout)
    origin = 'JFK'
    selected = flights_map[
        (flights_map.number_of_flights >= 100) &
        (flights_map.year == 2008) &
        (flights_map.origin_id == origin)
    ] 
    conn = sqlite3.connect("data/map.sql")
    origin = psql.read_sql("SELECT * FROM airports where iata == '%s'" % 'JFK', conn)
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
    figure = dict(data=flight_paths, layout=layout_individual, barmode = "stack")
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

# In[]:
# Main
if __name__ == '__main__':
    app.server.run(debug=True, threaded=True)
