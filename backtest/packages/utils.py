# utils.py

from .config import TradeSide


def apply_slippage(price: float, slippage: float, side: TradeSide) -> float:
    """
    Apply slippage to the execution price.
    - For BUY: price increases (worse entry).
    - For SELL: price decreases (worse exit).
    """
    if side == TradeSide.BUY:
        return price * (1 + slippage)
    elif side == TradeSide.SELL:
        return price * (1 - slippage)
    return price


def apply_fees(price: float, fee: float, side: TradeSide) -> float:
    """
    Apply trading fee to the execution price.
    Assumes fees are deducted from value (not quantity).
    """
    if side == TradeSide.BUY:
        return price * (1 + fee)
    elif side == TradeSide.SELL:
        return price * (1 - fee)
    return price