"""
PSIT -- Day 1 verification run.
Fetches ADC oncology trials, stores in SQLite,
verifies schema and source URL enforcement.
"""
import json
from ct_fetcher import fetch_trials, CT_BASE, QUERY_PARAMS
from db import init_db, upsert_trials, log_source_pull
 
REQUIRED_FIELDS = [
    'nct_id', 'brief_title', 'overall_status', 'phase',
    'sponsor', 'conditions', 'interventions',
    'source_url', 'pull_timestamp'
]
 
def main():
    print('\nPSIT -- Day 1 Verification Run')
    print('=' * 55)
 
    print('\n[1] Initializing database...')
    init_db()
 
    print('\n[2] Fetching ADC oncology trials from ClinicalTrials.gov...')
    trials, pull_ts = fetch_trials()
    print(f'  Fetched {len(trials)} trials at {pull_ts}')
 
    print('\n[3] Storing in SQLite...')
    upsert_trials(trials)
    log_source_pull(
        'ClinicalTrials.gov', CT_BASE,
        json.dumps({'query.term': QUERY_PARAMS['query.term']}),
        pull_ts, len(trials)
    )
 
    print('\n[4] Schema verification (first 5 trials):')
    for t in trials[:5]:
        missing = [f for f in REQUIRED_FIELDS if not getattr(t, f, None)]
        status = 'PASS' if not missing else f'FAIL -- missing: {missing}'
        print(f'  {t.nct_id}: {status}')
        print(f'    Phase: {t.phase or "None"} | Status: {t.overall_status}')
        print(f'    Sponsor: {t.sponsor[:50]}')
        print(f'    Source URL: {t.source_url}')
 
    print('\n[5] Source URL enforcement:')
    no_url = [t for t in trials if not t.source_url]
    if no_url:
        print(f'  FAIL -- {len(no_url)} trials missing source_url')
    else:
        print(f'  PASS -- all {len(trials)} trials have source_url')
 
    print(f'\n{"=" * 55}')
    print(f'Total trials fetched  : {len(trials)}')
    print(f'Stored in SQLite      : psit.db')
    print(f'Cache written         : cache/ct_raw_{pull_ts[:10]}.json')
    result = 'PASSED' if not no_url else 'FAILED'
    print(f'Source URL check      : {result}')
 
if __name__ == '__main__':
    main()
