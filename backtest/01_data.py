import pandas as pd
import requests
import time
import threading
import datetime as dt
from math import ceil
import numpy as np
from config import URL_PERP, URL_SPOT, PATH_PERP, PATH_SPOT, TIMEFRAME
from typing import List, Tuple
# Increase the number of columns displayed in pandas
pd.options.display.max_columns = 20


def get_data_binance(symbol, interval, api='PERPETUOS', start_time=None, end_time=None, limit=1000):
    """
    Fetch historical price data from Binance API for perpetual futures or spot markets.

    https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-data

    Args:
        symbol (str): Trading pair symbol (e.g., 'BTCUSDT')
        interval (str): Time interval for candles (e.g., '1m', '1h', '1d')
        api (str): API type ('PERPETUOS' or 'SPOT')
        start_time (int): Start time in milliseconds
        end_time (int): End time in milliseconds
        limit (int): Maximum number of candles to retrieve

    Returns:
        list: Candlestick data

    Ejemplo de perpetuos:
        [
          [
            1499040000000,      // Open time
            "0.01634790",       // Open
            "0.80000000",       // High
            "0.01575800",       // Low
            "0.01577100",       // Close
            "148976.11427815",  // Volume
            1499644799999,      // Close time
            "2434.19055334",    // Quote asset volume
            308,                // Number of trades
            "1756.87402397",    // Taker buy base asset volume
            "28.46694368",      // Taker buy quote asset volume
            "17928899.62484339" // Ignore.
          ]
        ]

    Ejemplo de spot:
        [
          [
            1499040000000,      // Kline open time
            "0.01634790",       // Open price
            "0.80000000",       // High price
            "0.01575800",       // Low price
            "0.01577100",       // Close price
            "148976.11427815",  // Volume
            1499644799999,      // Kline close time
            "2434.19055334",    // Quote asset volume
            308,                // Number of trades
            "1756.87402397",    // Taker buy base asset volume
            "28.46694368",      // Taker buy quote asset volume
            "0"                 // Unused field. Ignore.
          ]
        ]

    """
    url = URL_PERP + PATH_PERP if api == 'PERPETUOS' else URL_SPOT + PATH_SPOT

    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }

    if start_time:
        params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time

    response = requests.get(url, params=params)
    return response.json()


def chunk_dates(timestamp_init, timestamp_fin, frequency, workers=20, limit=999):
    """
    Split the date range into chunks for parallel processing.

    Args:
        timestamp_init (int): Initial timestamp
        timestamp_fin (int): Final timestamp
        frequency (str): Time frequency ('1s', '1m', '1h', etc.)
        workers (int): Number of worker threads
        limit (int): API request limit

    Returns:
        list: List of date chunks for each worker
    """
    # Define time multipliers for different frequencies
    frequency_multipliers = {
        '1s': 1000,
        '1m': 60000,
        '1h': 3600000,
        '4h': 14400000,
        '8h': 28800000,
        '1d': 86400000,
        '1w': 604800000,
    }

    multiplier = frequency_multipliers.get(frequency, 1)  # Default to 1 if frequency is not found

    k_requests = ceil(((timestamp_fin - timestamp_init) / multiplier) / limit)  # Number of requests needed
    step = multiplier * limit  # Step size for each request

    dates_init = [timestamp_init]  # Initial list of dates
    timestamp_provisory = timestamp_init  # Provisory timestamp

    for _ in range(k_requests):  # Loop to create the date chunks
        timestamp_provisory += step
        if timestamp_provisory > timestamp_fin:
            break
        dates_init.append(timestamp_provisory)

    return np.array_split(dates_init, workers)


def work_list_binance(list_data):
    """
    Process the raw data from Binance API into a pandas DataFrame.

    Args:
        list_data (list): Raw data from Binance API

    Returns:
        pd.DataFrame: Processed DataFrame
    """
    df = pd.DataFrame(list_data)
    df.drop([6, 9, 10, 11], axis=1, inplace=True)
    df.columns = ['time', 'o', 'h', 'l', 'c', 'v', 'v_q', 'n']
    return df


def work_download(ticker, list_periods, api, frequency, bad_request, df, limit):
    """
    Download data for a specific ticker and time periods.

    Args:
        ticker (str): Trading pair symbol
        list_periods (list): List of time periods to download
        api (str): API type ('SPOT' or 'PERPETUOS')
        frequency (str): Time frequency
        bad_request (list): List to store failed requests
        df (list): List to store successful DataFrame chunks
        limit (int): API request limit
    """
    df_provisory = []
    bad_request_provisorio = []

    for period in list_periods:
        time.sleep(0.5)
        result = get_data_binance(symbol=ticker, interval=frequency, api=api, start_time=period)

        if not result:
            bad_request_provisorio.append(period)
        else:
            result = work_list_binance(result)
            df_provisory.append(result)

    bad_request.extend(bad_request_provisorio)
    df.extend(df_provisory)


