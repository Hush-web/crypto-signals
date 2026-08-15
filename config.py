# config.py
import os
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

COINS = [
    'BTC-USD', 'ETH-USD', 'SOL-USD',
    'AVAX-USD', 'LINK-USD', 'MATIC-USD',
    'NEAR-USD', 'OP-USD'
]

LOOKBACK_PERIOD = '180d'
INTERVAL = '1h'

RSI_PERIOD = 14
RSI_OVERSOLD = 25
RSI_OVERBOUGHT = 75

TARGET_PCT = 0.015
STOP_LOSS_PCT = 0.012

POSITION_SIZING = {'HIGH': 0.04, 'MEDIUM': 0.02, 'LOW': 0.01}
DB_PATH = 'signals.db'
CSV_EXPORT_PATH = 'signals_export.csv'
ONLY_ACT_ON_SIGNALS = True
MIN_VOTES = 3

print(f"📊 Config loaded: {', '.join(COINS)}")