"""
telegram.py — Sends formatted signal alerts to a Telegram chat via bot API.

Setup (see README for the full walkthrough):
    1. Message @BotFather on Telegram, run /newbot, copy the token.
    2. Message your new bot once (so it's allowed to message you back).
    3. Get your chat_id by visiting:
       https://api.telegram.org/bot<TOKEN>/getUpdates
    4. Put both values in your .env / GitHub secrets as
       TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
"""

import requests
import config

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramError(Exception):
    pass


def _confidence_emoji(confidence: str) -> str:
    return {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🟠"}.get(confidence, "⚪️")


def _action_emoji(action: str) -> str:
    return {"BUY": "📈", "SELL": "📉"}.get(action, "⏸")


def format_signal_message(signal: dict) -> str:
    """Build a human-friendly Telegram message (Markdown) for one signal."""
    conf_emoji = _confidence_emoji(signal["confidence"])
    act_emoji = _action_emoji(signal["action"])

    lines = [
        f"{act_emoji} *{signal['action']} SIGNAL* — `{signal['coin']}`",
        f"{conf_emoji} Confidence: *{signal['confidence']}*",
        "",
        f"Entry: `{signal['entry_price']}`",
        f"Target: `{signal['target']}`",
        f"Stop Loss: `{signal['stop_loss']}`",
        "",
        f"_Reason: {signal['reason']}_",
        "",
        f"🕒 {signal['timestamp']}",
        "",
        "⚠️ Not financial advice. Trade at your own risk.",
    ]
    return "\n".join(lines)


def send_telegram_message(text: str, bot_token: str = None, chat_id: str = None) -> bool:
    """
    Send a raw text message to Telegram. Returns True on success, False on
    failure (never raises, so one bad send doesn't kill the whole run) —
    unless raise_on_error=True is desired, use send_telegram_message_strict.
    """
    bot_token = bot_token or config.TELEGRAM_BOT_TOKEN
    chat_id = chat_id or config.TELEGRAM_CHAT_ID

    if not bot_token or not chat_id:
        print("[telegram] Skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        return False

    url = TELEGRAM_API_URL.format(token=bot_token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code != 200:
            print(f"[telegram] Failed ({resp.status_code}): {resp.text}")
            return False
        return True
    except requests.RequestException as e:
        print(f"[telegram] Request error: {e}")
        return False


def send_signal_alert(signal: dict, bot_token: str = None, chat_id: str = None) -> bool:
    """Convenience wrapper: format + send a single signal dict."""
    message = format_signal_message(signal)
    return send_telegram_message(message, bot_token, chat_id)


def send_summary(signals: list, bot_token: str = None, chat_id: str = None) -> bool:
    """Send a short run summary (how many BUY/SELL/HOLD/errors this run produced)."""
    counts = {"BUY": 0, "SELL": 0, "HOLD": 0, "ERROR": 0}
    for s in signals:
        counts[s["action"]] = counts.get(s["action"], 0) + 1

    text = (
        "🤖 *Signal run complete*\n"
        f"📈 BUY: {counts['BUY']}  📉 SELL: {counts['SELL']}  "
        f"⏸ HOLD: {counts['HOLD']}  ⚠️ Errors: {counts['ERROR']}"
    )
    return send_telegram_message(text, bot_token, chat_id)
