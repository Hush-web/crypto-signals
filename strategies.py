# strategies.py — 5 Strategies + Consensus Voting
import pandas as pd
import numpy as np
import config

class StrategyBase:
    def __init__(self, df):
        self.df = df.copy()
        self._calculate()
    def _calculate(self):
        raise NotImplementedError
    def signal(self):
        raise NotImplementedError

class RSIStrategy(StrategyBase):
    def _calculate(self):
        delta = self.df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        self.df['RSI'] = 100 - (100 / (1 + rs))
    def signal(self):
        latest = self.df.iloc[-1]
        rsi = latest['RSI']
        if rsi < 25:
            return 'BUY', 'HIGH', f'RSI oversold ({rsi:.1f})'
        elif rsi > 75:
            return 'SELL', 'HIGH', f'RSI overbought ({rsi:.1f})'
        return 'HOLD', 'LOW', f'RSI neutral ({rsi:.1f})'

class EMATrendStrategy(StrategyBase):
    def _calculate(self):
        self.df['EMA_50'] = self.df['Close'].ewm(span=50).mean()
        self.df['EMA_200'] = self.df['Close'].ewm(span=200).mean()
    def signal(self):
        latest = self.df.iloc[-1]
        price = latest['Close']
        ema50 = latest['EMA_50']
        ema200 = latest['EMA_200']
        if price > ema200 and price > ema50:
            return 'BUY', 'MEDIUM', 'Uptrend (price above EMAs)'
        elif price < ema200 and price < ema50:
            return 'SELL', 'MEDIUM', 'Downtrend (price below EMAs)'
        return 'HOLD', 'LOW', 'Sideways trend'

class MACDStrategy(StrategyBase):
    def _calculate(self):
        exp1 = self.df['Close'].ewm(span=12).mean()
        exp2 = self.df['Close'].ewm(span=26).mean()
        self.df['MACD'] = exp1 - exp2
        self.df['MACD_Signal'] = self.df['MACD'].ewm(span=9).mean()
    def signal(self):
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2] if len(self.df) > 1 else latest
        if prev['MACD'] <= prev['MACD_Signal'] and latest['MACD'] > latest['MACD_Signal']:
            return 'BUY', 'HIGH', 'MACD bullish crossover'
        elif prev['MACD'] >= prev['MACD_Signal'] and latest['MACD'] < latest['MACD_Signal']:
            return 'SELL', 'HIGH', 'MACD bearish crossover'
        elif latest['MACD'] > latest['MACD_Signal']:
            return 'BUY', 'MEDIUM', 'MACD above signal'
        elif latest['MACD'] < latest['MACD_Signal']:
            return 'SELL', 'MEDIUM', 'MACD below signal'
        return 'HOLD', 'LOW', 'MACD neutral'

class BollingerStrategy(StrategyBase):
    def _calculate(self):
        sma20 = self.df['Close'].rolling(20).mean()
        std20 = self.df['Close'].rolling(20).std()
        self.df['BB_Upper'] = sma20 + 2 * std20
        self.df['BB_Lower'] = sma20 - 2 * std20
    def signal(self):
        latest = self.df.iloc[-1]
        price = latest['Close']
        upper = latest['BB_Upper']
        lower = latest['BB_Lower']
        if price < lower:
            return 'BUY', 'HIGH', f'Price below lower band'
        elif price > upper:
            return 'SELL', 'HIGH', f'Price above upper band'
        return 'HOLD', 'MEDIUM', f'Price within bands'

class SuperTrendStrategy(StrategyBase):
    def _calculate(self):
        high, low, close = self.df['High'], self.df['Low'], self.df['Close']
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(10).mean()
        upper = (high + low) / 2 + 3 * atr
        lower = (high + low) / 2 - 3 * atr
        self.df['ST_Trend'] = 1
        for i in range(1, len(self.df)):
            if close.iloc[i] > upper.iloc[i-1]:
                self.df.loc[self.df.index[i], 'ST_Trend'] = 1
            elif close.iloc[i] < lower.iloc[i-1]:
                self.df.loc[self.df.index[i], 'ST_Trend'] = -1
            else:
                self.df.loc[self.df.index[i], 'ST_Trend'] = self.df['ST_Trend'].iloc[i-1]
    def signal(self):
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2] if len(self.df) > 1 else latest
        if prev['ST_Trend'] == -1 and latest['ST_Trend'] == 1:
            return 'BUY', 'HIGH', 'SuperTrend bullish crossover'
        elif prev['ST_Trend'] == 1 and latest['ST_Trend'] == -1:
            return 'SELL', 'HIGH', 'SuperTrend bearish crossover'
        elif latest['ST_Trend'] == 1:
            return 'BUY', 'MEDIUM', 'In uptrend'
        elif latest['ST_Trend'] == -1:
            return 'SELL', 'MEDIUM', 'In downtrend'
        return 'HOLD', 'LOW', 'Trend unclear'

def analyze_strategies(df):
    strategies = [
        RSIStrategy(df), EMATrendStrategy(df), MACDStrategy(df),
        BollingerStrategy(df), SuperTrendStrategy(df)
    ]
    results = []
    for s in strategies:
        action, confidence, reason = s.signal()
        results.append({'strategy': s.__class__.__name__, 'action': action, 'confidence': confidence, 'reason': reason})
    
    votes = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    for r in results:
        votes[r['action']] += 1
    
    if votes['BUY'] > votes['SELL'] and votes['BUY'] >= 2:
        action = 'BUY'
        confidence = 'HIGH' if votes['BUY'] >= 4 else 'MEDIUM'
    elif votes['SELL'] > votes['BUY'] and votes['SELL'] >= 2:
        action = 'SELL'
        confidence = 'HIGH' if votes['SELL'] >= 4 else 'MEDIUM'
    else:
        action = 'HOLD'
        confidence = 'LOW'
    
    reasons = [f"{r['strategy']}: {r['reason']}" for r in results if r['action'] != 'HOLD']
    return {'action': action, 'confidence': confidence, 'votes': votes, 'strategy_results': results, 'reason': ' | '.join(reasons) if reasons else 'No clear signal'}
