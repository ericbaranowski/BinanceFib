from binance.client import Client
from binance.enums import *

import ccxt
import time
MELONA_FACTOR = 0.06
HIGH_SELL_FACTOR = 0.8
LOW_SELL_FACTOR = 0.4
PROFIT = 1.03
LOSS = 0.97
RETRACEMENT = 0.6

#MODE = 15
MODE = 60

exchange = ccxt.binance()
exchange_time = exchange.public_get_time()['serverTime']
your_time = exchange.milliseconds()
binance = ccxt.binance({'verbose': True})
print('Exchange UTC time:', exchange_time, exchange.iso8601(exchange_time))
print('Your UTC time:', your_time, exchange.iso8601(your_time))

api_key = "EDT2ijcCZN2XA80qUOEYjPDdB8Y6TZUNvZ8alYy1lhlPVL1HLGmIh0pNKEcor6Iv"
api_secret = "d1fTcDdbtUIwZtx3D6ML5WXw8UjpHO7LXogwYgA3KrKgc8c51yzKxYTxGSpeOc13"
client = Client(api_key, api_secret)

#order = client.create_order(
#    symbol='EVXBTC',
#    side=SIDE_BUY,
#    type=ORDER_TYPE_LIMIT,
#    timeInForce=TIME_IN_FORCE_GTC,
#    quantity=10,
#    price='0.00020000')
def containCount(symbol, buy_trace, sell_trace):
    count = 0
    for i in buy_trace:
        if i['symbol'] == symbol:
            count = count + 1
    for i in sell_trace:
        if i['symbol'] == symbol:
            count = count + 1
    return count


def isPos(candle):
    if candle[1] < candle[4]:
        return True
    else:
        return False

def setTrace(orderId, buyPrice):
   #life time
    return False

def getNowPrice(client, symbol):
    return float(client.get_recent_trades(symbol=symbol, limit=5)[1]['price'])

def printTimestamp():
    now = time.localtime()
    s = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
    print s
    return 0

all_products = client.get_products()['data']
btc_product = []
buy_trace = []
sell_trace = []
time_count = 60

for i in all_products:
    symbol = i['symbol']
    if 'BTC' in symbol and 'USDT' not in symbol:
        btc_product.append(i)

while True:
    time_count = time_count + 1
    if time_count >= 55 :
        time_count = 0

        printTimestamp()

        for i in btc_product:
            symbol = i['symbol']
            mode_str = ""
            if MODE == 15:
                mode_str = "1 hour ago UTC"
                kline = Client.KLINE_INTERVAL_15MINUTE
            elif MODE == 60:
                mode_str = "4 hour ago UTC"
                kline = Client.KLINE_INTERVAL_1HOUR

            history = client.get_historical_klines(symbol, kline, mode_str)
            if len(history) == 4:
                start = round(float(history[0][3]), 9)
                end = round(float(history[2][2]), 9)
                up = end - start
                new_end = round(float(history[3][4]), 9)

                if up > round(float(start) * MELONA_FACTOR, 9):
                    if isPos(history[0]) and isPos(history[1]) and isPos(history[2]) and not isPos(history[3]):
                        print "3 Melona found :", symbol, "up : %.8f" % up, "factor : %.8f" % round(float(start) * MELONA_FACTOR, 9), "/ expect to buy : %.8f" % round(up * RETRACEMENT + start, 9), "/ current : %.8f" % new_end
                        if containCount(symbol, buy_trace, sell_trace) == 0:
                            #if round(up * RETRACEMENT + start, 9) < new_end:
                            print "set", symbol ,"buy trace / expect to buy : %.8f" % round(up * RETRACEMENT + start, 9), "/ current : %.8f" % new_end
                            trace = {'symbol': symbol,
                                     'start': start,
                                     'up': up,
                                     'orderId': 1,
                                     'expect_buy_price': round(up * RETRACEMENT + start, 9),
                                     'prev_high': round(end, 9),
                                     'timeout': MODE * 60 * 1}
                            buy_trace.append(trace)
                    else:
                        print "up up : ", symbol, "up : %.8f" % up, "factor : %.8f" % round(float(start) * MELONA_FACTOR, 9)
            else:
                print "num of history is not 4 : ", len(history)

        print "product search done"

    #for i in range(len(buy_trace), 0, -1):
        #orderId Trace, if success then append sell_trace
        #if timeout : cancel
    #test

    copy_trace = buy_trace
    for i in copy_trace:
        now_price = getNowPrice(client, i['symbol'])
        i['timeout'] = i['timeout'] - 1
        print "buy", i['symbol'], "timeout", i['timeout'], "/ current price : %.8f" % now_price, "/ expect to buy price : %.8f" % i['expect_buy_price']
        if now_price <= i['expect_buy_price']:
            # do low buy
            print "buy success.", i['symbol'], "/ buy price : %.8f" % now_price, "/ expect to buy price : %.8f" % i['expect_buy_price']
            i['expect_buy_price'] = now_price
            i['timeout'] = MODE * 60 * 3
            i['high_sell_price'] = max(i['up'] * HIGH_SELL_FACTOR + i['start'], i['expect_buy_price'] * PROFIT)
            i['low_sell_price'] = min(i['up'] * LOW_SELL_FACTOR + i['start'], i['expect_buy_price'] * LOSS)
            print "set sell trace.", i['symbol'], "/ expect to sell : %.8f" % i['high_sell_price']
            sell_trace.append(i)
            buy_trace.remove(i)
        elif i['timeout'] <= 0:
            print "timeout. buy", i['symbol']
            buy_trace.remove(i)

    copy_trace = sell_trace
    for i in copy_trace:
        now_price = getNowPrice(client, i['symbol'])
        i['timeout'] = i['timeout'] - 1
        #print "sell", i['symbol'], "timeout", i['timeout'], "/ current price : %.8f" % now_price, "/ expect sell high_price : %.8f" % i['high_sell_price'], "/ expect sell low_price : %.8f" % i['low_sell_price']
        if now_price >= i['high_sell_price']:
            #do high sell
            print "----------------------", i['symbol'], "GOOD SELL price :", now_price, "/ profit : %.8f" % (now_price - i['expect_buy_price'])
            sell_trace.remove(i)
        elif now_price <= i['low_sell_price']:
            print "----------------------", i['symbol'], "BAD SELL price :", now_price, "/ profit : %.8f" % (now_price - i['expect_buy_price'])
            sell_trace.remove(i)
        elif i['timeout'] <= 0:
            #if timeout : sell all
            print "timeout. sell", i['symbol']
            sell_trace.remove(i)


    time.sleep(1)

#order = client.create_test_order(
#    symbol='BNBBTC',
#    side=SIDE_BUY,
#    type=ORDER_TYPE_LIMIT,
#    timeInForce=TIME_IN_FORCE_GTC,
#    quantity=100,
#    price='0.0000001')

"""
[
    [
        1499040000000,      # Open time
        "0.01634790",       # Open
        "0.80000000",       # High
        "0.01575800",       # Low
        "0.01577100",       # Close
        "148976.11427815",  # Volume
        1499644799999,      # Close time
        "2434.19055334",    # Quote asset volume
        308,                # Number of trades
        "1756.87402397",    # Taker buy base asset volume
        "28.46694368",      # Taker buy quote asset volume
        "17928899.62484339" # Can be ignored
    ]
]
"""
