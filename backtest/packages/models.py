# models.py

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import datetime


class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    CLOSE = "CLOSE"


@dataclass
class Signal:
    timestamp: datetime.datetime
    side: TradeSide
    price: float
    asset: str  # e.g., "BTC", "ETH", "SOL"


@dataclass
class Position:
    side: TradeSide
    entry_price: float
    quantity: float
    entry_time: datetime.datetime

    def market_value(self, market_price: float) -> float:
        return self.quantity * market_price


@dataclass
class Trade:
    entry_time: datetime.datetime
    exit_time: datetime.datetime
    side: TradeSide
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    return_pct: float
    exit_value: float

    @classmethod
    def from_position(cls, position: Position, exit_price: float, exit_time: datetime.datetime) -> "Trade":
        quantity = position.quantity
        entry_price = position.entry_price
        side = position.side

        if side == TradeSide.BUY:
            pnl = (exit_price - entry_price) * quantity
        elif side == TradeSide.SELL:
            pnl = (entry_price - exit_price) * quantity
        else:
            raise ValueError("Invalid trade side for position")

        entry_value = entry_price * quantity
        exit_value = exit_price * quantity
        return_pct = (pnl / entry_value) * 100 if entry_value != 0 else 0

        return cls(
            entry_time=position.entry_time,
            exit_time=exit_time,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            pnl=pnl,
            return_pct=return_pct,
            exit_value=exit_value,
        )