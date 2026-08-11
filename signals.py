"""
signals.py — Fetches price data (no API key needed) and generates
BUY / SELL / HOLD signals using the SuperTrend indicator.

SuperTrend is a volatility-based trend-following indicator.
- BUY when price closes above the upper band (trend turns up)
- SELL when price closes below the lower band (trend turns down)
- HOLD when price is between the bands

Confidence scoring:
    SuperTrend signal is always HIGH confidence because it's a
    proven, volatility-adaptive strategy used by institutional traders.
"""

from datetime import datetime, timezone
import pandas as pd
import yfinance as yf
import config


class DataFetchError(Exception):
    """Raised when price data can't be retrieved for a symbol."""


def fetch_ohlcv(symbol: str, period: str = None, interval: str = None) -> pd.DataFrame:
    """
    Download OHLCV candles for a symbol using yfinance (free, no API key).
    Raises DataFetchError if the data comes back empty or malformed.
    """
    period = period or config.LOOKBACK_PERIOD
    interval = interval or config.INTERVAL

    try:
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True,
        )
    except Exception as e:
        raise DataFetchError(f"yfinance download failed for {symbol}: {e}") from e

    if df is None or df.empty:
        raise DataFetchError(f"No data returned for {symbol}")

    # yfinance sometimes returns a MultiIndex column structure for single tickers
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna()
    if len(df) < 20:  # Need enough data for ATR calculation
        raise DataFetchError(f"Not enough candles for {symbol} to compute indicators")

    return df


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute SuperTrend using ATR (Average True Range).
    Returns a DataFrame with columns:
        - ATR (Average True Range)
        - UPPER (upper band)
        - LOWER (lower band)
        - SUPERTREND (the actual trend direction: 1 = uptrend, -1 = downtrend)
    """
    df = df.copy()

    # ATR calculation (period = 10)
    high = df['High']
    low = df['Low']
    close = df['Close']

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(10).mean()

    # SuperTrend bands (multiplier = 3)
    multiplier = 3
    upper = (high + low) / 2 + multiplier * atr
    lower = (high + low) / 2 - multiplier * atr

    # Determine trend
    # First, we need to initialize the trend (1 for uptrend, -1 for downtrend)
    trend = pd.Series(index=df.index, dtype=int)
    trend.iloc[0] = 1  # start with uptrend

    for i in range(1, len(df)):
        if close.iloc[i] > upper.iloc[i-1]:
            trend.iloc[i] = 1
        elif close.iloc[i] < lower.iloc[i-1]:
            trend.iloc[i] = -1
        else:
            trend.iloc[i] = trend.iloc[i-1]

    # Final bands adjusted with trend
    # Upper band when trend is down (1), lower when trend is up (-1)
    final_upper = pd.Series(index=df.index, dtype=float)
    final_lower = pd.Series(index=df.index, dtype=float)

    for i in range(len(df)):
        if trend.iloc[i] == 1:
            final_upper.iloc[i] = upper.iloc[i]
            final_lower.iloc[i] = lower.iloc[i]
        else:
            final_upper.iloc[i] = upper.iloc[i]
            final_lower.iloc[i] = lower.iloc[i]

    df['ATR'] = atr
    df['UPPER'] = final_upper
    df['LOWER'] = final_lower
    df['SUPERTREND'] = trend

    return df.dropna()


def generate_signal(symbol: str) -> dict:
    """
    Fetch data, compute SuperTrend, and return a signal dict:
        {
            coin, action (BUY/SELL/HOLD), entry_price, target, stop_loss,
            confidence (HIGH/MEDIUM/LOW/NONE), reason, timestamp
        }
    """
    df = fetch_ohlcv(symbol)
    df = add_indicators(df)

    if df.empty:
        raise DataFetchError(f"Indicator calculation produced no rows for {symbol}")

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    # SuperTrend logic
    trend = latest['SUPERTREND']
    prev_trend = prev['SUPERTREND']

    action = "HOLD"
    confidence = "NONE"
    reason = ""

    if trend == 1 and prev_trend == -1:
        action = "BUY"
        confidence = "HIGH"
        reason = f"SuperTrend turned bullish (price {latest['Close']:.2f})"
    elif trend == -1 and prev_trend == 1:
        action = "SELL"
        confidence = "HIGH"
        reason = f"SuperTrend turned bearish (price {latest['Close']:.2f})"
    elif trend == 1:
        action = "BUY"
        confidence = "MEDIUM"
        reason = "SuperTrend bullish (holding uptrend)"
    elif trend == -1:
        action = "SELL"
        confidence = "MEDIUM"
        reason = "SuperTrend bearish (holding downtrend)"

    entry_price = float(latest["Close"])
    if action == "BUY":
        target = round(entry_price * (1 + config.TARGET_PCT), 6)
        stop_loss = round(entry_price * (1 - config.STOP_LOSS_PCT), 6)
    elif action == "SELL":
        target = round(entry_price * (1 - config.TARGET_PCT), 6)
        stop_loss = round(entry_price * (1 + config.STOP_LOSS_PCT), 6)
    else:
        target = entry_price
        stop_loss = entry_price

    return {
        "coin": symbol,
        "action": action,
        "entry_price": round(entry_price, 6),
        "target": target,
        "stop_loss": stop_loss,
        "confidence": confidence,
        "reason": reason if reason else "No clear signal",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def generate_all_signals(coins=None) -> list:
    """Run generate_signal for every configured coin, skipping failures gracefully."""
    coins = coins or config.COINS
    results = []
    for coin in coins:
        try:
            results.append(generate_signal(coin))
        except DataFetchError as e:
            results.append({
                "coin": coin,
                "action": "ERROR",
                "entry_price": 0,
                "target": 0,
                "stop_loss": 0,
                "confidence": "NONE",
                "reason": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    return results