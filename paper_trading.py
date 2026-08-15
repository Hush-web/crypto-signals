# paper_trading.py — Paper Trading Simulator
import sqlite3
import config
from datetime import datetime

def init_paper_account():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER,
            coin TEXT,
            action TEXT,
            entry_price REAL,
            target REAL,
            stop_loss REAL,
            position_size REAL,
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
        CREATE TABLE IF NOT EXISTS paper_account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            balance REAL DEFAULT 10000,
            equity REAL DEFAULT 10000,
            updated_at DATETIME
        )
    ''')
    c.execute('SELECT COUNT(*) FROM paper_account')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO paper_account (balance, equity, updated_at) VALUES (10000, 10000, ?)', (datetime.now().isoformat(),))
    conn.commit()
    conn.close()
    print("[Paper] Account initialized with $10,000 virtual balance")

def get_balance():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT balance FROM paper_account ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    return row[0] if row else 10000

def update_balance(new_balance):
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE paper_account SET balance = ?, updated_at = ? WHERE id = (SELECT id FROM paper_account ORDER BY id DESC LIMIT 1)', (new_balance, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def calculate_position_size(balance, entry_price, stop_loss, risk_percent=0.03):
    """3% risk per trade — AGGRESSIVE"""
    risk_amount = balance * risk_percent
    stop_loss_pct = abs((stop_loss - entry_price) / entry_price) if entry_price != 0 else 0.01
    if stop_loss_pct == 0:
        stop_loss_pct = 0.01
    position_size = risk_amount / (entry_price * stop_loss_pct)
    return position_size

def open_paper_trade(signal_id, coin, action, entry, target, stop):
    balance = get_balance()
    position_size = calculate_position_size(balance, entry, stop)
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO paper_trades (signal_id, coin, action, entry_price, target, stop_loss, position_size, entry_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (signal_id, coin, action, entry, target, stop, position_size, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    print(f"[Paper] {action} {coin} opened @ ${entry:.2f} (size: {position_size:.4f} units)")

def close_paper_trade(trade_id, exit_price, reason):
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT coin, action, entry_price, position_size FROM paper_trades WHERE id = ?', (trade_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return
    coin, action, entry, position_size = row
    if action == 'BUY':
        pnl_usd = (exit_price - entry) * position_size
        pnl_pct = (exit_price - entry) / entry * 100
    else:
        pnl_usd = (entry - exit_price) * position_size
        pnl_pct = (entry - exit_price) / entry * 100
    c.execute('UPDATE paper_trades SET exit_price = ?, pnl_pct = ?, pnl_usd = ?, status = "CLOSED", exit_time = ? WHERE id = ?', (exit_price, pnl_pct, pnl_usd, datetime.now().isoformat(), trade_id))
    conn.commit()
    conn.close()
    balance = get_balance()
    new_balance = balance + pnl_usd
    update_balance(new_balance)
    emoji = "✅" if pnl_usd > 0 else "❌"
    print(f"[Paper] {emoji} {coin} closed: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%) | Balance: ${new_balance:.2f}")

def get_open_paper_trades():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, coin, action, entry_price, target, stop_loss FROM paper_trades WHERE status = "OPEN"')
    rows = c.fetchall()
    conn.close()
    return rows

def get_performance_summary():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM paper_trades')
    total = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM paper_trades WHERE status = "CLOSED"')
    closed = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM paper_trades WHERE status = "CLOSED" AND pnl_pct > 0')
    wins = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM paper_trades WHERE status = "CLOSED" AND pnl_pct < 0')
    losses = c.fetchone()[0]
    c.execute('SELECT SUM(pnl_usd) FROM paper_trades WHERE status = "CLOSED"')
    total_pnl = c.fetchone()[0] or 0
    win_rate = (wins / closed * 100) if closed > 0 else 0
    balance = get_balance()
    conn.close()
    return {
        'total': total,
        'closed': closed,
        'open': total - closed,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'balance': balance,
        'initial_balance': 10000,
        'return_pct': ((balance - 10000) / 10000) * 100
    }

def print_performance_report():
    stats = get_performance_summary()
    print("\n" + "=" * 60)
    print("📊 PAPER TRADING PERFORMANCE — AGGRESSIVE")
    print("=" * 60)
    print(f"  Initial Balance:  $10,000.00")
    print(f"  Current Balance:  ${stats['balance']:.2f}")
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