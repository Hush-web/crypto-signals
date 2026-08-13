import sqlite3

conn = sqlite3.connect('signals.db')
c = conn.cursor()

c.execute('''
    SELECT id, coin, action, entry_price, target, stop_loss,
           (target - entry_price) / entry_price * 100 as tp_pct,
           (stop_loss - entry_price) / entry_price * 100 as sl_pct
    FROM signals
    WHERE status = 'OPEN'
    ORDER BY id DESC
    LIMIT 10
''')

rows = c.fetchall()
for row in rows:
    print(row)

conn.close()