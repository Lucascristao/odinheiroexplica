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
             diagnostics: dict[str, Any] | None = None) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não configurada no GitHub Actions.")
    selected = model or os.environ.get("ODE_NEWS_GROQ_MODEL", MODEL)
    if diagnostics is not None:
        diagnostics.update({"provider": "groq", "model": selected, "attempt": 0,
                            "http_status": None,
                            **_transport_metadata({})})
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
        "max_completion_tokens": 5800 if json_mode else 1200,
        "reasoning_effort": "low",
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    # 8K tokens/minute on free GPT-OSS 120B; no burst fanout.
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
                raise RuntimeError("Groq indisponível após tentativas de conexão.") from exc
            time.sleep(min(60, 12 * (attempt + 1)))
            continue
        if diagnostics is not None:
            diagnostics["http_status"] = response.status_code
        if response.status_code == 200:
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
                seconds = min(90, max(5, float(wait))) if wait else min(75, 22 * (attempt + 1))
            except ValueError:
                seconds = 40
            print("GROQ_RETRY", response.status_code, "seconds", round(seconds), flush=True)
            time.sleep(seconds)
            continue
        # Never emit raw response: it can include content from news pages.
        detail = ""
        try:
            detail = str(response.json().get("error", {}).get("message", ""))[:170]
        except ValueError:
            pass
        raise RuntimeError(f"Groq respondeu HTTP {response.status_code}: {detail}")
    raise RuntimeError("Groq não respondeu após tentativas limitadas.")

