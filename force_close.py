# force_close.py
import sqlite3
import config
import paper_trading

def close_all_trades():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, coin, entry_price, position_size FROM paper_trades WHERE status = "OPEN"')
    open_trades = c.fetchall()

    print(f"🔴 Closing {len(open_trades)} open trades at current market price...")
    print("=" * 60)

    total_pnl = 0
    wins = 0
    losses = 0

    for trade_id, coin, entry_price, position_size in open_trades:
        current_price = paper_trading.get_current_price(coin)
        if current_price:
            paper_trading.close_paper_trade(trade_id, current_price, 'MANUAL_CLOSE')
            pnl = (current_price - entry_price) * position_size
            total_pnl += pnl
            if pnl > 0:
                wins += 1
            else:
                losses += 1
        else:
            print(f"⚠️ Could not fetch price for {coin}. Skipping.")

    conn.close()
    cash = paper_trading.get_cash_balance()
    print("=" * 60)
    print(f"📊 Total Realized PnL: ${total_pnl:.2f}")
    print(f"✅ Wins: {wins}")
    print(f"❌ Losses: {losses}")
    print(f"💰 Final Cash Balance: ${cash:.2f}")
    print("=" * 60)

if __name__ == "__main__":
    close_all_trades()