import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import plotly.express as px

import pandas as pd

from models import get_whole_sample_factor_loadings, get_rolling_factor_loadings

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.title = 'Factor Playground'

app.layout = html.Div(children=[
    html.H1(children='Factor Playground'),

    html.Div(children='''
        Visualize how your favorite stock or fund's returns can be decomposed into risk factors.
    '''),

    html.Br(),

    html.Div(["Enter a ticker: ",
              dcc.Dropdown(
                  id='ticker-dropdown',
                  options=[
                      {'label': 'MSFT', 'value': 'MSFT'},
                      {'label': 'AAPL', 'value': 'AAPL'},
                      {'label': 'TSLA', 'value': 'TSLA'}
                  ],
                  value='TSLA'
              )]),

    html.Br(),

    dcc.Graph(
        id='whole-sample-factor-loadings'
    ),

    html.Br(),

    html.Div(["Choose an estimation window (business days): ",
              dcc.Slider(
                  id='rolling-window-slider',
                  min=60,
                  max=720,
                  value=240,
                  marks={i: str(i) for i in range(60, 750, 30)},
                  step=None
              )]
             ),

    dcc.Graph(
        id='rolling-factor-loadings'
    )
])


@ app.callback(
    Output('whole-sample-factor-loadings', 'figure'),
    [Input('ticker-dropdown', 'value')]
)
def update_graph(ticker):

    data = get_whole_sample_factor_loadings(ticker)

    if data == -1:

        raise PreventUpdate

    else:

        df = data.get('factor_loadings')

        title = f"Factor loadings for {data.get('fund_name')} - Whole sample from {data.get('min_year').strftime('%Y')} to {data.get('max_year').strftime('%Y')}"

        fig = px.bar(
            df, x='index', y='params', title=title
        )

        return fig


@ app.callback(
    Output('rolling-factor-loadings', 'figure'),
    [Input('ticker-dropdown', 'value'),
     Input('rolling-window-slider', 'value')
     ]
)
def update_rolling_factors(ticker, window):

    data = get_rolling_factor_loadings(ticker, window)

    if data == -1:

        raise PreventUpdate

    else:

        df = data.get('rolling_factor_loadings')

        title = f"Factor loadings over time for {data.get('fund_name')} over a {window} days window"

        fig = px.line(df, x='index', y='value', color='variable', title=title)

        return fig


if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server()
