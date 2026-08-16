import sqlite3
import config
import os

def reset_all():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()
    
    # Clear all tables
    c.execute('DELETE FROM signals')
    c.execute('DELETE FROM paper_trades')
    c.execute('DELETE FROM paper_account')
    
    # Reset account
    c.execute('''
        INSERT INTO paper_account (balance, equity, updated_at)
        VALUES (10000, 10000, datetime('now'))
    ''')
    
    # Reset counters
    c.execute('DELETE FROM sqlite_sequence')
    
    conn.commit()
    conn.close()
    print('✅ All data cleared. Account reset to $10,000.')

if __name__ == "__main__":
    reset_all()