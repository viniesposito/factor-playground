from models import get_stock_long_name, get_whole_sample_factor_loadings, get_rolling_factor_loadings

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import plotly.express as px

import pandas as pd
import datetime

from data import ticker_list
from models import rolling_window_list

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.title = 'Factor Playground'

factors_df = pd.read_csv('factors.csv', parse_dates=[0], index_col=[0])
whole_sample_regressions_df = pd.read_csv(
    'whole_sample_regressions_output.csv', index_col=[0])
rolling_regressions_df = pd.read_csv(
    'rolling_regressions_output.csv', index_col=[0])
pca_df = pd.read_csv('rolling_pca_var_explained.csv',
                     index_col=[0])
macro_df = pd.read_csv('macro_data.csv', index_col=[0])

# Helper functions


def plotly_chart_title(title):

    title = dict(
        text=title,
        x=0.5,
        y=0.95,
        xanchor='center',
        yanchor='top'
    )

    return title

# Factor correlation heatmap


factor_corr_heatmap = px.imshow(factors_df.corr())

factor_corr_heatmap.update_layout(
    title=plotly_chart_title('Factor correlation')
)

factor_corr_heatmap.layout.coloraxis.showscale = False

# PCA explained variance over time

pca_plot = px.area(pca_df, x='Dates', y='value', color='variable',
                   labels={'Dates': '',
                           'value': '',
                           'variable': ''})

pca_plot.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=0.01,
    xanchor="center",
    x=0.5,
    font=dict(
        size=7
    )),
    title=plotly_chart_title(
        'Share of variance explained by each principle component'
)
)

# Layout begins

app.layout = html.Div(children=[
    html.H1(children='Factor Playground'),

    html.Br(),

    html.Div(["Choose a starting year ",
              dcc.Slider(
                  id='start-year-slider',
                  min=min(factors_df.index).year,
                  max=max(factors_df.index).year,
                  value=2005,
                  marks={
                      i: str(i) for i in factors_df.index.year.unique().values.tolist()},
                  step=None
              )]
             ),

    dcc.Loading(
        id="loading-factor-performance",
        type="default",
        children=html.Div(dcc.Graph(
            id='factor-performance'
        )
        )),

    html.Div([
        html.Div([
            dcc.Loading(
                id="loading-3",
                type="default",
                children=html.Div(dcc.Graph(
                    id='factor-correlation-heatmap',
                    figure=factor_corr_heatmap
                ))
            ),
        ], className='five columns'),
        html.Div([
            dcc.Loading(
                id="loading-4",
                type="default",
                children=html.Div(dcc.Graph(
                    id='pca-plot',
                    figure=pca_plot
                ))
            ),
        ], className='seven columns')
    ],
        className='row'),

    html.Br(),

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

]
)


@app.callback(
    Output('factor-performance', 'figure'),
    [Input('start-year-slider', 'value')]
)
def update_factor_performance_graph(year):

    min_date = min(factors_df.index)

    new_date = datetime.datetime(year, 1, 1)

    df = factors_df.copy()

    if new_date > min_date:
        df = df.loc[new_date:]

    df = (1+df).cumprod().reset_index()

    df = pd.melt(df, id_vars=df.columns[0])

    fig = px.line(
        df, x=df.columns[0], y='value', color='variable',
        labels={
            df.columns[0]: '',
            'value': '',
            'variable': 'Factors'
        }
    )

    fig.update_layout(title=plotly_chart_title('Factor cumulative performance')
                      )

    return fig


@ app.callback(
    Output('whole-sample-factor-loadings', 'figure'),
    [Input('ticker-dropdown', 'value')]
)
def update_whole_sample_regressions_graph(ticker):

    df = whole_sample_regressions_df.copy()

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

    fig.update_layout(title=plotly_chart_title(title)
                      )

    return fig


@ app.callback(
    Output('rolling-factor-loadings', 'figure'),
    [Input('ticker-dropdown', 'value'),
     Input('rolling-window-slider', 'value')
     ]
)
def update_rolling_factors(ticker, window):

    df = rolling_regressions_df.copy()

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

    fig.update_layout(title=plotly_chart_title(title)
                      )

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
    # app.run_server()
