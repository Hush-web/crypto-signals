# config.py — Aggressive Strategy Configuration (Cleaned & Optimized)
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# MODE SELECTION
# ============================================
SIMULATION_MODE = False
PAPER_TRADE = True

# ============================================
# TELEGRAM
# ============================================
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# ============================================
# COINS — Only the profitable ones
# ============================================
COINS = [
    'BTC-USD',
    'ETH-USD',
    'SOL-USD',
    'BNB-USD',
    'XRP-USD',
    'AVAX-USD',
    'LINK-USD',
    'DOT-USD',
    'ATOM-USD',
]

# ============================================
# DATA
# ============================================
LOOKBACK_PERIOD = '180d'
INTERVAL = '1h'

# ============================================
# RSI
# ============================================
RSI_PERIOD = 14
RSI_OVERSOLD = 25
RSI_OVERBOUGHT = 75

# ============================================
# RISK — TIGHTENED
# ============================================
TARGET_PCT = 0.03
STOP_LOSS_PCT = 0.02

POSITION_SIZING = {
    'HIGH': 0.05,
    'MEDIUM': 0.03,
    'LOW': 0.015,
}

# ============================================
# RISK MANAGEMENT (New Rules)
# ============================================
POSITION_SIZE_PCT = 0.10          # 10% of cash per trade  <-- ADD THIS
MAX_CONCURRENT_TRADES = 3
MAX_TRADES_PER_DAY = 150
TIMEOUT_MINUTES = 60

# ============================================
# DATABASE
# ============================================
DB_PATH = 'signals.db'
CSV_EXPORT_PATH = 'signals_export.csv'

# ============================================
# SIGNAL FILTERING
# ============================================
ONLY_ACT_ON_SIGNALS = True
MIN_VOTES = 3

# ============================================
# PRINT CONFIG
# ============================================
print(f"📊 Config loaded (AGGRESSIVE):")
print(f"   Coins: {len(COINS)} coins")
print(f"   Target: {TARGET_PCT*100}% | Stop: {STOP_LOSS_PCT*100}%")
print(f"   Position Sizing: HIGH={POSITION_SIZING['HIGH']*100}%, MEDIUM={POSITION_SIZING['MEDIUM']*100}%, LOW={POSITION_SIZING['LOW']*100}%")
print(f"   Max Concurrent Trades: {MAX_CONCURRENT_TRADES}")
print(f"   Max Trades/Day: {MAX_TRADES_PER_DAY}")
print(f"   Timeout: {TIMEOUT_MINUTES} minutes")