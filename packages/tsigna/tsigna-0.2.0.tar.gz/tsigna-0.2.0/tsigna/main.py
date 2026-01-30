#!/usr/bin/env python3

"""
Terminal tool to plot stocks, crypto, pair ratios, and technical indicators.

This is a Python financial analysis tool that runs entirely in the terminal. It
fetches historical stock data from Yahoo Finance, calculates technical
indicators including moving averages, MACD, and RSI, and displays them as text-
based charts using the plotille library. The tool supports single ticker
analysis, ratio comparisons between two tickers, and a special MMRI calculation.
Users can customize the time period and split the terminal display to show
multiple indicators simultaneously.

Copyright (c) 2025 Monsieur Linux

Licensed under the MIT License. See the LICENSE file for details.
"""

# Standard library imports
import argparse
import logging
import math
import os
import shutil
import sys
import textwrap
import time
import tomllib
from pathlib import Path

# Third-party library imports
import pandas as pd
import plotille
import requests
from curl_cffi import requests as curlreqs
from yahooquery import Ticker  # Alternative fork: ybankinplay

# Add project root to sys.path so script can be called directly w/o 'python3 -m'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Local imports
from tsigna import __version__

CONFIG = {}

INDICATOR_DESCRIPTIONS = {
    "ATR (Average True Range)": {
        "category": "Volatility Indicator",
        "description": "Measures market volatility by decomposing the entire range of an asset price for that period. Use it to set stop-loss levels (placing them wider than the ATR) or to determine position sizing based on current market noise."
    },
    "Bollinger Bands": {
        "category": "Volatility Indicator",
        "description": "Consists of a middle band (SMA) and two outer bands that expand and contract based on volatility. Use it to identify overbought/oversold conditions (price near bands) and potential breakouts after periods of low volatility (squeeze)."
    },
    "MACD (Moving Average Convergence Divergence)": {
        "category": "Trend / Momentum Indicator",
        "description": "Shows the relationship between two moving averages. Look for signal line crossovers to identify trend direction and divergences (where price moves opposite to the indicator) to spot potential reversals."
    },
    "MFI (Money Flow Index)": {
        "category": "Momentum Oscillator",
        "description": "Incorporates both price and volume data to measure buying and selling pressure. Use it like RSI to identify overbought/oversold levels, but rely on it more heavily as volume-driven divergence is often a stronger signal."
    },
    "Moving Averages": {
        "category": "Trend Indicator",
        "description": "Smooths out price data to identify the direction of the trend. Use it to determine entry points (e.g., buy when price crosses above the line) or dynamic support/resistance levels."
    },
    "OBV (On-Balance Volume)": {
        "category": "Volume Indicator",
        "description": "A cumulative indicator that adds volume on up days and subtracts volume on down days. Use it to confirm the strength of a trend (e.g., rising price + rising OBV = strong trend) or spot reversals via divergence."
    },
    "RSI (Relative Strength Index)": {
        "category": "Momentum Oscillator",
        "description": "Measures the speed and change of price movements on a scale of 0 to 100. Use it to identify overbought conditions (above 70) or oversold conditions (below 30) and to spot bullish or bearish divergences."
    },
    "Stochastics": {
        "category": "Momentum Oscillator",
        "description": "Compares a particular closing price of an asset to a range of its prices over a certain period of time. Look for the lines to cross in overbought (above 80) or oversold (below 20) areas to time reversals."
    },
}

INDICATOR_CATEGORIES = {
    "Trend Indicator": "Identifies market direction.",
    "Trend / Momentum Indicator": "Measures trend strength and direction.",
    "Momentum Oscillator": "Identifies overbought or oversold levels.",
    "Volatility Indicator": "Measures price fluctuation range.",
    "Volume Indicator": "Confirms trend strength via activity.",
}

# Get a logger for this script
logger = logging.getLogger(__name__)


