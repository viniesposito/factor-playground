from models import get_stock_long_name, get_whole_sample_factor_loadings, get_rolling_factor_loadings

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import plotly.express as px

import pandas as pd

from data import ticker_list
from models import rolling_window_list

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

    html.Div(["Choose a ticker: ",
              dcc.Dropdown(
                  id='ticker-dropdown',
                  options=[{'label': val, 'value': val}
                           for val in ticker_list.upper().split()],
                  value='TSLA'
              )], style={'width': '15%'}),

    html.Br(),

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
                  min=min(rolling_window_list),
                  max=max(rolling_window_list),
                  value=rolling_window_list[int(len(rolling_window_list)/2)],
                  marks={i: str(i) for i in rolling_window_list},
                  step=None
              )], style={'width': '40%'}
             ),

    dcc.Loading(
        id="loading-2",
        type="default",
        children=html.Div(dcc.Graph(
            id='rolling-factor-loadings'
        )
        ))

],
    style={'width': '70%', 'margin': 'auto'}
)


@ app.callback(
    Output('whole-sample-factor-loadings', 'figure'),
    [Input('ticker-dropdown', 'value')]
)
def update_graph(ticker):

    df = pd.read_csv('whole_sample_regressions_output.csv', index_col=[0])

    df = df[df['ticker'] == ticker].drop('ticker', axis=1)

    min_year = df['min_year']
    min_year = min_year.unique()[0][:4]

    max_year = df['max_year']
    max_year = max_year.unique()[0][:4]

    df.drop(['min_year', 'max_year'], axis=1, inplace=True)

    fund_name = get_stock_long_name(ticker)

    title = f"Factor loadings for {fund_name} - Whole sample from {min_year} to {max_year}"

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

    df = pd.read_csv('rolling_regressions_output.csv', index_col=[0])

    condition = (df['ticker'] == ticker) & (df['window_size'] == window)

    df = df[condition].drop(['ticker', 'window_size'], axis=1)

    fund_name = get_stock_long_name(ticker)

    title = f"Factor loadings over time for {fund_name} over a {window} days window"

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
    app.run_server(debug=True)
    # app.run_server()
