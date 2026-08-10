"""
database.py — SQLite persistence for generated signals.

Table: signals
    id            INTEGER PRIMARY KEY
    timestamp     TEXT     (ISO 8601, UTC)
    coin          TEXT
    action        TEXT     (BUY / SELL)
    entry_price   REAL
    target        REAL
    stop_loss     REAL
    confidence    TEXT     (HIGH / MEDIUM / LOW)
    reason        TEXT
    status        TEXT     (pending / win / loss)
"""

import sqlite3
import csv
from contextlib import contextmanager
from datetime import datetime, timezone

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    coin TEXT NOT NULL,
    action TEXT NOT NULL,
    entry_price REAL NOT NULL,
    target REAL NOT NULL,
    stop_loss REAL NOT NULL,
    confidence TEXT NOT NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
);
"""


@contextmanager
def get_conn(db_path: str = None):
    path = db_path or config.DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str = None):
    """Create the signals table if it doesn't already exist."""
    with get_conn(db_path) as conn:
        conn.execute(SCHEMA)


def insert_signal(signal: dict, db_path: str = None) -> int:
    """Insert a signal dict and return its new row id."""
    with get_conn(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO signals
                (timestamp, coin, action, entry_price, target, stop_loss,
                 confidence, reason, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal.get("timestamp", datetime.now(timezone.utc).isoformat()),
                signal["coin"],
                signal["action"],
                signal["entry_price"],
                signal["target"],
                signal["stop_loss"],
                signal["confidence"],
                signal.get("reason", ""),
                signal.get("status", "pending"),
            ),
        )
        return cur.lastrowid


def update_status(signal_id: int, status: str, db_path: str = None):
    """Mark a signal as 'win', 'loss', or back to 'pending'."""
    if status not in ("pending", "win", "loss"):
        raise ValueError("status must be one of: pending, win, loss")
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE signals SET status = ? WHERE id = ?", (status, signal_id)
        )


def get_all_signals(db_path: str = None):
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM signals ORDER BY timestamp DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_pending_signals(coin: str = None, db_path: str = None):
    with get_conn(db_path) as conn:
        if coin:
            rows = conn.execute(
                "SELECT * FROM signals WHERE status = 'pending' AND coin = ?",
                (coin,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM signals WHERE status = 'pending'"
            ).fetchall()
        return [dict(r) for r in rows]


def get_win_rate(db_path: str = None) -> dict:
    """Return win/loss counts and win rate % across all resolved signals."""
    with get_conn(db_path) as conn:
        wins = conn.execute(
            "SELECT COUNT(*) FROM signals WHERE status = 'win'"
        ).fetchone()[0]
        losses = conn.execute(
            "SELECT COUNT(*) FROM signals WHERE status = 'loss'"
        ).fetchone()[0]
        pending = conn.execute(
            "SELECT COUNT(*) FROM signals WHERE status = 'pending'"
        ).fetchone()[0]

    resolved = wins + losses
    win_rate = (wins / resolved * 100) if resolved else 0.0
    return {
        "wins": wins,
        "losses": losses,
        "pending": pending,
        "resolved": resolved,
        "win_rate_pct": round(win_rate, 2),
    }


def export_csv(csv_path: str = None, db_path: str = None):
    """Dump the full signals table to a CSV file (used for the GitHub Actions artifact)."""
    csv_path = csv_path or config.CSV_EXPORT_PATH
    signals = get_all_signals(db_path)
    fieldnames = [
        "id", "timestamp", "coin", "action", "entry_price", "target",
        "stop_loss", "confidence", "reason", "status",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in signals:
            writer.writerow(row)
    return csv_path


def auto_resolve_pending(current_prices: dict, db_path: str = None):
    """
    Optional helper: given {coin: current_price}, automatically mark pending
    signals as 'win' if price hit target, 'loss' if it hit stop_loss.
    Leaves the signal as 'pending' if neither level has been reached yet.
    """
    pending = get_pending_signals(db_path=db_path)
    updated = []
    for sig in pending:
        price = current_prices.get(sig["coin"])
        if price is None:
            continue
        if sig["action"] == "BUY":
            if price >= sig["target"]:
                update_status(sig["id"], "win", db_path)
                updated.append((sig["id"], "win"))
            elif price <= sig["stop_loss"]:
                update_status(sig["id"], "loss", db_path)
                updated.append((sig["id"], "loss"))
        elif sig["action"] == "SELL":
            if price <= sig["target"]:
                update_status(sig["id"], "win", db_path)
                updated.append((sig["id"], "win"))
            elif price >= sig["stop_loss"]:
                update_status(sig["id"], "loss", db_path)
                updated.append((sig["id"], "loss"))
    return updated