def main():
    try:
        load_config()
    except FileNotFoundError as e:
        logger.error(f'Failed to load config: {e}')
        return

    parser = argparse.ArgumentParser()

    parser.add_argument('ticker1', nargs='?', metavar='TICKER1', 
                        help='first or only ticker (or special MMRI ticker)')
    parser.add_argument('ticker2', nargs='?', metavar='TICKER2', 
                        help='second ticker for ratio plot')
    parser.add_argument('-a', '--atr', action='store_true',
                        help='display ATR indicator (Average True Range)')
    parser.add_argument('-A', '--atr-only', action='store_true',
                        help='display only ATR indicator')
    parser.add_argument('-b', '--bollinger', action='store_true',
                        help='display Bollinger Bands indicator')
    parser.add_argument('-f', '--mfi', action='store_true',
                        help='display MFI indicator (Money Flow Index)')
    parser.add_argument('-F', '--mfi-only', action='store_true',
                        help='display only MFI indicator')
    parser.add_argument('-i', '--indicator-info', action='store_true',
                        help='show indicator information')
    parser.add_argument('-m', '--macd', action='store_true',
                        help='display MACD indicator (Moving Average Convergence Divergence)')
    parser.add_argument('-M', '--macd-only', action='store_true',
                        help='display only MACD indicator')
    parser.add_argument('-n', '--no-cache', action='store_true',
                        help='bypass cache and get latest data')
    parser.add_argument('-o', '--obv', action='store_true',
                        help='display OBV indicator (On-Balance Volume)')
    parser.add_argument('-O', '--obv-only', action='store_true',
                        help='display only OBV indicator')
    parser.add_argument('-r', '--rsi', action='store_true',
                        help='display RSI indicator (Relative Strength Index)')
    parser.add_argument('-R', '--rsi-only', action='store_true',
                        help='display only RSI indicator')
    parser.add_argument('-s', '--stoch', action='store_true',
                        help='display Stochastics indicator')
    parser.add_argument('-S', '--stoch-only', action='store_true',
                        help='display only Stochastics indicator')
    parser.add_argument('-v', '--version', action='version', 
                        version=f'%(prog)s {__version__}')
    parser.add_argument('-w', '--volume', action='store_true',
                        help='display volume')
    parser.add_argument('-W', '--volume-only', action='store_true',
                        help='display only volume')
    parser.add_argument('-y', '--years', type=int, default=CONFIG['plot']['years_to_plot'],
                        help='set years to plot, use 0 for ytd (default: 1)')
    args = parser.parse_args()

    ticker1, ticker2, plot_name = get_tickers_and_plot_name(args)

    if args.indicator_info:
        # User asked for indicator information
        print_indicator_info()
        return
    elif not ticker1:
        # User did not ask for information nor provide a ticker
        parser.print_usage()
        logger.error(f'Please provide a ticker or use -i for indicator information')
        return
    elif ticker2 and (args.volume or args.volume_only):
        logger.error(f'Volume not available for ratio plot')
        return
    elif ticker2 and (args.mfi or args.mfi_only):
        logger.error(f'MFI indicator not available for ratio plot')
        return
    elif ticker2 and (args.stoch or args.stoch_only):
        logger.error(f'Stochastics indicator not available for ratio plot')
        return
    elif ticker2 and (args.atr or args.atr_only):
        logger.error(f'ATR indicator not available for ratio plot')
        return
    elif ticker2 and (args.obv or args.obv_only):
        logger.error(f'OBV indicator not available for ratio plot')
        return

    main_ind = 'bb' if args.bollinger else 'ma'
    xtra_ind = []
    if args.volume or args.volume_only: xtra_ind.append('vol')
    if args.macd or args.macd_only: xtra_ind.append('macd')
    if args.rsi or args.rsi_only: xtra_ind.append('rsi')
    if args.mfi or args.mfi_only: xtra_ind.append('mfi')
    if args.stoch or args.stoch_only: xtra_ind.append('stoch')
    if args.atr or args.atr_only: xtra_ind.append('atr')
    if args.obv or args.obv_only: xtra_ind.append('obv')

    try:
        df1, df2 = get_data(ticker1, ticker2, no_cache=args.no_cache)
    except KeyError as e:
        logger.error(f'Invalid ticker: {e}')
    except (requests.exceptions.RequestException,
            curlreqs.exceptions.RequestException) as e:
        logger.error(f'Network error: {e}')
    except AssertionError as e:
        logger.error(f'Assert failed: {e}')
    except Exception as e:
        logger.exception(f'Unexpected error: {e}')
    else:
        df = process_data(df1, df2, args.years, plot_name, main_ind, xtra_ind)
        if args.volume_only:
            plot_data(df, plot_name, 'vol')
        elif args.macd_only:
            plot_data(df, plot_name, 'macd')
        elif args.rsi_only:
            plot_data(df, plot_name, 'rsi')
        elif args.mfi_only:
            plot_data(df, plot_name, 'mfi')
        elif args.stoch_only:
            plot_data(df, plot_name, 'stoch')
        elif args.atr_only:
            plot_data(df, plot_name, 'atr')
        elif args.obv_only:
            plot_data(df, plot_name, 'obv')
        else:
            num_ind = len(xtra_ind)
            ratio = CONFIG['plot']['indicator_height_ratio']
            if num_ind > 2:
                logger.error(f'A maximum of two indicators can be displayed')
            elif num_ind == 2:
                plot_data(df, plot_name, main_ind, 1-2*ratio)
                plot_data(df, plot_name, xtra_ind[0], ratio)
                plot_data(df, plot_name, xtra_ind[1], ratio)
            elif num_ind == 1:
                plot_data(df, plot_name, main_ind, 1-ratio)
                plot_data(df, plot_name, xtra_ind[0], ratio)
            else:
                plot_data(df, plot_name, main_ind)


