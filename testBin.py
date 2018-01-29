from binance.client import Client

from binance.enums import *
import ccxt
import time
MELONA_FACTOR = 0.07
HIGH_SELL_FACTOR = 0.9
LOW_SELL_FACTOR = 0.45
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
trace = []

for i in all_products:
   symbol = i['symbol']
   if 'BTC' in symbol and 'USDT' not in symbol:
       btc_product.append(i)

while True:
   now = time.localtime()
   s = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
   print(s)
   for i in btc_product:
       history = client.get_historical_klines(i['symbol'], Client.KLINE_INTERVAL_1HOUR, "4 hour ago UTC")
       if len(history) == 4:
           start = float(history[0][3])
           end = float(history[2][2])
           up = end - start

           if isPos(history[0]) and isPos(history[1]) and isPos(history[2]) and not isPos(history[3]):
               if up > float(start) * MELONA_FACTOR:
                   print(i['symbol'], up, float(start) * MELONA_FACTOR)
                   print("BUY : ", up * RETRACEMENT + start, start, end)
                   info = [i['symbol'], up * RETRACEMENT + start, end]
                   trace.append(info)
       else:
           print("num of history is not 4 : ", len(history))

   print("product search done")

   for i in trace:
       nowPrice = getNowPrice(client, i[0])
       if nowPrice >= i[2] * HIGH_SELL_FACTOR:
           print(i[0], "GOOD SELL : ", nowPrice, nowPrice - i[1])
           trace.remove(i)
       if nowPrice <= i[2] * LOW_SELL_FACTOR:
           print(i[0], "BAD SELL : ", nowPrice, nowPrice - i[1])
           trace.remove(i)

   print("trace done")
   time.sleep(60)


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

