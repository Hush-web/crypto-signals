# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Coins
COINS = ['BTC-USD', 'ETH-USD', 'SOL-USD']

# Data
LOOKBACK_PERIOD = '180d'
INTERVAL = '1h'

# RSI
RSI_PERIOD = 14
RSI_OVERSOLD = 45
RSI_OVERBOUGHT = 55

# Risk
TARGET_PCT = 0.03
STOP_LOSS_PCT = 0.025

POSITION_SIZING = {
    'HIGH': 0.04,
    'MEDIUM': 0.02,
    'LOW': 0.01,
}

# Database
DB_PATH = 'signals.db'
CSV_EXPORT_PATH = 'signals_export.csv'

# Signal Filtering
ONLY_ACT_ON_SIGNALS = True