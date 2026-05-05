"""
PSIT -- Overlay refresh orchestrator.
Run independently of psit_hello.py.
Fetches FDA, EMA, and news signals and stores them in SQLite.
"""
from fda_fetcher import fetch_fda_signals
from ema_fetcher import fetch_ema_signals
from news_fetcher import fetch_news_signals
from db import init_db, insert_regulatory_signals, insert_news_signals


def run_overlays():
    print('\nPSIT -- Overlay Refresh')
    print('=' * 55)
    init_db()

    print('\n[1] FDA regulatory signals...')
    fda = fetch_fda_signals()
    print('\n[2] EMA regulatory signals...')
    ema = fetch_ema_signals()
    reg = fda + ema
    print(f'\n  Total regulatory signals: {len(reg)}')
    insert_regulatory_signals(reg)

    print('\n[3] News signals...')
    news = fetch_news_signals()
    print(f'  Total news signals: {len(news)}')
    insert_news_signals(news)
    print('\nOverlay refresh complete.')


if __name__ == '__main__':
    run_overlays()
