# check_all.py
import sqlite3

conn = sqlite3.connect('signals.db')
c = conn.cursor()

# Check how many total trades
c.execute('SELECT COUNT(*) FROM signals')
total = c.fetchone()[0]

# Check status distribution
c.execute('SELECT status, COUNT(*) FROM signals GROUP BY status')
status_counts = c.fetchall()

# Show last 5 trades with all columns
c.execute('SELECT * FROM signals ORDER BY id DESC LIMIT 5')
rows = c.fetchall()

# Get column names
col_names = [description[0] for description in c.description]

print(f"Total trades: {total}")
print("\nStatus distribution:")
for status, count in status_counts:
    print(f"  {status}: {count}")

print("\nLast 5 trades:")
for row in rows:
    print(dict(zip(col_names, row)))

conn.close()