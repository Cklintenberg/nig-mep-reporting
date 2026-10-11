"""Reproducible smoke check with synthetic inputs and no provider/API calls."""
import json
import os
from pathlib import Path
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import date

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ingestion import prepare_metrics, prepare_sources
from workflow import build_report
from exports import render_html
from presentation_export import render_presentation


def main():
    folder=ROOT/'sample_data'/'Demo files'
    metrics,_=prepare_metrics('platform-metrics.xlsx',(folder/'platform-metrics.xlsx').read_bytes())
    names=['engineering-notes.docx','partner-call.vtt','vendor-call.srt','bd-follow-up-notes.txt']
    source_bytes,_=prepare_sources([(n,(folder/n).read_bytes()) for n in names],'',date(2026,9,28))
    pack=json.loads(source_bytes)
    assert len(pack['sources'])==4, 'Expected four synthetic meeting sources'
    pack['sources']=[]  # Actual figures-only workflow: intentionally no model call.
    report=build_report(metrics,json.dumps(pack).encode(),mode='live')
    values={m['key']:m for m in report['metrics']}
    assert values['weekly_active_users']['current']==1200
    assert values['weekly_active_users']['delta']==20
    assert report['usage']['model']=='none'
    output=ROOT/'runs'/'submission-check';output.mkdir(parents=True,exist_ok=True)
    (output/'figures-only.html').write_text(render_html(report))
    os.environ['MEP_EXPORT_RENDERER']='portable'
    pptx=render_presentation(report)
    with zipfile.ZipFile(pptx) as z:
        assert z.testzip() is None
        assert 'ppt/presentation.xml' in z.namelist()
        assert any(n.startswith('ppt/charts/') and n.endswith('.xml') for n in z.namelist())
        assert any(n.endswith('.xlsx') for n in z.namelist())
        for n in z.namelist():
            if n.endswith('.xml'): ET.fromstring(z.read(n))
    (output/'figures-only.pptx').write_bytes(pptx.read_bytes())
    print('PASS: five synthetic files parsed; 1,200 users / +20%; no AI call; HTML and editable PPTX exported.')
    print('Outputs: runs/submission-check (ignored by Git). Visual viewer compatibility is a separate check.')

if __name__=='__main__': main()
