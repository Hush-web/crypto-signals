"""
config.py — Central configuration for the signal bot.

Edit the values below to change which coins are tracked, how sensitive
the indicators are, and where data gets saved. Nothing here requires
an API key.
"""

import os

# ---------------------------------------------------------------------------
# Coins to scan. Must be valid Yahoo Finance tickers (crypto pairs end in -USD).
# ---------------------------------------------------------------------------
COINS = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "BNB-USD",
    "XRP-USD",
    "ADA-USD",
    "DOGE-USD",
]

# ---------------------------------------------------------------------------
# Data fetch settings (yfinance)
# ---------------------------------------------------------------------------
INTERVAL = "1h"          # candle size: 1m,5m,15m,30m,1h,1d ...
LOOKBACK_PERIOD = "60d"  # how much history to pull each run
                          # NOTE: yfinance limits intraday intervals to ~60-730 days

# ---------------------------------------------------------------------------
# Indicator settings
# ---------------------------------------------------------------------------
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

EMA_FAST = 9
EMA_SLOW = 21

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# ---------------------------------------------------------------------------
# Risk / target settings (simple % based)
# ---------------------------------------------------------------------------
TARGET_PCT = 0.03     # +3% take-profit target
STOP_LOSS_PCT = 0.02  # -2% stop loss

# ---------------------------------------------------------------------------
# Confidence scoring
# A signal fires only when at least MIN_SCORE_TO_FIRE indicators agree.
# 3/3 agreeing indicators = HIGH, 2/3 = MEDIUM, 1/3 = LOW (not fired by default)
# ---------------------------------------------------------------------------
MIN_SCORE_TO_FIRE = 2

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
DB_PATH = os.getenv("DB_PATH", "signals.db")
CSV_EXPORT_PATH = os.getenv("CSV_EXPORT_PATH", "signals_export.csv")

# ---------------------------------------------------------------------------
# Telegram (set these as environment variables / GitHub secrets — never hardcode)
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# If True, HOLD (no-signal) coins are skipped entirely and never sent/saved.
ONLY_ACT_ON_SIGNALS = True