def get_tickers_and_plot_name(args):
    ticker1 = args.ticker1.upper() if args.ticker1 else None
    ticker2 = args.ticker2.upper() if args.ticker2 else None
    plot_name = None

    if ticker1 and ticker2:
        # Plot the ratio between ticker1 and ticker2
        plot_name = ticker1 + ' vs ' + ticker2
    elif ticker1:
        plot_name = ticker1
        if ticker1 == 'MMRI':
            # Special "ticker" to plot the Mannarino Market Risk Indicator
            # MMRI = DX * 10Y / 1.61
            ticker1 = 'DX=F'
            ticker2 = '^TNX'  # '10Y=F' has no historical data

    return ticker1, ticker2, plot_name


def get_data(ticker1, ticker2, no_cache=False):
    cache_enable = CONFIG['cache']['enable']
    cache_expiry = CONFIG['cache']['expiry']
    fetch_data = True
    df2 = pd.DataFrame()
    cache1 = Path(f'{CACHE_DIR}/{ticker1.lower()}.csv') if ticker1 else None
    cache2 = Path(f'{CACHE_DIR}/{ticker2.lower()}.csv') if ticker2 else None

    if cache_enable and not no_cache:
        fetch_data = False
        now = time.time()

        if cache1.is_file() and (now - cache1.stat().st_mtime < cache_expiry):
            logger.info(f'Getting {ticker1} data from cache')
            df1 = pd.read_csv(cache1, parse_dates=['date'])
            df1.set_index('date', inplace=True)
        else:
            fetch_data = True
        
        if ticker2:
            if cache2.is_file() and (now - cache2.stat().st_mtime < cache_expiry):
                logger.info(f'Getting {ticker2} data from cache')
                df2 = pd.read_csv(cache2, parse_dates=['date'])
                df2.set_index('date', inplace=True)
            else:
                fetch_data = True

    if fetch_data:
        logger.info('Getting ticker(s) data from Yahoo Finance')
        tickers = [ticker1, ticker2] if ticker2 else [ticker1]       
        tickers = Ticker(tickers)

        df = tickers.history(period='10y', interval='1d')
        df1 = df.loc[ticker1]
        if cache_enable: df1.to_csv(cache1, index=True)

        if ticker2:
            df2 = df.loc[ticker2]
            if cache_enable: df2.to_csv(cache2, index=True)

    # Make sure all dates have the same format (remove time from last date)
    # normalize() sets the time to midnight while keeping pandas dates types
    df1.index = pd.to_datetime(df1.index,utc=True,format='ISO8601').normalize()
    df2.index = pd.to_datetime(df2.index,utc=True,format='ISO8601').normalize()
    assert df1.index.is_unique, f'Duplicate date for {ticker1}'
    assert df2.index.is_unique, f'Duplicate date for {ticker2}'
    df1 = df1.groupby(df1.index).last()  # Make sure there are no duplicates
    df2 = df2.groupby(df2.index).last()

    return df1, df2