def download_data(ticker, frequency, date_init: str, date_fin: str, api='SPOT', workers=20, limit=1000):
    """
    Download historical data for a given ticker using multiple threads.

    Args:
        ticker (str): Trading pair symbol
        frequency (str): Time frequency
        date_init (str): Start date in 'YYYY-MM-DD' format
        date_fin (str): End date in 'YYYY-MM-DD' format
        api (str): API type ('SPOT' or 'PERPETUOS')
        workers (int): Number of worker threads
        limit (int): API request limit

    Returns:
        tuple: (pd.DataFrame, list) Processed DataFrame and list of bad requests
    """
    timestamp_init = int(time.mktime(dt.datetime.strptime(date_init, "%Y-%m-%d").timetuple()) * 1000)
    timestamp_fin = int(time.mktime(dt.datetime.strptime(date_fin, "%Y-%m-%d").timetuple()) * 1000)

    list_for_workers = chunk_dates(timestamp_init, timestamp_fin, frequency, workers, limit)

    df = []
    bad_requests = []

    threads = []
    for chunk in list_for_workers:
        t = threading.Thread(target=work_download, args=(ticker, chunk, api, frequency, bad_requests, df, limit))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    df = pd.concat(df, axis=0)
    df.drop_duplicates(subset='time', keep='first', inplace=True)
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)

    # index to datetime
    df.index = pd.to_datetime(df.index, unit='ms')

    return df, bad_requests


def test_data(symbol: str, tf: str, directory: str = 'data') -> List[List[str]]:
    frecuencias = {
        '1m': '1min',
        '5m': '5min',
        '15m': '15min',
        '45m': '45min',
        '1h': 'h',
        '1d': 'd',
        '1w': 'W'
    }

    file = f'{directory}/{symbol}_{tf}.feather'
    try:
        df = pd.read_feather(file).sort_index()
        df.index = pd.to_datetime(df.index, utc=True)  # Ensure index is datetime and UTC
    except FileNotFoundError:
        print(f"Error: File {file} not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    # cortar la data desde 2020
    df = df.loc['2020':]

    # Adjust the start date to the beginning of the week
    start_date = df.index.min()
    if tf == '1w':
        return check_weekly_data(df)
    else:
        return check_other_timeframes(df, tf, frecuencias[tf])

    rango_completo = pd.date_range(start=start_date, end=df.index.max(), freq=frecuencias[tf])  # Create a complete date range
    fechas_faltantes = rango_completo.difference(df.index)

    if not fechas_faltantes.empty:
        print(f"Faltan {len(fechas_faltantes)} intervalos de {tf} en el índice.")
        return find_missing_date_ranges(fechas_faltantes, tf)
    else:
        print("El índice está completo. No faltan intervalos.")
        return []


def check_weekly_data(df: pd.DataFrame) -> List[List[str]]:
    # Resample to weekly frequency, keeping only the first day of each week
    weekly_dates = df.resample('W-MON', label='left', closed='left').first().index

    # Create a complete range of weeks
    full_range = pd.date_range(start=weekly_dates.min(), end=weekly_dates.max(), freq='W-MON')

    missing_weeks = full_range.difference(weekly_dates)

    if missing_weeks.empty:
        print("El índice está completo. No faltan semanas.")
        return []
    else:
        print(f"Faltan {len(missing_weeks)} semanas en el índice.")
        return format_date_ranges([(week, week + pd.Timedelta(days=6)) for week in missing_weeks], '1w')


def check_other_timeframes(df: pd.DataFrame, tf: str, freq: str) -> List[List[str]]:
    rango_completo = pd.date_range(start=df.index.min(), end=df.index.max(), freq=freq)
    fechas_faltantes = rango_completo.difference(df.index)

    if fechas_faltantes.empty:
        print("El índice está completo. No faltan intervalos.")
        return []
    else:
        print(f"Faltan {len(fechas_faltantes)} intervalos de {tf} en el índice.")
        return find_missing_date_ranges(fechas_faltantes, tf)


def find_missing_date_ranges(fechas_faltantes: pd.DatetimeIndex, tf: str) -> List[List[str]]:
    rangos_faltantes = []
    inicio_rango = None

    for i, fecha in enumerate(fechas_faltantes):
        if inicio_rango is None:
            inicio_rango = fecha

        if i == len(fechas_faltantes) - 1 or fechas_faltantes[i + 1] - fecha > pd.Timedelta(tf):
            fin_rango = fecha
            if fin_rango - inicio_rango >= pd.Timedelta(tf):
                rangos_faltantes.append((inicio_rango, fin_rango))
            inicio_rango = None

    print(f"Se encontraron {len(rangos_faltantes)} rangos de fechas faltantes:")

    return format_date_ranges(rangos_faltantes, tf)


def format_date_ranges(rangos_faltantes: List[Tuple[pd.Timestamp, pd.Timestamp]], tf: str) -> List[List[str]]:
    formatted_ranges = []
    for inicio, fin in rangos_faltantes:
        inicio_str = inicio.strftime('%Y-%m-%d %H:%M:%S')
        fin_str = (fin + pd.Timedelta(tf)).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Desde {inicio_str} hasta {fin_str}")
        formatted_ranges.append([inicio_str, fin_str])
    return formatted_ranges


if __name__ == '__main__':
    symbol = 'BTCUSDT'
    interval = '1h'
    # # interval = '1w'

    """ DATA RECIENTE """
    # data = get_data_binance(symbol=symbol, interval=interval)
    # print(data)

    """ DATA HISTORICA """
    # start_time = time.time()
    # data = download_data(symbol, interval, date_init='2017-01-01', date_fin='2024-10-13', api='SPOT')
    # df = data[0]
    # bad_requests = data[1]
    # print(df)
    # df.to_feather(f'data/{symbol}_{interval}.feather')  # Save the data to a feather file for faster loading
    # print(f"--- {time.time() - start_time:.2f} seconds ---")

    """ TEST DE DATA COMPLETA """
    test_data(symbol, interval)