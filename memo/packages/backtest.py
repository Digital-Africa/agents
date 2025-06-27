from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum
import datetime
import pandas as pd
import numpy as np

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class Signal:
    timestamp: datetime.datetime
    side: Side
    price: float
    confidence: Optional[float] = None
    ticker: str = ""

@dataclass
class Position:
    entry_time: datetime.datetime
    entry_price: float
    side: Side
    size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_time: Optional[datetime.datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None

class BacktestEngine:
    def __init__(
        self,
        initial_balance: float = 10000.0,
        slippage: float = 0.001,  # 0.1%
        position_size: float = 0.1,  # 10% of balance
        stop_loss_pct: float = 0.02,  # 2%
        take_profit_pct: float = 0.04,  # 4%
        allow_multiple_positions: bool = False
    ):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.slippage = slippage
        self.position_size = position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.allow_multiple_positions = allow_multiple_positions
        
        self.positions: List[Position] = []
        self.open_positions: Dict[str, Position] = {}
        self.trades: List[Dict] = []
        
    def process_signal(self, signal: Signal) -> None:
        """Process a trading signal and execute trades accordingly."""
        if signal.side == Side.BUY:
            self._handle_buy_signal(signal)
        elif signal.side == Side.SELL:
            self._handle_sell_signal(signal)
            
    def _handle_buy_signal(self, signal: Signal) -> None:
        """Handle buy signals and execute trades."""
        if not self.allow_multiple_positions and self.open_positions:
            return
            
        position_size = self.balance * self.position_size
        entry_price = signal.price * (1 + self.slippage)
        stop_loss = entry_price * (1 - self.stop_loss_pct)
        take_profit = entry_price * (1 + self.take_profit_pct)
        
        position = Position(
            entry_time=signal.timestamp,
            entry_price=entry_price,
            side=Side.BUY,
            size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.open_positions[signal.ticker] = position
        self.positions.append(position)
        
    def _handle_sell_signal(self, signal: Signal) -> None:
        """Handle sell signals and execute trades."""
        if signal.ticker in self.open_positions:
            position = self.open_positions[signal.ticker]
            exit_price = signal.price * (1 - self.slippage)
            
            # Calculate PnL
            if position.side == Side.BUY:
                pnl = (exit_price - position.entry_price) * position.size
            else:
                pnl = (position.entry_price - exit_price) * position.size
                
            position.exit_time = signal.timestamp
            position.exit_price = exit_price
            position.pnl = pnl
            
            self.balance += pnl
            self.trades.append({
                'entry_time': position.entry_time,
                'exit_time': position.exit_time,
                'entry_price': position.entry_price,
                'exit_price': position.exit_price,
                'side': position.side.value,
                'size': position.size,
                'pnl': pnl
            })
            
            del self.open_positions[signal.ticker]
            
    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics for the backtest."""
        if not self.trades:
            return {}
            
        trades_df = pd.DataFrame(self.trades)
        
        # Basic metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] <= 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Profit metrics
        total_profit = trades_df['pnl'].sum()
        avg_profit = trades_df['pnl'].mean()
        
        # Drawdown calculation
        cumulative_returns = trades_df['pnl'].cumsum()
        running_max = cumulative_returns.cummax()
        drawdown = (running_max - cumulative_returns) / running_max
        max_drawdown = drawdown.max()
        
        # Risk-adjusted returns
        returns = trades_df['pnl'] / self.initial_balance
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 1 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'avg_profit': avg_profit,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'final_balance': self.balance,
            'return_pct': (self.balance - self.initial_balance) / self.initial_balance * 100
        }
