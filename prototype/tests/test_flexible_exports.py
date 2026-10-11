import json
import pytest
import workflow
from workflow import load_sample,build_report
from exports import approve_report,render_html
from presentation_export import verify_approval


def test_notes_only_keeps_absent_metrics_distinct(monkeypatch):
    _,sources=load_sample('normal')
    calls=[]
    def generate(pack,*args):
        calls.append(pack)
        return workflow.baseline_narrative(pack),{'mode':'test AI','model':'test'}
    monkeypatch.setattr(workflow,'generate_narrative',generate)
    report=build_report(None,sources,mode='live')
    assert len(calls)==1 and report['metrics']==[] and report['metrics_csv'] is None
    assert any(i['code']=='no_metrics' for i in report['issues'])
    assert 'No KPIs have been inferred' in render_html(approve_report(report,'Tester',True))


def test_metrics_only_skips_ai_and_has_no_fabricated_findings(monkeypatch):
    metrics,sources=load_sample('normal');pack=json.loads(sources);pack['sources']=[]
    monkeypatch.setattr(workflow,'generate_narrative',lambda *a:pytest.fail('No AI needed'))
    report=build_report(metrics,json.dumps(pack).encode(),mode='live')
    assert report['narrative']['findings']==[]
    assert report['usage']['estimated_cost_usd']==0
    assert 'Figures alone' in render_html(approve_report(report,'Tester',True))
    with pytest.raises(ValueError,match='Upload a metrics'):
        build_report(None,json.dumps(pack).encode(),mode='live')
    with pytest.raises(ValueError):
        build_report(b'invalid,data\n1,2',json.dumps(pack).encode(),mode='live')


def test_changed_or_unapproved_content_cannot_export():
    r=build_report(*load_sample('normal'))
    with pytest.raises(ValueError,match='Approve'): verify_approval(r)
    a=approve_report(r,'Tester',True);verify_approval(a)
    a['metrics'][0]['current']=99999
    with pytest.raises(ValueError,match='changed after approval'): verify_approval(a)


def test_chart_workbook_keeps_decimal_values_and_is_idempotent(tmp_path):
    import zipfile
    from io import BytesIO
    from decimal import Decimal
    import xml.etree.ElementTree as ET
    from chart_workbooks import embed_chart_workbooks,C,T
    p=tmp_path/'chart.pptx'
    chart=f'''<c:chartSpace xmlns:c="{C}"><c:chart><c:plotArea><c:barChart><c:ser><c:tx><c:v>Availability</c:v></c:tx><c:cat><c:strLit><c:ptCount val="2"/><c:pt idx="0"><c:v>Previous</c:v></c:pt><c:pt idx="1"><c:v>Current</c:v></c:pt></c:strLit></c:cat><c:val><c:numLit><c:ptCount val="2"/><c:pt idx="0"><c:v>99.8</c:v></c:pt><c:pt idx="1"><c:v>99.9</c:v></c:pt></c:numLit></c:val></c:ser></c:barChart></c:plotArea></c:chart></c:chartSpace>'''
    with zipfile.ZipFile(p,'w') as z:
        z.writestr('[Content_Types].xml',f'<Types xmlns="{T}"/>')
        z.writestr('ppt/slides/charts/chart1.xml',chart)
    embed_chart_workbooks(p);embed_chart_workbooks(p)
    with zipfile.ZipFile(p) as z:
        books=[n for n in z.namelist() if n.endswith('.xlsx')]
        assert len(books)==1
        with zipfile.ZipFile(BytesIO(z.read(books[0]))) as w:
            root=ET.fromstring(w.read('xl/worksheets/sheet1.xml'))
            ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            assert Decimal(root.find(".//s:c[@r='B3']/s:v",ns).text)==Decimal('99.9')


def test_download_checks_without_human_approval():
    from exports import validate_export
    from presentation_export import presentation_path
    r=build_report(*load_sample('normal'))
    validate_export(r)
    first=presentation_path(r)
    r['narrative']['findings'][0]['summary']='Updated summary.'
    assert presentation_path(r)!=first
    r['narrative']['findings'][0]['evidence'][0]['quote']='Invented quotation.'
    with pytest.raises(ValueError,match='automatic checks'): presentation_path(r)
    with pytest.raises(ValueError,match='automatic checks'): render_html(r)


def test_portable_renderer_without_local_runtime(monkeypatch, tmp_path):
    import presentation_export as pe
    monkeypatch.setattr(pe, 'ROOT', tmp_path)
    monkeypatch.delenv('MEP_ARTIFACT_MODULE', raising=False)
    monkeypatch.delenv('MEP_EXPORT_NODE', raising=False)
    monkeypatch.setenv('MEP_EXPORT_RENDERER', 'auto')
    assert pe.renderer_config()[0] == 'portable'


def test_portable_export_embeds_editable_charts_and_preserves_missing(monkeypatch, tmp_path):
    import shutil
    import zipfile
    import xml.etree.ElementTree as ET
    import presentation_export as pe
    if not shutil.which('node') or not (pe.ROOT/'presentation/node_modules/pptxgenjs').exists():
        pytest.skip('Install Node and run npm ci in presentation to test real PPTX export.')
    monkeypatch.setenv('MEP_EXPORT_RENDERER', 'portable')
    r=build_report(*load_sample('missing_data'))
    monkeypatch.setattr(pe,'presentation_path',lambda report: tmp_path/'report.pptx')
    p=pe.render_presentation(r)
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        charts=[n for n in z.namelist() if n.startswith('ppt/charts/') and n.endswith('.xml')]
        assert charts and any(n.endswith('.xlsx') for n in z.namelist())
        texts=' '.join(' '.join(ET.fromstring(z.read(n)).itertext()) for n in z.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml'))
        assert 'Not supplied' in texts
        assert all(f['title'] in texts for f in r['narrative']['findings'])
        assert all(i['message'] in texts for i in r['issues'])
