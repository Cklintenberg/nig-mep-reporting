import json
from copy import deepcopy
from datetime import date
import pytest
from pydantic import ValidationError
import ai
from exports import approve_report, content_hash, render_html
from workflow import build_report, check_evidence, load_sample, validate_inputs
from schemas import Narrative, SourcePack


def test_changes_are_deterministic_and_use_correct_units():
    r=build_report(*load_sample('normal'))
    m={v['key']:v for v in r['metrics']}
    assert m['weekly_active_users']['delta']==20
    assert m['availability']['delta']==.1
    assert m['availability']['delta_kind']=='percentage points'
    assert m['analytics_freshness']['delta']==12
    assert m['api_error_rate']['delta']==-.1
    assert m['weekly_active_users']['source_rows']==[2,3]


def test_missing_data_is_neither_zero_nor_a_change():
    r=build_report(*load_sample('missing_data'))
    m=next(v for v in r['metrics'] if v['key']=='availability')
    assert m['current'] is None and m['delta'] is None
    assert any(i['code']=='missing_metric' for i in r['issues'])


def test_zero_denominator_stays_undefined():
    csv,notes=load_sample('normal')
    r=build_report(csv.replace(b',1000,users',b',0,users'),notes)
    assert r['metrics'][0]['delta'] is None
    assert any(i['code']=='zero_baseline' for i in r['issues'])

@pytest.mark.parametrize('change,match',[
    (lambda b:b+b.splitlines()[1]+b'\n','Duplicate'),
    (lambda b:b.replace(b',99.9,%',b',101,%'),'percentage'),
    (lambda b:b.replace(b',1200,users',b',NaN,users'),'finite'),
    (lambda b:b.replace(b',1200,users',b',1200,hours'),'unit'),
    (lambda b:b.replace(b'2026-09-28',b'2026-10-05'),'dates'),
    (lambda b:b.replace(b'MEP beta matched cohort',b'Other cohort',1),'cohort'),
])
def test_bad_metrics_fail_before_any_model_call(change,match):
    csv,notes=load_sample('normal')
    with pytest.raises(ValueError,match=match): build_report(change(csv),notes)


def test_source_ids_unique_and_week_is_monday():
    csv,notes=load_sample('normal');pack=json.loads(notes)
    pack['sources'].append(pack['sources'][0])
    with pytest.raises(ValueError,match='unique'): validate_inputs(csv,json.dumps(pack).encode())
    pack['sources'].pop();pack['week_start']='2026-09-29'
    with pytest.raises(ValueError,match='Monday'): validate_inputs(csv,json.dumps(pack).encode())


def test_duplicate_feedback_warns_without_summing_it():
    r=build_report(*load_sample('duplicate_feedback'))
    assert any(i['code']=='duplicate_source' for i in r['issues'])
    assert r['metrics'][0]['current']==1200


def test_fabricated_quote_and_source_block_approval():
    r=build_report(*load_sample('normal'))
    r['narrative']['findings'][0]['evidence'][0]['quote']='This sentence is invented.'
    issues=check_evidence(Narrative.model_validate(r['narrative']),SourcePack.model_validate(r['pack']))
    assert issues[0].code=='invalid_quote'
    with pytest.raises(ValueError,match='evidence'): approve_report(r,'Demo reviewer',True)
    r['narrative']['findings'][0]['evidence'][0]['source_id']='UNKNOWN'
    assert check_evidence(Narrative.model_validate(r['narrative']),SourcePack.model_validate(r['pack']))[0].code=='unknown_source'


def test_approval_requires_human_and_fingerprints_edits():
    r=build_report(*load_sample('normal'))
    with pytest.raises(ValueError): approve_report(r,'',True)
    with pytest.raises(ValueError): approve_report(r,'Reviewer',False)
    approved=approve_report(r,'Reviewer',True)
    assert 'approval' not in r
    assert approved['approval']['content_hash']==content_hash(r)
    r['narrative']['findings'][0]['summary']='A reviewed correction.'
    assert approved['approval']['content_hash']!=content_hash(r)


