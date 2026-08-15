import sqlite3
import config

def main():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()

    print("\n=== SIGNALS vs PAPER TRADES (Last 24h) ===\n")

    # Total signals
    c.execute("SELECT COUNT(*) FROM signals WHERE timestamp > datetime('now', '-1 day')")
    total_signals = c.fetchone()[0]
    print(f"Total signals in last 24h: {total_signals}")

    # Signals by action
    c.execute("SELECT action, COUNT(*) FROM signals WHERE timestamp > datetime('now', '-1 day') GROUP BY action")
    actions = c.fetchall()
    print("\nSignal actions:")
    for action, count in actions:
        print(f"  {action}: {count}")

    # Paper trades opened in last 24h
    c.execute("SELECT COUNT(*) FROM paper_trades WHERE entry_time > datetime('now', '-1 day')")
    paper_trades = c.fetchone()[0]
    print(f"\nPaper trades opened in last 24h: {paper_trades}")

    # Signals without paper trades (only BUY/SELL)
    c.execute("""
        SELECT COUNT(*) FROM signals s
        LEFT JOIN paper_trades pt ON pt.signal_id = s.id
        WHERE s.timestamp > datetime('now', '-1 day')
        AND s.action IN ('BUY', 'SELL')
        AND pt.id IS NULL
    """)
    missing_paper = c.fetchone()[0]
    print(f"BUY/SELL signals WITHOUT paper trades: {missing_paper}")

    # Show recent signals with paper trade status
    c.execute("""
        SELECT 
            s.id, s.coin, s.action, s.timestamp,
            CASE WHEN pt.id IS NOT NULL THEN '✅ PAPER' ELSE '❌ NO PAPER' END AS paper_status
        FROM signals s
        LEFT JOIN paper_trades pt ON pt.signal_id = s.id
        WHERE s.timestamp > datetime('now', '-1 day')
        ORDER BY s.id DESC
        LIMIT 15
    """)
    rows = c.fetchall()
    print("\nRecent signals (last 15):")
    for row in rows:
        print(f"  ID:{row[0]} {row[1]} {row[2]} {row[3][:16]} => {row[4]}")

    conn.close()

if __name__ == "__main__":
    main()