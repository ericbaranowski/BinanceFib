from binance.client import Client
from binance.enums import *

import os
import ccxt
import time
import numpy as np
import pandas as pd

from stockstats import StockDataFrame as Sdf

def binToDt(bin):
    ret = list()
    for v in bin:
        tmp = list()
        for i in range(0, 6):
            tmp.append(float(v[i]))
        ret.append(tmp)
    return ret

def RSI(df, base="Close", period=21):
    delta = df[base].diff()
    up, down = delta.copy(), delta.copy()

    up[up < 0] = 0
    down[down > 0] = 0

    rUp = up.ewm(com=period - 1, adjust=False).mean()
    rDown = down.ewm(com=period - 1, adjust=False).mean().abs()

    df['RSI_' + str(period)] = 100 - 100 / (1 + rUp / rDown)
    df['RSI_' + str(period)].fillna(0, inplace=True)

    return df


def EMA(df, base, target, period, alpha=False):
    """
    Function to compute Exponential Moving Average (EMA)

    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        base : String indicating the column name from which the EMA needs to be computed from
        target : String indicates the column name to which the computed data needs to be stored
        period : Integer indicates the period of computation in terms of number of candles
        alpha : Boolean if True indicates to use the formula for computing EMA using alpha (default is False)

    Returns :
        df : Pandas DataFrame with new column added with name 'target'
    """

    con = pd.concat([df[:period][base].rolling(window=period).mean(), df[period:][base]])

    if (alpha == True):
        # (1 - alpha) * previous_val + alpha * current_val where alpha = 1 / period
        df[target] = con.ewm(alpha=float(1.0 / period), adjust=False).mean()
    else:
        # ((current_val - previous_val) * coeff) + previous_val where coeff = 2 / (period + 1)
        df[target] = con.ewm(span=period, adjust=False).mean()

    df[target].fillna(0, inplace=True)
    return df

def ATR(df, period, ohlc=['Open', 'High', 'Low', 'Close']):
    """
    Function to compute Average True Range (ATR)

    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        period : Integer indicates the period of computation in terms of number of candles
        ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])

    Returns :
        df : Pandas DataFrame with new columns added for
            True Range (TR)
            ATR (ATR_$period)
    """
    atr = 'ATR_' + str(period)

    # Compute true range only if it is not computed and stored earlier in the df
    if not 'TR' in df.columns:
        df['h-l'] = df[ohlc[1]] - df[ohlc[2]]
        df['h-yc'] = abs(df[ohlc[1]] - df[ohlc[3]].shift())
        df['l-yc'] = abs(df[ohlc[2]] - df[ohlc[3]].shift())

        df['TR'] = df[['h-l', 'h-yc', 'l-yc']].max(axis=1)

        df.drop(['h-l', 'h-yc', 'l-yc'], inplace=True, axis=1)

    # Compute EMA of true range using ATR formula after ignoring first row
    EMA(df, 'TR', atr, period, alpha=True)

    return df

def SuperTrend(df, period, multiplier, ohlc=['Open', 'High', 'Low', 'Close']):
    """
    Function to compute SuperTrend

    Args :
        df : Pandas DataFrame which contains ['date', 'open', 'high', 'low', 'close', 'volume'] columns
        period : Integer indicates the period of computation in terms of number of candles
        multiplier : Integer indicates value to multiply the ATR
        ohlc: List defining OHLC Column names (default ['Open', 'High', 'Low', 'Close'])

    Returns :
        df : Pandas DataFrame with new columns added for
            True Range (TR), ATR (ATR_$period)
            SuperTrend (ST_$period_$multiplier)
            SuperTrend Direction (STX_$period_$multiplier)
    """

    ATR(df, period, ohlc=ohlc)
    atr = 'ATR_' + str(period)
    st = 'ST_' + str(period) + '_' + str(multiplier)
    stx = 'STX_' + str(period) + '_' + str(multiplier)

    """
    SuperTrend Algorithm :

        BASIC UPPERBAND = (HIGH + LOW) / 2 + Multiplier * ATR
        BASIC LOWERBAND = (HIGH + LOW) / 2 - Multiplier * ATR

        FINAL UPPERBAND = IF( (Current BASICUPPERBAND < Previous FINAL UPPERBAND) or (Previous Close > Previous FINAL UPPERBAND))
                            THEN (Current BASIC UPPERBAND) ELSE Previous FINALUPPERBAND)
        FINAL LOWERBAND = IF( (Current BASIC LOWERBAND > Previous FINAL LOWERBAND) or (Previous Close < Previous FINAL LOWERBAND)) 
                            THEN (Current BASIC LOWERBAND) ELSE Previous FINAL LOWERBAND)

        SUPERTREND = IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close <= Current FINAL UPPERBAND)) THEN
                        Current FINAL UPPERBAND
                    ELSE
                        IF((Previous SUPERTREND = Previous FINAL UPPERBAND) and (Current Close > Current FINAL UPPERBAND)) THEN
                            Current FINAL LOWERBAND
                        ELSE
                            IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close >= Current FINAL LOWERBAND)) THEN
                                Current FINAL LOWERBAND
                            ELSE
                                IF((Previous SUPERTREND = Previous FINAL LOWERBAND) and (Current Close < Current FINAL LOWERBAND)) THEN
                                    Current FINAL UPPERBAND
    """

    # Compute basic upper and lower bands
    df['basic_ub'] = (df[ohlc[1]] + df[ohlc[2]]) / 2 + multiplier * df[atr]
    df['basic_lb'] = (df[ohlc[1]] + df[ohlc[2]]) / 2 - multiplier * df[atr]

    # Compute final upper and lower bands
    df['final_ub'] = 0.00
    df['final_lb'] = 0.00
    for i in range(period, len(df)):
        df['final_ub'].iat[i] = df['basic_ub'].iat[i] if df['basic_ub'].iat[i] < df['final_ub'].iat[i - 1] or \
                                                         df['Close'].iat[i - 1] > df['final_ub'].iat[i - 1] else \
        df['final_ub'].iat[i - 1]
        df['final_lb'].iat[i] = df['basic_lb'].iat[i] if df['basic_lb'].iat[i] > df['final_lb'].iat[i - 1] or \
                                                         df['Close'].iat[i - 1] < df['final_lb'].iat[i - 1] else \
        df['final_lb'].iat[i - 1]

    # Set the Supertrend value
    df[st] = 0.00
    for i in range(period, len(df)):
        df[st].iat[i] = df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df['Close'].iat[
            i] <= df['final_ub'].iat[i] else \
            df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df['Close'].iat[i] > \
                                     df['final_ub'].iat[i] else \
                df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df['Close'].iat[i] >= \
                                         df['final_lb'].iat[i] else \
                    df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df['Close'].iat[i] < \
                                             df['final_lb'].iat[i] else 0.00

        # Mark the trend direction up/down
    df[stx] = np.where((df[st] > 0.00), np.where((df[ohlc[3]] < df[st]), 'down', 'up'), np.NaN)

    # Remove basic and final bands from the columns
    df.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)

    df.fillna(0, inplace=True)

    return df

