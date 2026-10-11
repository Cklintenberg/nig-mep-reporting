"""Read-only scoring of retained outputs and a standalone business evidence page."""
from pathlib import Path
from statistics import median
from collections import Counter
from html import escape as e
from datetime import datetime,timezone
import json,math

def rounding_only(f):
    """Post-run descriptive classification; does not change the frozen strict score."""
    a,g=f.get("actual"),f["expected"]
    if not f["unsafe_value"] or not a or g["status"]!="extracted" or g["key"] not in ["analytics_delay","availability","api_error_rate"]:return False
    try:return math.isclose(float(a["value"]),float(g["value"]),rel_tol=0,abs_tol=.0001)
    except (ValueError,TypeError):return False

from .runner import ROOT,MODELS,score,Intake
COLORS={'Anthropic':'#CA7B57','Gemini':'#507DE5','Mistral':'#E99B25'}
NAMES={'Anthropic':'Claude Haiku 5.5','Gemini':'Gemini 3.8 Flash','Mistral':'Mistral Small 4'}
def percentile(values,p):
    if not values:return None
    a=sorted(values);return a[max(0,math.ceil(len(a)*p)-1)]
def collect():
    cases=json.loads((ROOT/'cases.json').read_text());by={c['id']:c for c in cases};rows=[]
    for phase in ['development','holdout']:
        for f in sorted((ROOT/phase).glob('*/*.json')):
            r=json.loads(f.read_text());r['original_score']=r.pop('score',None)
            if r['status']=='completed':r['score']=score(r['output'],by[r['case']])
            rows.append(r)
    return cases,rows

def summarise(rows,cases):
    data={};by={c['id']:c for c in cases}
    for p in MODELS:
        selected=[r for r in rows if r['provider']==p];completed=[r for r in selected if r['status']=='completed'];fields=[f for r in completed for f in r['score']['fields']]
        truth_count=sum(len(by[r['case']]['gold']) for r in selected)
        extractable=sum(g['status']=='extracted' for r in selected for g in by[r['case']]['gold'])
        nonextractable=sum(g['status']!='extracted' for r in selected for g in by[r['case']]['gold'])
        supplied=[f for f in fields if f['actual'] and f['actual']['value'] is not None]
        costs=[r['usage']['estimated_cost_usd'] for r in selected if r.get('usage')];times=[r['latency_seconds'] for r in selected]
        passes=sum(r['score']['case_pass'] for r in completed)
        bycase={cid:all(r['status']=='completed' and r['score']['case_pass'] for r in rr) and len(rr)==3 for cid in by if (rr:=[r for r in selected if r['case']==cid])}
        data[p]={'model':MODELS[p],'attempts':len(selected),'completed':len(completed),'expected_calls':3*sum(c['split'] in {r['split'] for r in selected} for c in cases),'case_passes':passes,'full_case_pass_pct':100*passes/len(selected) if selected else 0,'stable_cases':sum(bycase.values()),'total_cases':len(bycase),
        'returned_field_count':len(fields),'returned_field_accuracy_pct':100*sum(f['correct'] for f in fields)/len(fields) if fields else 0,'field_count':truth_count,'correct_fields':sum(f['correct'] for f in fields),'field_accuracy_pct':100*sum(f['correct'] for f in fields)/truth_count if truth_count else 0,
        'supplied_fields':len(supplied),'unsafe_values':sum(f['unsafe_value'] for f in fields),'rounding_only_mismatches':sum(rounding_only(f) for f in fields),'substantive_wrong_values':sum(f['unsafe_value'] and not rounding_only(f) for f in fields),'safe_value_precision_pct':100*sum(not f['unsafe_value'] for f in supplied)/len(supplied) if supplied else 0,
        'extractable_fields':extractable,'correct_extracted_fields':sum(f['correct'] and f['expected']['status']=='extracted' for f in fields),
        'coverage_pct':100*sum(f['correct'] and f['expected']['status']=='extracted' for f in fields)/extractable if extractable else 0,
        'unavailable_fields':nonextractable,'correct_abstentions':sum(f['expected']['status']!='extracted' and f['actual'] and f['actual']['value'] is None and f['actual']['status']!='extracted' for f in fields),
        'provenance_failures':sum(not f['provenance_correct'] for f in fields),'mechanical_passes':sum(not r['score']['mechanical_errors'] for r in completed),
        'unsafe_mechanical_passes':sum(r['score']['unsafe_values']>0 and not r['score']['mechanical_errors'] for r in completed),
        'restriction_flags_correct':sum(r['score']['restriction_flag_correct'] for r in completed),'injection_flags_correct':sum(r['score']['injection_flag_correct'] for r in completed),
        'attack_markers':sum(r['score']['attack_marker_output'] for r in completed),'median_seconds':median(times) if times else 0,'p95_seconds':percentile(times,.95),
        'total_cost_usd':sum(costs),'cost_per_1000_usd':sum(costs)/len(costs)*1000 if costs else 0,'unpriced_attempts':len(selected)-len(costs),'cost_per_passing_case_usd':sum(costs)/passes if passes else None,
        'cached_input_tokens':sum(r.get('usage',{}).get('cached_tokens',0) for r in selected),'input_tokens':sum(r.get('usage',{}).get('input_tokens',0) for r in selected),'output_tokens':sum(r.get('usage',{}).get('output_tokens',0) for r in selected)}
    return data

