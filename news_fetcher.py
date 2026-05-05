"""
PSIT -- News signal overlay (Tier 3).
Endpoints News and STAT News public RSS, filtered for ADC-oncology relevance.
Non-blocking on feed failure. Labeled TIER_3 throughout.
"""
import datetime

import feedparser

from fda_fetcher import ADC_KEYWORDS


NEWS_SOURCES = [
    ('Endpoints News', 'https://endpts.com/feed/'),
    ('STAT News', 'https://www.statnews.com/feed/'),
]


def fetch_news_signals() -> list[dict]:
    pull_ts = datetime.datetime.utcnow().isoformat() + 'Z'
    signals = []
    for source_name, rss_url in NEWS_SOURCES:
        try:
            feed = feedparser.parse(rss_url)
            count_before = len(signals)
            for entry in feed.entries:
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                text = (title + ' ' + summary).lower()
                if any(kw.lower() in text for kw in ADC_KEYWORDS):
                    signals.append({
                        'source_name': source_name,
                        'source_url': entry.get('link', ''),
                        'title': title,
                        'summary': summary[:300],
                        'published': entry.get('published', ''),
                        'pull_timestamp': pull_ts,
                        'signal_tier': 'TIER_3',
                    })
            found = len(signals) - count_before
            print(f'  {source_name}: {found} signals found.')
        except Exception as e:
            print(f'  Warning: {source_name} RSS unavailable: {e}')
    return signals
