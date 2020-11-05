import pandas as pd

import yfinance as yf


import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS


def get_stock_return(ticker):

    return pd.read_csv('stocks.csv', parse_dates=[
        0], index_col=[0])[[ticker]].dropna()


def prep_data_for_regression(ticker, stock):

    df = pd.read_csv('factors.csv', parse_dates=[0], index_col=[0])

    returns = get_stock_return(ticker)

    df = df.join(returns, how='inner')

    X = df.drop(['RF', ticker], axis=1)
    X = sm.add_constant(X)

    Y = df[ticker] - df['RF']

    return Y, X, df


def get_whole_sample_factor_loadings(ticker):

    returns = get_stock_return(ticker)

    if returns.empty:

        out = -1

    else:

        Y, X, df = prep_data_for_regression(ticker, returns)

        model = sm.OLS(Y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 1})

        factor_loadings = pd.DataFrame(model.params).reset_index()
        factor_loadings.columns = ['index', 'params']

        min_year = min(df.index)
        max_year = max(df.index)

        fund_name = yf.Ticker(ticker).info.get('longName')

        out = {
            'factor_loadings': factor_loadings,
            'min_year': min_year,
            'max_year': max_year,
            'fund_name': fund_name
        }

    return out


def get_rolling_factor_loadings(ticker, rolling_window):

    returns = get_stock_return(ticker)

    if returns.empty:

        out = -1

    else:

        Y, X, _ = prep_data_for_regression(ticker, returns)

        rollingmodel = RollingOLS(Y, X, window=rolling_window).fit(
            cov_type='HAC', cov_kwds={'maxlags': 1})

        rolling_factor_loadings = rollingmodel.params.reset_index().dropna()
        rolling_factor_loadings = pd.melt(
            rolling_factor_loadings, id_vars=['index'])

        fund_name = yf.Ticker(ticker).info.get('longName')

        out = {
            'rolling_factor_loadings': rolling_factor_loadings,
            'fund_name': fund_name
        }

    return out
