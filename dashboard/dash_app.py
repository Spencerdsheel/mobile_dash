import dash
from dash import html, dcc, callback, Output, Input, dash_table
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

#import pandas as pd
#from sklearn import datasets
#from sklearn.cluster import KMeans


#data 
#df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')
df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv')


# Add Bootstrap theme
app = DjangoDash('Dashboard', external_stylesheets=[dbc.themes.BOOTSTRAP], external_scripts=['https://cdn.plot.ly/plotly-2.18.2.min.js'])

# Create figure (indicator)
fig = go.Figure()
fig.add_trace(go.Indicator(
    mode="number+delta",
    value=300,
    domain={'row': 0, 'column': 1}
))

# Dropdown for selecting indicator
dropdown = html.Div(
    [
        dbc.Label("Select indicator (y-axis)"),
        dcc.Dropdown(
            ["gdpPercap", "lifeExp", "pop"],
            "pop",
            id="indicator",
            clearable=False,
        ),
    ],
    className="mb-4",
)

# App layout with dropdown and graph included
app.layout = html.Div([
    html.H3("My First App with Data and a Graph"),
    
    # Dropdown
    dropdown,

    # Table
    dash_table.DataTable(data=df.to_dict('records'), page_size=10),

    # Graph
    dcc.Graph(id="histogram", figure=px.histogram(df, x='continent', y='lifeExp', histfunc='avg')),

    # Indicator
    dcc.Graph(id="indicator-graph", figure=fig)
])

# Callback for updating the graph based on dropdown selection
@callback(
    Output("histogram", "figure"),
    Input("indicator", "value")
)
def update_graph(selected_indicator):
    fig = px.histogram(df, x='continent', y=selected_indicator, histfunc='avg')
    return fig