"""Repeatable synthetic engineering-report comparison; no production documents."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from html import escape
import json
from pathlib import Path
from statistics import median
from uuid import uuid4

from ai import settings
from benchmark import CRITERIA, summary_rows
from ingestion import prepare_metrics, prepare_sources
from workflow import build_report, load_sample, SAMPLES

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'evaluation/workflow-model-comparison.json'
CONFIGS=[{'mode':'live','provider':p,'model':m} for p,m in [
    ('Anthropic','claude-haiku-5-5'),('Gemini','gemini-3.5-flash-lite'),('Mistral','mistral-small-2603')]]


def prepare():
    frozen={}
    for case in SAMPLES:
        metrics,sources=load_sample(case)
        frozen[case]={'metrics':metrics.decode(),'sources':sources.decode(),'intake':None,
                      'checks':CRITERIA[case]['checks']}
    folder=ROOT/'sample_data/Demo files'
    metrics,origin=prepare_metrics('platform-metrics.xlsx',(folder/'platform-metrics.xlsx').read_bytes())
    names=['partner-call.vtt','engineering-notes.docx','vendor-call.srt','bd-follow-up-notes.txt']
    sources,notes=prepare_sources([(n,(folder/n).read_bytes()) for n in names],'',date(2026,9,28))
    frozen['uploaded_demo']={'metrics':metrics.decode(),'sources':sources.decode(),
        'intake':{'metrics':origin,'notes':notes},'checks':[
        'Swisscom analytics need, unknown root cause and no confirmed fix date are preserved.',
        'Vodafone onboarding checklist remains pending partner validation.',
        'Previous BD action remains open; no invented completion or named assignee.',
        'Vendor maintenance remains a proposal, not an approved outage.',
        'No measured revenue impact or causal attribution is invented.']}
    result={'id':str(uuid4()),'created_at':datetime.now(timezone.utc).isoformat(),
        'configurations':CONFIGS,'repetitions':2,'frozen_inputs':frozen,'rows':[],
        'protocol':{'report_type':'Engineering','calls_per_model':12,'max_output_tokens':6000,
        'reasoning':{'Anthropic':'low adaptive','Gemini':'low','Mistral':'none (instruct)'},
        'timeout_seconds':75,'automatic_retries':0,'concurrency':'At most one request per provider; two providers may run simultaneously.',
        'costs':'Dated standard token estimates; reasoning tokens included when exposed. Failed-call cost unknown. No billing verification.',
        'retention':'Not measured by this benchmark; no assertion that accounts have ZDR.',
        'scope':'Frozen synthetic development/regression cases, not fresh holdouts. Does not measure OCR/DOC support, long documents or multilingual quality.'},
        'limitations':'Two trials per case/model. Small synthetic sample; no production reliability claim. Assistant review is separate from independent human sign-off.'}
    for case,inputs in frozen.items():
        report=build_report(inputs['metrics'].encode(),inputs['sources'].encode(),intake=inputs['intake'])
        result['rows'].append({'case':case,'trial':0,'configuration':{'mode':'baseline'},
            'status':'completed','citation_checks_pass':not any(i['severity']=='error' for i in report['issues']),
            'report':report,'manual_checks':inputs['checks'],'manual_result':'NOT REVIEWED','evaluation_role':'development/regression'})
    return result


def write(result):
    result['updated_at']=datetime.now(timezone.utc).isoformat()
    tmp=OUT.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2,ensure_ascii=False));tmp.replace(OUT)
    render(result)


def render(result):
    cards=[]
    for config in CONFIGS:
        provider=config['provider'];rows=[r for r in result['rows'] if r['configuration'].get('provider')==provider]
        done=[r for r in rows if r['status']=='completed']
        cost=sum(r['report']['usage']['estimated_cost_usd'] or 0 for r in done)
        latency=f"{median(r['report']['elapsed_seconds'] for r in done):.2f}s" if done else '—'
        failures=[r for r in rows if r['status']=='failed']
        state='Complete' if len(done)==12 else ('Blocked / incomplete' if failures else ('In progress' if rows else 'Pending access / run'))
        estimate=f'${cost:.6f} total · ${cost/len(done):.6f} / report' if done else 'Unavailable'
        error='<p>'+escape(failures[-1]['error'])+'</p>' if failures else ''
        cards.append(f'<article><small>{escape(provider)}</small><h2>{escape(config["model"])}</h2><b>{len(done)} / 12 completed</b><p>{state}</p><p>Median: {latency}<br>Completed-call estimate: {estimate}</p><p>Quote checks: {sum(r.get("citation_checks_pass",False) for r in done)} / {len(done)}<br>Human review: pending</p>{error}</article>')
    details=[]
    for row in result['rows']:
        label=f'{row["case"]} · {row["configuration"].get("model","Non-AI")} · trial {row["trial"]} · {row["status"]}'
        content=escape(json.dumps(row.get('report',{}).get('narrative',{'error':row.get('error','')}),indent=2,ensure_ascii=False))
        review=row.get('assistant_review',{})
        review_html='<p>Assistant review (not human sign-off): '+escape(json.dumps(review,ensure_ascii=False))+'</p>' if review else ''
        checks='<ul>'+''.join('<li>'+escape(c)+'</li>' for c in row['manual_checks'])+'</ul>'
        details.append(f'<details><summary>{escape(label)}</summary>{checks}{review_html}<pre>{content}</pre></details>')
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>MEP · Workflow model comparison</title><style>body{font:15px/1.6 -apple-system,BlinkMacSystemFont,Arial,sans-serif;background:#f7f7fb;color:#292b36;margin:0}main{max-width:1180px;margin:auto;padding:40px 25px}h1{font-size:32px;margin:0}h2{font-size:18px}small{color:#7662bc}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px;margin:24px 0}article,details{background:white;border:1px solid #e2deeb;padding:20px;border-radius:12px}details{margin:10px 0}summary{cursor:pointer;font-weight:600}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}a{color:#705bb3}.note{padding:15px;background:#efeafa;border-radius:10px}</style><main><small>NIG · SYNTHETIC WORKFLOW EVALUATION</small><h1>Which model works for this report?</h1><p>Same six engineering-report cases. Two trials per model. Frozen inputs, prompt and output contract; provider reasoning settings differ.</p>'''
    html+='<div class="cards">'+''.join(cards)+'</div><p class="note">Quotation checks establish traceability, not completeness or correctness. Independent human review is pending. Pending providers have no benchmark result. Retention is not tested. These familiar synthetic cases are development evidence, not a production ranking.</p>'
    review=result.get('assistant_summary',{})
    if review:
        html+='<article><h2>What the outputs show</h2><p>'+escape(review['recommendation'])+'</p><ul>'+''.join('<li>'+escape(s)+'</li>' for s in review['observations'])+'</ul><p>Assistant assessment; independent human sign-off is pending.</p></article>'
    html+='<h2>How to read this comparison</h2><p>Five regression cases plus the actual five demo files, each run twice. Excel figures are calculated locally; models see extracted meeting text. Missing-data handling therefore tests Python, not the model. PDF/OCR, legacy DOC, long documents and production load are not evaluated here. Reasoning settings differ: Haiku low adaptive, Gemini low, Mistral instruct.</p>'
    html+='<p>Input, prompt and schema hashes are recorded per output. Prices are standard token estimates, not invoices or confirmed account charges. Failed/setup calls and diagnostic calls are excluded; their cost is unknown. Latency measures local workflow wall time. Provider runs occurred at different times, so this is an indicative comparison.</p>'
    html+='<p>Pricing references: <a href="https://www.anthropic.com/claude-haiku-5-5">Haiku</a> · <a href="https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite">Gemini</a> · <a href="https://docs.mistral.ai/models/mistral-small-4-0-26-03">Mistral</a>. Retention depends on account terms and deployment; this test does not verify those.</p>'
    html+=f'<p>{len(result.get("setup_failures",[]))} setup failures and {len(result.get("prior_attempts",[]))} prior benchmark attempts retained in the evidence JSON.</p>'
    html+='<p><a href="workflow-model-comparison.json">Download full evidence JSON</a></p><h2>Outputs and review notes</h2>'+''.join(details)
    for case,inputs in result['frozen_inputs'].items():
        html+='<details><summary>Frozen sources · '+escape(case)+'</summary><pre>'+escape(inputs['sources'])+'</pre></details>'
    html+='</main></html>'
    OUT.with_suffix('.html').write_text(html)


def run_provider(config, frozen, completed):
    rows=[]
    # One worker serializes this provider's requests to avoid quota bursts.
    for trial in (1,2):
        for case,inputs in frozen.items():
            if (case,trial) in completed: continue
            row={'case':case,'trial':trial,'configuration':config,'manual_checks':inputs['checks'],
                 'manual_result':'NOT REVIEWED','evaluation_role':'development/regression'}
            try:
                report=build_report(inputs['metrics'].encode(),inputs['sources'].encode(),intake=inputs['intake'],**config)
                row.update(status='completed',citation_checks_pass=not any(i['severity']=='error' for i in report['issues']),report=report)
            except Exception as exc:
                message=str(exc) if isinstance(exc,RuntimeError) else f'{type(exc).__name__}: generation or validation failed'
                row.update(status='failed',error=message)
            # Durable per-attempt checkpoint; main process merges these after workers finish.
            folder=ROOT/'.local'/('comparison-'+config['provider']);folder.mkdir(parents=True,exist_ok=True)
            (folder/f'{case}-{trial}.json').write_text(json.dumps(row,indent=2,ensure_ascii=False))
            rows.append(row)
            print(f'{config["provider"]} {case} trial {trial}: {row["status"]}',flush=True)
            if row['status']=='failed' and any(x in row['error'] for x in ['HTTP 400','HTTP 401','HTTP 403','HTTP 404','HTTP 429','network request','connection','Connection']):
                break
        if rows and rows[-1]['status']=='failed': break
    return rows


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--providers',nargs='*',default=['Anthropic','Gemini','Mistral']);parser.add_argument('--retry-failed',action='store_true');args=parser.parse_args()
    result=json.loads(OUT.read_text()) if OUT.exists() else prepare()
    if args.retry_failed:
        failed=[r for r in result['rows'] if r['status']=='failed' and r['configuration'].get('provider') in args.providers]
        result.setdefault('prior_attempts',[]).extend(failed)
        result['rows']=[r for r in result['rows'] if r not in failed]
    write(result)
    configs=[c for c in CONFIGS if c['provider'] in args.providers and settings(c['provider'])['has_key']]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[]
        for c in configs:
            completed={(r['case'],r['trial']) for r in result['rows'] if r['configuration']==c}
            futures.append(pool.submit(run_provider,c,result['frozen_inputs'],completed))
        for future in as_completed(futures):
            result['rows'].extend(future.result());write(result)
    print(json.dumps(summary_rows(result),indent=2))


if __name__=='__main__': main()
