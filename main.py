# main.py — Complete with CoinGecko fallback for new coins
import sys
import sqlite3
import argparse
import yfinance as yf
import requests
from datetime import datetime, timedelta
import config
import database
import signals as signal_engine
import telegram
from market_data import get_fear_greed, get_whale_sentiment

BATCH_COUNTER = 1

def get_current_prices():
    """
    Fetch live prices for all tracked coins.
    Tries yfinance first, then falls back to CoinGecko.
    """
    prices = {}
    coin_ids = {
        'BTC-USD': 'bitcoin',
        'ETH-USD': 'ethereum',
        'SOL-USD': 'solana',
        'AVAX-USD': 'avalanche-2',
        'LINK-USD': 'chainlink',
        'MATIC-USD': 'matic-network',
        'NEAR-USD': 'near',
        'OP-USD': 'optimism'
    }
    
    for coin in config.COINS:
        price = 0
        # Try yfinance
        try:
            ticker = yf.Ticker(coin)
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                price = data['Close'].iloc[-1]
                print(f"✅ Live price for {coin}: ${price:.2f} (yfinance)")
                prices[coin] = price
                continue
        except Exception as e:
            print(f"⚠️ yfinance failed for {coin}: {e}")
        
        # If yfinance fails, try CoinGecko
        try:
            coin_id = coin_ids.get(coin, 'bitcoin')
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                price = data.get(coin_id, {}).get('usd', 0)
                if price:
                    print(f"✅ Live price for {coin}: ${price:.2f} (CoinGecko)")
                    prices[coin] = price
                    continue
        except Exception as e:
            print(f"⚠️ CoinGecko failed for {coin}: {e}")
        
        prices[coin] = 0
        print(f"❌ No live data for {coin}")
    
    print(f"[DEBUG] get_current_prices returned: {prices}")
    return prices

def check_open_trades(current_prices):
    open_trades = database.get_open_trades()
    print(f"[DEBUG] Found {len(open_trades)} open trades to check.")
    
    for trade in open_trades:
        trade_id, coin, action, entry, target, stop = trade
        price = current_prices.get(coin)
        if not price or price == 0:
            print(f"⚠️ Skipping {coin} (no live price)")
            continue
        
        print(f"[DEBUG] Checking {coin} {action}: entry={entry:.2f}, target={target:.2f}, stop={stop:.2f}, current={price:.2f}")
        
        if action == 'BUY':
            if price >= target:
                pnl = (target - entry) / entry * 100
                database.close_trade(trade_id, target, pnl, 'TARGET')
                print(f"🎯 {coin} hit TARGET! +{pnl:.2f}%")
            elif price <= stop:
                pnl = (stop - entry) / entry * 100
                database.close_trade(trade_id, stop, pnl, 'STOP_LOSS')
                print(f"⛔ {coin} hit STOP LOSS! {pnl:.2f}%")
        elif action == 'SELL':
            if price <= target:
                pnl = (entry - target) / entry * 100
                database.close_trade(trade_id, target, pnl, 'TARGET')
                print(f"🎯 {coin} hit TARGET! +{pnl:.2f}%")
            elif price >= stop:
                pnl = (entry - stop) / entry * 100
                database.close_trade(trade_id, stop, pnl, 'STOP_LOSS')
                print(f"⛔ {coin} hit STOP LOSS! {pnl:.2f}%")

def send_daily_digest():
    database.init_db()
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM signals WHERE timestamp > datetime("now", "-24 hours") ORDER BY id DESC LIMIT 10')
    signals = c.fetchall()
    conn.close()
    
    pnl = database.get_pnl_metrics(30)
    fear_val, fear_label = get_fear_greed()
    whale_signal, whale_reason = get_whale_sentiment()
    
    msg = f"""
📊 DAILY CRYPTO DIGEST — {datetime.now().strftime('%B %d, %Y')}

📈 TODAY'S SIGNALS:
"""
    if signals:
        for s in signals[:5]:
            msg += f"  • {s[2]}: {s[3]} @ {s[4]} ({s[7]})\n"
    else:
        msg += "  • No signals recorded in the last 24 hours.\n"
    
    msg += f"""
📊 30-DAY PERFORMANCE:
  Total Trades: {pnl['total_trades']}
  Wins: {pnl['wins']} | Losses: {pnl['losses']}
  Win Rate: {pnl['win_rate']:.1f}%
  Total PnL: {pnl['total_pnl']:.2f}%
  Avg Win: {pnl['avg_win']:.2f}% | Avg Loss: {pnl['avg_loss']:.2f}%

📊 SENTIMENT:
  Fear & Greed: {fear_label} ({fear_val})
  Whale: {whale_signal} — {whale_reason}

🎯 SNIPER STREAK: 🔥 Track your own results

⚠️ Not financial advice. Trade at your own risk.
"""
    telegram.send_digest(msg)
    telegram.send_poll("📊 Community Sentiment: Will BTC be UP or DOWN in 24h?")

def run(pairs=None, send_alerts=True, export_csv=True):
    global BATCH_COUNTER
    database.init_db()
    
    results = signal_engine.generate_all_signals(pairs or config.COINS)
    
    print("\n[DEBUG] Checking open trades with live prices...")
    prices = get_current_prices()
    check_open_trades(prices)
    
    active_signals = []
    for sig in results:
        if sig['action'] == 'ERROR':
            print(f"[main] {sig['coin']}: ERROR — {sig.get('reason', 'Unknown')}")
            continue
        if sig['action'] == 'HOLD':
            print(f"[main] {sig['coin']}: HOLD")
            continue
        print(f"[main] {sig['coin']}: {sig['action']} @ {sig['entry_price']:.2f} ({sig['confidence']})")
        database.insert_signal(sig)
        active_signals.append(sig)
    
    if send_alerts and active_signals:
        telegram.send_batch(active_signals, BATCH_COUNTER)
        BATCH_COUNTER += 1
    
    print(f"[main] Done. {len(active_signals)} signal(s) fired.")
    if export_csv:
        path = database.export_csv()
        print(f"[main] Exported CSV to {path}")

def main():
    parser = argparse.ArgumentParser(description="Crypto signal generator")
    parser.add_argument("--digest", action="store_true", help="Send daily digest")
    parser.add_argument("--pairs", nargs="+", help="Override pairs list")
    parser.add_argument("--no-telegram", action="store_true", help="Skip Telegram alerts")
    parser.add_argument("--no-csv", action="store_true", help="Skip CSV export")
    args = parser.parse_args()
    
    if args.digest:
        send_daily_digest()
        return
    
    pairs = args.pairs or config.COINS
    run(pairs=pairs, send_alerts=not args.no_telegram, export_csv=not args.no_csv)

if __name__ == '__main__':
    main()