exchange = ccxt.binance()
exchange_time = exchange.public_get_time()['serverTime']
your_time = exchange.milliseconds()
binance = ccxt.binance({'verbose': True})
print('Exchange UTC time:', exchange_time, exchange.iso8601(exchange_time))
print('Your UTC time:', your_time, exchange.iso8601(your_time))

# Add keys to .env file with command:
# echo 'export api_key="<API_KEY>"' >> .env
api_key = os.environ['api_key']
api_secret = os.environ['api_secret']
client = Client(api_key, api_secret)

all_products = client.get_products()['data']
btc_product = []
for i in all_products:
    symbol = i['symbol']
    if 'BTC' in symbol and 'USDT' not in symbol:
        btc_product.append(i)

mode_str = "12 month ago UTC"
kline = Client.KLINE_INTERVAL_30MINUTE
history = client.get_historical_klines("ETHBTC", kline, mode_str)
history = binToDt(history)

data = {
    "data": {
        "candles": history
    }
}
df = pd.DataFrame(data["data"]["candles"], columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
print df

def testStRsi(df, rsi, bandwidth, period, multiplier):
    df = RSI(df, 'Close', rsi)
    df = SuperTrend(df, period, multiplier)
    #stock = Sdf.retype(df)

    prev = "nan"
    prev_price = 0.0
    profit_target = 1.1
    stop_loss = 0.9
    cal = list()
    for index, row in df.iterrows():
        stx = 'STX_' + str(period)+ '_' + str(multiplier)
        if prev_price == 0.0 and prev == "down" and row['RSI_' + str(rsi)] >= 50 + bandwidth and row[stx] == "up":
            cal.append(["buy", row['Close']])
            prev_price = row['Close']
            #print "BUY", row['Close']
            #print "buy", exchange.iso8601(row['Date']), index, row['Close']
        elif prev_price > 0.0 and prev == "up" and row['RSI_'+ str(rsi)] <= 50 - bandwidth and row[stx] == "down":
            cal.append(["sell", row['Close']])
            prev_price = 0.0
            #print "SELL", row['Close']
        #if prev_price > 0.0:
            #print "DEBUG!!", row['Close'], prev_price * profit_target
            #if row['Close'] >= prev_price * profit_target:
                #cal.append(["sell", row['Close']])
                #prev_price = 0.0
                #print "DEBUG3", row['Close']
            #elif row['Close'] <= prev_price * stop_loss:
                #cal.append(["sell", row['Close']])
                #prev_price = 0.0
                #print "DEBUG4", row['Close']
        #if prev == "up" and row['RSI_'+ str(rsi)] >= 70 :
            #cal.append(["sell", row['Close']])
            #print "sell", exchange.iso8601(row['Date']), index, row['Close']
        prev = row[stx]

    prev = ["nan", 0.0]
    profit = 0.0
    for v in cal:
        if prev[0] == v[0]:
            continue
        if prev[0] == "buy" and v[0] == "sell":
            profit = profit + v[1] - prev[1]
        prev = v

    return profit

cnt = 0
avg = 0.0

print testStRsi(df, 7, 3, 3, 39 / 10.0)
"""
for j in range(2, 5):
    for k in range(20, 40):
        ret = testStRsi(df, 7, 3, j, k / 10.0)
        cnt = cnt + 1
        avg = avg + ret
        #if ret > 0.0:
        #if ret > df['Close'].iloc[-1] - df['Close'].iloc[0]:
        print j, k / 10.0, "%.8f"%ret
"""
cnt = 1
print "avg: ", avg / cnt, "zonber: ", df['Close'].iloc[-1] - df['Close'].iloc[0]

