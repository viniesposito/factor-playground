from models import get_stock_long_name, get_whole_sample_factor_loadings, get_rolling_factor_loadings

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd
import datetime

from data import ticker_list, DATA_PATH
from models import rolling_window_list

app = dash.Dash(__name__)

server = app.server

app.title = 'Factor Playground'

# Reading in data

factors_df = pd.read_csv(DATA_PATH + 'factors.csv',
                         parse_dates=[0], index_col=[0])
whole_sample_regressions_df = pd.read_csv(
    DATA_PATH + 'whole_sample_regressions_output.csv', index_col=[0])
rolling_regressions_df = pd.read_csv(
    DATA_PATH + 'rolling_regressions_output.csv', index_col=[0])
pca_df = pd.read_csv(DATA_PATH + 'rolling_pca_var_explained.csv',
                     index_col=[0])
macro_df = pd.read_csv(DATA_PATH + 'macro_data.csv',
                       parse_dates=[0], index_col=[0])

# Helper functions and dicts


def plotly_chart_title(title):

    title = dict(
        text=title,
        x=0.5,
        # y=0.95,
        xanchor='center',
        yanchor='top'
    )

    return title


def fig_update_layout(fig, title='Bruh write a title'):

    fig.update_layout(
        title=plotly_chart_title(title),
        font=dict(
            family='Oswald, sans-serif',
            size=16
        ),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(252, 250, 242, 0.4)',
        legend=dict(
            bgcolor='rgba(252, 250, 242, 0.2)',
            borderwidth=1,
            bordercolor='rgba(50, 50, 50, 0.5)'
        ),
        xaxis=dict(
            linecolor='rgba(50, 50, 50, 0.5)',
            linewidth=1,
            mirror=True,
            showline=True
        ),
        yaxis=dict(
            linecolor='rgba(50, 50, 50, 0.5)',
            linewidth=1,
            mirror=True,
            showline=True
        )
    )


macro_var_dict = dict(
    DFII10='US 10Y Real Yield',
    T10YIE='US 10Y Break-even Inflation',
    DGS10='US 10Y Nominal Yield'
)

# Factor correlation heatmap


factor_corr_heatmap = px.imshow(
    factors_df.corr(), color_continuous_scale='RdBu_r')

fig_update_layout(factor_corr_heatmap, title='Cross-factor correlation')

factor_corr_heatmap.layout.coloraxis.showscale = False


# Factor and macro variable correlation


def make_factor_macro_correlations_plot():

    m_df = macro_df[(macro_df != 0).all(1)]
    m_df = m_df.pct_change()

    df = factors_df.join(m_df, how='inner').dropna()

    corr = df.corr()

    macro_vars = macro_df.columns.values.tolist()

    corr = corr[macro_vars].T.drop(macro_vars, axis=1).reset_index()
    corr = pd.melt(corr, id_vars='index')
    corr = corr.replace(macro_var_dict)

    fig = px.bar(
        corr, x='variable', y='value', color='index', barmode="group",
        labels={
            'variable': '',
            'value': 'Correlation',
            'index': ''
        })

    fig_update_layout(fig, title='Factor correlation to macro variables')

    fig.update_layout(
        legend=dict(
            orientation="h",
            x=0.1
        )
    )

    return fig


factor_macro_correlations_plot = make_factor_macro_correlations_plot()

# PCA explained variance over time


# pca_plot = px.area(pca_df, x='Dates', y='value', color='variable',
#                    labels={'Dates': '',
#                            'value': '',
#                            'variable': ''})

# pca_plot.update_layout(
#     legend=dict(
#         orientation="h",
#         yanchor="bottom",
#         y=0.01,
#         xanchor="center",
#         x=0.5,
#     ),
#     title=plotly_chart_title(
#         'Share of variance explained by each principle component'
#     )
# )

# Layout begins

app.layout = html.Div(children=[

    html.Div(children=[
        html.Div(html.Img(src=app.get_asset_url('betahat.png'),
                          style={'height': '50px', 'width': 'auto'}), className='one columns'),
        html.Div(html.H1(children='Factor Playground'),
                 style={'font-size': '50px', 'text-align': 'center'}, className='ten columns'),
        html.Div(html.A(html.Button('Code', style={'height': '50px', 'width': 'auto'}), href='https://github.com/viniesposito/factor-playground'),
                 className='one columns')
    ], className='row flex-display'),

    html.Br(),

    html.Div(children=[
        '''
            This interactive dashboard allows you to play with equity factor performance using solely publicly available data.
        ''',
        html.Br(),
        '''
            Factor data is from Ken French's Data Library and AQR Capital Management, macro data is from FRED, and stock data is from Yahoo! Finance.
        '''
    ]),

    html.Br(),

    html.H4('Explore equity factor dynamics'),

    html.Div(children=[
        html.Div(["Choose a starting year:",
                  dcc.Slider(
                      id='start-year-slider',
                      min=min(factors_df.index).year,
                      max=max(factors_df.index).year,
                      value=2005,
                      marks={i: str(i) for i in range(
                          min(factors_df.index).year, max(factors_df.index).year, 3)},
                      step=None)],
                 className='six columns'
                 ),

        html.Div(["Overlay macro variables (data only available since 2003):",
                  dcc.Dropdown(
                      id='macro-variables-dropdown',
                      options=[
                          {'label': 'US 10Y Real Yield', 'value': 'DFII10'},
                          {'label': 'US 10Y Break-even Inflation',
                           'value': 'T10YIE'},
                          {'label': 'US 10Y Nominal Yield', 'value': 'DGS10'},
                      ],
                      multi=True
                  )], className='six columns')
    ], style={'marginBottom': '3.5em'}),

    html.Br(),

    dcc.Loading(
        id="loading-factor-performance",
        type="default",
        children=html.Div(dcc.Graph(
            id='factor-performance'
        )
        )),

    # html.Br(),

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
                    id='factor-macro-correlation-plot',
                    figure=factor_macro_correlations_plot
                ))
            ),
        ], className='seven columns')
    ],
        className='row'),

    html.Br(),

    html.H4('Pick a stock!'),

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

    # html.Br(),

    html.Div(["Choose an estimation window (business days): ",
              dcc.Slider(
                  id='rolling-window-slider',
                  min=min(rolling_window_list),
                  max=max(rolling_window_list),
                  value=rolling_window_list[int(
                      len(rolling_window_list)/2)],
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


@ app.callback(
    Output('factor-performance', 'figure'),
    [Input('start-year-slider', 'value'),
     Input('macro-variables-dropdown', 'value')
     ]
)
def update_factor_performance_graph(year, macro_vars):

    min_date = min(factors_df.index)

    new_date = datetime.datetime(year, 1, 1)

    df = factors_df.copy()

    if new_date > min_date:
        df = df.loc[new_date:]

    df = (1+df).cumprod()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for col in df.columns:

        fig.add_trace(
            go.Scatter(
                x=df.index, y=df[col], mode='lines', name=col
            ),
            secondary_y=False
        )

    if macro_vars:

        if isinstance(macro_vars, str):

            macro_vars = [macro_vars]

        m_df = macro_df[macro_vars].dropna()

        m_df = m_df.loc[(min(df.index)):]

        for col in m_df.columns:

            fig.add_trace(
                go.Scatter(
                    x=m_df.index, y=m_df[col], mode='lines', name=macro_var_dict.get(col) + ' (rhs)',
                    line=dict(dash='dash')
                ),
                secondary_y=True
            )

    fig_update_layout(fig, title='Factor cumulative performance')

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

    fig_update_layout(fig, title=title)

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

    fig_update_layout(fig, title=title)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
    # app.run_server()
