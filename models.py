import pandas as pd
import pickle

import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS

from data import ticker_list


def get_stock_return(ticker):

    return pd.read_csv('stocks.csv', parse_dates=[
        0], index_col=[0])[[ticker]].dropna()


def get_stock_long_name(ticker):

    infile = open('stock_metadata', 'rb')

    data = pickle.load(infile)

    infile.close()

    return data.get(ticker).get('longName')


def prep_data_for_regression(ticker, stock):

    df = pd.read_csv('factors.csv', parse_dates=[0], index_col=[0])

    returns = get_stock_return(ticker)

    df = df.join(returns, how='inner')

    X = df.drop(['RF', ticker], axis=1)
    X = sm.add_constant(X)

    Y = df[ticker] - df['RF']

    return Y, X


def get_whole_sample_factor_loadings(ticker):

    returns = get_stock_return(ticker)

    Y, X = prep_data_for_regression(ticker, returns)

    model = sm.OLS(Y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 1})

    factor_loadings = pd.DataFrame(model.params).reset_index()
    factor_loadings.columns = ['index', 'params']
    factor_loadings['ticker'] = ticker
    factor_loadings['min_year'] = min(X.index)
    factor_loadings['max_year'] = max(X.index)

    return factor_loadings


def run_whole_sample_regressions(ticker_list):

    tickers = ticker_list.upper().split()

    out_df = pd.DataFrame(columns=['a', 'b', 'c', 'd', 'e'])

    for ticker in tickers:

        data = get_whole_sample_factor_loadings(ticker)

        if out_df.empty:

            out_df.columns = data.columns

        out_df = pd.concat([out_df, data])

    out_df.to_csv('whole_sample_regressions_output.csv')


def get_rolling_factor_loadings(ticker, rolling_window):

    returns = get_stock_return(ticker)

    Y, X = prep_data_for_regression(ticker, returns)

    rollingmodel = RollingOLS(Y, X, window=rolling_window).fit(
        cov_type='HAC', cov_kwds={'maxlags': 1})

    rolling_factor_loadings = rollingmodel.params.reset_index().dropna()
    rolling_factor_loadings = pd.melt(
        rolling_factor_loadings, id_vars=['index'])

    rolling_factor_loadings['ticker'] = ticker
    rolling_factor_loadings['window_size'] = rolling_window

    return rolling_factor_loadings


def run_rolling_regressions(ticker_list, rolling_window_list):

    ticker_list = ticker_list.upper().split()

    out_df = pd.DataFrame(columns=['a', 'b', 'c', 'd', 'e'])

    for ticker in ticker_list:

        for rolling_window in rolling_window_list:

            df = get_rolling_factor_loadings(ticker, rolling_window)

            if out_df.empty:
                out_df.columns = df.columns

            out_df = pd.concat([out_df, df])

    out_df.to_csv('rolling_regressions_output.csv')


rolling_window_list = [60, 120, 250]

if __name__ == '__main__':
    run_whole_sample_regressions(ticker_list)
    run_rolling_regressions(ticker_list, rolling_window_list)
