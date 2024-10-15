URL_SPOT = 'https://api.binance.com'
PATH_SPOT = '/api/v3/klines'
URL_PERP = 'https://fapi.binance.com'
PATH_PERP = '/fapi/v1/klines'

TIMEFRAME = '1h'

EMA_FAST = 20
EMA_SLOW = 50

SENS_EMA_FAST = list(range(1, 1000, 1))
SENS_EMA_SLOW = list(range(50, 200, 10))
SENS_RSI = list(range(14, 90, 10))

if __name__ == '__main__':
    # CUANTAS VECES CORRE EL CODIGO?
    count = 0
    for rsi in SENS_RSI:
        for ema_slow in SENS_EMA_SLOW:
            for ema_fast in SENS_EMA_FAST:
                if ema_fast >= ema_slow:
                    continue
                count += 1
    print(count)

    count = sum(1 for rsi in SENS_RSI for ema_slow in SENS_EMA_SLOW for ema_fast in SENS_EMA_FAST if ema_fast < ema_slow)
    print(count)

