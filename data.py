import pandas as pd

import yfinance as yf


def get_data_from_ken_french(url):
    return pd.read_csv(url, compression='zip', skiprows=6, parse_dates=[0], index_col=[0])


def get_data_from_aqr(url, factor_name):
    df = pd.read_excel(url, sheet_name=f'{factor_name} Factors', skiprows=18,
                       usecols=['DATE', 'Global'], parse_dates=[0], index_col=[0])
    return df.rename(columns={'Global': factor_name})


def get_factor_data():
    five_factors_url = 'http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Developed_5_Factors_Daily_CSV.zip'
    momentum_url = 'http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Developed_Mom_Factor_Daily_CSV.zip'

    five_factors_df = get_data_from_ken_french(five_factors_url)
    momentum_df = get_data_from_ken_french(momentum_url)

    quality_url = 'https://images.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Quality-Minus-Junk-Factors-Daily.xlsx'
    bab_url = 'https://images.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Betting-Against-Beta-Equity-Factors-Daily.xlsx'

    quality_df = get_data_from_aqr(quality_url, 'QMJ')
    bab_df = get_data_from_aqr(bab_url, 'BAB')

    ff_df = five_factors_df.join(momentum_df, how='inner')
    ff_df = ff_df / 100

    aqr_df = quality_df.join(bab_df, how='inner')

    df = ff_df.join(aqr_df, how='inner')

    df.to_csv('factors.csv')


def get_stock_returns(tickers):

    df = yf.download(tickers=tickers, period='max')['Adj Close'].pct_change()

    df.to_csv('stocks.csv')


stocks = 'tsla msft aapl ttek blk c ko gm'

get_factor_data()
get_stock_returns(stocks)
