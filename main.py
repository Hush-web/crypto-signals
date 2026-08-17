# main.py — with continuous monitoring for 24/7 deployment
import sys
import sqlite3
import argparse
import yfinance as yf
import requests
import time
from datetime import datetime, timedelta
import config
import database
import signals as signal_engine
import telegram
import paper_trading
from market_data import get_fear_greed, get_whale_sentiment
import threading

import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def health():
    return "Crypto Bot is running 24/7", 200

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

def generate_and_open_trades():
    """Generate signals and open new paper trades"""
    results = signal_engine.generate_all_signals(config.COINS)
    active_signals = []
    for sig in results:
        if sig['action'] == 'ERROR':
            print(f"[main] {sig['coin']}: ERROR")
            continue
        if sig['action'] == 'HOLD':
            continue
        print(f"[main] {sig['coin']}: {sig['action']} @ {sig['entry_price']:.2f}")
        signal_id = database.insert_signal(sig)
        paper_trading.open_paper_trade(signal_id, sig['coin'], sig['action'], sig['entry_price'], sig['target'], sig['stop_loss'])
        active_signals.append(sig)
    return active_signals

def run_continuous():
    """Run the bot continuously – checks prices every 5 seconds"""
    print("🔴 Starting continuous monitoring mode (24/7)...")
    database.init_db()
    paper_trading.init_paper_account()
    
    loop_count = 0
    while True:
        try:
            # Fetch live prices
            prices = get_current_prices()
            
            # Check and close any trades that hit TP/SL
            paper_trading.check_paper_trades(prices)
            
            # Every 60 loops (~5 minutes), print a heartbeat
            if loop_count % 60 == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Heartbeat – monitoring...")
            
            loop_count += 1
            time.sleep(5)  # Check every 5 seconds
            
        except KeyboardInterrupt:
            print("\n🔴 Shutting down...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(10)

def run_continuous_with_signals():
    """Run continuously with signal generation every hour"""
    print("🔴 Starting continuous monitoring with periodic signal generation...")
    database.init_db()
    paper_trading.init_paper_account()
    
    last_signal_time = time.time()
    signal_interval = 3600  # Generate new signals every hour
    loop_count = 0
    
    while True:
        try:
            # Fetch live prices
            prices = get_current_prices()
            
            # 1. Check and close trades
            paper_trading.check_paper_trades(prices)
            
            # 2. Generate new signals periodically
            if time.time() - last_signal_time > signal_interval:
                print(f"\n[main] Generating new signals at {datetime.now().strftime('%H:%M:%S')}")
                generate_and_open_trades()
                last_signal_time = time.time()
            
            if loop_count % 60 == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Heartbeat – monitoring...")
            
            loop_count += 1
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n🔴 Shutting down...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(10)

def run():
    """Original run mode – single pass for cron jobs"""
    database.init_db()
    paper_trading.init_paper_account()
    
    prices = get_current_prices()
    paper_trading.check_paper_trades(prices)
    
    results = signal_engine.generate_all_signals(config.COINS)
    active_signals = []
    for sig in results:
        if sig['action'] == 'ERROR':
            print(f"[main] {sig['coin']}: ERROR")
            continue
        if sig['action'] == 'HOLD':
            print(f"[main] {sig['coin']}: HOLD")
            continue
        print(f"[main] {sig['coin']}: {sig['action']} @ {sig['entry_price']:.2f}")
        signal_id = database.insert_signal(sig)
        paper_trading.open_paper_trade(signal_id, sig['coin'], sig['action'], sig['entry_price'], sig['target'], sig['stop_loss'])
        active_signals.append(sig)
    
    print(f"[main] Done. {len(active_signals)} signal(s) fired.")
    paper_trading.print_performance_report()
    database.export_csv()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--digest", action="store_true", help="Send daily digest")
    parser.add_argument("--continuous", action="store_true", help="Run in continuous monitoring mode (24/7)")
    parser.add_argument("--continuous-with-signals", action="store_true", help="Continuous + periodic signal generation")
    args = parser.parse_args()
    
    if args.digest:
        send_daily_digest()
        return
    if args.continuous:
        run_continuous()
        return
    if args.continuous_with_signals:
        run_continuous_with_signals()
        return
    run()
if __name__ == '__main__':
    if "--continuous" in sys.argv:
        # Start Flask server (so Render keeps the service alive)
        port = int(os.environ.get('PORT', 10000))
        threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False), daemon=True).start()
        # Start the bot loop
        run_continuous()
    elif "--continuous-with-signals" in sys.argv:
        # Start Flask server
        port = int(os.environ.get('PORT', 10000))
        threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False), daemon=True).start()
        run_continuous_with_signals()
    else:
        main()