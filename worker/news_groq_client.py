"""Groq Free Tier editor transport: text only, bounded TPM retries, no web search billing.

All facts and quotations come from fetched publisher pages supplied by our code.
Do not log API keys or complete article bodies.
"""
import json
import os
import random
import time
from typing import Any

import requests

ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"


def _token_count(value):
    return value if type(value) is int and value >= 0 else None


def _transport_metadata(data):
    """Only bounded state and token counts; never copy model content or reasoning."""
    choices = data.get("choices") if isinstance(data, dict) else None
    choice = choices[0] if isinstance(choices, list) and choices and isinstance(choices[0], dict) else {}
    raw_finish = choice.get("finish_reason")
    if raw_finish is None:
        finish = None
    elif isinstance(raw_finish, str) and raw_finish in {
        "stop", "length", "tool_calls", "function_call", "content_filter"
    }:
        finish = raw_finish
    else:
        finish = "unknown"
    raw_usage = data.get("usage") if isinstance(data, dict) else None
    usage = raw_usage if isinstance(raw_usage, dict) else {}
    raw_details = usage.get("completion_tokens_details")
    details = raw_details if isinstance(raw_details, dict) else {}
    reasoning = _token_count(details.get("reasoning_tokens"))
    if reasoning is None:
        reasoning = _token_count(usage.get("reasoning_tokens"))
    return {"finish_reason": finish, "usage": {
        "prompt_tokens": _token_count(usage.get("prompt_tokens")),
        "completion_tokens": _token_count(usage.get("completion_tokens")),
        "total_tokens": _token_count(usage.get("total_tokens")),
        "reasoning_tokens": reasoning,
    }}


