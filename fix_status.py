# fix_status.py — Update all 'pending' trades to 'OPEN'
import sqlite3

conn = sqlite3.connect('signals.db')
c = conn.cursor()

# Update all pending trades to OPEN
c.execute("UPDATE signals SET status = 'OPEN' WHERE status = 'pending'")
updated = c.rowcount
conn.commit()
conn.close()

print(f"✅ Updated {updated} trades from 'pending' to 'OPEN'")
print("   Now run 'python main.py' to check open trades against live prices.")