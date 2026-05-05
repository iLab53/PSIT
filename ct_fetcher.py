"""
PSIT -- ClinicalTrials.gov v2 API fetcher for ADC oncology.
Paginates automatically. Caches raw JSON. Returns Trial list.
"""
import requests, json, datetime, pathlib
from models import Trial
 
CT_BASE  = 'https://clinicaltrials.gov/api/v2/studies'
CACHE_DIR = pathlib.Path('cache')
CACHE_DIR.mkdir(exist_ok=True)
 
QUERY_PARAMS = {
    'query.term': 'antibody-drug conjugate',
    'query.cond': 'cancer OR oncology OR tumor OR carcinoma OR lymphoma OR leukemia',
    'pageSize': 1000,
    'format': 'json',
}
 
def fetch_trials() -> tuple[list[Trial], str]:
    pull_ts = datetime.datetime.utcnow().isoformat() + 'Z'
    all_studies, params, page = [], QUERY_PARAMS.copy(), 1
 
    while True:
        print(f'  Fetching page {page}...')
        resp = requests.get(CT_BASE, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get('studies', [])
        all_studies.extend(batch)
        print(f'  Got {len(batch)} studies (total: {len(all_studies)})')
        token = data.get('nextPageToken')
        if not token:
            break
        params['pageToken'] = token
        page += 1
 
    # Write raw cache
    cache_path = CACHE_DIR / f'ct_raw_{pull_ts[:10]}.json'
    cache_path.write_text(json.dumps({
        'pull_timestamp': pull_ts,
        'total': len(all_studies),
        'studies': all_studies
    }, indent=2))
    print(f'  Cached {len(all_studies)} studies -> {cache_path}')
 
    return [_parse(s, pull_ts) for s in all_studies], pull_ts
 
 
def _parse(study: dict, pull_ts: str) -> Trial:
    ps      = study.get('protocolSection', {})
    id_mod  = ps.get('identificationModule', {})
    st_mod  = ps.get('statusModule', {})
    sp_mod  = ps.get('sponsorCollaboratorsModule', {})
    co_mod  = ps.get('conditionsModule', {})
    in_mod  = ps.get('armsInterventionsModule', {})
    de_mod  = ps.get('designModule', {})
 
    nct_id = id_mod.get('nctId', '')
    return Trial(
        nct_id=nct_id,
        brief_title=id_mod.get('briefTitle', ''),
        overall_status=st_mod.get('overallStatus', ''),
        phase='|'.join(de_mod.get('phases', [])),
        sponsor=sp_mod.get('leadSponsor', {}).get('name', ''),
        conditions='|'.join(co_mod.get('conditions', [])),
        interventions='|'.join(
            i.get('name', '') for i in in_mod.get('interventions', [])
        ),
        start_date=st_mod.get('startDateStruct', {}).get('date'),
        primary_completion_date=st_mod.get(
            'primaryCompletionDateStruct', {}).get('date'),
        last_update_date=st_mod.get('lastUpdateSubmitDate'),
        study_type=de_mod.get('studyType', ''),
        enrollment=de_mod.get('enrollmentInfo', {}).get('count'),
        source_url=f'https://clinicaltrials.gov/study/{nct_id}',
        pull_timestamp=pull_ts,
    )
