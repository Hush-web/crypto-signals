# Crypto Signal System

## Overview
Automated crypto signal bot using multi-strategy ensemble, sentiment, and whale tracking.

- 5 technical strategies (RSI, EMA, MACD, Bollinger, SuperTrend)
- Fear & Greed sentiment
- Whale Alert tracking
- PnL tracking with TP/SL auto-close
- Telegram alerts with Sniper Mode
- GitHub Actions (free, runs every 30 min)

## Setup

1. Copy `.env.example` to `.env` and add your Telegram credentials.
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python main.py`
4. Daily digest: `python main.py --digest`

## Pricing
- Free: 2 delayed signals/week
- Premium: $25/month

## ⚠️ Important
This is not financial advice. Trade at your own risk.