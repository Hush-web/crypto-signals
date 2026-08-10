"""
main.py — Entry point. Run this locally or via GitHub Actions.

Usage:
    python main.py                # generate signals for all coins in config.py
    python main.py --coins BTC-USD ETH-USD
    python main.py --no-telegram  # generate + save, but don't send alerts
    python main.py --winrate      # just print the current win rate and exit
"""

import argparse
import sys

import config
import database
import signals as signal_engine
import telegram


def run(coins=None, send_alerts=True, export_csv=True):
    print(f"[main] Starting signal run for {coins or config.COINS}")
    database.init_db()

    results = signal_engine.generate_all_signals(coins)

    fired = []
    for sig in results:
        coin = sig["coin"]
        action = sig["action"]

        if action == "ERROR":
            print(f"[main]  {coin}: ERROR — {sig['reason']}")
            continue

        if action == "HOLD":
            print(f"[main]  {coin}: HOLD (no confluence)")
            if config.ONLY_ACT_ON_SIGNALS:
                continue

        print(
            f"[main]  {coin}: {action} @ {sig['entry_price']} "
            f"(confidence={sig['confidence']}) — {sig['reason']}"
        )

        signal_id = database.insert_signal(sig)
        sig["id"] = signal_id
        fired.append(sig)

        if send_alerts and action in ("BUY", "SELL"):
            ok = telegram.send_signal_alert(sig)
            if not ok:
                print(f"[main]  Telegram alert failed for {coin} (see log above)")

    if send_alerts:
        telegram.send_summary(results)

    if export_csv:
        path = database.export_csv()
        print(f"[main] Exported all signals to {path}")

    print(f"[main] Done. {len(fired)} signal(s) fired this run.")
    return fired


def print_win_rate():
    database.init_db()
    stats = database.get_win_rate()
    print("=== Win Rate ===")
    print(f"Wins:     {stats['wins']}")
    print(f"Losses:   {stats['losses']}")
    print(f"Pending:  {stats['pending']}")
    print(f"Resolved: {stats['resolved']}")
    print(f"Win rate: {stats['win_rate_pct']}%")


def main():
    parser = argparse.ArgumentParser(description="Crypto signal generator")
    parser.add_argument("--coins", nargs="+", help="Override coin list, e.g. --coins BTC-USD ETH-USD")
    parser.add_argument("--no-telegram", action="store_true", help="Don't send Telegram alerts")
    parser.add_argument("--no-csv", action="store_true", help="Don't export CSV")
    parser.add_argument("--winrate", action="store_true", help="Print win rate and exit")
    args = parser.parse_args()

    if args.winrate:
        print_win_rate()
        sys.exit(0)

    run(
        coins=args.coins,
        send_alerts=not args.no_telegram,
        export_csv=not args.no_csv,
    )


if __name__ == "__main__":
    main()
