# hard_reset.py — Hard reset: drop and recreate tables
import sqlite3
import config

def hard_reset():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    
    # Drop all paper trading tables
    c.execute('DROP TABLE IF EXISTS paper_trades')
    c.execute('DROP TABLE IF EXISTS paper_account')
    
    # Recreate them with correct schema (copy from paper_trading.init_paper_account)
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
    
    # Insert initial account
    from datetime import datetime
    c.execute('INSERT INTO paper_account (cash, equity, updated_at) VALUES (10000, 10000, ?)', (datetime.now().isoformat(),))
    
    conn.commit()
    conn.close()
    print('✅ Hard reset complete. All paper trades cleared. Account reset to $10,000 cash.')

if __name__ == '__main__':
    hard_reset()