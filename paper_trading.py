# paper_trading.py — Realistic Paper Trading Simulator
import sqlite3
import config
import random
from datetime import datetime

# === REALISTIC SETTINGS ===
TRADING_FEE_PCT = 0.001      # 0.1% per trade (Binance spot)
SLIPPAGE_PCT = 0.001         # 0.1% slippage
EXECUTION_DELAY_PCT = 0.0005 # 0.05% random delay

def init_paper_account():
    """Initialize paper trading account with realistic settings."""
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
            fees REAL DEFAULT 0,
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
    print("[Paper] Account initialized with $10,000 (fees & slippage simulated)")

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

def calculate_position_size(balance, entry_price, stop_loss, risk_percent=0.02):
    risk_amount = balance * risk_percent
    stop_loss_pct = abs((stop_loss - entry_price) / entry_price) if entry_price != 0 else 0.01
    if stop_loss_pct == 0:
        stop_loss_pct = 0.01
    position_size = risk_amount / (entry_price * stop_loss_pct)
    return position_size

def open_paper_trade(signal_id, coin, action, entry, target, stop):
    balance = get_balance()
    
    # Slippage on entry
    slippage_shift = random.uniform(-SLIPPAGE_PCT, SLIPPAGE_PCT)
    adjusted_entry = entry * (1 + slippage_shift)
    if action == 'BUY':
        adjusted_entry = max(adjusted_entry, entry * 0.995)
    else:
        adjusted_entry = min(adjusted_entry, entry * 1.005)
    
    # Execution delay
    delay_shift = random.uniform(-EXECUTION_DELAY_PCT, EXECUTION_DELAY_PCT)
    final_entry = adjusted_entry * (1 + delay_shift)
    
    position_size = calculate_position_size(balance, final_entry, stop)
    
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO paper_trades (signal_id, coin, action, entry_price, target, stop_loss, position_size, entry_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (signal_id, coin, action, final_entry, target, stop, position_size, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    print(f"[Paper] {action} {coin} @ ${final_entry:.2f} (size: {position_size:.4f})")

def close_paper_trade(trade_id, exit_price, reason):
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT coin, action, entry_price, position_size FROM paper_trades WHERE id = ?', (trade_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return
    coin, action, entry, position_size = row
    
    # Slippage on exit
    slippage_shift = random.uniform(-SLIPPAGE_PCT, SLIPPAGE_PCT)
    exit_price_adj = exit_price * (1 + slippage_shift)
    
    # Gross PnL
    if action == 'BUY':
        gross_pnl = (exit_price_adj - entry) * position_size
    else:
        gross_pnl = (entry - exit_price_adj) * position_size
    
    # Trading fees
    fee = abs(gross_pnl) * TRADING_FEE_PCT
    pnl_usd = gross_pnl - fee
    pnl_pct = (pnl_usd / (entry * position_size)) * 100 if (entry * position_size) != 0 else 0
    
    c.execute('''
        UPDATE paper_trades 
        SET exit_price = ?, pnl_pct = ?, pnl_usd = ?, fees = ?, status = 'CLOSED', exit_time = ?
        WHERE id = ?
    ''', (exit_price_adj, pnl_pct, pnl_usd, fee, datetime.now().isoformat(), trade_id))
    conn.commit()
    conn.close()
    
    balance = get_balance()
    new_balance = balance + pnl_usd
    update_balance(new_balance)
    
    emoji = "✅" if pnl_usd > 0 else "❌"
    print(f"[Paper] {emoji} {coin} closed: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%) | Fee: ${fee:.2f} | Balance: ${new_balance:.2f}")

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
    c.execute('SELECT SUM(fees) FROM paper_trades WHERE status = "CLOSED"')
    total_fees = c.fetchone()[0] or 0
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
        'total_fees': total_fees,
        'balance': balance,
        'initial_balance': 10000,
        'return_pct': ((balance - 10000) / 10000) * 100
    }

def print_performance_report():
    stats = get_performance_summary()
    print("\n" + "=" * 60)
    print("📊 PAPER TRADING PERFORMANCE")
    print("=" * 60)
    print(f"  Initial Balance:  $10,000.00")
    print(f"  Current Balance:  ${stats['balance']:.2f}")
    print(f"  Total Return:     {stats['return_pct']:+.2f}%")
    print(f"  Total PnL:        ${stats['total_pnl']:+.2f}")
    print(f"  Total Fees Paid:  ${stats['total_fees']:.2f}")
    print("-" * 60)
    print(f"  Total Trades:     {stats['total']}")
    print(f"  Open:             {stats['open']}")
    print(f"  Closed:           {stats['closed']}")
    print(f"  Wins:             {stats['wins']}")
    print(f"  Losses:           {stats['losses']}")
    print(f"  Win Rate:         {stats['win_rate']:.1f}%")
    print("=" * 60)