def render():
    cases,rows=collect();summary=summarise(rows,cases);privacy=json.loads((ROOT/'privacy.json').read_text());complete=len(rows)==360
    result={'updated_at':datetime.now(timezone.utc).isoformat(),'complete':complete,'scoring_version':2,'protocol':json.loads((ROOT/'protocol.json').read_text()),'summary':summary,'development':summarise([r for r in rows if r['split']=='development'],cases),'holdout':summarise([r for r in rows if r['split']=='holdout'],cases),'privacy':privacy,'rows':rows}
    setup_rows=[json.loads(f.read_text()) for f in (ROOT/'setup').glob('*/*.json')]
    result['setup_cost_usd']=sum(r.get('usage',{}).get('estimated_cost_usd',0) for r in setup_rows)
    result['scored_cost_usd']=sum(s['total_cost_usd'] for s in summary.values())
    decisionfile=ROOT/'decision.json';decision=json.loads(decisionfile.read_text()) if decisionfile.exists() else {'headline':'Benchmark in progress','recommendation':'A recommendation follows the full repeated run and holdout assessment. No winner declared yet.'}
    result['decision']=decision
    (ROOT/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    def table(headers,records):return '<div class="table"><table><thead><tr>'+''.join('<th>'+e(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in r)+'</tr>' for r in records)+'</tbody></table></div>'
    def chart(title,key,fmt,maximum=None):
        maximum=maximum or max((s[key] for s in summary.values()),default=1) or 1
        return '<article><h3>'+title+'</h3><div class="chart">'+''.join(f'<div class="barcol"><strong>{fmt(s[key])}</strong><div class="bar" style="height:{s[key]/maximum*155:.1f}px;background:{COLORS[p]}"></div><span>{NAMES[p]}</span></div>' for p,s in summary.items())+'</div></article>'
    body='<div class="eyebrow">NIG / MEP · ENGINEERING DECISION EVIDENCE · 9 OCTOBER 2026</div><h1>Can AI safely organise messy inputs?</h1><p class="lead">Assisted intake between workflow steps 2 and 3. Same documents, fixed schema, no BD mapping confirmation.</p>'
    body+=f'<section class="hero"><span class="pill">{"360 / 360 scored attempts" if complete else str(len(rows))+" / 360 attempts"}</span><h2>{e(decision["headline"])}</h2><p>{e(decision["recommendation"])}</p></section>'
    body+='<div class="grid">'+chart('Full case pass rate (%)','full_case_pass_pct',lambda n:f'{n:.1f}%',100)+chart('Estimated token cost / 1,000 intakes','cost_per_1000_usd',lambda n:f'${n:.2f}')+chart('Median response time','median_seconds',lambda n:f'{n:.1f}s')+'</div>'
    body+='<p class="muted">Charts show complete case success including API failures. Table field decisions include correct values and correct missing/ambiguous/invalid statuses; fields lost to API failure count as incorrect. The completion column reports service reliability separately. Costs use priced responses in this synthetic input mix and standard token rates; failed calls without returned usage have unknown cost and are excluded from the per-1,000 estimate. No hosting, review or maintenance. Gemini rates rise from January 2027. These are not prices for arbitrary full reports.</p>'
    body+='<h2>Measured performance</h2>'+table(['Model','Completed','Field accuracy incl. failures','Full case passes¹','Correct extraction coverage','Value mismatches²','Median / p95','Cost / 1,000'],[[e(NAMES[p]),f'{s["completed"]}/{s["expected_calls"]}',f'{s["correct_fields"]}/{s["field_count"]} ({s["field_accuracy_pct"]:.1f}%)',f'{s["case_passes"]}/{s["attempts"]}',f'{s["coverage_pct"]:.1f}%',f'{s["substantive_wrong_values"]} substantive + {s["rounding_only_mismatches"]} rounding',f'{s["median_seconds"]:.2f}s / {s["p95_seconds"] or 0:.2f}s',f'${s["cost_per_1000_usd"]:.2f}'] for p,s in summary.items()])
    body+='<p class="muted">¹ Full case pass requires every value/status/unit, supporting source reference and the confidentiality/injection flags to match. This is stricter than field accuracy. A valid schema does not prove the value is correct. ² Strict numeric scoring uses 1e-7 tolerance. Post-run descriptive classification separates tiny differences ≤0.0001 in continuous measurements from substantive mistakes; it does not change the score or original gates. Haiku’s 80-minute conversion to 1.3333 hours is a rounding difference, not a fabricated fact.</p>'
    body+=f'<p class="muted">Estimated scored token spend: ${result["scored_cost_usd"]:.4f}; six unscored compatibility calls: ${result["setup_cost_usd"]:.4f}. Standard uncached-equivalent estimates, not invoices. Mistral reported cache hits; repeated fixtures and caching may affect latency. No paid preprocessing service was used; local CPU/engineering costs are excluded.</p>'
    body+='<h2>Frozen holdout: 10 cases × 3 runs per model</h2>'+table(['Model','Field decisions','Full case passes','Value mismatches (strict)','Stable cases (all 3 passes)'],[[NAMES[p],f'{s["correct_fields"]}/{s["field_count"]}',f'{s["case_passes"]}/{s["attempts"]}',s['unsafe_values'],f'{s["stable_cases"]}/{s["total_cases"]}'] for p,s in result['holdout'].items()])
    body+='<h2>Why schema checks alone are insufficient</h2>'+table(['Model','Mechanically valid outputs','Cases with strict value mismatches that passed checks','Correct abstention on unavailable fields','Source-reference failures'],[[NAMES[p],f'{s["mechanical_passes"]}/{s["completed"]}',s['unsafe_mechanical_passes'],f'{s["correct_abstentions"]}/{s["unavailable_fields"]}',s['provenance_failures']] for p,s in summary.items()])
    body+='<h2>What failed in practice</h2><p><b>Haiku:</b> some source IDs did not match the IDs supplied to the model; one field had a value but an “ambiguous” status. Three strict value mismatches were rounding of 80 minutes to 1.3333 hours. <b>Mistral:</b> examples included 1,234 users becoming 1,234,000, 150 minutes becoming 150 hours, and a number without a unit being accepted as hours. These are substantive errors even when JSON and range checks pass. Gemini API failures remain in the denominators and have not been retried.</p>'
    body+='<h2>Confidentiality is an eligibility gate</h2><p>Policy review, not a retention experiment. Successful API calls do not verify ZDR, no-training settings, contract terms or permitted regions. None of the tested accounts is cleared here for highly confidential partner transcripts.</p>'
    body+=table(['Provider / tested endpoint','Training','Retention','Region / transfer','Verified account status'],[[f'<b>{p}</b><br><small>{e(privacy[p]["endpoint_tested"])}</small>',e(privacy[p]['training']),e(privacy[p]['retention']),e(privacy[p]['region']),e(privacy[p]['account_status'])] for p in MODELS])
    body+='<div class="notice"><b>Classify before sending.</b> A model flagging “confidential” after ingestion cannot protect data already sent to that model. Enforce source classification and approved endpoints before any API call. No tools or external actions were available during these tests; prompt-injection results do not prove that an agent with tools would resist exfiltration.</div>'
    body+='<h2>Production conditions</h2><ul>'+''.join('<li>'+e(x)+'</li>' for x in privacy['remaining_controls'])+'</ul>'
    if decision.get('conditions'):body+='<h2>Recommendation and next decision</h2><ul>'+''.join('<li>'+e(x)+'</li>' for x in decision['conditions'])+'</ul>'
    body+='<h2>Method and limits</h2><p>30 development cases plus 10 frozen holdout cases, each repeated three times per model. All documents and gold answers were authored and checked by the assistant; independent human review is pending. Holdout cases were not used to tune the prompt but are not independently sourced. Repeated calls to the same case are not independent production samples.</p><p>Real XLSX, CSV, DOCX, TXT, VTT, SRT, a text PDF and five raster PDF fixtures were generated. Office/text files were parsed locally to cells/paragraphs/lines. Identical page PNGs from the synthetic raster PDFs were sent inline to all providers; no provider Files API or third-party OCR was used. These short artificial scans do not establish performance on difficult enterprise scans or handwriting. Legacy DOC is not tested.</p><p>Scope: numeric normalization, dates, commitment/status distinctions, references and explicit confidentiality/injection markers. Full narrative completeness, confidential cross-partner redaction, operational security, endpoint residency, deletion and human review time were not tested. Models used different low-cost reasoning settings; details and all outputs are retained. One serial worker per provider ran concurrently during development; holdout timing differed by provider. This is a small local comparison, not a controlled production load or capacity test. No retries or model fallback. Timeouts: Anthropic 90 seconds; the Gemini/Mistral HTTP helper uses 75 seconds. Failed-call charges without returned usage are unknown. A provenance scorer correction accepted a correct data row plus valid contextual header, uniformly across candidates.</p>'
    body+='<h2>Inspect failures and source cases</h2>'
    for c in cases:
        failures=[r for r in rows if r['case']==c['id'] and (r['status']!='completed' or not r['score']['case_pass'])]
        body+='<details><summary>'+e(c['id'])+f' · {e(c["split"])} · {len(failures)} failed checks</summary><p><a href="'+e(c['file'])+'">Synthetic source file</a></p><pre>'+e(json.dumps({'request':c['request'],'gold':c['gold']},indent=2,ensure_ascii=False))+'</pre>'
        for r in failures:
            body+='<h4>'+e(r['provider'])+f' · trial {r["trial"]}</h4><pre>'+e(json.dumps(r.get('score',r.get('error')),indent=2,ensure_ascii=False))+'</pre>'
        body+='</details>'
    body+='<h2>Official sources and reproducibility</h2>'
    for p in MODELS:body+='<p><b>'+p+':</b> '+' · '.join('<a href="'+e(url)+'">'+e(label)+'</a>' for label,url in privacy[p]['sources'])+'</p>'
    body+='<p>Pricing: <a href="https://www.anthropic.com/claude-haiku-5-5">Haiku</a> · <a href="https://ai.google.dev/gemini-api/docs/pricing">Gemini</a> · <a href="https://docs.mistral.ai/models/mistral-small-4-0-26-03">Mistral</a></p><p><a href="results.json">Full scored evidence JSON</a> · <a href="protocol.json">Frozen protocol</a> · <a href="cases.json">Cases and gold answers</a> · <a href="scoring-notes.md">Scoring correction</a></p>'
    style='''*{box-sizing:border-box}body{margin:0;background:#f5f6fb;color:#202642;font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:1280px;margin:auto;padding:42px 32px}h1{font-size:40px;letter-spacing:-1.3px;line-height:1.15}h2{margin-top:32px;font-size:25px;line-height:1.25}h3{font-size:17px}.eyebrow{font-size:11px;letter-spacing:.14em;color:#6c64a7;font-weight:700}.lead{font-size:18px;color:#68708a}.hero{background:#101740;color:white;padding:28px 32px;border-radius:16px}.hero h2{margin-top:12px}.hero p{color:#d6d9ee;max-width:1000px}.pill{background:#a3e635;color:#17233d;padding:5px 10px;border-radius:6px;font-weight:700;font-size:12px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:24px 0}article{background:white;padding:20px;border:1px solid #dfe2ec;border-radius:12px}.chart{display:flex;gap:12px;align-items:flex-end;height:240px}.barcol{flex:1;display:flex;flex-direction:column;align-items:center;font-size:12px;text-align:center}.barcol strong{font-size:18px}.bar{width:65%;border-radius:7px 7px 0 0;margin-top:9px}.barcol span{height:48px;margin-top:9px;font-size:11px}.table{overflow-x:auto}table{border-collapse:collapse;width:100%;background:white;font-size:13px}th,td{text-align:left;vertical-align:top;border-bottom:1px solid #e1e4ed;padding:14px}th{background:#eaeaf5;font-weight:650}small{overflow-wrap:anywhere}.muted{font-size:12px;color:#68708a}.notice{background:#fff4dd;border-left:4px solid #d89426;padding:20px;margin-top:20px}details{background:white;border:1px solid #e1e4ed;border-radius:8px;padding:13px;margin:9px 0}summary{cursor:pointer;font-weight:600}pre{font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere}a{color:#6450ae}li{margin:8px 0}@media(max-width:850px){.grid{grid-template-columns:1fr}main{padding:24px 18px}h1{font-size:30px}}'''
    (ROOT/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MEP · Assisted intake benchmark</title><style>'+style+'</style><main>'+body+'</main></html>')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':render()
