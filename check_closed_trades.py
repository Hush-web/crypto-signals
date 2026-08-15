import sqlite3
import config

conn = sqlite3.connect(config.DB_PATH)
c = conn.cursor()
c.execute('SELECT id, coin, action, entry_price, exit_price, pnl_pct FROM paper_trades WHERE status = "CLOSED"')
rows = c.fetchall()
print('Closed trades:', len(rows))
for r in rows:
    print(f'ID:{r[0]} {r[1]} {r[2]} entry={r[3]:.2f} exit={r[4]:.2f} PnL={r[5]:.2f}%')
conn.close()