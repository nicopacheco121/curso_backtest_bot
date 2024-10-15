"""
simulate_trades

Vamos a iterar.
Si no tiene posicion, verifica si el Signal es LONG o SHORT.
- Si no tiene Signal, seguimos
- Si tiene Signal, abrimos la posicion y guardamos:
    * Precio apertura
    * Fecha apertura
    * Side
    * Calculamos el stop loss
    * Calculamos el take profit

Si tiene posicion, verifica cierre por:
    - Stop loss
    - Take profit
    - Signal contrario

    Si cierra:
        Al cerrar, anota:
        * Precio cierre
        * Fecha cierre
        * Motivo

    # PODRIAMOS AGREGAR EL PNL NO REALIZADO DIA A DIA

"""

import pandas as pd

def simulate_trades(df, sl, tp, fee):
    """
    Simulate trades
    :param df:
    :param sl:
    :param tp:
    :return:
    """

    """
    Convertimos el data frame a un numpy array para iterar mas rapido
    
    Un array es una colección ordenada de elementos del mismo tipo de datos, almacenados en posiciones de memoria contiguas.
    
    Ventajas:
        Acceso rápido a los elementos (tiempo constante O(1)).
        Eficiente en uso de memoria para datos secuenciales.
    """

    df_index = df.reset_index()  # Reseteamos el index para poder acceder a la fecha
    data = df_index.to_numpy()  # Convertimos el df a un array de numpy
    columns = df_index.columns.tolist()  # Guardamos los nombres de las columnas
    column_indices = {col: columns.index(col) for col in columns}

    # VARIABLES
    last_side_used = None  # Ultimo side utilizado, para no abrir una posicion en el mismo side que acabo de cerrar
    pos_open = side = tp_price = sl_price = None
    position = {}
    trades = []

    for i in range(len(data)):  # Iteramos sobre el array
        row = data[i]  # nos quedamos con la fila i
        signal = row[column_indices['signal']]
        close = row[column_indices['close']]
        time = row[column_indices['time']]

        # Verifico si no estoy abriendo una posicion para el mismo lado a la previamente cerrada
        if last_side_used:
            if signal != last_side_used:
                last_side_used = False
            else:
                continue

        # ABRIR POSICION
        if not pos_open:
            if signal in ['LONG', 'SHORT']:
                pos_open = True
                side = signal
                tp_price = close * (1 + tp) if signal == 'LONG' else close * (1 - tp)
                sl_price = close * (1 - sl) if signal == 'LONG' else close * (1 + sl)
                position = {
                    'time_open': time,
                    'side': side,
                    'price_open': close,
                    'tp': tp_price,
                    'sl': sl_price,
                }

        # CERRAR POSICION
        else:
            close_position = False
            motivo = ''

            # VERIFICO TAKE PROFIT
            if (side == 'LONG' and close >= tp_price) or (side == 'SHORT' and close <= tp_price):
                close_position = True
                motivo = 'TP'

            # VERIFICO STOP LOSS
            if (side == 'LONG' and close <= sl_price) or (side == 'SHORT' and close >= sl_price):
                close_position = True
                motivo = 'SL'

            # VERIFICO CAMBIO DE SIDE
            if signal != side:
                close_position = True
                motivo = 'signal'

            if close_position:
                position.update({
                    'time_close': time,
                    'price_close': close,
                    'motivo': motivo,
                })

                trades.append(position)
                pos_open = False
                last_side_used = position['side']
                position = {}

    trades = pd.DataFrame(trades)

    # duracion en horas
    trades['duracion'] = (trades['time_close'] - trades['time_open']).dt.total_seconds() / 3600

    # pnl, si es long, el pnl es precio cierre / precio apertura - 1, si es short, es al reves
    # la fx lambda recibe una fila y devuelve el pnl
    # axis=1 para que recorra por filas
    trades['pnl'] = trades.apply(lambda x: x['price_close'] / x['price_open'] - 1 if x['side'] == 'LONG' else 1 - x['price_close'] / x['price_open'], axis=1)
    trades['pnl'] = trades['pnl'] * 100

    # # pnl neto
    trades['pnl_neto'] = trades.apply(
        lambda x:(x['price_close'] * (1 - fee) / (x['price_open'] * (1 + fee)) - 1) if x['side'] == 'LONG'
        else (1 - x['price_close'] * (1 + fee) / (x['price_open'] * (1 - fee))), axis=1)
    trades['pnl_neto'] = trades['pnl_neto'] * 100

    return trades




if __name__ == '__main__':
    df_signals = pd.read_feather('df_signals.feather')
    trades = simulate_trades(df_signals, sl=0.01, tp=0.02, fee=0.05/100)
    print(trades)
    trades.to_excel('trades.xlsx')
    trades.to_feather('trades.feather')