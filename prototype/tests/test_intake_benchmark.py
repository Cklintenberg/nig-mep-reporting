from copy import deepcopy
import json
from intake_benchmark.runner import score,mechanical,ROOT,checksum


def example():
    c=json.loads((ROOT/'cases.json').read_text())[0]
    out={'fields':[{'key':g['key'],'value':g['value'],'unit':g['unit'],'status':g['status'],'source_refs':g['allowed_refs'],'reason':'test'} for g in c['gold']],
         'restricted_content_detected':False,'untrusted_instruction_detected':False}
    return c,out


def test_corpus_is_frozen_and_no_answers_in_payload():
    from intake_benchmark.runner import input_for
    cases=json.loads((ROOT/'cases.json').read_text());p=json.loads((ROOT/'protocol.json').read_text())
    assert checksum(cases)==p['cases_hash']
    assert len(cases)==40 and sum(c['split']=='holdout' for c in cases)==10
    assert 'gold' not in json.loads(input_for(cases[0]))


def test_semantically_wrong_but_plausible_number_is_scored_unsafe():
    c,out=example();out['fields'][0]['value']='1246'
    assert mechanical(out,c)==[]  # Schema/range checks cannot detect this wrong fact.
    assert score(out,c)['unsafe_values']==1


def test_missing_value_cannot_be_zero():
    c,out=example();c['gold'][0].update(value=None,status='missing');out['fields'][0]['value']='0'
    assert score(out,c)['unsafe_values']==1


def test_value_reference_plus_valid_header_is_allowed():
    c,out=example();out['fields'][0]['source_refs']=['Operations!A1','Operations!A3']
    assert score(out,c)['case_pass']
    out['fields'][0]['source_refs']=['Operations!A1']
    assert not score(out,c)['case_pass']


def test_unknown_cell_reference_fails_mechanical_checks():
    c,out=example();out['fields'][0]['source_refs']=['Operations!B3']
    assert mechanical(out,c)


def test_rounding_breakdown_does_not_change_strict_score():
    from intake_benchmark.report import rounding_only
    f={'unsafe_value':True,'expected':{'key':'analytics_delay','status':'extracted','value':'1.3333333333333333'},'actual':{'value':'1.3333'}}
    assert rounding_only(f)
    f['actual']['value']='80'
    assert not rounding_only(f)
    f['expected']['key']='weekly_active_users';f['actual']['value']='1.3333'
    assert not rounding_only(f)
