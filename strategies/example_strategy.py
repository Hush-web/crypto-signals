"""
example_strategy.py — Template for writing your own signal strategy.

Copy this file, rename it, and modify the logic in `evaluate()`.
Then, in signals.py, you can swap out the built-in RSI/EMA/MACD voting
in generate_signal() for a call to your strategy's evaluate() function.

This example is a simple "Bollinger-style breakout" idea using only
the Close price (no extra indicators needed), to show the expected
input/output shape.
"""

import pandas as pd


def evaluate(df: pd.DataFrame, lookback: int = 20, num_std: float = 2.0) -> dict:
    """
    Very simple mean-reversion example:
    - If price closes below (mean - num_std * std) -> BUY (oversold breakout)
    - If price closes above (mean + num_std * std) -> SELL (overbought breakout)
    - Otherwise -> HOLD

    Args:
        df: DataFrame with at least a 'Close' column, most recent row last.
        lookback: rolling window size for mean/std.
        num_std: number of standard deviations for the bands.

    Returns:
        dict with keys: action, confidence, reason
    """
    if len(df) < lookback:
        return {"action": "HOLD", "confidence": "NONE", "reason": "Not enough data"}

    window = df["Close"].tail(lookback)
    mean = window.mean()
    std = window.std()
    price = df["Close"].iloc[-1]

    upper_band = mean + num_std * std
    lower_band = mean - num_std * std

    if price < lower_band:
        return {
            "action": "BUY",
            "confidence": "MEDIUM",
            "reason": f"Price {price:.4f} broke below lower band {lower_band:.4f}",
        }
    if price > upper_band:
        return {
            "action": "SELL",
            "confidence": "MEDIUM",
            "reason": f"Price {price:.4f} broke above upper band {upper_band:.4f}",
        }

    return {
        "action": "HOLD",
        "confidence": "NONE",
        "reason": f"Price {price:.4f} within bands [{lower_band:.4f}, {upper_band:.4f}]",
    }
