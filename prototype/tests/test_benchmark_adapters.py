import httpx
import pytest
import ai
from schemas import SourcePack
from workflow import build_report, load_sample


def fixture_data():
    metrics, sources = load_sample('normal')
    return SourcePack.model_validate_json(sources), build_report(metrics, sources)['narrative']


def test_gemini_no_storage_id_and_reasoning_cost(monkeypatch):
    pack, narrative = fixture_data()
    import json
    def post(url, headers, payload, provider):
        assert payload['store'] is False
        assert payload['response_format']['schema'] == ai.Narrative.model_json_schema()
        assert payload['input'] == pack.model_dump_json()
        return {'status': 'completed', 'model': 'gemini-3.5-flash-lite',
                'steps': [{'type': 'model_output', 'content': [{'type': 'text', 'text': json.dumps(narrative)}]}],
                'usage': {'total_input_tokens': 100, 'total_output_tokens': 40, 'total_thought_tokens': 10}}
    monkeypatch.setattr(ai, '_post_json', post)
    result = ai._gemini(pack, 'gemini-3.5-flash-lite', 'test-key')
    assert result[0].model_dump() == narrative
    assert result[2:] == (None, 100, 50, 0)


def test_mistral_structured_contract_and_truncation(monkeypatch):
    pack, narrative = fixture_data()
    import json
    response = {'model': 'mistral-small-2603', 'id': 'test',
                'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(narrative)}}],
                'usage': {'prompt_tokens': 100, 'completion_tokens': 50}}
    def post(url, headers, payload, provider):
        assert payload['response_format']['json_schema']['schema'] == ai.Narrative.model_json_schema()
        assert payload['messages'][1]['content'] == pack.model_dump_json()
        assert payload['reasoning_effort'] == 'none'
        return response
    monkeypatch.setattr(ai, '_post_json', post)
    assert ai._mistral(pack, 'mistral-small-2603', 'test-key')[0].model_dump() == narrative
    response['choices'][0]['finish_reason'] = 'length'
    with pytest.raises(RuntimeError, match='incomplete'):
        ai._mistral(pack, 'mistral-small-2603', 'test-key')


def test_http_error_excludes_credentials_and_raw_body(monkeypatch):
    def post(*args, **kwargs):
        return httpx.Response(429, json={'message': 'secret body'},
                              request=httpx.Request('POST', 'https://example.test', headers={'Authorization': 'secret key'}))
    monkeypatch.setattr(httpx, 'post', post)
    with pytest.raises(RuntimeError, match='HTTP 429') as error:
        ai._post_json('https://example.test', {}, {}, 'Mistral')
    assert 'secret' not in str(error.value)
