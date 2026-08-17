import sqlite3
import config

conn = sqlite3.connect(config.DB_PATH)
c = conn.cursor()

# Delete all ARB-USD trades (permanently, not just close)
c.execute('DELETE FROM paper_trades WHERE coin = "ARB-USD"')
print(f'Deleted {c.rowcount} ARB-USD trades')

conn.commit()
conn.close()