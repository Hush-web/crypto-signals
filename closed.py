import sqlite3

conn = sqlite3.connect('signals.db')
c = conn.cursor()

c.execute('''
    SELECT id, coin, action, entry_price, exit_price, pnl_pct, exit_reason
    FROM signals
    WHERE status = "CLOSED"
    ORDER BY id DESC
    LIMIT 10
''')
rows = c.fetchall()

print("=== CLOSED TRADES (Last 10) ===")
if rows:
    for row in rows:
        print(f"ID: {row[0]}, {row[1]} {row[2]}, Entry: {row[3]:.2f}, Exit: {row[4]:.2f}, PnL: {row[5]:.2f}%, Reason: {row[6]}")
else:
    print("No closed trades found.")

conn.close()