"""
signals.py — Fetches price data (no API key needed) and generates
BUY / SELL / HOLD signals from RSI, EMA crossover, and MACD crossover.

Confidence scoring:
    Each of the 3 indicators "votes" BUY, SELL, or neutral.
    - If BUY votes > SELL votes and BUY votes >= MIN_SCORE_TO_FIRE -> BUY signal
    - If SELL votes > BUY votes and SELL votes >= MIN_SCORE_TO_FIRE -> SELL signal
    - Otherwise -> HOLD (no signal)
    3/3 agreeing = HIGH confidence, 2/3 = MEDIUM, 1/3 = LOW
"""

from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
import pandas_ta as ta

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
    if len(df) < max(config.EMA_SLOW, config.MACD_SLOW, config.RSI_PERIOD) + 5:
        raise DataFetchError(f"Not enough candles for {symbol} to compute indicators")

    return df


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Attach RSI, EMA fast/slow, and MACD columns to the dataframe."""
    df = df.copy()

    df["RSI"] = ta.rsi(df["Close"], length=config.RSI_PERIOD)

    df["EMA_FAST"] = ta.ema(df["Close"], length=config.EMA_FAST)
    df["EMA_SLOW"] = ta.ema(df["Close"], length=config.EMA_SLOW)

    macd = ta.macd(
        df["Close"],
        fast=config.MACD_FAST,
        slow=config.MACD_SLOW,
        signal=config.MACD_SIGNAL,
    )
    if macd is not None:
        df = df.join(macd)

    return df.dropna()


def _macd_columns(df: pd.DataFrame):
    """pandas_ta names MACD columns like MACD_12_26_9 / MACDs_12_26_9."""
    macd_col = f"MACD_{config.MACD_FAST}_{config.MACD_SLOW}_{config.MACD_SIGNAL}"
    signal_col = f"MACDs_{config.MACD_FAST}_{config.MACD_SLOW}_{config.MACD_SIGNAL}"
    return macd_col, signal_col


def generate_signal(symbol: str) -> dict:
    """
    Fetch data, compute indicators, and return a signal dict:
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

    macd_col, signal_col = _macd_columns(df)

    votes = {"BUY": 0, "SELL": 0}
    reasons = []

    # --- RSI vote ---
    rsi = latest["RSI"]
    if rsi < config.RSI_OVERSOLD:
        votes["BUY"] += 1
        reasons.append(f"RSI oversold ({rsi:.1f} < {config.RSI_OVERSOLD})")
    elif rsi > config.RSI_OVERBOUGHT:
        votes["SELL"] += 1
        reasons.append(f"RSI overbought ({rsi:.1f} > {config.RSI_OVERBOUGHT})")

    # --- EMA crossover vote ---
    ema_fast, ema_slow = latest["EMA_FAST"], latest["EMA_SLOW"]
    prev_fast, prev_slow = prev["EMA_FAST"], prev["EMA_SLOW"]
    if prev_fast <= prev_slow and ema_fast > ema_slow:
        votes["BUY"] += 1
        reasons.append(f"EMA{config.EMA_FAST} crossed above EMA{config.EMA_SLOW} (bullish)")
    elif prev_fast >= prev_slow and ema_fast < ema_slow:
        votes["SELL"] += 1
        reasons.append(f"EMA{config.EMA_FAST} crossed below EMA{config.EMA_SLOW} (bearish)")
    elif ema_fast > ema_slow:
        votes["BUY"] += 1
        reasons.append(f"EMA{config.EMA_FAST} above EMA{config.EMA_SLOW} (uptrend)")
    elif ema_fast < ema_slow:
        votes["SELL"] += 1
        reasons.append(f"EMA{config.EMA_FAST} below EMA{config.EMA_SLOW} (downtrend)")

    # --- MACD crossover vote ---
    if macd_col in latest and signal_col in latest:
        macd_val, macd_sig = latest[macd_col], latest[signal_col]
        prev_macd, prev_sig = prev.get(macd_col), prev.get(signal_col)
        if prev_macd is not None and prev_sig is not None:
            if prev_macd <= prev_sig and macd_val > macd_sig:
                votes["BUY"] += 1
                reasons.append("MACD crossed above signal line (bullish)")
            elif prev_macd >= prev_sig and macd_val < macd_sig:
                votes["SELL"] += 1
                reasons.append("MACD crossed below signal line (bearish)")
            elif macd_val > macd_sig:
                votes["BUY"] += 1
                reasons.append("MACD above signal line")
            elif macd_val < macd_sig:
                votes["SELL"] += 1
                reasons.append("MACD below signal line")

    action = "HOLD"
    confidence = "NONE"
    score = 0

    if votes["BUY"] > votes["SELL"] and votes["BUY"] >= config.MIN_SCORE_TO_FIRE:
        action = "BUY"
        score = votes["BUY"]
    elif votes["SELL"] > votes["BUY"] and votes["SELL"] >= config.MIN_SCORE_TO_FIRE:
        action = "SELL"
        score = votes["SELL"]

    if score == 3:
        confidence = "HIGH"
    elif score == 2:
        confidence = "MEDIUM"
    elif score == 1:
        confidence = "LOW"

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
        "reason": "; ".join(reasons) if reasons else "No indicators triggered",
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
