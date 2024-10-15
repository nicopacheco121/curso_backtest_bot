"""
Vamos a probar si los parametros corren bien y luego vamos a probar los parametros en la serie de datos de testeo

Best annualized return: 39.786508738786615
-3.029605944560481


"""
import numpy as np
import pandas as pd



parametros = {
    'adx_level': np.int64(10), 'rsi_level_long': np.int64(23), 'rsi_level_short': np.int64(62),
    'ema_slow': np.int64(45), 'ema_fast': np.int64(10), 'distance_ma': 0.03364350986765402, 'sl': 0.032660981595814084,
    'tp': 0.08368297764744757
    ,'excel': True
}

symbol = 'ETHUSDT'
df_week = pd.read_feather(f'data/{symbol}_1w.feather')
df = pd.read_feather(f'data/{symbol}_1h.feather')
start_date = '2020-01-01'
# start_date = '2023-10-31 12:00:00'
fee = 0.05 / 100

# cortar data frame hasta 2024-01-09 18:00:00
# df = df[df.index <= '2023-10-31 12:00:00']

from backtest import run

result = run(data_week=df_week, data=df, start_date=start_date, fee=fee, **parametros)
print(result)