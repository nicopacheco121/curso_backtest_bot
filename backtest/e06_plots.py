"""
Vamos a graficar el resultado de la estrategia
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


def plot_trading_results(trades, train_start=None, train_end=None, test_start=None, test_end=None):
    """
    Crea gráficos para visualizar los resultados del trading, con opción de destacar períodos de entrenamiento y prueba.

    :param trades: DataFrame con las columnas 'time_close', 'pnl_neto', 'cumulative_pnl', 'drawdown', 'running_max'
    :param train_start: Fecha de inicio del período de entrenamiento (opcional, string en formato 'YYYY-MM-DD')
    :param train_end: Fecha de fin del período de entrenamiento (opcional, string en formato 'YYYY-MM-DD')
    :param test_start: Fecha de inicio del período de prueba (opcional, string en formato 'YYYY-MM-DD')
    :param test_end: Fecha de fin del período de prueba (opcional, string en formato 'YYYY-MM-DD')
    """

    plt.style.use('default')

    trades['cumulative_pnl'] = trades['pnl_neto'].cumsum()
    trades['running_max'] = trades['cumulative_pnl'].cummax()  # va guardando el máximo de la serie
    trades['drawdown'] = trades['running_max'] - trades[
        'cumulative_pnl']  # drawdown es la diferencia entre el máximo y el actual

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 18), sharex=True)

    # Convertir fechas a datetime si no lo son
    trades['time_close'] = pd.to_datetime(trades['time_close'])

    # Función para plotear PNL acumulado con color específico
    def plot_pnl(ax, data, color, label):
        ax.plot(data['time_close'], data['cumulative_pnl'], color=color, label=label)

    # Plotear PNL acumulado
    if all([train_start, train_end, test_start, test_end]):
        train_start = pd.to_datetime(train_start)
        train_end = pd.to_datetime(train_end)
        test_start = pd.to_datetime(test_start)
        test_end = pd.to_datetime(test_end)

        train_data = trades[(trades['time_close'] >= train_start) & (trades['time_close'] <= train_end)]
        test_data = trades[(trades['time_close'] >= test_start) & (trades['time_close'] <= test_end)]
        plot_pnl(ax1, train_data, 'blue', 'PNL Acumulado (Entrenamiento)')
        plot_pnl(ax1, test_data, 'green', 'PNL Acumulado (Prueba)')
    else:
        plot_pnl(ax1, trades, 'blue', 'PNL Acumulado')

    # Plotear Drawdown
    ax1.fill_between(trades['time_close'], trades['cumulative_pnl'], trades['running_max'],
                     where=(trades['running_max'] > trades['cumulative_pnl']),
                     color='red', alpha=0.3, label='Drawdown')
    ax1.set_title('PNL Acumulado y Máximo Drawdown')
    ax1.set_ylabel('PNL')
    ax1.legend()

    # Gráfico de PNL por trade
    ax2.bar(trades['time_close'], trades['pnl_neto'], label='PNL por Trade')
    ax2.axhline(y=0, color='r', linestyle='-', linewidth=0.5)
    ax2.set_title('PNL por Trade')
    ax2.set_ylabel('PNL')
    ax2.legend()

    # Gráfico de Drawdown
    ax3.fill_between(trades['time_close'], 0, trades['drawdown'], color='red', alpha=0.3)
    ax3.set_title('Drawdown')
    ax3.set_ylabel('Drawdown')
    ax3.set_xlabel('Fecha')

    # Configurar el formato de las fechas en el eje x
    for ax in [ax1, ax2, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())

    # Rotar y alinear las etiquetas de fecha
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Añadir líneas verticales para las fechas de inicio y fin de entrenamiento y prueba
    if train_start:
        for ax in [ax1, ax2, ax3]:
            ax.axvline(x=train_start, color='blue', linestyle='--', linewidth=1)
    if train_end:
        for ax in [ax1, ax2, ax3]:
            ax.axvline(x=train_end, color='blue', linestyle='--', linewidth=1)
    if test_start:
        for ax in [ax1, ax2, ax3]:
            ax.axvline(x=test_start, color='green', linestyle='--', linewidth=1)
    if test_end:
        for ax in [ax1, ax2, ax3]:
            ax.axvline(x=test_end, color='green', linestyle='--', linewidth=1)

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    trades = pd.read_feather('df_trades.feather')
    # Usar la función
    # plot_trading_results(trades)

    # Ejemplo de uso:
    plot_trading_results(trades,
                         train_start='2020-01-01',
                         train_end='2023-10-31',
                         test_start='2023-10-31',
                         test_end='2024-10-15')
