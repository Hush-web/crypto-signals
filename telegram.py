# telegram.py — with Sniper Mode
import requests
import config
import json

def get_signal_tag(confidence):
    if confidence == 'HIGH':
        return '🎯 SNIPER MODE'
    elif confidence == 'MEDIUM':
        return '📡 LASER LOCKED'
    else:
        return '🔭 SCOUTING'

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

def send_signal(signal):
    if signal['action'] == 'HOLD':
        return
    
    tag = get_signal_tag(signal['confidence'])
    
    msg = f"""
{tag} — {signal['coin']}

Action: {signal['action']}
Entry: ${signal['entry_price']}
Target: ${signal['target']} (+{config.TARGET_PCT*100}%)
Stop Loss: ${signal['stop_loss']} (-{config.STOP_LOSS_PCT*100}%)

📈 Reason: {signal['reason']}
🔒 Confidence: {signal['confidence']}

⚠️ Not financial advice.
"""
    send_telegram(msg)

def send_digest(digest):
    send_telegram(digest)