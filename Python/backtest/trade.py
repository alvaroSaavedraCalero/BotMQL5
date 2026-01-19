"""
Gestión de Operaciones (Trades)
================================

Define la estructura y comportamiento de las operaciones de trading.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TradeType(Enum):
    """Tipo de operación"""
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(Enum):
    """Estado de la operación"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIAL_CLOSE = "PARTIAL_CLOSE"


@dataclass
class Trade:
    """
    Representa una operación de trading
    """
    # Información básica
    ticket: int
    symbol: str
    trade_type: TradeType
    entry_time: datetime
    entry_price: float
    volume: float

    # Stop Loss y Take Profit
    stop_loss: float
    take_profit_partial: float
    take_profit_final: float

    # Estado
    status: TradeStatus = TradeStatus.OPEN
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None

    # Volumen gestionado
    volume_open: float = field(init=False)
    volume_closed: float = 0.0

    # Resultados
    profit: float = 0.0
    profit_pips: float = 0.0
    commission: float = 0.0
    swap: float = 0.0

    # Información adicional
    comment: str = ""
    break_even_triggered: bool = False
    partial_close_triggered: bool = False

    def __post_init__(self):
        """Inicializa volumen abierto"""
        self.volume_open = self.volume

    def update_profit(self, current_price: float, pip_value: float):
        """
        Actualiza el profit flotante

        Args:
            current_price: Precio actual del mercado
            pip_value: Valor de un pip para el símbolo
        """
        if self.status == TradeStatus.CLOSED:
            return

        if self.trade_type == TradeType.BUY:
            pips = (current_price - self.entry_price) * 10000
        else:
            pips = (self.entry_price - current_price) * 10000

        self.profit_pips = pips
        self.profit = pips * pip_value * self.volume_open

    def check_stop_loss(self, current_price: float) -> bool:
        """
        Verifica si se ha tocado el stop loss

        Args:
            current_price: Precio actual

        Returns:
            True si se tocó el SL
        """
        if self.trade_type == TradeType.BUY:
            return current_price <= self.stop_loss
        else:
            return current_price >= self.stop_loss

    def check_take_profit_partial(self, current_price: float) -> bool:
        """
        Verifica si se debe hacer cierre parcial

        Args:
            current_price: Precio actual

        Returns:
            True si se debe cerrar parcialmente
        """
        if self.partial_close_triggered:
            return False

        if self.trade_type == TradeType.BUY:
            return current_price >= self.take_profit_partial
        else:
            return current_price <= self.take_profit_partial

    def check_take_profit_final(self, current_price: float) -> bool:
        """
        Verifica si se debe hacer cierre final

        Args:
            current_price: Precio actual

        Returns:
            True si se debe cerrar completamente
        """
        if self.trade_type == TradeType.BUY:
            return current_price >= self.take_profit_final
        else:
            return current_price <= self.take_profit_final

    def close_partial(
        self,
        price: float,
        time: datetime,
        pip_value: float,
        percent: float = 0.5
    ) -> float:
        """
        Cierra parcialmente la posición

        Args:
            price: Precio de cierre
            time: Tiempo de cierre
            pip_value: Valor del pip
            percent: Porcentaje a cerrar (default 50%)

        Returns:
            Profit del cierre parcial
        """
        if self.status == TradeStatus.CLOSED:
            return 0.0

        volume_to_close = self.volume_open * percent

        # Calcular profit del cierre parcial
        if self.trade_type == TradeType.BUY:
            pips = (price - self.entry_price) * 10000
        else:
            pips = (self.entry_price - price) * 10000

        partial_profit = pips * pip_value * volume_to_close

        # Actualizar estado
        self.volume_closed += volume_to_close
        self.volume_open -= volume_to_close
        self.profit += partial_profit
        self.partial_close_triggered = True
        self.status = TradeStatus.PARTIAL_CLOSE

        return partial_profit

    def move_to_break_even(self):
        """Mueve el stop loss a break even"""
        if not self.break_even_triggered:
            self.stop_loss = self.entry_price
            self.break_even_triggered = True

    def close(
        self,
        price: float,
        time: datetime,
        pip_value: float,
        reason: str = ""
    ) -> float:
        """
        Cierra completamente la posición

        Args:
            price: Precio de cierre
            time: Tiempo de cierre
            pip_value: Valor del pip
            reason: Razón del cierre

        Returns:
            Profit del cierre
        """
        if self.status == TradeStatus.CLOSED:
            return 0.0

        # Calcular profit del volumen restante
        if self.trade_type == TradeType.BUY:
            pips = (price - self.entry_price) * 10000
        else:
            pips = (self.entry_price - price) * 10000

        final_profit = pips * pip_value * self.volume_open

        # Actualizar estado
        self.volume_closed += self.volume_open
        self.volume_open = 0.0
        self.profit += final_profit
        self.status = TradeStatus.CLOSED
        self.exit_time = time
        self.exit_price = price
        self.comment = reason

        return final_profit

    def to_dict(self) -> dict:
        """Convierte el trade a diccionario"""
        return {
            "ticket": self.ticket,
            "symbol": self.symbol,
            "type": self.trade_type.value,
            "entry_time": self.entry_time.isoformat(),
            "entry_price": self.entry_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_price": self.exit_price,
            "volume": self.volume,
            "volume_closed": self.volume_closed,
            "stop_loss": self.stop_loss,
            "profit": self.profit,
            "profit_pips": self.profit_pips,
            "status": self.status.value,
            "comment": self.comment,
        }
