# main.py — with full debug check_paper_trades
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
import paper_trading
from market_data import get_fear_greed, get_whale_sentiment

BATCH_COUNTER = 1

def get_current_prices():
    prices = {}
    coin_ids = {
        'BTC-USD': 'bitcoin', 'ETH-USD': 'ethereum', 'SOL-USD': 'solana',
        'AVAX-USD': 'avalanche-2', 'LINK-USD': 'chainlink',
        'NEAR-USD': 'near', 'ATOM-USD': 'cosmos', 'DOT-USD': 'polkadot',
        'SEI-USD': 'sei-network', 'INJ-USD': 'injective',
        'MNT-USD': 'mantle', 'TIA-USD': 'celestia',
        'BNB-USD': 'binancecoin', 'XRP-USD': 'ripple', 'ADA-USD': 'cardano'
    }
    for coin in config.COINS:
        price = 0
        try:
            ticker = yf.Ticker(coin)
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                price = data['Close'].iloc[-1]
                print(f"✅ Live price for {coin}: ${price:.2f}")
                prices[coin] = price
                continue
        except:
            pass
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
        except:
            pass
        prices[coin] = 0
    return prices

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
    paper_trading.init_paper_account()
    
    # ===== STEP 1: FETCH LIVE PRICES =====
    prices = get_current_prices()
    
    # ===== STEP 2: CLOSE EXISTING OPEN TRADES =====
    print("\n[DEBUG] ==== First pass: checking existing open trades ====")
    paper_trading.check_paper_trades(prices)
    
    # ===== STEP 3: GENERATE NEW SIGNALS =====
    results = signal_engine.generate_all_signals(pairs or config.COINS)
    
    # ===== STEP 4: OPEN NEW PAPER TRADES =====
    active_signals = []
    for sig in results:
        if sig['action'] == 'ERROR':
            print(f"[main] {sig['coin']}: ERROR")
            continue
        if sig['action'] == 'HOLD':
            print(f"[main] {sig['coin']}: HOLD")
            continue
        print(f"[main] {sig['coin']}: {sig['action']} @ {sig['entry_price']:.2f} ({sig['confidence']})")
        signal_id = database.insert_signal(sig)
        paper_trading.open_paper_trade(signal_id, sig['coin'], sig['action'], sig['entry_price'], sig['target'], sig['stop_loss'])
        active_signals.append(sig)
    
    # ===== STEP 5: CHECK AGAIN IMMEDIATELY =====
    if active_signals:
        print("\n[DEBUG] ==== Second pass: re-checking after opening new trades ====")
        prices = get_current_prices()  # Refresh prices
        paper_trading.check_paper_trades(prices)
    
    if send_alerts and active_signals:
        telegram.send_batch(active_signals, BATCH_COUNTER)
        BATCH_COUNTER += 1
    
    print(f"[main] Done. {len(active_signals)} signal(s) fired.")
    paper_trading.print_performance_report()
    if export_csv:
        path = database.export_csv()
        print(f"[main] Exported CSV to {path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--digest", action="store_true", help="Send daily digest")
    args = parser.parse_args()
    if args.digest:
        send_daily_digest()
        return
    run()

if __name__ == '__main__':
    main()