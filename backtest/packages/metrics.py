# metrics.py

import pandas as pd
from typing import List
from .models import Trade


def compute_kpis(trades, initial_capital, equity_curve=None, config=None):
    if not trades:
        kpis = {
            "total_return_pct": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown_pct": 0.0,
            "hit_ratio": 0.0,
            "total_trades": 0,
            "final_balances": {}
        }
        if config and hasattr(config, 'mode'):
            kpis["mode"] = config.mode
        return kpis

    returns = pd.Series([t.return_pct for t in trades])
    equity = pd.Series([t.exit_value for t in trades]).cumsum() + initial_capital - trades[0].exit_value
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    hit_ratio = sum(1 for t in trades if t.pnl > 0) / len(trades)

    if equity_curve is not None and not equity_curve.empty:
        final_equity = equity_curve["equity_usdc"].iloc[-1]
    else:
        final_equity = sum(t.exit_value for t in trades)

    kpis = {
        "total_return_pct": (final_equity - initial_capital) / initial_capital * 100,
        "sharpe_ratio": returns.mean() / (returns.std() + 1e-6),
        "max_drawdown_pct": drawdown.min() * 100,
        "hit_ratio": hit_ratio,
        "total_trades": len(trades),
    }

    if equity_curve is not None and not equity_curve.empty:
        last_snapshot = equity_curve.iloc[-1].to_dict()
        balances = {k: v for k, v in last_snapshot.items() if "_balance" in k or "_value" in k or k == "cash_usdc"}
        kpis["final_balances"] = balances

    if config and hasattr(config, 'mode'):
        kpis["mode"] = config.mode

    return kpis