# force_close.py
import sqlite3

conn = sqlite3.connect('signals.db')
c = conn.cursor()

# Force close the oldest pending trade (ID 1)
c.execute('''
    UPDATE signals 
    SET status = 'CLOSED', 
        exit_price = 63500, 
        pnl_pct = -0.53, 
        exit_reason = 'TEST'
    WHERE id = 1 AND status = 'pending'
''')

conn.commit()
conn.close()

print("✅ Trade ID 1 force closed for testing.")