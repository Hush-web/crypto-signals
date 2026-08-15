# config.py — Aggressive Strategy Configuration
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# TELEGRAM
# ============================================

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# ============================================
# COINS — Expanded to 20 for more signals
# ============================================

COINS = [
    # Large Caps (Stable)
    'BTC-USD',
    'ETH-USD',
    'SOL-USD',
    'BNB-USD',
    'XRP-USD',
    'ADA-USD',
    
    # Mid Caps (Volatile)
    'AVAX-USD',
    'LINK-USD',
    'MATIC-USD',
    'NEAR-USD',
    'OP-USD',
    'ARB-USD',
    'ATOM-USD',
    'DOT-USD',
    'APT-USD',
    'SUI-USD',
    'SEI-USD',
    'INJ-USD',
    'MNT-USD',
    'TIA-USD',
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
# RISK — AGGRESSIVE CONFIG
# ============================================

TARGET_PCT = 0.03      # 3% target (was 1.5%)  ← CHANGED
STOP_LOSS_PCT = 0.02   # 2% stop (was 1.2%)   ← CHANGED

POSITION_SIZING = {
    'HIGH': 0.05,      # 5% of account (was 4%)
    'MEDIUM': 0.03,    # 3% of account (was 2%)
    'LOW': 0.015,      # 1.5% of account (was 1%)
}

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
print(f"   Position Sizing: HIGH={POSITION_SIZING['HIGH']*100}%, MEDIUM={POSITION_SIZING['MEDIUM']*100}%, LOW={POSITION_SIZING['LOW']*100}%")# config.py — Aggressive Strategy Configuration
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# TELEGRAM
# ============================================

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# ============================================
# COINS — Expanded to 20 for more signals
# ============================================

COINS = [
    # Large Caps (Stable)
    'BTC-USD',
    'ETH-USD',
    'SOL-USD',
    'BNB-USD',
    'XRP-USD',
    'ADA-USD',
    
    # Mid Caps (Volatile)
    'AVAX-USD',
    'LINK-USD',
    'MATIC-USD',
    'NEAR-USD',
    'ARB-USD',
    'ATOM-USD',
    'DOT-USD',
    'APT-USD',
    'SUI-USD',
    'SEI-USD',
    'INJ-USD',
    'MNT-USD',
    'TIA-USD',
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
# RISK — AGGRESSIVE CONFIG
# ============================================

TARGET_PCT = 0.03      # 3% target (was 1.5%)  ← CHANGED
STOP_LOSS_PCT = 0.02   # 2% stop (was 1.2%)   ← CHANGED

POSITION_SIZING = {
    'HIGH': 0.05,      # 5% of account (was 4%)
    'MEDIUM': 0.03,    # 3% of account (was 2%)
    'LOW': 0.015,      # 1.5% of account (was 1%)
}

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