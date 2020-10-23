import pandas as pd

import yfinance as yf

import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS


def get_stock_return(ticker):

    df = yf.Ticker(ticker).history(period="max")[['Close']].pct_change()

    return df.dropna().rename(columns={'Close': ticker})


def get_whole_sample_factor_loadings(ticker):

    df = pd.read_csv('factors.csv', parse_dates=[0], index_col=[0])

    returns = get_stock_return(ticker)

    df = df.join(returns, how='inner')

    X = df.drop(['RF', ticker], axis=1)
    X = sm.add_constant(X)

    Y = df[ticker] - df['RF']

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
