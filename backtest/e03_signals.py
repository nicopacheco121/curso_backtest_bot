import numpy as np
import pandas as pd

def add_signals(df, adx_level, rsi_level_long, rsi_level_short, distance_ma):
    """
    Si el ADX esta por encima del adx_level, estamos en tendencia. Usamos distance_ma.
        Si el cruce de ema es mayor a distance_ma == LONG
        Sl el cruce de ema es negativo y el valor absoluto es mayor a distance_ma == SHORT

    Si el ADX esta por debajo del adx_level, estamos en tendencia lateral. Usamos el RSI
        Si el RSI es mayor a rsi_level_long == LONG
        Si el RSI es menor a rsi_level_short == SHORT

    :param df:
    :param adx_level: int
    :param rsi_level_long: float
    :param rsi_level_short: float
    :param distance_ma: float
    :return: df con las señales de LONG y SHORT
    """

    # Create conditions for trend signals
    trend_long_condition = (df['ADX'] > adx_level) & (df['cruce'] > distance_ma)
    trend_short_condition = (df['ADX'] > adx_level) & (df['cruce'] < -distance_ma)

    # Create conditions for lateral trend signals
    lateral_long_condition = (df['ADX'] <= adx_level) & (df['rsi'] < rsi_level_long)
    lateral_short_condition = (df['ADX'] <= adx_level) & (df['rsi'] > rsi_level_short)

    # Combine all conditions using numpy.where()
    df['signal'] = np.where(trend_long_condition, 'LONG',
                            np.where(trend_short_condition, 'SHORT',
                                     np.where(lateral_long_condition, 'LONG',
                                              np.where(lateral_short_condition, 'SHORT', ''))))

    return df
