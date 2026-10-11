"""Human approval and safe, standalone exports. No automatic sending."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
from uuid import uuid4
from schemas import Narrative, SourcePack
from workflow import check_evidence

ROOT=Path(__file__).resolve().parent


def content_hash(report):
    return sha256(json.dumps(report,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def approve_report(report, reviewer, checked):
    if not reviewer.strip() or not checked:
        raise ValueError("Enter a reviewer name and confirm the source and metric review.")
    issues=check_evidence(Narrative.model_validate(report['narrative']), SourcePack.model_validate(report['pack']))
    if any(i['severity']=='error' for i in report['issues']) or issues:
        raise ValueError("Resolve evidence validation errors by generating a new draft before approval.")
    result=deepcopy(report)
    result['approval']={'reviewer':reviewer.strip(), 'approved_at':datetime.now(timezone.utc).isoformat(),
                        'content_hash':content_hash(report), 'id':str(uuid4()),
                        'scope':'Human-reviewed local prototype; reviewer identity is self-declared.'}
    return result


def validate_export(report):
    """Mechanical checks only; downloading never attests human approval."""
    issues=check_evidence(Narrative.model_validate(report['narrative']), SourcePack.model_validate(report['pack']))
    if any(i['severity']=='error' for i in report['issues']) or issues:
        raise ValueError('This report could not pass its automatic checks. Create a new report from the source files.')


def render_html(report):
    validate_export(report)
    e=lambda v: escape(str(v),quote=True)
    report_type=report['pack'].get('report_type','Engineering')
    approval=report.get('approval')
    status='Prepared for internal use · Review before sharing'
    metricrows=''.join(f"<tr><th>{e(m['label'])}</th><td>{e(m['previous']) if m['previous'] is not None else 'Missing'}</td><td>{e(m['current']) if m['current'] is not None else 'Missing'}</td><td>{e(m['delta'])+' '+e(m['delta_kind']) if m['delta'] is not None else 'Not calculated'}</td><td>{e(m['unit'])}</td></tr>" for m in report['metrics'])
    findings=''.join(f"<article><small>{e(f['category'])}</small><h3>{e(f['title'])}</h3><p>{e(f['summary'])}</p>"+
                     (f"<p class='note'>Review note: {e(f['review_reason'])}</p>" if f['needs_review'] else '')+'</article>' for f in report['narrative']['findings'])
    warnings=''.join(f"<li>{e(i['message'])}</li>" for i in report['issues'])
    questions=''.join(f"<li>{e(q)}</li>" for q in report['narrative']['discussion_questions'])
    sources=''.join(f"<details id=\"source-{e(s['id'])}\"><summary>{e(s['id'])} · {e(s['title'])} · {e(s['date'] or 'Meeting date not supplied')}</summary><p style='white-space:pre-wrap'>{e(s['text'])}</p></details>" for s in report['pack']['sources'])
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MEP weekly review</title>
<style>body{{font:16px/1.6 system-ui;background:#f7f8f5;color:#17261e;margin:0}}main{{max-width:980px;margin:auto;padding:44px 28px}}header{{background:#142b26;color:white;padding:28px;border-radius:16px}}h1{{font-size:36px;line-height:1.1}}small{{text-transform:uppercase;letter-spacing:.06em}}article{{background:white;padding:20px 26px;margin:20px 0;border:1px solid #dce2d6;border-radius:12px}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{text-align:left;padding:12px;border-bottom:1px solid #ddd}}blockquote{{border-left:3px solid #adc978;padding-left:15px;color:#52604f}}.note{{color:#815300}}details{{margin:10px 0}}footer{{font-size:12px;overflow-wrap:anywhere}}@media print{{body{{background:white}}main{{padding:0}}article{{break-inside:avoid}}}}</style>
<main><header><small>NIG / MEP · Fictional case study · Internal BD preparation</small><h1>Weekly {e(report_type.lower())} review</h1><p>Week of {e(report['pack']['week_start'])} · {e(report['usage']['mode'])}</p><p>{status}</p><p>Check the audience and sensitive content before sharing.</p></header>
<h2>Platform signals</h2><p>{'Same cohort: '+e(report['metrics'][0]['cohort'])+'. Previous week vs reporting week. Python calculates all values and changes.' if report['metrics'] else 'No metrics spreadsheet supplied. No KPIs have been inferred.'}</p>{'<table><tr><th>Metric</th><th>Previous</th><th>Current</th><th>Change</th><th>Unit</th></tr>'+metricrows+'</table>' if report['metrics'] else ''}
{'<h2>Data quality notes</h2><ul>'+warnings+'</ul>' if warnings else ''}<h2>Key findings</h2>{findings or '<p>No meeting material supplied. Figures alone do not establish causes or commitments.</p>'}
{'<h2>Questions for the meeting</h2><ul>'+questions+'</ul>' if questions else ''}
<footer><p>Prepared from the supplied files. Review before use. Nothing is sent or published automatically.</p></footer></main></html>'''


def save_approved(report):
    if 'approval' not in report: raise ValueError('Only approved reports can be saved here.')
    folder=ROOT/'runs'/report['approval']['id']
    folder.mkdir(parents=True,exist_ok=False)
    (folder/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    (folder/'report.html').write_text(render_html(report))
    return folder
