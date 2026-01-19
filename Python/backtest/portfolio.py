"""
Gestión de Portfolio
====================

Gestiona la cuenta, balance, equity y posiciones abiertas.
"""

from datetime import datetime
from typing import List, Optional
from .trade import Trade, TradeStatus


class Portfolio:
    """
    Gestiona el portfolio y la cuenta del backtesting
    """

    def __init__(
        self,
        initial_balance: float,
        leverage: int = 100,
        commission_per_lot: float = 0.0,
        spread_pips: float = 1.0
    ):
        """
        Inicializa el portfolio

        Args:
            initial_balance: Balance inicial
            leverage: Apalancamiento
            commission_per_lot: Comisión por lote
            spread_pips: Spread en pips
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.equity = initial_balance
        self.leverage = leverage
        self.commission_per_lot = commission_per_lot
        self.spread_pips = spread_pips

        # Posiciones
        self.open_trades: List[Trade] = []
        self.closed_trades: List[Trade] = []

        # Estadísticas
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.gross_profit = 0.0
        self.gross_loss = 0.0

        # Control de drawdown
        self.peak_balance = initial_balance
        self.max_drawdown = 0.0
        self.max_drawdown_percent = 0.0

        # Histórico de equity
        self.equity_curve: List[dict] = []

        # Control diario
        self.daily_trades = 0
        self.daily_profit = 0.0
        self.current_date: Optional[datetime] = None

    def add_trade(self, trade: Trade):
        """
        Añade un trade abierto al portfolio

        Args:
            trade: Trade a añadir
        """
        self.open_trades.append(trade)
        self.total_trades += 1

        # Aplicar comisión de entrada
        commission = self.commission_per_lot * trade.volume
        self.balance -= commission
        trade.commission += commission

    def update_equity(self, current_time: datetime, current_prices: dict):
        """
        Actualiza equity considerando posiciones abiertas

        Args:
            current_time: Tiempo actual
            current_prices: Dict con precios actuales {symbol: price}
        """
        floating_pl = 0.0

        for trade in self.open_trades:
            if trade.symbol in current_prices:
                # Obtener precio (bid para buy, ask para sell)
                price = current_prices[trade.symbol]

                # Actualizar profit flotante
                pip_value = self._get_pip_value(trade.symbol, trade.volume)
                trade.update_profit(price, pip_value)
                floating_pl += trade.profit

        self.equity = self.balance + floating_pl

        # Actualizar drawdown
        if self.equity > self.peak_balance:
            self.peak_balance = self.equity

        drawdown = self.peak_balance - self.equity
        drawdown_percent = (drawdown / self.peak_balance) * 100

        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
            self.max_drawdown_percent = drawdown_percent

        # Registrar equity
        self.equity_curve.append({
            "time": current_time,
            "balance": self.balance,
            "equity": self.equity,
            "floating_pl": floating_pl,
        })

    def close_trade(
        self,
        trade: Trade,
        price: float,
        time: datetime,
        reason: str = ""
    ):
        """
        Cierra un trade completamente

        Args:
            trade: Trade a cerrar
            price: Precio de cierre
            time: Tiempo de cierre
            reason: Razón del cierre
        """
        if trade not in self.open_trades:
            return

        pip_value = self._get_pip_value(trade.symbol, trade.volume)
        profit = trade.close(price, time, pip_value, reason)

        # Aplicar comisión de salida
        commission = self.commission_per_lot * trade.volume_closed
        profit -= commission
        trade.commission += commission

        # Actualizar balance
        self.balance += profit

        # Estadísticas
        if profit > 0:
            self.winning_trades += 1
            self.gross_profit += profit
        else:
            self.losing_trades += 1
            self.gross_loss += abs(profit)

        # Mover a trades cerrados
        self.open_trades.remove(trade)
        self.closed_trades.append(trade)

        # Control diario
        self.daily_trades += 1
        self.daily_profit += profit

    def partial_close_trade(
        self,
        trade: Trade,
        price: float,
        time: datetime,
        percent: float = 0.5
    ):
        """
        Cierra parcialmente un trade

        Args:
            trade: Trade a cerrar parcialmente
            price: Precio de cierre
            time: Tiempo de cierre
            percent: Porcentaje a cerrar
        """
        if trade not in self.open_trades:
            return

        pip_value = self._get_pip_value(trade.symbol, trade.volume)
        profit = trade.close_partial(price, time, pip_value, percent)

        # Aplicar comisión
        volume_closed = trade.volume * percent
        commission = self.commission_per_lot * volume_closed
        profit -= commission
        trade.commission += commission

        # Actualizar balance
        self.balance += profit

        # Estadísticas (se cuentan en el cierre final)

        # Mover SL a break even
        trade.move_to_break_even()

    def reset_daily_stats(self):
        """Resetea estadísticas diarias"""
        self.daily_trades = 0
        self.daily_profit = 0.0

    def check_daily_limits(
        self,
        max_trades: int,
        max_loss_percent: float
    ) -> bool:
        """
        Verifica si se han alcanzado límites diarios

        Args:
            max_trades: Máximo de trades por día
            max_loss_percent: Máximo de pérdida diaria en %

        Returns:
            True si se puede seguir operando
        """
        # Verificar trades
        if self.daily_trades >= max_trades:
            return False

        # Verificar pérdida diaria
        loss_percent = (abs(self.daily_profit) / self.balance) * 100
        if self.daily_profit < 0 and loss_percent >= max_loss_percent:
            return False

        return True

    def check_global_drawdown(self, max_drawdown_percent: float) -> bool:
        """
        Verifica drawdown global

        Args:
            max_drawdown_percent: Máximo drawdown permitido en %

        Returns:
            True si está dentro del límite
        """
        return self.max_drawdown_percent < max_drawdown_percent

    def get_statistics(self) -> dict:
        """
        Retorna estadísticas del portfolio

        Returns:
            Dict con estadísticas
        """
        total_closed = len(self.closed_trades)
        win_rate = (
            (self.winning_trades / total_closed * 100)
            if total_closed > 0
            else 0.0
        )

        profit_factor = (
            self.gross_profit / abs(self.gross_loss)
            if self.gross_loss != 0
            else 0.0
        )

        net_profit = self.balance - self.initial_balance
        net_profit_percent = (net_profit / self.initial_balance) * 100

        expectancy = (
            net_profit / total_closed
            if total_closed > 0
            else 0.0
        )

        return {
            "initial_balance": self.initial_balance,
            "final_balance": self.balance,
            "final_equity": self.equity,
            "net_profit": net_profit,
            "net_profit_percent": net_profit_percent,
            "total_trades": total_closed,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": win_rate,
            "gross_profit": self.gross_profit,
            "gross_loss": self.gross_loss,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_percent": self.max_drawdown_percent,
            "open_trades": len(self.open_trades),
        }

    def _get_pip_value(self, symbol: str, volume: float) -> float:
        """
        Calcula el valor de un pip

        Args:
            symbol: Símbolo
            volume: Volumen del trade

        Returns:
            Valor de un pip
        """
        # Valor simplificado: 1 pip = 0.0001
        # Para pares JPY sería 0.01
        if "JPY" in symbol:
            return 0.01 * volume * 100000
        else:
            return 0.0001 * volume * 100000

    def close_all_trades(self, price: float, time: datetime, reason: str = "Force close"):
        """
        Cierra todas las posiciones abiertas

        Args:
            price: Precio de cierre
            time: Tiempo de cierre
            reason: Razón del cierre
        """
        trades_to_close = self.open_trades.copy()
        for trade in trades_to_close:
            self.close_trade(trade, price, time, reason)
