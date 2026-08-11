# database.py — with automatic migration
import sqlite3
import csv
import config

def init_db():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    
    # Create signals table (if not exists)
    c.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            coin TEXT,
            action TEXT,
            entry_price REAL,
            target REAL,
            stop_loss REAL,
            confidence TEXT,
            reason TEXT
        )
    ''')
    
    # Add new columns if they don't exist (migration)
    c.execute("PRAGMA table_info(signals)")
    existing_cols = [row[1] for row in c.fetchall()]
    
    new_cols = {
        'status': 'TEXT DEFAULT "OPEN"',
        'exit_price': 'REAL DEFAULT 0',
        'pnl_pct': 'REAL DEFAULT 0',
        'exit_reason': 'TEXT DEFAULT NULL'
    }
    
    for col, definition in new_cols.items():
        if col not in existing_cols:
            c.execute(f'ALTER TABLE signals ADD COLUMN {col} {definition}')
    
    # Create polls table
    c.execute('''
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            question TEXT,
            up_votes INTEGER DEFAULT 0,
            down_votes INTEGER DEFAULT 0,
            result TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[DB] Schema ready (migration applied if needed)")

def insert_signal(signal):
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO signals (timestamp, coin, action, entry_price, target, stop_loss, confidence, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (signal['timestamp'], signal['coin'], signal['action'],
          signal['entry_price'], signal['target'], signal['stop_loss'],
          signal['confidence'], signal['reason']))
    conn.commit()
    conn.close()

def get_open_trades():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, coin, action, entry_price, target, stop_loss FROM signals WHERE status = "OPEN"')
    rows = c.fetchall()
    conn.close()
    return rows

def close_trade(trade_id, exit_price, pnl_pct, reason):
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE signals SET status = 'CLOSED', exit_price = ?, pnl_pct = ?, exit_reason = ?
        WHERE id = ?
    ''', (exit_price, pnl_pct, reason, trade_id))
    conn.commit()
    conn.close()

def get_pnl_metrics(days=30):
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            SELECT pnl_pct FROM signals WHERE status = 'CLOSED' AND timestamp > datetime('now', ?)
        ''', (f'-{days} days',))
        rows = c.fetchall()
    except sqlite3.OperationalError:
        # Column might not exist yet; return empty
        rows = []
    conn.close()
    if not rows:
        return {'total_trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0, 'total_pnl': 0, 'avg_win': 0, 'avg_loss': 0}
    pnls = [r[0] for r in rows]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    return {
        'total_trades': len(rows),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': len(wins) / len(rows) * 100 if rows else 0,
        'total_pnl': sum(pnls),
        'avg_win': sum(wins) / len(wins) if wins else 0,
        'avg_loss': sum(losses) / len(losses) if losses else 0,
    }

def export_csv(path=None):
    path = path or config.CSV_EXPORT_PATH
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM signals ORDER BY id DESC')
    rows = c.fetchall()
    cols = [desc[0] for desc in c.description]
    conn.close()
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)
    return path