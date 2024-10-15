import pandas as pd
import numpy as np
import pprint

def stats(trades):
    """

    :param trades:
    :return:
    """

    # Calcular ratio ganancia/pérdida
    trades['is_profit'] = trades['pnl_neto'] > 0  # si es profit el valor es True, si no, False
    total_profit = trades[trades['is_profit']]['pnl_neto'].sum()  # sumo los profit, SIMULO ORDEN FIJA
    total_loss = abs(trades[~trades['is_profit']]['pnl_neto'].sum())  # con ~ niego la condicion, es decir, si no es profit
    profit_loss_ratio = total_profit / total_loss if total_loss != 0 else np.inf  # si total_loss es 0, devuelvo infinito

    # Calcular porcentaje de trades ganadores
    win_rate = (trades['is_profit'].sum() / len(trades)) * 100  # trades ganadores / total trades

    # Calcular esperanza matemática (expectancy)
    avg_win = trades[trades['is_profit']]['pnl_neto'].mean()
    avg_loss = trades[~trades['is_profit']]['pnl_neto'].mean()
    expectancy = avg_win * win_rate + avg_loss * (100 - win_rate)

    # Calcular drawdown
    trades['cumulative_pnl'] = trades['pnl_neto'].cumsum()
    trades['running_max'] = trades['cumulative_pnl'].cummax()  # va guardando el máximo de la serie
    trades['drawdown'] = trades['running_max'] - trades['cumulative_pnl']  # drawdown es la diferencia entre el máximo y el actual
    max_drawdown = trades['drawdown'].max()  # el máximo drawdown

    # Calcular fechas de inicio y fin del MaxDD
    max_dd_end = trades.loc[trades['drawdown'] == max_drawdown, 'time_close'].iloc[0]
    max_dd_start = trades.loc[trades['cumulative_pnl'] == trades.loc[
        trades['time_close'] <= max_dd_end, 'running_max'].max(), 'time_close'].iloc[0]

    # Calcular máximo de trades consecutivos ganadores y perdedores
    trades['streak'] = (trades['is_profit'] != trades['is_profit'].shift()).cumsum()  # si el valor actual es distinto al anterior, sumo 1
    win_streaks = trades[trades['is_profit']].groupby('streak').size()  # agrupo por streak y cuento cuantos hay
    lose_streaks = trades[~trades['is_profit']].groupby('streak').size()  # lo mismo para los perdedores
    max_win_streak = win_streaks.max() if not win_streaks.empty else 0  # si no hay trades ganadores devuelvo 0
    max_lose_streak = lose_streaks.max() if not lose_streaks.empty else 0  # si no hay trades perdedores devuelvo 0

    # Sharpe
    total_hours = (trades['time_close'].iloc[-1] - trades['time_open'].iloc[0]).total_seconds() / 3600
    total_return = trades['pnl_neto'].sum()
    annualized_return = (total_return / total_hours) * 24 * 365

    # Calcular volatilidad anualizada
    hourly_returns = trades['pnl_neto'] / trades['duracion']  # pnl por hora
    volatility = hourly_returns.std() * np.sqrt(24 * 365)  # desviación estándar de los retornos por hora
    # con np.sqrt multiplico por la raiz cuadrada de las horas de trading al año y obtengo la volatilidad anualizada

    sharpe = annualized_return / volatility if volatility != 0 else np.inf  # sharpe ratio

    # Calcular el factor de beneficio (Profit Factor)
    profit_factor = total_profit / abs(total_loss) if total_loss != 0 else np.inf

    metrics = {
        'profit_loss_ratio': profit_loss_ratio,
        'win_rate': win_rate,
        'esperanza_matematica': expectancy,
        'max_drawdown': max_drawdown,
        'max_dd_start': max_dd_start,
        'max_dd_end': max_dd_end,
        'max_win_streak': max_win_streak,
        'max_lose_streak': max_lose_streak,
        'sharpe': sharpe,
        'profit_factor': profit_factor,
        'total_return': total_return,
        'annualized_return': annualized_return,
    }

    return metrics

if __name__ == '__main__':
    trades = pd.read_feather('trades.feather')
    metrics = stats(trades)
    pprint.pprint(metrics)