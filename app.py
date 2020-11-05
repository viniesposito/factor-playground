from models import get_whole_sample_factor_loadings, get_rolling_factor_loadings
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import plotly.express as px

import pandas as pd

from data import ticker_list
# ticker_list = 'tsla msft aapl ttek blk c ko gm'

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.title = 'Factor Playground'

app.layout = html.Div(children=[
    html.H1(children='Factor Playground'),

    html.Div(children='''
        Visualize how your favorite stock's returns can be decomposed into risk factors.
    '''),

    html.Br(),

    html.Div(["Enter a ticker: ",
              dcc.Dropdown(
                  id='ticker-dropdown',
                  options=[{'label': val, 'value': val}
                           for val in ticker_list.upper().split()],
                  value='TSLA'
              )]
             ),

    dcc.Loading(
        id="loading-1",
        type="default",
        children=html.Div(dcc.Graph(
            id='whole-sample-factor-loadings'
        ))
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

    dcc.Loading(
        id="loading-2",
        type="default",
        children=html.Div(dcc.Graph(
            id='rolling-factor-loadings'
        )
        ))

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
            df, x='index', y='params',
            labels={
                'index': '',
                'params': 'Factor loading'
            }
        )

        fig.update_layout(title={
            'text': title,
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }
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

        fig = px.line(df, x='index', y='value', color='variable',
                      labels={
                          'index': '',
                          'value': 'Factor loading',
                          'variable': 'Factors'
                      })

        fig.update_layout(title={
            'text': title,
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }
        )

        return fig


if __name__ == '__main__':
    # app.run_server(debug=True)
    app.run_server()
