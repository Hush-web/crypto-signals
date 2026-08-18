# reset_db.py — Reset paper trading database to clean state
import sqlite3
import config
from datetime import datetime

def reset_database():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()

    c.execute('DELETE FROM paper_trades')
    c.execute('DELETE FROM paper_account')

    c.execute('''
        INSERT INTO paper_account (cash, equity, updated_at)
        VALUES (10000, 10000, ?)
    ''', (datetime.now().isoformat(),))

    c.execute('DELETE FROM sqlite_sequence WHERE name IN ("paper_trades", "paper_account")')

    conn.commit()
    conn.close()
    print('✅ Database reset. Fresh start with $10,000 cash.')

if __name__ == '__main__':
    reset_database()