def process_data(df1, df2, years, plot_name, main_ind = 'ma' , xtra_ind = []):
    if df2.empty:
        # Only one ticker has been provided, so this is the data to plot
        df = df1
    else:
        # Two tickers has been provided, so compute the ratios between them
        # Align the indices by finding dates present in both DataFrames
        dates = df1.index.unique().intersection(df2.index)

        # Extract the series for 'adjclose' only for the common dates
        values1 = df1.loc[dates, 'adjclose']
        values2 = df2.loc[dates, 'adjclose']

        # Filter out dates where values are not positive
        valid_mask = (values1 > 0) & (values2 > 0)
        values1 = values1[valid_mask]
        values2 = values2[valid_mask]

        # Calculate the values using vectorized operations
        if plot_name == 'MMRI':
            values = (values1 * values2) / 1.61
        else:
            values = values1 / values2

        df = values.to_frame('adjclose')

    # Calculate and add columns for requested indicators
    if 'ma' in main_ind: df = add_moving_averages(df)
    if 'bb' in main_ind: df = add_bollinger_bands(df)
    if 'macd' in xtra_ind: df = add_macd(df)
    if 'rsi' in xtra_ind: df = add_rsi(df)

    if 'low' in df.columns:
        # Indicators N/A for ratio plots (OHLC prices and/or volume required)
        if 'mfi' in xtra_ind: df = add_mfi(df)
        if 'stoch' in xtra_ind: df = add_stochastics(df)
        if 'atr' in xtra_ind: df = add_atr(df)
        if 'obv' in xtra_ind: df = add_obv(df)

    # Keep only the data range to be plotted (use pandas dates types)
    today = pd.Timestamp.now(tz='UTC').normalize()
    
    if years == 0:
        start_day = today.replace(month=1, day=1)  # ytd plot
    else:
        start_day = today.replace(year=today.year - years)

    df = df[df.index >= start_day]
    
    logger.debug(f'today is {today}')
    logger.debug(f'start_day is {start_day}')

    return df


