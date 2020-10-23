import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px

import pandas as pd
import yfinance as yf

from models import get_whole_sample_factor_loadings

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

ticker = 'FCNTX'

data = get_whole_sample_factor_loadings(ticker)

df = data.get('factor_loadings')

title = f"Factor loadings for {data.get('fund_name')} - Whole sample from {data.get('min_year').strftime('%Y')} to {data.get('max_year').strftime('%Y')}"

fig = factor_loading_bar_plot = px.bar(df, x='index', y='params', title=title)

app.layout = html.Div(children=[
    html.H1(children='Factor Playground'),

    html.Div(children='''
        By Vinicius Esposito
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
