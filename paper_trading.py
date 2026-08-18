# paper_trading.py — Paper Trading Simulator (Fixed Position Sizing)
import sqlite3
import config
from datetime import datetime
import yfinance as yf

def init_paper_account():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS paper_trades')
    c.execute('DROP TABLE IF EXISTS paper_account')
    c.execute('''
        CREATE TABLE paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER,
            coin TEXT,
            action TEXT,
            entry_price REAL,
            target REAL,
            stop_loss REAL,
            position_size REAL,
            cost_basis REAL,
            exit_price REAL DEFAULT 0,
            pnl_pct REAL DEFAULT 0,
            pnl_usd REAL DEFAULT 0,
            status TEXT DEFAULT 'OPEN',
            entry_time DATETIME,
            exit_time DATETIME,
            FOREIGN KEY(signal_id) REFERENCES signals(id)
        )
    ''')
    c.execute('''
        CREATE TABLE paper_account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cash REAL DEFAULT 10000,
            equity REAL DEFAULT 10000,
            updated_at DATETIME
        )
    ''')
    c.execute('INSERT INTO paper_account (cash, equity, updated_at) VALUES (10000, 10000, ?)', (datetime.now().isoformat(),))
    conn.commit()
    conn.close()
    print("[Paper] Account initialized with $10,000 cash")

def get_cash_balance():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT cash FROM paper_account ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    return row[0] if row else 10000

def get_equity():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT equity FROM paper_account ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    return row[0] if row else 10000

def update_cash_balance(new_cash):
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE paper_account SET cash = ?, updated_at = ? WHERE id = (SELECT id FROM paper_account ORDER BY id DESC LIMIT 1)', (new_cash, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def calculate_position_size(entry_price, stop_loss):
    """
    Calculate position size as a fixed percentage of cash.
    Uses config.POSITION_SIZE_PCT (default 0.10 = 10%)
    """
    cash = get_cash_balance()
    position_value = cash * config.POSITION_SIZE_PCT
    if position_value > cash:
        position_value = cash
    position_size = position_value / entry_price
    return position_size

def open_paper_trade(signal_id, coin, action, entry, target, stop):
    cash = get_cash_balance()
    if cash <= 0:
        print(f"[Paper] Insufficient cash to open trade for {coin}")
        return

    position_size = calculate_position_size(entry, stop)
    cost = entry * position_size

    if cost > cash:
        position_size = cash / entry
        cost = cash
        print(f"[Paper] Position size reduced to fit cash: {position_size:.4f} units")

    new_cash = cash - cost
    update_cash_balance(new_cash)

    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO paper_trades
        (signal_id, coin, action, entry_price, target, stop_loss, position_size, cost_basis, entry_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (signal_id, coin, action, entry, target, stop, position_size, cost, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    print(f"[Paper] {action} {coin} opened @ ${entry:.2f} (size: {position_size:.4f} units, cost: ${cost:.2f})")

def close_paper_trade(trade_id, exit_price, reason):
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT coin, action, entry_price, position_size, cost_basis FROM paper_trades WHERE id = ?', (trade_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return
    coin, action, entry, position_size, cost = row

    proceeds = exit_price * position_size
    pnl_usd = proceeds - cost
    pnl_pct = (pnl_usd / cost) * 100 if cost != 0 else 0

    c.execute('''
        UPDATE paper_trades
        SET exit_price = ?, pnl_pct = ?, pnl_usd = ?, status = "CLOSED", exit_time = ?
        WHERE id = ?
    ''', (exit_price, pnl_pct, pnl_usd, datetime.now().isoformat(), trade_id))
    conn.commit()
    conn.close()

    cash = get_cash_balance()
    new_cash = cash + proceeds
    update_cash_balance(new_cash)

    emoji = "✅" if pnl_usd > 0 else "❌"
    print(f"[Paper] {emoji} {coin} closed: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%) | Cash: ${new_cash:.2f}")

def get_open_paper_trades():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, coin, action, entry_price, target, stop_loss FROM paper_trades WHERE status = "OPEN"')
    rows = c.fetchall()
    conn.close()
    return rows

def check_paper_trades(current_prices):
    open_trades = get_open_paper_trades()
    print(f"\n[DEBUG] Checking {len(open_trades)} open trades...")
    closed_count = 0
    for trade in open_trades:
        trade_id, coin, action, entry, target, stop = trade
        price = current_prices.get(coin, 0)
        if price == 0:
            continue
        if action == 'BUY':
            if price >= target:
                close_paper_trade(trade_id, target, 'TARGET')
                closed_count += 1
                print(f"[DEBUG] {coin} BUY hit TARGET! (entry={entry:.4f}, target={target:.4f}, price={price:.4f})")
            elif price <= stop:
                close_paper_trade(trade_id, stop, 'STOP_LOSS')
                closed_count += 1
                print(f"[DEBUG] {coin} BUY hit STOP_LOSS! (entry={entry:.4f}, stop={stop:.4f}, price={price:.4f})")
        elif action == 'SELL':
            if price <= target:
                close_paper_trade(trade_id, target, 'TARGET')
                closed_count += 1
                print(f"[DEBUG] {coin} SELL hit TARGET! (entry={entry:.4f}, target={target:.4f}, price={price:.4f})")
            elif price >= stop:
                close_paper_trade(trade_id, stop, 'STOP_LOSS')
                closed_count += 1
                print(f"[DEBUG] {coin} SELL hit STOP_LOSS! (entry={entry:.4f}, stop={stop:.4f}, price={price:.4f})")
    if closed_count > 0:
        print(f"[DEBUG] Closed {closed_count} trade(s) in this cycle.")

def get_performance_summary():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM paper_trades')
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM paper_trades WHERE status = "CLOSED"')
    closed = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM paper_trades WHERE status = "CLOSED" AND pnl_usd > 0')
    wins = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM paper_trades WHERE status = "CLOSED" AND pnl_usd < 0')
    losses = c.fetchone()[0]
    c.execute('SELECT SUM(pnl_usd) FROM paper_trades WHERE status = "CLOSED"')
    total_pnl = c.fetchone()[0] or 0
    win_rate = (wins / closed * 100) if closed > 0 else 0
    cash = get_cash_balance()
    conn.close()
    return {
        'total': total,
        'closed': closed,
        'open': total - closed,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'balance': cash,
        'initial_balance': 10000,
        'return_pct': ((cash - 10000) / 10000) * 100
    }

def print_performance_report():
    stats = get_performance_summary()
    print("\n" + "=" * 60)
    print("📊 PAPER TRADING PERFORMANCE — AGGRESSIVE")
    print("=" * 60)
    print(f"  Initial Balance:  $10,000.00")
    print(f"  Current Cash:     ${stats['balance']:.2f}")
    print(f"  Total Return:     {stats['return_pct']:+.2f}%")
    print(f"  Total PnL:        ${stats['total_pnl']:+.2f}")
    print("-" * 60)
    print(f"  Total Trades:     {stats['total']}")
    print(f"  Open:             {stats['open']}")
    print(f"  Closed:           {stats['closed']}")
    print(f"  Wins:             {stats['wins']}")
    print(f"  Losses:           {stats['losses']}")
    print(f"  Win Rate:         {stats['win_rate']:.1f}%")
    print("=" * 60)

def get_current_price(coin):
    try:
        ticker = yf.Ticker(coin)
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            return data['Close'].iloc[-1]
    except:
        pass
    return None