# 🤖 Crypto Signal Bot

Automated crypto trading signal generator using RSI, EMA crossover, and MACD.
Runs on a free GitHub Actions schedule (every 6 hours) — **no paid API keys,
no servers, no hosting bill.** Signals are saved to SQLite, exported to CSV,
and pushed to Telegram.

> ⚠️ **This is not financial advice.** Signals are generated from simple
> technical indicators and can be wrong. Never trade money you can't afford
> to lose, and don't rely solely on this tool (or any tool) to make trading
> decisions. Past signal performance does not guarantee future results.

---

## 📁 Project Structure

```
crypto-signals/
├── main.py                      # entry point — run this
├── signals.py                   # RSI / EMA / MACD signal logic
├── database.py                  # SQLite storage + win-rate tracking
├── telegram.py                  # Telegram alert formatting/sending
├── config.py                    # coins, thresholds, all settings
├── requirements.txt
├── .env.example                 # copy to .env for local runs
├── strategies/
│   ├── __init__.py
│   └── example_strategy.py      # template for writing your own strategy
└── .github/workflows/
    └── signals.yml               # runs every 6h on GitHub Actions
```

---

## 🚀 Setup (5 minutes)

### 1. Get the code onto GitHub
Create a new **private** GitHub repo and push this folder into it:
```bash
cd crypto-signals
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```
Private is recommended if you plan to sell access — you don't want to give
the strategy away for free in a public repo.

### 2. Create a Telegram bot (2 minutes)
1. Open Telegram, search for **@BotFather**, and send `/newbot`.
2. Follow the prompts, choose a name — BotFather gives you a **bot token**
   like `123456789:AAExampleTokenxxxxxxxxxxxxxxxxxxx`.
3. Send your new bot any message (e.g. "hi") so it's allowed to reply to you.
4. Visit this URL in your browser (replace `<TOKEN>`):
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. Find `"chat":{"id":123456789,...}` in the JSON response — that number is
   your **chat ID**.

For a group chat instead of a DM: add the bot to the group, send a message
in the group, then use the same `getUpdates` URL — the chat id will be
negative (e.g. `-1001234567890`).

### 3. Add your secrets to GitHub
In your repo: **Settings → Secrets and variables → Actions → New repository secret**
Add two secrets:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 4. Turn on the workflow
Go to the **Actions** tab of your repo → you'll see "Crypto Signal Bot" →
click **Enable workflow** if prompted. It will now run automatically every
6 hours. You can also trigger it manually any time: Actions → Crypto Signal
Bot → **Run workflow**.

That's it — you're live. ✅

---

## 🖥️ Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your .env
cp .env.example .env
# edit .env and paste in your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID

# 3. Load the .env (or just export the vars manually) and run
export $(cat .env | xargs)   # macOS/Linux
python main.py
```

Useful flags:
```bash
python main.py --coins BTC-USD ETH-USD   # only scan specific coins
python main.py --no-telegram             # generate + save signals, skip alerts
python main.py --no-csv                  # skip CSV export
python main.py --winrate                 # print win/loss stats and exit
```

---

## ⚙️ Configuring Coins & Thresholds

Everything lives in `config.py`:

```python
COINS = ["BTC-USD", "ETH-USD", "SOL-USD", ...]   # any Yahoo Finance ticker

RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

EMA_FAST = 9
EMA_SLOW = 21

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

TARGET_PCT = 0.03      # +3% take-profit
STOP_LOSS_PCT = 0.02   # -2% stop loss

MIN_SCORE_TO_FIRE = 2  # need 2 of 3 indicators to agree before firing
```

To add a coin, just add its Yahoo Finance ticker to `COINS` (crypto tickers
are `SYMBOL-USD`, e.g. `AVAX-USD`, `LINK-USD`, `MATIC-USD`).

To change how "picky" the bot is, raise `MIN_SCORE_TO_FIRE` to `3` (only
fire when RSI, EMA, and MACD all agree — fewer, higher-conviction signals)
or lower it to `1` (more signals, lower average quality).

---

## 🧠 How Signals Are Generated

Each run, for every coin, three indicators "vote":

| Indicator | Votes BUY when... | Votes SELL when... |
|---|---|---|
| RSI | below `RSI_OVERSOLD` (default 30) | above `RSI_OVERBOUGHT` (default 70) |
| EMA crossover | fast EMA crosses above / stays above slow EMA | fast EMA crosses below / stays below slow EMA |
| MACD | MACD line crosses above / stays above signal line | MACD line crosses below / stays below signal line |

- **3/3 agree → HIGH confidence**
- **2/3 agree → MEDIUM confidence**
- **1/3 agree → LOW confidence** (not fired by default — raise/lower `MIN_SCORE_TO_FIRE` to change this)
- Otherwise → HOLD (no signal, nothing sent/saved)

Entry price is the latest close. Target and stop loss are simple
percentage offsets (`TARGET_PCT` / `STOP_LOSS_PCT`) from entry — adjust
these in `config.py` to match your own risk tolerance.

---

## 🗄️ Viewing Saved Signals

All signals persist in `signals.db` (SQLite) and get re-exported to
`signals_export.csv` every run. To inspect them:

```bash
# Quick look with the sqlite3 CLI
sqlite3 signals.db "SELECT timestamp, coin, action, confidence, status FROM signals ORDER BY timestamp DESC LIMIT 20;"