def plot_data(df, plot_name, plot_type, height_ratio=1):
    # Display the plot in the terminal
    dates = df.index.tolist()
    
    if plot_type == 'vol':
        volume = df['volume'].tolist()
        all_values = volume
    elif plot_type == 'macd':
        macd = df['macd'].tolist()
        signal = df['signal'].tolist()
        histogram = df['histogram'].tolist()
        all_values = macd + signal + histogram
    elif plot_type == 'rsi':
        rsi = df['rsi'].tolist()
        ob_level = CONFIG['rsi']['overbought_level']
        os_level = CONFIG['rsi']['oversold_level']
        overbought = [ob_level] * len(dates)
        oversold = [os_level] * len(dates)
        # The '+5' and '-5' are to make sure the overbought/sold lines are shown
        all_values = rsi + [ob_level+5] + [os_level-5]
    elif plot_type == 'mfi':
        mfi = df['mfi'].tolist()
        ob_level = CONFIG['mfi']['overbought_level']
        os_level = CONFIG['mfi']['oversold_level']
        overbought = [ob_level] * len(dates)
        oversold = [os_level] * len(dates)
        all_values = mfi + [ob_level+5] + [os_level-5]
    elif plot_type == 'stoch':
        stoch_k = df['stoch_k'].tolist()
        stoch_d = df['stoch_d'].tolist()
        ob_level = CONFIG['stoch']['overbought_level']
        os_level = CONFIG['stoch']['oversold_level']
        overbought = [ob_level] * len(dates)
        oversold = [os_level] * len(dates)
        all_values = stoch_k + stoch_d + [ob_level+5] + [os_level-5]
    elif plot_type == 'atr':
        atr = df['atr'].tolist()
        all_values = atr
    elif plot_type == 'obv':
        obv = df['obv'].tolist()
        all_values = obv
    elif plot_type == 'bb':
        close = df['adjclose'].tolist()
        sma = df['sma'].tolist()
        upper = df['upper'].tolist()
        lower = df['lower'].tolist()
        all_values = close + sma + upper + lower
    else:  # Main plot with moving averages
        close = df['adjclose'].tolist()
        ma1 = df['ma1'].tolist()
        ma2 = df['ma2'].tolist()
        ma3 = df['ma3'].tolist()
        all_values = close + ma1 + ma2 + ma3
        
    fig = plotille.Figure()
    fig.y_ticks_fkt = get_y_tick

    # Determine the dimensions and limits of the plot
    fig.width = shutil.get_terminal_size()[0] - 21
    fig.height = math.floor(shutil.get_terminal_size()[1] * height_ratio) - 5
    fig.set_x_limits(dates[0], dates[-1])

    # set_y_limits() needs min and max to be different, so ensure it's the case.
    # Otherwise volume indicator will fail if all values are 0, e.g. for cad=x.
    min_y = min(all_values)
    max_y = max(all_values)
    if min_y == max_y: max_y = min_y + 1
    fig.set_y_limits(min_y, max_y)

    # Eventually get more color choices, but beware of compatibility issues
    # https://github.com/tammoippen/plotille/blob/master/plotille/_colors.py
    # https://en.wikipedia.org/wiki/ANSI_escape_code#3-bit_and_4-bit
    #fig.color_mode = 'rgb'

    # Prepare the plots and text to display
    main_line_color = CONFIG['plot']['colors']['main_line']
    overbought_color = CONFIG['plot']['colors']['overbought']
    oversold_color = CONFIG['plot']['colors']['oversold']
    if plot_type == 'vol':
        fig.plot(dates, volume, lc=main_line_color)
        last = f'{volume[-1]:,.0f}'
        text = f'Volume last value: {last}'
    elif plot_type == 'macd':
        fig.plot(dates, signal, lc=CONFIG['macd']['colors']['signal'])
        fig.plot(dates, macd, lc=main_line_color)
        fig.plot(dates, histogram, lc=CONFIG['macd']['colors']['histogram'])
        last = f'{histogram[-1]:,.2f}'
        text = f'MACD histogram last value: {last}'
    elif plot_type == 'rsi':
        fig.plot(dates, overbought, lc=overbought_color)
        fig.plot(dates, oversold, lc=oversold_color)
        fig.plot(dates, rsi, lc=main_line_color)
        last = f'{rsi[-1]:,.2f}'
        text = f'RSI last value: {last}'
    elif plot_type == 'mfi':
        fig.plot(dates, overbought, lc=overbought_color)
        fig.plot(dates, oversold, lc=oversold_color)
        fig.plot(dates, mfi, lc=main_line_color)
        last = f'{mfi[-1]:,.2f}'
        text = f'MFI last value: {last}'
    elif plot_type == 'stoch':
        fig.plot(dates, overbought, lc=overbought_color)
        fig.plot(dates, oversold, lc=oversold_color)
        fig.plot(dates, stoch_k, lc=CONFIG['stoch']['colors']['k_line'])
        fig.plot(dates, stoch_d, lc=CONFIG['stoch']['colors']['d_line'])
        last = f'{stoch_d[-1]:,.2f}'
        text = f'Stochastics last value: {last}'
    elif plot_type == 'atr':
        fig.plot(dates, atr, lc=main_line_color)
        last = f'{atr[-1]:,.2f}'
        text = f'ATR last value: {last}'
    elif plot_type == 'obv':
        fig.plot(dates, obv, lc=main_line_color)
        last = f'{obv[-1]:,.0f}'
        text = f'OBV last value: {last}'
    elif plot_type == 'bb':
        fig.plot(dates, sma, lc=CONFIG['bb']['colors']['sma'])
        fig.plot(dates, close, lc=main_line_color)
        fig.plot(dates, upper, lc=CONFIG['bb']['colors']['upper_band'])
        fig.plot(dates, lower, lc=CONFIG['bb']['colors']['lower_band'])
        last = f'{close[-1]:.4f}' if close[-1] < 10 else f'{close[-1]:,.2f}'
        change = f'{(close[-1] / close[0] - 1) * 100:+.0f}'
        text = f'{plot_name} last value: {last} ({change}%)'
    else:  # Main plot with moving averages
        fig.plot(dates, ma3, lc=CONFIG['ma']['colors']['ma_3'])
        fig.plot(dates, ma2, lc=CONFIG['ma']['colors']['ma_2'])
        fig.plot(dates, ma1, lc=CONFIG['ma']['colors']['ma_1'])
        fig.plot(dates, close, lc=main_line_color)
        last = f'{close[-1]:.4f}' if close[-1] < 10 else f'{close[-1]:,.2f}'
        change = f'{(close[-1] / close[0] - 1) * 100:+.0f}'
        text = f'{plot_name} last value: {last} ({change}%)'

    # Display the last value text
    x = dates[0] + (dates[-1] - dates[0]) * 0.55
    y = min(all_values)
    fig.text([x], [y], [text], lc=CONFIG['plot']['colors']['text'])

    print(fig.show(legend=False))