def test_export_escapes_untrusted_source_and_reviewer_html():
    r=build_report(*load_sample('normal'))
    r['pack']['sources'][0]['text']+='<script>alert(1)</script>'
    r=approve_report(r,'<img src=x onerror=alert(1)>',True)
    html=render_html(r)
    assert '<script>' not in html and '<img src=x' not in html
    assert 'alert(1)' not in html  # Raw sources and reviewer metadata are excluded.

@pytest.mark.parametrize('provider,adapter,keyname', [('OpenAI','_openai','OPENAI_API_KEY'),('Anthropic','_anthropic','ANTHROPIC_API_KEY'),('Gemini','_gemini','GEMINI_API_KEY'),('Mistral','_mistral','MISTRAL_API_KEY')])
def test_provider_switch_preserves_contract_and_selects_only_its_key(monkeypatch,provider,adapter,keyname):
    csv,notes=load_sample('normal');pack=SourcePack.model_validate_json(notes)
    narrative=Narrative.model_validate(build_report(csv,notes)['narrative'])
    observed=[]
    monkeypatch.setattr(ai,'local_setting',lambda name,default='': 'test-'+name)
    def fake(pack_arg,model,key):
        observed.append((pack_arg,model,key));return narrative,model,'test-id',100,50,0
    monkeypatch.setattr(ai,adapter,fake)
    result,usage=ai.generate_narrative(pack,'custom-model',provider)
    assert result==narrative
    assert observed==[(pack,'custom-model','test-'+keyname)]
    assert usage['provider']==provider and usage['estimated_cost_usd'] is None
    assert 'test-'+keyname not in json.dumps(usage)


def test_missing_key_fails_explicitly_without_silent_baseline(monkeypatch):
    monkeypatch.setattr(ai,'local_setting',lambda *a:'')
    pack=SourcePack.model_validate_json(load_sample('normal')[1])
    with pytest.raises(ValueError,match='ANTHROPIC_API_KEY'): ai.generate_narrative(pack,'model','Anthropic')


def test_anthropic_workspace_is_sent_with_request(monkeypatch):
    from types import SimpleNamespace
    pack=SourcePack.model_validate_json(load_sample('normal')[1])
    narrative=Narrative.model_validate(build_report(*load_sample('normal'))['narrative'])
    seen={}
    def fake_client(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(messages=SimpleNamespace(parse=lambda **kw: SimpleNamespace(
            stop_reason='end_turn',parsed_output=narrative,model='test-model',id='test-response',
            usage=SimpleNamespace(input_tokens=100,output_tokens=50,cache_read_input_tokens=0))))
    monkeypatch.setattr(ai,'Anthropic',fake_client)
    monkeypatch.setattr(ai,'local_setting',lambda name,default='':'wrkspc_test')
    result=ai._anthropic(pack,'test-model','test-key')
    assert seen['default_headers']=={'anthropic-workspace-id':'wrkspc_test'}
    assert result[0]==narrative


@pytest.mark.parametrize('report_type',['Engineering','Vendor','Partner'])
def test_audience_is_preserved_in_prompt_export_and_input_identity(report_type):
    from report_types import for_report_type
    from hashlib import sha256
    csv,notes=load_sample('normal')
    report=build_report(csv,for_report_type(notes,report_type))
    pack=SourcePack.model_validate(report['pack'])
    assert pack.report_type==report_type
    assert report_type in ai.prompt_for(pack)
    assert report['prompt_hash']==sha256(ai.prompt_for(pack).encode()).hexdigest()
    assert f'Weekly {report_type.lower()} review' in render_html(report)
    assert 'Internal BD preparation' in render_html(report)
    if report_type!='Engineering':
        other=build_report(csv,for_report_type(notes,'Engineering'))
        assert report['input_hash']!=other['input_hash']
        assert report['prompt_hash']!=other['prompt_hash']
        assert report['metrics']==other['metrics']


def test_unknown_report_audience_is_rejected():
    from report_types import for_report_type
    with pytest.raises(ValueError): for_report_type(load_sample('normal')[1],'Anything')