# Or just open signals_export.csv in Excel/Google Sheets
```

On GitHub Actions, the CSV is also uploaded as a downloadable **workflow
artifact** on every run (Actions tab → pick a run → Artifacts section),
and — if you keep the "commit database back to repo" step in the
workflow — `signals.db` and `signals_export.csv` get committed straight
back into your repo so history accumulates automatically.

---

## 📊 Tracking Win Rate

Signals start as `status = "pending"`. As trades play out, mark them:

```python
import database
database.update_status(signal_id=42, status="win")   # or "loss"
```

Then check your stats:
```bash
python main.py --winrate
```
```
=== Win Rate ===
Wins:     14
Losses:   6
Pending:  3
Resolved: 20
Win rate: 70.0%
```

There's also `database.auto_resolve_pending(current_prices)` in
`database.py` if you want to automate resolution by feeding it a
`{coin: current_price}` dict (e.g. from a scheduled job) — it marks a
signal `win` once price hits `target` or `loss` once it hits `stop_loss`.

---

## 🧩 Writing a Custom Strategy

See `strategies/example_strategy.py` for a template (a simple mean-reversion
band-breakout strategy). To wire your own strategy in:

1. Copy `example_strategy.py`, rename it, and write your own `evaluate(df)`
   function that returns `{"action", "confidence", "reason"}`.
2. In `signals.py`, import your strategy and call it inside
   `generate_signal()` — either alongside the existing RSI/EMA/MACD votes,
   or as a full replacement.

Keeping strategies in their own files makes it easy to A/B test different
approaches, or offer different strategies to different subscriber tiers.

---

## 💰 Using This as a Paid Product

A common setup:
- **Free tier**: run the bot on a public/free Telegram channel with signals
  delayed (e.g. only post them a few hours after generation), or limit to
  2 signals/week by filtering to `confidence == "HIGH"` only.
- **Premium ($25/mo)**: private Telegram channel/group, all signals in
  real-time, and optionally the reasoning (`reason` field) included.

To run two tiers, add a second Telegram chat ID (e.g.
`TELEGRAM_CHAT_ID_FREE` and `TELEGRAM_CHAT_ID_PREMIUM`) and adjust
`main.py` to send full detail to premium and a delayed/filtered subset to
free. Since Anthropic (the maker of Claude) doesn't offer financial or
legal advice, you should independently check what disclosures,
disclaimers, or licensing apply in your jurisdiction before selling
trading signals commercially — this generally falls under financial
promotion/advisory rules in many countries.

---

## 🛠️ Troubleshooting

| Problem | Likely cause / fix |
|---|---|
| `No data returned for <coin>` | Ticker may be wrong (must end in `-USD`), or Yahoo Finance rate-limited the request — wait and retry. |
| `Not enough candles for <coin>` | `LOOKBACK_PERIOD` too short for your `INTERVAL` — increase `LOOKBACK_PERIOD` in `config.py`. |
| Telegram messages not arriving | Double check `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`, and that you've messaged the bot at least once. Check the Action's logs for the exact HTTP error. |
| GitHub Action fails to push `signals.db` | Make sure `permissions: contents: write` is present in `signals.yml` (already included) and that branch protection rules on `main` allow the bot to push. |
| Duplicate signals every run | Expected if the same conditions persist across multiple 1h candles — raise `MIN_SCORE_TO_FIRE` or use a longer `INTERVAL` (e.g. `4h`) for less frequent, higher-conviction signals. |

---

## 📜 License / Disclaimer

Provided as-is, for educational purposes. Trading cryptocurrency carries
significant risk of loss. Nothing in this repository constitutes financial,
investment, or legal advice.
