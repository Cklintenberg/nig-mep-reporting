"""Provider adapters: one bounded call, one shared report contract."""
from pathlib import Path
import os
import time
import httpx
from dotenv import dotenv_values
from openai import OpenAI, APIError as OpenAIError
from anthropic import Anthropic, APIError as AnthropicError
from schemas import Narrative, SourcePack
from report_types import REPORT_TYPES

ROOT = Path(__file__).resolve().parent
PROMPT = (ROOT / "prompts/report.txt").read_text()
PROVIDERS = {
    "OpenAI": {"key": "OPENAI_API_KEY", "model_env": "MEP_OPENAI_MODEL", "models": ["gpt-6-luna", "gpt-6.1-sol"]},
    "Anthropic": {"key": "ANTHROPIC_API_KEY", "model_env": "MEP_ANTHROPIC_MODEL", "models": ["claude-haiku-5-5", "claude-sonnet-5-5"]},
    "Gemini": {"key": "GEMINI_API_KEY", "model_env": "MEP_GEMINI_MODEL", "models": ["gemini-3.5-flash-lite"]},
    "Mistral": {"key": "MISTRAL_API_KEY", "model_env": "MEP_MISTRAL_MODEL", "models": ["mistral-small-2603"]},
}
# USD / million tokens: input, cached input, output. Checked 2026-10-08.
# These small requests stay below the providers' long-context pricing thresholds.
RATES = {"gpt-6-luna": (.10, .01, .50), "gpt-6.1-sol": (2, .10, 10),
         "claude-haiku-5-5": (.10, .01, .50), "claude-sonnet-5-5": (2, .10, 10),
         "gemini-3.5-flash-lite": (.30, .03, 2.50), "mistral-small-2603": (.15, .15, .60)}


def prompt_for(pack):
    return PROMPT + '\nInternal BD meeting brief: ' + pack.report_type + '. ' + REPORT_TYPES[pack.report_type]['prompt'] + '\nThis is internal preparation, not an externally cleared document. Never assume all sources can be shared with a vendor or partner.'


def local_setting(name, default=""):
    # A blank local value must not hide a key exported in the shell.
    return (dotenv_values(ROOT / ".env").get(name) or os.getenv(name) or default).strip()


def settings(provider="OpenAI"):
    config = PROVIDERS[provider]
    return {"has_key": bool(local_setting(config["key"])), "key_name": config["key"],
            "model": local_setting(config["model_env"], config["models"][0])}


def report_settings():
    """Operator configuration; BD users do not choose a drafting method or model."""
    provider = local_setting('MEP_REPORT_PROVIDER', 'Anthropic')
    if provider not in PROVIDERS:
        raise ValueError('Unsupported report provider in the local configuration.')
    model = local_setting('MEP_REPORT_MODEL', PROVIDERS[provider]['models'][0])
    return {'provider': provider, 'model': model, 'has_key': settings(provider)['has_key']}


def estimate_cost(model, input_tokens, output_tokens, cached_tokens=0):
    if model not in RATES:
        return None
    i, cached, o = RATES[model]
    if model=='claude-haiku-5-5' and input_tokens>100_000:
        i,cached,o=.50,.05,2.50
    return ((input_tokens - cached_tokens) * i + cached_tokens * cached + output_tokens * o) / 1_000_000


def _openai(pack, model, key):
    response = OpenAI(api_key=key, timeout=75, max_retries=0).responses.parse(
        model=model, reasoning={"effort": "low"},
        input=[{"role": "developer", "content": prompt_for(pack)},
               {"role": "user", "content": pack.model_dump_json()}],
        text_format=Narrative, max_output_tokens=6000, store=False)
    if response.status != "completed" or response.output_parsed is None:
        raise RuntimeError("The model returned an incomplete report or a refusal. Retry or inspect the inputs.")
    u = response.usage
    return response.output_parsed, response.model, response.id, u.input_tokens, u.output_tokens, u.input_tokens_details.cached_tokens


def _anthropic(pack, model, key):
    workspace = local_setting("ANTHROPIC_WORKSPACE_ID")
    headers = {"anthropic-workspace-id": workspace} if workspace else {}
    response = Anthropic(api_key=key, timeout=75, max_retries=0, default_headers=headers).messages.parse(
        model=model, max_tokens=6000, system=prompt_for(pack),
        thinking={"type": "adaptive"}, output_config={"effort": "low"},
        messages=[{"role": "user", "content": pack.model_dump_json()}], output_format=Narrative)
    if response.stop_reason != "end_turn" or response.parsed_output is None:
        raise RuntimeError("The model returned an incomplete report or a refusal. Retry or inspect the inputs.")
    u = response.usage
    cached = u.cache_read_input_tokens or 0
    return response.parsed_output, response.model, response.id, u.input_tokens + cached, u.output_tokens, cached


