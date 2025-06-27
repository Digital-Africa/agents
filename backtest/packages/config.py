# config.py

from dataclasses import dataclass
from enum import Enum


class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    CLOSE = "CLOSE"


@dataclass
class BacktestConfig:
    slippage: float = 0.001  # 0.1% slippage
    fee: float = 0.001       # 0.1% trading fee per side
    stop_loss_pct: float = 0.0  # Disabled by default
    take_profit_pct: float = 0.0  # Disabled by default
    allow_short: bool = False
    mode: str = "compound"  # or "fixed"