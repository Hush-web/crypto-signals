# market_data.py — Sentiment & Whale (No API keys)
import requests
import xml.etree.ElementTree as ET

def get_fear_greed():
    try:
        resp = requests.get("https://api.alternative.me/fng/", timeout=5)
        data = resp.json()
        return int(data['data'][0]['value']), data['data'][0]['value_classification']
    except:
        return 50, 'NEUTRAL'

def get_whale_sentiment():
    try:
        resp = requests.get("https://whale-alert.io/rss/feed", timeout=10)
        root = ET.fromstring(resp.content)
        buy = sell = 0
        for item in root.findall('./channel/item'):
            title = item.find('title').text or ''
            if 'moved to' in title.lower() and 'exchange' in title.lower():
                sell += 1
            elif 'moved from' in title.lower() and 'exchange' in title.lower():
                buy += 1
        if buy > sell:
            return 'BULLISH', f'Whales accumulating ({buy} buys)'
        elif sell > buy:
            return 'BEARISH', f'Whales distributing ({sell} sells)'
        return 'NEUTRAL', 'No clear whale signal'
    except:
        return 'NEUTRAL', 'Whale data unavailable'