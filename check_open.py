# check_open.py
import sqlite3

conn = sqlite3.connect('signals.db')
c = conn.cursor()

c.execute('SELECT id, coin, action, entry_price, target, stop_loss, status FROM signals WHERE status = "OPEN" ORDER BY id DESC')
rows = c.fetchall()

print("=== OPEN TRADES ===")
if rows:
    for row in rows:
        print(f"ID: {row[0]}, {row[1]} {row[2]}, Entry: {row[3]:.2f}, Target: {row[4]:.2f}, Stop: {row[5]:.2f}, Status: {row[6]}")
else:
    print("No open trades.")

conn.close()