# signals.py — Fetch data + generate signals with sentiment & whale
from datetime import datetime, timezone
import pandas as pd
import yfinance as yf
import config
from strategies import analyze_strategies
from market_data import get_fear_greed, get_whale_sentiment

class DataFetchError(Exception):
    pass

def fetch_ohlcv(symbol, period=None, interval=None):
    period = period or config.LOOKBACK_PERIOD
    interval = interval or config.INTERVAL
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
    except Exception as e:
        raise DataFetchError(f"yfinance failed: {e}")
    if df is None or df.empty:
        raise DataFetchError(f"No data for {symbol}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna()
    if len(df) < 50:
        raise DataFetchError(f"Not enough candles for {symbol}")
    return df

def generate_signal(symbol):
    df = fetch_ohlcv(symbol)
    tech = analyze_strategies(df)

    # --- DEBUG: Print individual strategy votes ---
    print(f"\n[DEBUG] {symbol} strategy votes:")
    for r in tech['strategy_results']:
        print(f"  {r['strategy']}: {r['action']} ({r['confidence']})")
    print(f"  Final: {tech['action']} ({tech['confidence']})")
    print(f"  Votes: BUY={tech['votes']['BUY']} SELL={tech['votes']['SELL']} HOLD={tech['votes']['HOLD']}")

    # Sentiment & Whale
    fear_val, fear_label = get_fear_greed()
    whale_signal, whale_reason = get_whale_sentiment()

    # Combine votes
    buy_votes = 0
    sell_votes = 0

    # Technical (weight: 3)
    if tech['action'] == 'BUY':
        buy_votes += 3
    elif tech['action'] == 'SELL':
        sell_votes += 3

    # Sentiment (weight: 1)
    if fear_val < 25:
        buy_votes += 1
    elif fear_val > 75:
        sell_votes += 1

    # Whale (weight: 2)
    if whale_signal == 'BULLISH':
        buy_votes += 2
    elif whale_signal == 'BEARISH':
        sell_votes += 2

    # === THRESHOLD = 3 (more stable, fewer signals) ===
    # Only trigger when weighted votes >= 3
    if buy_votes > sell_votes and buy_votes >= 3:
        action = 'BUY'
        if buy_votes >= 5:
            confidence = 'HIGH'   # 🎯 SNIPER MODE
        elif buy_votes >= 3:
            confidence = 'MEDIUM'  # 📡 LASER LOCKED
        else:
            confidence = 'LOW'     # 🔭 SCOUTING
    elif sell_votes > buy_votes and sell_votes >= 3:
        action = 'SELL'
        if sell_votes >= 5:
            confidence = 'HIGH'   # 🎯 SNIPER MODE
        elif sell_votes >= 3:
            confidence = 'MEDIUM'  # 📡 LASER LOCKED
        else:
            confidence = 'LOW'     # 🔭 SCOUTING
    else:
        action = 'HOLD'
        confidence = 'LOW'

    price = df['Close'].iloc[-1]

    if action == 'BUY':
        target = price * (1 + config.TARGET_PCT)
        stop = price * (1 - config.STOP_LOSS_PCT)
    elif action == 'SELL':
        target = price * (1 - config.TARGET_PCT)
        stop = price * (1 + config.STOP_LOSS_PCT)
    else:
        target = stop = price

    return {
        'coin': symbol,
        'action': action,
        'entry_price': round(price, 6),
        'target': round(target, 6),
        'stop_loss': round(stop, 6),
        'confidence': confidence,
        'reason': f"Tech: {tech['reason']} | Sentiment: {fear_label} ({fear_val}) | Whale: {whale_reason}",
        'votes': tech['votes'],
        'strategy_results': tech['strategy_results'],
        'sentiment': {'value': fear_val, 'label': fear_label},
        'whale': {'signal': whale_signal, 'reason': whale_reason},
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

def generate_all_signals(coins=None):
    coins = coins or config.COINS
    results = []
    for coin in coins:
        try:
            results.append(generate_signal(coin))
        except DataFetchError as e:
            results.append({'coin': coin, 'action': 'ERROR', 'reason': str(e)})
    return results