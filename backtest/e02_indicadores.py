import pandas as pd
import ta.trend
import ta.momentum


def get_adx(df):
    data = df.copy()  # hacemos una copia para no modificar el original y evitar warnings

    # Initialize the ADX indicator
    adx_indicator = ta.trend.ADXIndicator(high=data['high'],
                                          low=data['low'],
                                          close=data['close'],
                                          window=14,
                                          fillna=False)

    # Calculate the ADX
    data['ADX'] = adx_indicator.adx()

    return data['ADX']


def get_rsi(df):
    data = df.copy()

    # Initialize the RSI indicator
    rsi_indicator = ta.momentum.RSIIndicator(close=data['close'], window=14, fillna=False)

    # Calculate the RSI
    data['RSI'] = rsi_indicator.rsi()

    return data['RSI']


def cruce_ema(df, slow, fast):
    """
    Cruce de medias exponenciales
    :param df:
    :param slow:
    :param fast:
    :return:
    """
    data = df.copy()

    data['ema_fast'] = ta.trend.EMAIndicator(close=data['close'], window=fast, fillna=False).ema_indicator()
    data['ema_slow'] = ta.trend.EMAIndicator(close=data['close'], window=slow, fillna=False).ema_indicator()

    data['cruce'] = data['ema_fast'] / data['ema_slow'] - 1

    return data['cruce']


def add_indicadores(df, parametros):
    """
    Agrega los indicadores al df
    :param df:
    :return:
    """

    data = df.copy()
    slow = parametros['ema_slow']
    fast = parametros['ema_fast']

    data['ADX'] = get_adx(data)
    data['RSI'] = get_rsi(data)
    data['cruce'] = cruce_ema(data, slow, fast)

    return data


def add_adx_to_data(df_week, df_hour):
    """
    Add the ADX to the data
    :param data:
    :return:
    """
    df_weekly_resampled = df_week['ADX'].resample('1h').ffill()  # Resample the weekly data to hourly
    df_hour['ADX'] = df_weekly_resampled.reindex(df_hour.index, method='ffill')  # Add the ADX to the hourly data

    return df_hour


def adx_strategy(df_week, df_hour):
    """
    Agrego el df_week al df_hourly
    :param df_week:
    :param df:
    :return:
    """

    df_hour = df_hour.copy()
    df_week = df_week.copy()

    df_week['ADX'] = get_adx(df_week)  # Add the ADX to the weekly data

    df_hour = add_adx_to_data(df_week, df_hour)  # Add the ADX to the hourly data

    return df_hour


if __name__ == '__main__':
    """ 
    Vamos a agregar el ADX a la data semanal, y luego lo vamos a agregar a la data horaria.
        
    https://github.com/bukosabino/ta
    """

    symbol = 'BTCUSDT'
    interval = '1w'

    # Get the data
    data_week = pd.read_feather('data/BTCUSDT_1w.feather')
    print(data_week)

    # Add the ADX to the weekly data
    data_week['ADX'] = get_adx(data_week)
    print(data_week)

    # Get the hourly data
    data_hour = pd.read_feather('data/BTCUSDT_1h.feather')
    print(data_hour)

    # Add the ADX to the hourly data
    data_hour = add_adx_to_data(data_week, data_hour)
    print(data_hour)





