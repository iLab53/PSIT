"""
PSIT -- EMA regulatory signal overlay (Tier 2).
Shares ADC_KEYWORDS from fda_fetcher.
"""
import datetime

import feedparser

from fda_fetcher import ADC_KEYWORDS


EMA_RSS = 'https://www.ema.europa.eu/en/rss-feeds/ema-news.xml'


def fetch_ema_signals() -> list[dict]:
    pull_ts = datetime.datetime.utcnow().isoformat() + 'Z'
    try:
        feed = feedparser.parse(EMA_RSS)
    except Exception as e:
        print(f'  Warning: EMA RSS unavailable: {e}')
        return []

    signals = []
    for entry in feed.entries:
        title = entry.get('title', '')
        summary = entry.get('summary', '')
        text = (title + ' ' + summary).lower()
        if any(kw.lower() in text for kw in ADC_KEYWORDS):
            signals.append({
                'source_name': 'EMA',
                'source_url': entry.get('link', ''),
                'title': title,
                'summary': summary[:300],
                'published': entry.get('published', ''),
                'pull_timestamp': pull_ts,
                'signal_tier': 'TIER_2',
            })
    print(f'  EMA: {len(signals)} ADC-relevant signals found.')
    return signals
