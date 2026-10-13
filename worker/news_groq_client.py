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


def complete(prompt: str, *, json_mode: bool = False, model: str | None = None,
             max_retries: int = 4) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não configurada no GitHub Actions.")
    selected = model or os.environ.get("ODE_NEWS_GROQ_MODEL", MODEL)
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
        if response.status_code == 200:
            data = response.json()
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