def get_y_tick(min_, max_):
    tick = ''
    
    # Make sure we don't exceed 10 characters
    if min_ > 9999999999:
        tick = min_            # Leave the tick in scientific notation
    elif min_ > 999999.99:
        tick = f'{min_:.4e}'   # Convert the tick to scientific notation
    elif min_ < 10:
        tick = f'{min_:.4f}'   # Show 4 decimals
    else:
        tick = f'{min_:,.2f}'  # Show 2 decimals and thousands separator

    return tick


def add_moving_averages(df):
    # Calculate and add moving averages
    df = df.copy()
    df['ma1'] = df['adjclose'].rolling(window=CONFIG['ma']['ma_1'], min_periods=1).mean()
    df['ma2'] = df['adjclose'].rolling(window=CONFIG['ma']['ma_2'], min_periods=1).mean()
    df['ma3'] = df['adjclose'].rolling(window=CONFIG['ma']['ma_3'], min_periods=1).mean()
    return df
    

def add_macd(df):
    # Calculate and add MACD indicator (Moving Average Convergence Divergence)
    df = df.copy()
    fast = df['adjclose'].ewm(span=CONFIG['macd']['fast_len'], adjust=False).mean()
    slow = df['adjclose'].ewm(span=CONFIG['macd']['slow_len'], adjust=False).mean()
    df['macd'] = fast - slow
    df['signal'] = df['macd'].ewm(span=CONFIG['macd']['signal_len'], adjust=False).mean()
    df['histogram'] = df['macd'] - df['signal']
    return df
    

def add_rsi(df):
    # Calculate and add RSI indicator (Relative Strength Index)
    # Calculate the average gain and average loss using Wilder's Smoothing
    # We use a 'com' span of period-1 to match the standard RSI calculation
    df = df.copy()
    period = CONFIG['rsi']['period']
    delta = df['adjclose'].diff()       # Difference from the previous day
    gain = delta.where(delta > 0, 0)    # Keep gains and replace losses with 0
    loss = -delta.where(delta < 0, 0)   # keep -losses and replace gains with 0
    avg_gain = gain.ewm(com=period-1, adjust=False).mean()  # Average gain
    avg_loss = loss.ewm(com=period-1, adjust=False).mean()  # Average loss
    rs = avg_gain / (avg_loss + 1e-10)  # RS (avoid division by zero)
    df['rsi'] = 100 - (100 / (1 + rs))  # RSI (normalize to a scale of 0 to 100)
    return df


def add_mfi(df):
    # Calculate and add MFI indicator (Money Flow Index)
    df = df.copy()
    period = CONFIG['mfi']['period']
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    money_flow = typical_price * df['volume']
    delta = typical_price.diff()  # Difference from the previous day
    pos_mf = money_flow.where(delta > 0, 0)  # Positive money flow
    neg_mf = money_flow.where(delta < 0, 0)  # Negative money flow
    avg_pos_mf = pos_mf.rolling(window=period, min_periods=1).mean()
    avg_neg_mf = neg_mf.rolling(window=period, min_periods=1).mean()
    mfr = avg_pos_mf / (avg_neg_mf + 1e-10)  # Avoid division by zero
    df['mfi'] = 100 - (100 / (1 + mfr))  # Normalize to a scale of 0 to 100
    return df


def add_stochastics(df):
    # Calculate and add Stochastic Oscillator indicator
    df = df.copy()
    low_min = df['low'].rolling(window=CONFIG['stoch']['k_period'], min_periods=1).min()
    high_max = df['high'].rolling(window=CONFIG['stoch']['k_period'], min_periods=1).max()
    fast_k = ((df['close'] - low_min) / (high_max - low_min)) * 100
    df['stoch_k'] = fast_k.rolling(window=CONFIG['stoch']['k_smoothing'], min_periods=1).mean()
    df['stoch_d'] = df['stoch_k'].rolling(window=CONFIG['stoch']['d_period'], min_periods=1).mean()
    return df


def add_bollinger_bands(df):
    # Calculate and add Bollinger Bands indicator
    df = df.copy()
    period = CONFIG['bb']['period']
    std_dev = CONFIG['bb']['std_dev']
    df['sma'] = df['adjclose'].rolling(window=period, min_periods=1).mean()
    std = df['adjclose'].rolling(window=period, min_periods=1).std()
    df['upper'] = df['sma'] + (std * std_dev)
    df['lower'] = df['sma'] - (std * std_dev)
    return df


