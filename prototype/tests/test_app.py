from streamlit.testing.v1 import AppTest
from pathlib import Path
import pytest
import exports
import benchmark
import report_store
import ai
import workflow
import streamlit as st
import json
from io import BytesIO
from workflow import load_sample

@pytest.fixture(autouse=True)
def isolated_runs(monkeypatch,tmp_path):
    monkeypatch.setattr(exports,"ROOT",tmp_path)
    monkeypatch.setattr(benchmark,"ROOT",tmp_path)
    monkeypatch.setattr(report_store,"ROOT",tmp_path)


@pytest.fixture(autouse=True)
def simulated_reporting_service(monkeypatch):
    """Exercise automatic AI routing without paid calls or real local credentials."""
    calls=[]
    monkeypatch.setattr(ai,'local_setting',lambda name,default='': 'test-key' if name.endswith('_API_KEY') else default)
    def generate(pack,model,provider):
        calls.append((provider,model))
        return workflow.baseline_narrative(pack), {'provider':provider,'model':model,'mode':'simulated AI response','estimated_cost_usd':0}
    monkeypatch.setattr(workflow,'generate_narrative',generate)
    return calls



@pytest.fixture(autouse=True)
def local_renderer(monkeypatch,tmp_path):
    import presentation_export
    output=tmp_path/'review.pptx';output.write_bytes(b'local-test-deck')
    monkeypatch.setattr(presentation_export,'render_presentation',lambda report: output)


@pytest.fixture
def uploads(monkeypatch):
    """Supply real file bytes at the upload boundary; AppTest has no upload action."""
    selected = {'case': 'normal', 'metric_count': 1, 'notes': True}
    def file(name, raw):
        result = BytesIO(raw)
        result.name = name
        return result
    def uploader(label, **kwargs):
        metrics, sources = load_sample(selected['case'])
        return [file(f'metrics-{i}.csv', metrics) for i in range(selected['metric_count'])]+[file(source['title']+'.txt', source['text'].encode())
                for source in (json.loads(sources)['sources'] if selected['notes'] else [])]
    monkeypatch.setattr(st, 'file_uploader', uploader)
    return selected


def test_unified_upload_rejects_multiple_spreadsheets(uploads):
    uploads['metric_count']=2
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=20).run()
    next(b for b in app.sidebar.button if b.label=='Weekly report').click().run()
    assert not app.exception
    assert next(b for b in app.button if b.label=='Create report draft').disabled
    assert any('Keep one platform spreadsheet' in x.value for x in app.error)


def test_downloads_available_without_approval(uploads):
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=20).run()
    next(b for b in app.sidebar.button if b.label=='Weekly report').click().run()
    next(b for b in app.button if b.label=='Create report draft').click().run()
    assert not app.exception
    assert len(app.metric)==4
    assert not any(t.label=='Reviewer name' for t in app.text_input)
    assert not app.checkbox
    assert not any(t.label=='Report text' for t in app.text_area)
    assert {b.proto.label for b in app.get('download_button')}=={'Download written report','Download PowerPoint'}
    assert 'approval' not in app.session_state['report']


def test_input_change_retains_previous_report_until_new_generation(uploads):
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=20).run()
    next(b for b in app.sidebar.button if b.label=='Weekly report').click().run()
    next(b for b in app.button if b.label=='Create report draft').click().run()
    uploads['case']='missing_data'
    app.run()
    assert app.text_area
    assert any("saved inputs" in info.value for info in app.info)
    next(b for b in app.button if b.label=='Create report draft').click().run()
    assert any('missing current week' in s.value for s in app.warning)
    assert not app.exception


def test_comparison_baseline_all_cases():
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=20).run()
    next(b for b in app.sidebar.button if b.label=='Model comparison').click().run()
    app.multiselect[0].set_value(['normal','missing_data','conflicting_dates','duplicate_feedback','untrusted_note']).run()
    next(b for b in app.button if b.label=='Run comparison').click().run()
    assert not app.exception
    assert len(app.expander)==5


