"""
Codigo principal que hace el backtest en base a los parametros que se le entregan

Parametros
- Data semanal
- Data horaria
- Nivel de ADX
- EMA slow
- EMA fast
- Nivel de cruce de EMA
- Stop loss
- Take Profit
- Start Date

"""

import pandas as pd
import e02_indicadores as ind
import e03_signals as sig
import e04_trades as trades
from e05_stats import stats


def run(**kwargs):
    df_week = kwargs['data_week']
    df = kwargs['data']
    adx_level = kwargs['adx_level']
    rsi_level_long = kwargs['rsi_level_long']
    rsi_level_short = kwargs['rsi_level_short']
    ema_slow = kwargs['ema_slow']
    ema_fast = kwargs['ema_fast']
    distance_ma = kwargs['distance_ma']
    stop_loss = kwargs['sl']
    take_profit = kwargs['tp']
    start_date = kwargs['start_date']
    fee = kwargs['fee']
    excel = kwargs.get('excel', False)

    df_week = df_week.copy()
    df = df.copy()

    """ AGREGO INDICADORES """

    df = ind.adx_strategy(df_week=df_week, df_hour=df)  # Agrego el ADX a la data horaria
    df['cruce'] = ind.cruce_ema(df, ema_slow, ema_fast)  # Agrego el cruce de EMA
    # (notar la diferencia que aca entrego una columna y en el anterior un df entero)
    df['rsi'] = ind.get_rsi(df)  # Agrego el RSI

    """ CORTO EL DATAFRAME DESDE LA FECHA DE INICIO """
    df = df.loc[start_date:]

    """ AGREGO SEÑALES """
    df = sig.add_signals(df, adx_level, rsi_level_long, rsi_level_short, distance_ma)
    if excel:
        df.to_excel('df_signals.xlsx')
    # df.to_feather('df_signals.feather')
    # print(df)


    # cantidad de señales LONG y SHORT
    k_signals = df['signal'].value_counts()
    k_long = k_signals.get('LONG', 0)
    k_short = k_signals.get('SHORT', 0)
    k_signals_total = k_long + k_short
    if k_signals_total == 0:
        # print si el signal si es LONG o SHORT
        print(
            f'adx level {adx_level}, rsi level long {rsi_level_long}, rsi level short {rsi_level_short}, ema slow {ema_slow}, ema fast {ema_fast}, distance ma {distance_ma}')

        print('No hay señales')
        return 0


    """ TRADES """
    df_trades = trades.simulate_trades(df, stop_loss, take_profit, fee)
    if excel:
        df_trades.to_excel('df_trades.xlsx')
        df_trades.to_feather('df_trades.feather')

    """ ESTADISTICAS """
    resultados = stats(df_trades)
    resultados = resultados['annualized_return']

    # rdto mas alto fue 100
    # maxdd -20
    # 0.8

    pondero_rdo = resultados['annualized_return'] / 120
    pondero_maxdd = resultados['max_drawdown'] / -20
    pondero_winrate = resultados['winrate'] / 80

    resultados = pondero_rdo * 0.8 + pondero_maxdd * 0.1 + pondero_winrate * 0.1


    print(resultados)

    return resultados



if __name__ == '__main__':
    parametros = {
        'data_week': pd.read_feather('data/BTCUSDT_1w.feather'),
        'data': pd.read_feather('data/BTCUSDT_1h.feather'),
        'adx_level': 20,
        'rsi_level_long': 30,
        'rsi_level_short': 70,
        'ema_slow': 50,
        'ema_fast': 20,
        'distance_ma': 0.01,
        'sl': 0.02,
        'tp': 0.05,
        'start_date': '2021-01-01',
        'fee': 0.05 / 100,
        'excel': False
    }

    run(**parametros)