def complete(prompt: str, *, json_mode: bool = False, model: str | None = None,
             max_retries: int = 4,
             diagnostics: dict[str, Any] | None = None,
             max_output_tokens: int | None = None,
             response_schema: dict | None = None) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não configurada no GitHub Actions.")
    selected = model or os.environ.get("ODE_NEWS_GROQ_MODEL", MODEL)
    def unavailable(reason):
        # Availability-only fallback. A rejected factual verdict never reaches
        # this branch, and no Google key/model is involved in editorial work.
        alternates = [name.strip() for name in os.environ.get("ODE_NEWS_GROQ_FALLBACK_MODELS", "").split(",") if name.strip()]
        primary = os.environ.get("ODE_NEWS_GROQ_MODEL", MODEL)
        if selected == primary:
            for alternate in alternates:
                if alternate == selected:
                    continue
                print("GROQ_AVAILABILITY_FALLBACK", selected, alternate, reason, flush=True)
                result = complete(prompt, json_mode=json_mode, model=alternate, max_retries=2,
                                  diagnostics=diagnostics, max_output_tokens=max_output_tokens, response_schema=response_schema)
                if diagnostics is not None:
                    diagnostics.update(fallback_from=selected, fallback_reason=reason)
                return result
        from news_free_fallback import enabled, complete_free
        if enabled() and selected in {primary, *alternates}:
            print('EDITORIAL_PROVIDER_FALLBACK groq openrouter/free', reason, flush=True)
            result = complete_free(prompt, json_mode=json_mode, diagnostics=diagnostics,
                                   max_output_tokens=max_output_tokens, response_schema=response_schema)
            if diagnostics is not None:
                diagnostics.update(fallback_from=selected, fallback_reason=reason)
            return result
        raise RuntimeError("Editorial model unavailable after bounded retries: " + reason)
    if diagnostics is not None:
        diagnostics.update({"provider": "groq", "model": selected, "attempt": 0,
                            "http_status": None,
                            **_transport_metadata({})})
    cooldown = globals().get('_model_cooldowns', {}).get(selected, 0)
    if cooldown > time.monotonic():
        return unavailable('recorded_quota_cooldown')
    payload: dict[str, Any] = {
        "model": selected,
        "messages": [
            {"role": "system", "content":
             "Você é editor de notícias brasileiras. Cite apenas dados e textos fornecidos no corpus. "
             "Não invente URL, data, acontecimento, citação, título nem publicação. "
             "Prefira confirmação do mesmo acontecimento de hoje em publicadores independentes. Uma notícia nova ou exclusiva em uma fonte real pode ser relatada com atribuição explícita, status statement e ausência de confirmação independente declarada; nunca invente a segunda fonte. Sem texto real ou prova de atualidade, informe insuficiência. "
             "O trabalho é jornalismo informativo: distinga fatos, alegações e opiniões."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2 if json_mode else 0.1,
        "max_completion_tokens": max_output_tokens or (5800 if json_mode else 2000),
        "reasoning_effort": "low",
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
        # Groq rejects json_object unless a message explicitly says JSON.
        payload["messages"][0]["content"] += " Responda exclusivamente com um objeto JSON válido."
    if response_schema:
        payload['response_format'] = {'type': 'json_schema', 'json_schema': {
            'name': 'ode_news_draft', 'strict': True, 'schema': response_schema}}
    # Pace sequential passes as well as retries; don't assume a free API is unlimited.
    interval = float(os.environ.get("ODE_NEWS_GROQ_MIN_INTERVAL_SECONDS", "0"))
    elapsed = time.monotonic() - globals().get("_last_completed_at", -1000)
    if elapsed < interval:
        time.sleep(interval - elapsed)
    for attempt in range(max_retries):
        if diagnostics is not None:
            diagnostics.update({"attempt": attempt + 1, "http_status": None,
                                **_transport_metadata({})})
        try:
            response = requests.post(
                ENDPOINT, json=payload, timeout=140,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            )
        except requests.RequestException as exc:
            if attempt == max_retries - 1:
                return unavailable("connection_failure")
            time.sleep(min(60, 12 * (attempt + 1)))
            continue
        if diagnostics is not None:
            diagnostics["http_status"] = response.status_code
        if response.status_code == 200:
            globals()["_last_completed_at"] = time.monotonic()
            data = response.json()
            if diagnostics is not None:
                diagnostics.update(_transport_metadata(data))
            message = data["choices"][0]["message"]["content"]
            if not isinstance(message, str) or not message.strip():
                raise RuntimeError("Groq retornou resposta editorial vazia.")
            print("GROQ_EDITOR_COMPLETION", selected, "json" if json_mode else "research",
                  "tokens", data.get("usage", {}).get("total_tokens", "?"), flush=True)
            return message
        if response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
            wait = response.headers.get("retry-after")
            try:
                seconds = max(5, float(wait)) if wait else min(90, 30 * (attempt + 1))
            except ValueError:
                seconds = 40
            print("GROQ_RETRY", response.status_code, "seconds", round(seconds), flush=True)
            has_backup = bool(os.environ.get('ODE_NEWS_GROQ_FALLBACK_MODELS', '').strip()) and selected == os.environ.get('ODE_NEWS_GROQ_MODEL', MODEL)
            from news_free_fallback import enabled
            has_backup = has_backup or enabled()
            if seconds > (90 if has_backup else 600):
                globals().setdefault('_model_cooldowns', {})[selected] = time.monotonic() + seconds
                return unavailable("primary_quota_retry_later")
            time.sleep(seconds)
            continue
        if response.status_code in (429, 500, 502, 503, 504):
            return unavailable("http_" + str(response.status_code))
        if response.status_code == 400 and response_schema:
            try:
                candidate = response.json().get('error', {}).get('failed_generation')
                if isinstance(candidate, str):
                    candidate = json.loads(candidate)
                if isinstance(candidate, (dict, list)):
                    if diagnostics is not None:
                        diagnostics['schema_candidate_recovered'] = True
                    print('GROQ_SCHEMA_CANDIDATE_RECOVERED: JSON only; factual review still required', flush=True)
                    return json.dumps(candidate, ensure_ascii=False)
            except (ValueError, TypeError):
                pass
            print('GROQ_SCHEMA_TRANSPORT_UNAVAILABLE: retry JSON object on same model; factual review unchanged', flush=True)
            guided = prompt + '\nEstrutura JSON exata; objetos são mapas, nunca listas de pares:\n' + json.dumps(response_schema, ensure_ascii=False)
            return complete(guided, json_mode=True, model=selected, max_retries=2, diagnostics=diagnostics,
                            max_output_tokens=max_output_tokens)
        # Never emit raw response: it can include content from news pages.
        detail = ""
        try:
            detail = str(response.json().get("error", {}).get("message", ""))[:170]
        except ValueError:
            pass
        raise RuntimeError(f"Groq respondeu HTTP {response.status_code}: {detail}")
    raise RuntimeError("Groq não respondeu após tentativas limitadas.")

