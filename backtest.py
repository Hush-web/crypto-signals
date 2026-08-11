# backtest.py
import sys
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import config
import signals

def backtest(coin='BTC-USD', days=180):
    """
    Full backtest for SuperTrend strategy.
    Simulates trades based on SuperTrend crossovers.
    Prints performance metrics.
    """
    print(f"\n🔍 Backtesting {coin} over {days} days...\n")
    
    # Fetch data
    df = signals.fetch_ohlcv(coin, period=f"{days}d", interval="1h")
    df = signals.add_indicators(df)
    
    if df.empty:
        print("No data.")
        return

    # We'll simulate trades
    trades = []
    in_position = False
    entry_price = 0
    entry_time = None
    trade_direction = None  # 'BUY' or 'SELL'

    # Iterate through each row (skip first row because we need previous trend)
    for i in range(1, len(df)):
        prev_trend = df['SUPERTREND'].iloc[i-1]
        current_trend = df['SUPERTREND'].iloc[i]
        price = df['Close'].iloc[i]
        time = df.index[i]

        # Check for crossover
        # BUY signal: trend changed from -1 to 1 (bearish to bullish)
        if prev_trend == -1 and current_trend == 1:
            if not in_position:
                # Enter BUY
                entry_price = price
                entry_time = time
                in_position = True
                trade_direction = 'BUY'
            elif in_position and trade_direction == 'SELL':
                # Close previous SELL trade and open BUY
                exit_price = price
                trades.append({
                    'entry': entry_price,
                    'exit': exit_price,
                    'direction': trade_direction,
                    'profit_pct': (exit_price - entry_price) / entry_price * 100 if trade_direction == 'BUY' else (entry_price - exit_price) / entry_price * 100,
                    'entry_time': entry_time,
                    'exit_time': time
                })
                entry_price = price
                entry_time = time
                trade_direction = 'BUY'

        # SELL signal: trend changed from 1 to -1 (bullish to bearish)
        elif prev_trend == 1 and current_trend == -1:
            if not in_position:
                # Enter SELL
                entry_price = price
                entry_time = time
                in_position = True
                trade_direction = 'SELL'
            elif in_position and trade_direction == 'BUY':
                # Close previous BUY trade and open SELL
                exit_price = price
                trades.append({
                    'entry': entry_price,
                    'exit': exit_price,
                    'direction': trade_direction,
                    'profit_pct': (exit_price - entry_price) / entry_price * 100 if trade_direction == 'BUY' else (entry_price - exit_price) / entry_price * 100,
                    'entry_time': entry_time,
                    'exit_time': time
                })
                entry_price = price
                entry_time = time
                trade_direction = 'SELL'

    # Close any open position at the last price
    if in_position:
        exit_price = df['Close'].iloc[-1]
        trades.append({
            'entry': entry_price,
            'exit': exit_price,
            'direction': trade_direction,
            'profit_pct': (exit_price - entry_price) / entry_price * 100 if trade_direction == 'BUY' else (entry_price - exit_price) / entry_price * 100,
            'entry_time': entry_time,
            'exit_time': df.index[-1]
        })

    if not trades:
        print("No trades were generated.")
        return

    # --- Performance Metrics ---
    df_trades = pd.DataFrame(trades)
    wins = df_trades[df_trades['profit_pct'] > 0]
    losses = df_trades[df_trades['profit_pct'] <= 0]
    total_trades = len(df_trades)
    win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
    avg_win = wins['profit_pct'].mean() if not wins.empty else 0
    avg_loss = losses['profit_pct'].mean() if not losses.empty else 0
    profit_factor = (wins['profit_pct'].sum()) / abs(losses['profit_pct'].sum()) if losses['profit_pct'].sum() != 0 else float('inf')
    total_return = df_trades['profit_pct'].sum()
    avg_trade = df_trades['profit_pct'].mean()
    max_drawdown = df_trades['profit_pct'].min()
    # Buy & hold return
    buy_hold_return = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100

    print(f"--- {coin} Backtest Results ---")
    print(f"  Total trades:        {total_trades}")
    print(f"  Win rate:            {win_rate:.2f}%")
    print(f"  Avg win:             {avg_win:.2f}%")
    print(f"  Avg loss:            {avg_loss:.2f}%")
    print(f"  Profit factor:       {profit_factor:.2f}")
    print(f"  Total return:        {total_return:.2f}%")
    print(f"  Avg trade:           {avg_trade:.2f}%")
    print(f"  Max drawdown:        {max_drawdown:.2f}%")
    print(f"  Buy & hold return:   {buy_hold_return:.2f}%")
    print(f"  Beat buy & hold:     {'YES' if total_return > buy_hold_return else 'NO'}")
    print(f"\n  Exit reasons:      (not tracked in this simple backtest)")
    print("  Verdict:           ", "✅ MAYBE profitable" if total_return > 0 and win_rate > 50 else "❌ likely not profitable")

if __name__ == "__main__":
    coin = sys.argv[1] if len(sys.argv) > 1 else 'BTC-USD'
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 180
    backtest(coin, days)