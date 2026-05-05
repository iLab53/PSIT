"""
PSIT -- FDA regulatory signal overlay (Tier 2).
Parses FDA press release RSS filtered for ADC-oncology relevance.
Returns [] if feed is unavailable -- overlay is non-blocking.
"""
import datetime

import feedparser


FDA_RSS = 'https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml'

# Extend this list as the ADC landscape evolves.
# Curated list -- not auto-generated.
ADC_KEYWORDS = [
    'antibody-drug conjugate',
    'adc',
    'trastuzumab deruxtecan',
    'enfortumab vedotin',
    'sacituzumab govitecan',
    'belantamab mafodotin',
    'mirvetuximab soravtansine',
    'loncastuximab tesirine',
    'disitamab vedotin',
    'datopotamab deruxtecan',
    'patritumab deruxtecan',
    'her2-targeting adc',
    'trop-2 adc',
    'nectin-4 adc',
]


def fetch_fda_signals() -> list[dict]:
    pull_ts = datetime.datetime.utcnow().isoformat() + 'Z'
    try:
        feed = feedparser.parse(FDA_RSS)
    except Exception as e:
        print(f'  Warning: FDA RSS unavailable: {e}')
        return []

    signals = []
    for entry in feed.entries:
        title = entry.get('title', '')
        summary = entry.get('summary', '')
        text = (title + ' ' + summary).lower()
        if any(kw.lower() in text for kw in ADC_KEYWORDS):
            signals.append({
                'source_name': 'FDA',
                'source_url': entry.get('link', ''),
                'title': title,
                'summary': summary[:300],
                'published': entry.get('published', ''),
                'pull_timestamp': pull_ts,
                'signal_tier': 'TIER_2',
            })
    print(f'  FDA: {len(signals)} ADC-relevant signals found.')
    return signals
