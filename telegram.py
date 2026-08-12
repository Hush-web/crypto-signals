# telegram.py — with Poll Support
import requests
import config
import json
from datetime import datetime

# Store last sent signal per coin to avoid duplicates
last_sent = {}

def get_signal_tag(confidence, votes):
    if confidence == 'HIGH' and votes >= 5:
        return '🎯 ELITE SNIPER', '🔥🔥🔥', 'MAXIMUM — All 5 strategies agree'
    elif confidence == 'HIGH':
        return '🎯 SNIPER MODE', '🔥🔥', 'HIGH — 4+ strategies agree'
    elif confidence == 'MEDIUM' and votes >= 4:
        return '📡 LASER LOCKED', '🔥', 'MEDIUM — 3+ strategies agree'
    elif confidence == 'MEDIUM':
        return '📡 LASER LOCKED', '💡', 'MEDIUM — 3 strategies agree'
    elif confidence == 'LOW' and votes >= 2:
        return '🔭 SCOUTING', '👀', 'LOW — Only 2 strategies agree'
    else:
        return '⚡ MONITORING', '🔍', 'WEAK — Watch only'

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
    """Send a poll to Telegram."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendPoll"
    data = {'chat_id': config.TELEGRAM_CHAT_ID, 'question': question, 'options': json.dumps(options)}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

def format_strategy_breakdown(results):
    lines = []
    for r in results[:5]:
        if r['action'] != 'HOLD':
            emoji = '🟢' if r['action'] == 'BUY' else '🔴'
            lines.append(f"  {emoji} {r['strategy']}: <b>{r['action']}</b> ({r['confidence']})")
    return '\n'.join(lines) if lines else '  ⚪ No active strategies'

def get_action_advice(confidence):
    if confidence == 'HIGH':
        return '🔴 <b>AGGRESSIVE</b> — 2-3% of portfolio'
    elif confidence == 'MEDIUM':
        return '🟡 <b>STANDARD</b> — 1-2% of portfolio'
    else:
        return '🟢 <b>CAUTIOUS</b> — 0.5-1% of portfolio'

def build_colorful_signal(signal, batch_id):
    tag, fire, quality = get_signal_tag(signal['confidence'], signal.get('vote_count', 0))
    
    # Strategy breakdown
    strategies = format_strategy_breakdown(signal.get('strategy_results', []))
    
    # Sentiment emoji
    sentiment = signal['sentiment']['label']
    sentiment_emoji = '😨' if 'Fear' in sentiment else '😊' if 'Greed' in sentiment else '😐'
    
    # Whale emoji
    whale = signal['whale']['signal']
    whale_emoji = '🐋' if whale == 'BULLISH' else '🐻' if whale == 'BEARISH' else '🐟'
    
    msg = f"""
{tag} — <b>{signal['coin']}</b>

<b>Action:</b> {signal['action']}
<b>Entry:</b> <code>${signal['entry_price']}</code>
<b>Target:</b> <code>${signal['target']}</code> (<b>+{config.TARGET_PCT*100}%</b>)
<b>Stop:</b> <code>${signal['stop_loss']}</code> (<b>-{config.STOP_LOSS_PCT*100}%</b>)

📊 <b>Signal Quality:</b> {fire} {quality}
🔒 <b>Confidence:</b> {signal['confidence']}

📈 <b>Strategy Votes:</b>
{strategies}

{sentiment_emoji} <b>Sentiment:</b> {sentiment} ({signal['sentiment']['value']})
{whale_emoji} <b>Whale:</b> {whale}

💡 <b>Action:</b> {get_action_advice(signal['confidence'])}

⚠️ <i>Not financial advice. Trade at your own risk.</i>
"""
    return msg

def send_signal(signal, batch_id):
    """Send a single signal, only if it's new."""
    if signal['action'] == 'HOLD':
        return False
    
    key = signal['coin']
    if key in last_sent:
        last = last_sent[key]
        if last['action'] == signal['action'] and last['confidence'] == signal['confidence']:
            return False
    
    last_sent[key] = {
        'action': signal['action'],
        'confidence': signal['confidence'],
        'timestamp': datetime.now().isoformat()
    }
    
    msg = build_colorful_signal(signal, batch_id)
    send_telegram(msg)
    return True

def send_batch(signals, batch_id):
    """Send a batch of signals, each only if changed."""
    active = [s for s in signals if s['action'] not in ['HOLD', 'ERROR']]
    if not active:
        return
    
    # Batch header
    now = datetime.now().strftime('%H:%M:%S')
    header = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>BATCH #{batch_id}</b> — <code>{now}</code>
📈 {len(active)} signal(s)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    send_telegram(header)
    
    sent_count = 0
    for sig in active:
        if send_signal(sig, batch_id):
            sent_count += 1
            send_telegram("━" * 40)
    
    if sent_count == 0:
        send_telegram("🔄 No new signals — market unchanged.")

def send_digest(digest):
    send_telegram(digest)

def reset_last_sent():
    global last_sent
    last_sent = {}