def _post_json(url,headers,payload,provider):
    try:
        response=httpx.post(url,headers=headers,json=payload,timeout=75)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        # Never persist provider error bodies, credentials or request payloads.
        raise RuntimeError(f'{provider} request failed (HTTP {exc.response.status_code}). Check account access, model compatibility and quota.') from None
    except httpx.RequestError:
        raise RuntimeError(f'{provider} network request failed or timed out. No automatic retry was made.') from None


def _gemini(pack,model,key):
    response=_post_json('https://generativelanguage.googleapis.com/v1beta/interactions',
        {'x-goog-api-key':key},{'model':model,'store':False,
        'system_instruction':prompt_for(pack),'input':pack.model_dump_json(),
        'generation_config':{'thinking_level':'low','max_output_tokens':6000},
        'response_format':{'type':'text','mime_type':'application/json','schema':Narrative.model_json_schema()}},'Gemini')
    if response.get('status')!='completed':
        raise RuntimeError('Gemini returned an incomplete report or refusal.')
    content=''.join(c.get('text','') for step in response.get('steps',[]) if step.get('type')=='model_output'
                    for c in step.get('content',[]) if c.get('type')=='text')
    u=response['usage']
    # Interactions reports thought tokens separately; both count toward output cost.
    output=u['total_output_tokens']+u.get('total_thought_tokens',0)
    # store=False responses need not include a persisted interaction ID.
    return Narrative.model_validate_json(content),response.get('model',model),response.get('id'),u['total_input_tokens'],output,u.get('total_cached_tokens',0)


def _mistral(pack,model,key):
    response=_post_json('https://api.mistral.ai/v1/chat/completions',
        {'Authorization':'Bearer '+key},{'model':model,'max_tokens':6000,'reasoning_effort':'none',
        'messages':[{'role':'system','content':prompt_for(pack)},{'role':'user','content':pack.model_dump_json()}],
        'response_format':{'type':'json_schema','json_schema':{'name':'Narrative','schema':Narrative.model_json_schema(),'strict':True}}},'Mistral')
    choice=response['choices'][0]
    if choice.get('finish_reason')!='stop':
        raise RuntimeError('Mistral returned an incomplete report or refusal.')
    content=choice['message']['content']
    if isinstance(content,list): content=''.join(c.get('text','') for c in content if c.get('type')=='text')
    u=response['usage']
    return Narrative.model_validate_json(content),response.get('model',model),response['id'],u['prompt_tokens'],u['completion_tokens'],0


def generate_narrative(pack: SourcePack, model: str, provider="OpenAI"):
    if provider not in PROVIDERS:
        raise ValueError("Choose a supported provider.")
    key_name = PROVIDERS[provider]["key"]
    key = local_setting(key_name)
    if not key:
        raise ValueError(f"Add {key_name} to the local .env file to use {provider}.")
    started = time.perf_counter()
    try:
        adapter={'OpenAI':_openai,'Anthropic':_anthropic,'Gemini':_gemini,'Mistral':_mistral}[provider]
        narrative, actual_model, request_id, ins, outs, cached = adapter(pack, model.strip(), key)
    except (OpenAIError, AnthropicError) as exc:
        status = getattr(exc, "status_code", None)
        advice = {400: "Check that the selected model supports structured output and low reasoning effort.",
                  401: "Check your API key.", 403: "Check model permissions.",
                  404: "This model is unavailable. Check the model ID and API account access.",
                  429: "Check API billing or quota, or retry later."}.get(status, "Check your connection and retry.")
        body = exc.body if isinstance(exc.body, dict) else {}
        detail = body.get("error", body)
        message = str(detail.get("message", "")) if isinstance(detail, dict) else ""
        if provider == "Anthropic" and "anthropic-workspace-id" in message:
            advice = "Set ANTHROPIC_WORKSPACE_ID in .env to a workspace this key can access, or use a workspace-scoped key."
        raise RuntimeError(f"{provider} request failed{f' (HTTP {status})' if status else ''}. {advice}") from None
    return narrative, {"provider": provider, "model": actual_model, "requested_model": model,
        "latency_seconds": round(time.perf_counter() - started, 3),
        "input_tokens": ins, "output_tokens": outs, "cached_tokens": cached,
        "estimated_cost_usd": estimate_cost(model, ins, outs, cached),
        "response_id": request_id, "mode": "live AI", "reasoning_effort": "none" if provider=='Mistral' else "low"}
