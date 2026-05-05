"""
PSIT -- Narrative summary layer.
LLM role: summarizer only. It receives structured data and returns ClaimObjects.
It does not generate facts. Its output is validated before reaching the UI.
Model: Claude Haiku (low cost, sufficient for constrained summarization).
"""
import anthropic, json, datetime
from claim import ClaimObject
from validator import validate_claims
 
client = anthropic.Anthropic()
MODEL  = 'claude-haiku-4-5-20251001'
 
SYSTEM_PROMPT = '''You are summarizing structured pharmaceutical trial registry data.
Your output will be displayed in a dashboard where every claim must have a verified source URL.
 
RULES -- follow these exactly:
1. Summarize ONLY facts present in the DATA section below.
2. Do NOT invent drug names, trial counts, sponsor names, or dates not in the data.
3. Do NOT add general pharmaceutical knowledge not supported by the data.
4. Use evidence_type SUMMARY for all claims you generate.
5. Use the source_url values from the data -- do not invent URLs.
6. Return a JSON array only. No markdown. No preamble. No explanation.
 
Each object in the array must have these exact fields:
  claim_text, source_url, source_name, evidence_type, pull_timestamp
'''
 
def _build_prompt(density: dict, pull_ts: str) -> str:
    data = {
        'total_trials': density['total_trials'],
        'top_sponsors': list(density['sponsor_leaderboard'].items())[:5],
        'phase_distribution': density['by_phase'],
        'status_distribution': density['by_status'],
        'source_url': 'https://clinicaltrials.gov/api/v2/studies',
        'source_name': 'ClinicalTrials.gov',
        'pull_timestamp': pull_ts,
    }
    return f'DATA:\n{json.dumps(data, indent=2)}'
 
 
def generate_summary(density: dict, pull_ts: str) -> list[ClaimObject]:
    """Generates citation-constrained summary claims from pipeline density data.
    Returns only validated ClaimObjects. Logs but suppresses rejected claims.
    Returns [] on API failure -- app degrades gracefully."""
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{
                'role': 'user',
                'content': _build_prompt(density, pull_ts)
            }]
        )
        raw = resp.content[0].text.strip()
        # Strip markdown fences if present
        if raw.startswith('```'):
            raw = '\n'.join(raw.split('\n')[1:-1])
 
        items = json.loads(raw)
        candidates = [ClaimObject(**item) for item in items]
 
    except Exception as e:
        print(f'  Narrator: API or parse error: {e}')
        return []
 
    valid, rejected = validate_claims(candidates)
 
    if rejected:
        print(f'  Narrator: {len(rejected)} claim(s) rejected by validator:')
        for claim, reason in rejected:
            print(f'    BLOCKED: {reason}')
 
    print(f'  Narrator: {len(valid)} validated claim(s) generated.')
    return valid
