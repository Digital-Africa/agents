# engine.py

from dataclasses import dataclass
from typing import List, Optional
import pandas as pd

from .models import Signal, Trade, Position
from .config import TradeSide, BacktestConfig
from .metrics import compute_kpis
from .utils import apply_slippage, apply_fees

@dataclass
class BacktestResult:
    trades: List[Trade]
    equity_curve: pd.DataFrame
    kpis: dict


import pandas as pd
from typing import List, Optional
from dataclasses import dataclass

from .models import Signal, Trade, Position
from .config import BacktestConfig
from .metrics import compute_kpis
from .utils import apply_slippage, apply_fees
from collections import defaultdict


@dataclass
class BacktestResult:
    trades: List[Trade]
    equity_curve: pd.DataFrame
    kpis: dict



class BacktestEngine:
    def __init__(
        self,
        signals: List[Signal],
        config: Optional[BacktestConfig] = None,
        initial_capital: float = 1000.0
    ):
        self.signals = sorted(signals, key=lambda s: s.timestamp)
        self.config = config or BacktestConfig()
        self.initial_capital = initial_capital

        self.trades: List[Trade] = []
        self.equity_curve = {}
        self.positions: dict[str, Optional[Position]] = defaultdict(lambda: None)
        self.asset_balances: dict[str, float] = defaultdict(float)
        self.cash_usdc = initial_capital

    def run(self) -> BacktestResult:
        for signal in self.signals:
            if signal.side in ["BUY", "SELL"]:
                self._open_position(signal)
            elif signal.side == "CLOSE":
                self._close_position(signal)

            self._update_equity(signal.timestamp)

        for asset, pos in self.positions.items():
            if pos:
                self._force_close_last_position(asset, self.signals[-1].timestamp, self.signals[-1].price)

        equity_df = pd.DataFrame.from_dict(self.equity_curve, orient="index")
        kpis = compute_kpis(self.trades, self.initial_capital, equity_df, self.config)
        return BacktestResult(trades=self.trades, equity_curve=equity_df, kpis=kpis)

    def _open_position(self, signal: Signal):
        asset = signal.asset
        if self.positions[asset]:
            return

        entry_price = apply_slippage(signal.price, self.config.slippage, signal.side)
        entry_price = apply_fees(entry_price, self.config.fee, signal.side)
        alloc_cash = self.cash_usdc / self._active_asset_count()

        if self.config.mode == "fixed":
            alloc_cash = min(alloc_cash, self.initial_capital / self._active_asset_count())
        quantity = alloc_cash / entry_price

        self.positions[asset] = Position(
            side=signal.side,
            entry_price=entry_price,
            quantity=quantity,
            entry_time=signal.timestamp
        )
        self.asset_balances[asset] = quantity if signal.side == "BUY" else -quantity
        self.cash_usdc -= alloc_cash

    def _close_position(self, signal: Signal):
        asset = signal.asset
        position = self.positions[asset]
        if not position:
            return

        exit_price = apply_slippage(signal.price, self.config.slippage, signal.side)
        exit_price = apply_fees(exit_price, self.config.fee, signal.side)

        trade = Trade.from_position(position, exit_price, signal.timestamp)
        self.trades.append(trade)

        self.cash_usdc += trade.exit_value
        self.asset_balances[asset] = 0.0
        self.positions[asset] = None

    def _force_close_last_position(self, asset: str, timestamp, price):
        if self.positions[asset]:
            self._close_position(Signal(timestamp=timestamp, side="CLOSE", price=price, asset=asset))

    def _update_equity(self, timestamp):
        total_value = self.cash_usdc
        snapshot = {"cash_usdc": self.cash_usdc}

        for asset, position in self.positions.items():
            if position:
                latest_price = next(
                    (s.price for s in reversed(self.signals) if s.asset == asset and s.timestamp <= timestamp),
                    position.entry_price
                )
                value = position.market_value(latest_price)
                total_value += value
                snapshot[f"{asset}_balance"] = position.quantity
                snapshot[f"{asset}_price"] = latest_price
                snapshot[f"{asset}_value"] = value
            else:
                snapshot[f"{asset}_balance"] = 0.0
                snapshot[f"{asset}_value"] = 0.0

        snapshot["equity_usdc"] = total_value
        self.equity_curve[timestamp] = snapshot
   
    def _active_asset_count(self) -> int:
        return len(set(s.asset for s in self.signals))