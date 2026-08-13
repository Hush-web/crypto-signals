# backtest.py — Complete Backtest for All Coins
import sys
import pandas as pd
import numpy as np
import yfinance as yf
import config
import strategies

def backtest(coin='BTC-USD', days=180):
    print(f"\n🔍 Backtesting {coin} over {days} days...")
    print("=" * 60)
    
    # Fetch data
    df = yf.download(coin, period=f"{days}d", interval="1h", progress=False)
    if df.empty:
        print("No data.")
        return
    
    print(f"📊 Loaded {len(df)} candles.")
    
    trades = []
    in_position = False
    entry_price = 0
    entry_time = None
    trade_direction = None
    total_bars = len(df)
    vote_threshold = 3
    
    for i in range(20, total_bars):
        if i % 200 == 0:
            print(f"  Processing bar {i}/{total_bars}...")
        
        slice_df = df.iloc[:i+1]
        try:
            result = strategies.analyze_strategies(slice_df)
        except Exception as e:
            continue
        
        action = result['action']
        price = slice_df['Close'].iloc[-1]
        time = slice_df.index[-1]
        
        if action == 'HOLD':
            continue
        
        vote_buy = result['votes']['BUY']
        vote_sell = result['votes']['SELL']
        if vote_buy >= vote_threshold and vote_buy > vote_sell:
            signal_action = 'BUY'
        elif vote_sell >= vote_threshold and vote_sell > vote_buy:
            signal_action = 'SELL'
        else:
            continue
        
        if not in_position:
            entry_price = price
            entry_time = time
            in_position = True
            trade_direction = signal_action
        else:
            if signal_action != trade_direction:
                exit_price = price
                if trade_direction == 'BUY':
                    pnl = (exit_price - entry_price) / entry_price * 100
                else:
                    pnl = (entry_price - exit_price) / entry_price * 100
                trades.append({
                    'entry': entry_price,
                    'exit': exit_price,
                    'direction': trade_direction,
                    'pnl_pct': pnl,
                    'entry_time': entry_time,
                    'exit_time': time
                })
                entry_price = price
                entry_time = time
                trade_direction = signal_action
    
    if in_position:
        exit_price = df['Close'].iloc[-1]
        if trade_direction == 'BUY':
            pnl = (exit_price - entry_price) / entry_price * 100
        else:
            pnl = (entry_price - exit_price) / entry_price * 100
        trades.append({
            'entry': entry_price,
            'exit': exit_price,
            'direction': trade_direction,
            'pnl_pct': pnl,
            'entry_time': entry_time,
            'exit_time': df.index[-1]
        })
    
    if not trades:
        print("No trades were generated.")
        return
    
    df_trades = pd.DataFrame(trades)
    wins = df_trades[df_trades['pnl_pct'] > 0]
    losses = df_trades[df_trades['pnl_pct'] <= 0]
    total_trades = len(df_trades)
    win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
    avg_win = wins['pnl_pct'].mean() if not wins.empty else 0
    avg_loss = losses['pnl_pct'].mean() if not losses.empty else 0
    profit_factor = (wins['pnl_pct'].sum()) / abs(losses['pnl_pct'].sum()) if losses['pnl_pct'].sum() != 0 else float('inf')
    total_return = df_trades['pnl_pct'].sum()
    avg_trade = df_trades['pnl_pct'].mean()
    max_drawdown = df_trades['pnl_pct'].min()
    buy_hold_return = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100
    
    print(f"\n--- {coin} Backtest Results (5-Strategy Ensemble) ---")
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
    print(f"  Verdict:            {'✅ MAYBE profitable' if total_return > 0 and win_rate > 50 else '❌ likely not profitable'}")

if __name__ == "__main__":
    coin = sys.argv[1] if len(sys.argv) > 1 else 'BTC-USD'
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 180
    backtest(coin, days)