def test_weekly_report_automatically_uses_haiku(uploads,simulated_reporting_service):
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=20).run()
    next(b for b in app.sidebar.button if b.label=='Weekly report').click().run()
    assert not app.toggle and not app.selectbox
    next(b for b in app.button if b.label=='Create report draft').click().run()
    assert not app.exception
    assert simulated_reporting_service==[('Anthropic','claude-haiku-5-5')]
    assert report_store.list_reports()[0]['model']=='claude-haiku-5-5'


def test_weekly_missing_credentials_blocks_creation(uploads,monkeypatch,simulated_reporting_service):
    monkeypatch.setattr(ai,'local_setting',lambda name,default='':default)
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=20).run()
    next(b for b in app.sidebar.button if b.label=='Weekly report').click().run()
    assert next(b for b in app.button if b.label=='Create report draft').disabled
    assert any('workspace administrator' in w.value for w in app.warning)
    assert not simulated_reporting_service


def test_weekly_service_failure_never_falls_back_to_non_ai(uploads,monkeypatch):
    def fail(*args,**kwargs): raise RuntimeError('Reporting service unavailable.')
    monkeypatch.setattr(workflow,'generate_narrative',fail)
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=20).run()
    next(b for b in app.sidebar.button if b.label=='Weekly report').click().run()
    next(b for b in app.button if b.label=='Create report draft').click().run()
    assert not app.exception
    assert any('Reporting service unavailable' in e.value for e in app.error)
    assert not report_store.list_reports()


def test_saved_report_reopens_without_approval(uploads):
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=20).run()
    next(b for b in app.sidebar.button if b.label=='Weekly report').click().run()
    next(b for b in app.button if b.label=='Create report draft').click().run()
    original=app.session_state['report']
    fresh=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=20).run()
    next(b for b in fresh.sidebar.button if b.label=='Report library').click().run()
    next(b for b in fresh.button if b.label=='Open saved report').click().run()
    assert not fresh.exception and fresh.session_state['report']==original
    assert len(report_store.list_reports())==1
    assert len(fresh.get('download_button'))==2


@pytest.mark.parametrize('metric_count,notes,ai_calls',[(0,True,1),(1,False,0)])
def test_each_input_type_can_generate_and_approve(uploads,simulated_reporting_service,metric_count,notes,ai_calls):
    uploads.update(metric_count=metric_count,notes=notes)
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=20).run()
    next(b for b in app.sidebar.button if b.label=='Weekly report').click().run()
    assert not next(b for b in app.button if b.label=='Create report draft').disabled
    next(b for b in app.button if b.label=='Create report draft').click().run()
    assert not app.exception
    assert len(simulated_reporting_service)==ai_calls
    assert len(app.get('download_button'))==2
    assert 'approval' not in app.session_state['report']


def test_metrics_only_does_not_require_api_key(uploads,monkeypatch):
    uploads['notes']=False
    monkeypatch.setattr(ai,'local_setting',lambda name,default='':default)
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=20).run()
    next(b for b in app.sidebar.button if b.label=='Weekly report').click().run()
    assert not next(b for b in app.button if b.label=='Create report draft').disabled
    next(b for b in app.button if b.label=='Create report draft').click().run()
    assert not app.exception
    assert app.session_state['report']['usage']['mode']=='metrics only'


def test_powerpoint_failure_preserves_written_download(uploads,monkeypatch):
    import presentation_export
    def fail(report): raise RuntimeError('PowerPoint export could not finish.')
    monkeypatch.setattr(presentation_export,'render_presentation',fail)
    app=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=20).run()
    next(b for b in app.sidebar.button if b.label=='Weekly report').click().run()
    next(b for b in app.button if b.label=='Create report draft').click().run()
    assert not app.exception
    assert any(b.proto.label=='Download written report' for b in app.get('download_button'))
    assert report_store.list_reports()
