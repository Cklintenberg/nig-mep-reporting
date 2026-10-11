"""Small, paired comparison. Citation checks are not a semantic quality score."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import median
from uuid import uuid4
from workflow import SAMPLES, build_report, load_sample

ROOT=Path(__file__).resolve().parent
CRITERIA=json.loads((ROOT/'evaluation/criteria.json').read_text())


def run_comparison(configurations, cases=None):
    cases=cases or list(SAMPLES)
    rows=[]
    for case in cases:
        metrics,sources=load_sample(case)
        for config in configurations:
            row={'case':case, 'configuration':config, 'manual_checks':CRITERIA[case]['checks'],
                 'manual_result':'NOT REVIEWED', 'evaluation_role':CRITERIA[case]['role']}
            try:
                report=build_report(metrics,sources,**config)
                evidence_errors=[i for i in report['issues'] if i['severity']=='error']
                row.update(status='completed', citation_checks_pass=not evidence_errors, report=report)
            except Exception as exc:
                # Adapters sanitize API errors; unexpected failures stay generic in the UI and artifact.
                message=str(exc) if isinstance(exc,(ValueError,RuntimeError)) else f'{type(exc).__name__}: report generation failed'
                row.update(status='failed',error=message)
            rows.append(row)
    result={'id':str(uuid4()), 'created_at':datetime.now(timezone.utc).isoformat(),
            'limitations':'One run per case and configuration. Synthetic examples, no statistical claim. Manual semantic review required. Cases and criteria are separate from model input.', 'rows':rows}
    folder=ROOT/'runs'/'benchmarks';folder.mkdir(parents=True,exist_ok=True)
    (folder/f"{result['id']}.json").write_text(json.dumps(result,indent=2))
    return result


def summary_rows(result):
    groups={}
    for row in result['rows']:
        c=row['configuration'];label='Non-AI baseline' if c['mode']=='baseline' else f"{c['provider']} / {c['model']}"
        groups.setdefault(label,[]).append(row)
    summary=[]
    for label,rows in groups.items():
        done=[r for r in rows if r['status']=='completed']
        costs=[r['report']['usage']['estimated_cost_usd'] for r in done]
        summary.append({'Configuration':label,'Completed':f'{len(done)}/{len(rows)}',
                        'Citation checks passed':f"{sum(r['citation_checks_pass'] for r in done)}/{len(rows)}",
                        'Median seconds':round(median(r['report']['elapsed_seconds'] for r in done),2) if done else None,
                        'Estimated USD (completed)':round(sum(costs),6) if costs and all(c is not None for c in costs) else None,
                        'Content quality':'Needs human review'})
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--provider',choices=['OpenAI','Anthropic'])
    parser.add_argument('--models',nargs='+')
    args=parser.parse_args()
    configurations=[{'mode':'baseline'}]
    if args.provider:
        if not args.models: parser.error('--models is required with --provider')
        configurations += [{'mode':'live','provider':args.provider,'model':m} for m in args.models]
    print(json.dumps(summary_rows(run_comparison(configurations)),indent=2))
