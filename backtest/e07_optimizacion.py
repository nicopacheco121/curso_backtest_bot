"""
Vamos a hacer optimizacion de los parametros con optimizacion bayesiana
"""
from backtest import run

import numpy as np
import pandas as pd
from skopt import gp_minimize
from skopt.space import Real, Integer
from skopt.utils import use_named_args
from tqdm import tqdm
from colorama import Fore, Style

# Define the parameter space
space = [
    Integer(10, 60, name='adx_level'),
    Integer(10, 40, name='rsi_level_long'),
    Integer(60, 90, name='rsi_level_short'),
    Integer(11, 100, name='ema_slow'),
    Integer(5, 10, name='ema_fast'),
    Real(0.001, 0.1, name='distance_ma'),
    Real(0.001, 0.1, name='sl'),
    Real(0.001, 0.1, name='tp')
]

symbol = 'ETHUSDT'
df_week = pd.read_feather(f'data/{symbol}_1w.feather')
df = pd.read_feather(f'data/{symbol}_1h.feather')
start_date = '2020-01-01'
fee = 0.05 / 100

# Definir el porcentaje para entrenamiento (por ejemplo, 80%)
train_percentage = 0.8
# index desde start_date
index_total = df.index
index_total = index_total[index_total >= start_date]
# corte de train
cutoff_index = int(train_percentage * len(index_total))
cutoff_date = index_total[cutoff_index]

# Dividir los datos en conjuntos de entrenamiento y testeo
df_week_train = df_week[df_week.index <= cutoff_date]
df_train = df[df.index <= cutoff_date]


print(f"Conjunto de entrenamiento:")
print(f"  Fecha de inicio: {start_date}")
print(f"  Fecha de fin: {cutoff_date}")
print(f"Conjunto de prueba:")
print(f"  Fecha de inicio: {cutoff_date}")
print(f"  Fecha de fin: {df.index[-1]}")


# Define the objective function
@use_named_args(space)
def objective(**params):
    # Add fixed parameters
    params['data_week'] = df_week_train  # Assume df_week is defined elsewhere
    params['data'] = df_train  # Assume df is defined elsewhere
    params['start_date'] = start_date  # Assume start_date is defined elsewhere
    params['fee'] = fee  # Assume fee is defined elsewhere

    # Run the backtest
    result = run(**params)

    # We want to maximize the return, so we return the negative value
    return -result

n_calls = 20
# Inicializa la barra de progreso
pbar = tqdm(total=n_calls, desc=Fore.GREEN + "Optimización")

def progress_callback(res):
  pbar.update(1)

res_gp = gp_minimize(objective, space, n_calls=n_calls, random_state=0, callback=[progress_callback])
pbar.close()

# Print the best parameters and corresponding performance
best_parametros = {name: res_gp.x[i] for i, name in enumerate(['adx_level', 'rsi_level_long', 'rsi_level_short', 'ema_slow', 'ema_fast', 'distance_ma', 'sl', 'tp'])}
print(f"Best parameters: {best_parametros}")
print(f"Best annualized return: {-res_gp.fun}")


# Test the best parameters on the test set
test_params = best_parametros.copy()
test_params['data_week'] = df_week
test_params['data'] = df
test_params['start_date'] = cutoff_date
test_params['fee'] = fee

test_result = run(**test_params)
print(f"Rendimiento anualizado en el conjunto de prueba: {test_result}")