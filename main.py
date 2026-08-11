# main.py — Full version with live prices, PnL, digest
import sys
import sqlite3
from datetime import datetime, timedelta
import config
import database
import signals as signal_engine
import telegram
import yfinance as yf
from market_data import get_fear_greed, get_whale_sentiment

def get_current_prices():
    """
    Fetch live prices for all tracked coins using yfinance.
    If yfinance fails, return 0 for that coin so we skip trade checks.
    """
    prices = {}
    for coin in config.COINS:
        try:
            ticker = yf.Ticker(coin)
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                prices[coin] = data['Close'].iloc[-1]
            else:
                prices[coin] = 0
                print(f"⚠️ No live data for {coin}, skipping trade checks.")
        except Exception as e:
            print(f"❌ Price fetch failed for {coin}: {e}")
            prices[coin] = 0
    return prices

def check_open_trades(current_prices):
    """
    Check all open trades against current prices.
    If price is 0 (fetch failed), skip that coin.
    """
    open_trades = database.get_open_trades()
    for trade in open_trades:
        trade_id, coin, action, entry, target, stop = trade
        price = current_prices.get(coin)
        if not price or price == 0:
            continue
        
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

def run(coins=None, send_alerts=True, export_csv=True):
    database.init_db()
    results = signal_engine.generate_all_signals(coins or config.COINS)
    
    # Fetch live prices and check open trades
    prices = get_current_prices()
    check_open_trades(prices)
    
    fired = 0
    for sig in results:
        if sig['action'] == 'ERROR':
            print(f"[main] {sig['coin']}: ERROR — {sig.get('reason', 'Unknown')}")
            continue
        if sig['action'] == 'HOLD':
            print(f"[main] {sig['coin']}: HOLD")
            continue
        print(f"[main] {sig['coin']}: {sig['action']} @ {sig['entry_price']} ({sig['confidence']})")
        database.insert_signal(sig)
        if send_alerts:
            telegram.send_signal(sig)
        fired += 1
    
    print(f"[main] Done. {fired} signal(s) fired.")
    if export_csv:
        path = database.export_csv()
        print(f"[main] Exported CSV to {path}")

def send_daily_digest():
    database.init_db()
    conn = sqlite3.connect('signals.db')
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
    for s in signals[:5]:
        msg += f"  • {s[2]}: {s[3]} @ {s[4]} ({s[7]})\n"
    
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

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--digest':
        send_daily_digest()
        return
    run()

if __name__ == '__main__':
    main()