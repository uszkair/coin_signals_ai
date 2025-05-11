import pandas as pd
import ta

def calculate_rsi(series: pd.Series, period=14):
    return ta.momentum.RSIIndicator(close=series, window=period).rsi()

def calculate_ema(series: pd.Series, period=20):
    return ta.trend.EMAIndicator(close=series, window=period).ema_indicator()

def calculate_macd(series: pd.Series):
    macd = ta.trend.MACD(close=series)
    return macd.macd(), macd.macd_signal()

def calculate_bollinger_bands(series: pd.Series, window=20, std=2):
    bb = ta.volatility.BollingerBands(close=series, window=window, window_dev=std)
    return bb.bollinger_hband(), bb.bollinger_lband()

def calculate_stoch_rsi(series: pd.Series):
    stoch_rsi = ta.momentum.StochRSIIndicator(close=series)
    return stoch_rsi.stochrsi_k(), stoch_rsi.stochrsi_d()
