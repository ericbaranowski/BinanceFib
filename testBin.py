from binance.client import Client
from binance.enums import *

import ccxt
import time
MELONA_FACTOR = 0.07
HIGH_SELL_FACTOR = 0.8
LOW_SELL_FACTOR = 0.45
PROFIT = 1.1
RETRACEMENT = 0.618

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
        if i[0] == symbol:
            count = count + 1
    for i in sell_trace:
        if i[0] == symbol:
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
    return float(client.get_recent_trades(symbol=symbol)[1]['price'])

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
        now = time.localtime()
        s = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
        print(s)

        for i in btc_product:
            symbol = i['symbol']
            history = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR, "4 hour ago UTC")
            if len(history) == 4:
                start = float(history[0][3])
                end = float(history[2][2])
                up = end - start
                new_end = float(history[3][2])

                if up > float(start) * MELONA_FACTOR:
                    if isPos(history[0]) and isPos(history[1]) and isPos(history[2]) and not isPos(history[3]):
                        print("3 Melona found : ", symbol, up, float(start) * MELONA_FACTOR)
                        if containCount(symbol, buy_trace, sell_trace) == 0:
                            if up * RETRACEMENT + start < new_end:
                                print("BUY(Limit) : ", up * RETRACEMENT + start, "Expect : ", )
                                orderId = 1
                                buy_trace.append([symbol, orderId, up * RETRACEMENT + start])
                            else:
                                print("BUY(Market) : ", new_end)
                                sell_trace.append([symbol, new_end, end])
                    #else:
                        #print("up up : ", symbol, up, float(start) * MELONA_FACTOR)
            else:
                print("num of history is not 4 : ", len(history))

        print("product search done")

    #for i in range(len(buy_trace), 0, -1):
        #orderId Trace, if success then append sell_trace
        #if timeout : cancel
    #test

    for i in xrange(len(buy_trace) - 1, -1, -1):
        now_price = getNowPrice(client, buy_trace[i][0])
        print("buy", buy_trace[i][0], now_price, buy_trace[i][2])
        if now_price >= buy_trace[i][2]:
            sell_trace.append([buy_trace[i][0], buy_trace[i][2], 0])
            del buy_trace[i]

    for i in xrange(len(sell_trace) - 1, -1, -1):
        now_price = getNowPrice(client, sell_trace[i][0])
        good_sell_price = max(sell_trace[i][2] * HIGH_SELL_FACTOR , sell_trace[i][1] * PROFIT)
        bad_sell_price = sell_trace[i][2] * LOW_SELL_FACTOR

        print("sell", sell_trace[i][0], sell_trace[i][2], now_price)
        if now_price >= good_sell_price:
            print(sell_trace[i][0], "GOOD SELL : ", now_price, now_price - sell_trace[i][1])
            del sell_trace[i]
        if now_price <= bad_sell_price:
            print(sell_trace[i][0], "BAD SELL : ", now_price, now_price - sell_trace[i][1])
            del sell_trace[i]

        #if timeout : sell all

    time.sleep(1)


#print(client.get_historical_klines("ETHBTC", Client.KLINE_INTERVAL_1HOUR, "2 hour ago UTC"))
#print(client.get_historical_klines("ETHBTC", Client.KLINE_INTERVAL_1HOUR, "1 hour ago UTC"))

#order = client.create_test_order(
#    symbol='BNBBTC',
#    side=SIDE_BUY,
#    type=ORDER_TYPE_LIMIT,
#    timeInForce=TIME_IN_FORCE_GTC,
#    quantity=100,
#    price='0.0000001')

#def findMerona():
#client.get_historical_klines("ETHBTC", Client.KLINE_INTERVAL_1HOUR, "2 hour ago UTC"))