def add_atr(df):
    # Calculate and add ATR indicator (Average True Range)
    df = df.copy()
    tr1 = df['high'] - df['low']                        # high - low
    tr2 = (df['high'] - df['close'].shift()).abs()      # high - previous close
    tr3 = (df['low'] - df['close'].shift()).abs()       # low - previous close
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1) # Max of the 3 components
    df['atr'] = tr.ewm(com=CONFIG['atr']['period']-1, adjust=False).mean() # Wilder's Smoothing
    return df


def add_obv(df):
    # Calculate and add OBV indicator (On-Balance Volume)
    df = df.copy()
    price_change = df['adjclose'].diff()                # Price direction
    direction = pd.Series(1, index=df.index)            # Start with 1
    direction = direction.where(price_change >= 0, -1)  # Set to -1 if dropped
    direction = direction.mask(price_change == 0, 0)    # Set to 0 if no change
    df['obv'] = (direction * df['volume']).cumsum()
    return df


def load_config():
    global CONFIG, CACHE_DIR

    app_name = 'tsigna'
    config_file = 'config.toml'

    config_dir = get_config_dir(app_name)
    CACHE_DIR = get_cache_dir(config_dir)
    user_config_file = config_dir / config_file
    default_config_file = PROJECT_ROOT / app_name / config_file

    if not user_config_file.exists():
        if default_config_file.exists():
            shutil.copy2(default_config_file, user_config_file)
            logger.debug(f'Config initialized at {user_config_file}')
        else:
            raise FileNotFoundError(f'Default config missing at {default_config_file}')
    else:
        logger.debug(f'Found config file at {user_config_file}')

    with open(user_config_file, 'rb') as f:
        CONFIG = tomllib.load(f)


def get_config_dir(app_name):
    if sys.platform == "win32":
        # Windows: Use %APPDATA% (%USERPROFILE%\AppData\Roaming)
        config_dir = Path(os.environ.get("APPDATA", "")) / app_name
    elif sys.platform == "darwin":
        # macOS: Use ~/Library/Preferences
        config_dir = Path.home() / "Library" / "Preferences" / app_name
    else:
        # Linux and other Unix-like: Use ~/.config or XDG_CONFIG_HOME if set
        config_home = os.environ.get("XDG_CONFIG_HOME", "")
        if config_home:
            config_dir = Path(config_home) / app_name
        else:
            config_dir = Path.home() / ".config" / app_name
    
    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir


def get_cache_dir(config_dir):
    cache_dir = config_dir / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def print_indicator_info():
    width = shutil.get_terminal_size()[0]
    indent = ' ' * 4
    
    # Print a section for each indicator with its description
    for name, data in INDICATOR_DESCRIPTIONS.items():
        title = plotille.color(name.upper(), fg='green')
        category = plotille.color(data['category'], fg='blue')
        description = f"{category} - {data['description']}"
        wrapper = textwrap.TextWrapper(width=width, initial_indent=indent,
                                       subsequent_indent=indent)
        description = wrapper.fill(description)
        print(f'\n{title}')
        print(description)

    # Print a section with the indicator categories descriptions
    title = plotille.color('INDICATOR CATEGORIES', fg='green')
    print(f'\n{title}')

    for category, description in INDICATOR_CATEGORIES.items():
        category = plotille.color(category, fg='blue')
        description = f'{category} - {description}'
        wrapper = textwrap.TextWrapper(width=width, initial_indent=indent,
                                       subsequent_indent=indent)
        description = wrapper.fill(description)
        print(description)

    print()


def log_data_frame(df, description = ''):
    """ This function is used only for debugging. """
    logger.debug(f'DataFrame {description}\n{df}')
    #logger.debug(f'DataFrame {description}\n{df.head(20)}')
    #logger.debug(f'DataFrame index data type: {df.index.dtype}')
    #logger.debug(f'DataFrame index class: {type(df.index)}')
    #logger.debug(f'DataFrame columns data types\n{df.dtypes}')
    #logger.debug(f'DataFrame statistics\n{df.describe()}')  # Mean, min, max...
    sys.exit()


if __name__ == '__main__':
    # Configure the root logger
    logging.basicConfig(level=logging.WARNING,
                        format='%(levelname)s - %(message)s')
    
    # Configure this script's logger
    #logger.setLevel(logging.DEBUG)

    main()
