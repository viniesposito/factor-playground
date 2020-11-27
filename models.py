from sklearn.decomposition import PCA
from data import ticker_list, DATA_PATH
from statsmodels.regression.rolling import RollingOLS
import statsmodels.api as sm
import pickle
import pandas as pd
import numpy as np


def get_stock_return(ticker):

    return pd.read_csv(DATA_PATH + 'stocks.csv', parse_dates=[
        0], index_col=[0])[[ticker]].dropna()


def get_stock_long_name(ticker):

    infile = open(DATA_PATH + 'stock_metadata', 'rb')

    data = pickle.load(infile)

    infile.close()

    return data.get(ticker).get('longName')


def prep_data_for_regression(ticker, stock):

    df = pd.read_csv(DATA_PATH + 'factors.csv', parse_dates=[0], index_col=[0])

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

    out_df.to_csv(DATA_PATH + 'whole_sample_regressions_output.csv')


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

    out_df.to_csv(DATA_PATH + 'rolling_regressions_output.csv')


def run_rolling_PCA(n_components, rolling_window):

    df = pd.read_csv('factors.csv', parse_dates=[0], index_col=[0])

    max_ = df.shape[0] - rolling_window

    pca = PCA(n_components=n_components)

    array = np.empty([0, n_components])

    for i in range(max_):
        rolling_df = df.iloc[i:(i+rolling_window), :]

        pca.fit(rolling_df)

        array = np.concatenate(
            (array, pca.explained_variance_ratio_.reshape(1, n_components)))

    var_explained_df = pd.DataFrame(array, columns=[f'PCA{i}' for i in range(
        1, n_components+1)], index=df.index[rolling_window:])

    var_explained_df['other'] = 1 - var_explained_df.sum(axis=1)

    var_explained_df.index.name = 'Dates'

    var_explained_df = pd.melt(
        var_explained_df.reset_index(), id_vars=['Dates'])

    var_explained_df.to_csv(DATA_PATH + 'rolling_pca_var_explained.csv')


rolling_window_list = [60, 120, 250]

if __name__ == '__main__':
    run_whole_sample_regressions(ticker_list)
    run_rolling_regressions(ticker_list, rolling_window_list)
    run_rolling_PCA(5, 250)
