# telegram.py — Telegram Alerts
import requests
import config
import json
from datetime import datetime

last_sent = {}

def send_telegram(message):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {'chat_id': config.TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

def send_poll(question, options=['🟢 UP', '🔴 DOWN']):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendPoll"
    data = {'chat_id': config.TELEGRAM_CHAT_ID, 'question': question, 'options': json.dumps(options)}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

def get_signal_tag(confidence, votes):
    if confidence == 'HIGH' and votes >= 5:
        return '🎯 ELITE SNIPER', '🔥🔥🔥'
    elif confidence == 'HIGH':
        return '🎯 SNIPER MODE', '🔥🔥'
    elif confidence == 'MEDIUM':
        return '📡 LASER LOCKED', '🔥'
    elif confidence == 'LOW' and votes >= 2:
        return '🔭 SCOUTING', '👀'
    else:
        return '⚡ MONITORING', '🔍'

def send_signal(signal):
    if signal['action'] == 'HOLD':
        return
    tag, fire = get_signal_tag(signal['confidence'], signal['votes'].get('BUY', 0) + signal['votes'].get('SELL', 0))
    msg = f"""
{tag} — {signal['coin']}

Action: <b>{signal['action']}</b>
Entry: ${signal['entry_price']}
Target: ${signal['target']} (+{config.TARGET_PCT*100}%)
Stop: ${signal['stop_loss']} (-{config.STOP_LOSS_PCT*100}%)

📈 Reason: {signal['reason']}
🔒 Confidence: {signal['confidence']}

⚠️ Not financial advice.
"""
    send_telegram(msg)

def send_batch(signals, batch_id):
    active = [s for s in signals if s['action'] not in ['HOLD', 'ERROR']]
    if not active:
        return
    now = datetime.now().strftime('%H:%M:%S')
    header = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 BATCH #{batch_id} — {now}
📈 {len(active)} signal(s)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    send_telegram(header)
    for sig in active:
        send_signal(sig)
        send_telegram("━" * 40)

def send_digest(digest):
    send_telegram(digest)