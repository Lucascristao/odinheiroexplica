# VideoProject v1.0

O `VideoProject` é o contrato entre o ChatGPT e o painel.

## Objetivo

O pacote precisa ser suficiente para:

- identificar a história e o ângulo;
- auditar fontes e afirmações;
- construir roteiro e cenas;
- gerar alternativas de título e thumbnail;
- preparar publicação;
- permitir renderização futura sem reinterpretar texto livre.

## Estrutura mínima

```json
{
  "version": "1.0",
  "story": {
    "subject": "Assunto",
    "angle": "Ângulo editorial",
    "promise": "O que o espectador recebe",
    "why_now": "Por que agora",
    "category": "company"
  },
  "editorial": {
    "viral_score": 80,
    "strengths": [],
    "risk_flags": []
  },
  "sources": [],
  "claims": [],
  "packaging": {
    "titles": [],
    "thumbnails": []
  },
  "script": {
    "hook": "Gancho",
    "beats": [],
    "scenes": [],
    "closing": "Fechamento"
  },
  "publication": {
    "description": "",
    "chapters": [],
    "disclosure_ai": false
  }
}
```

## Categorias

- `news`
- `company`
- `economy`
- `money`
- `evergreen`

## Fontes

Cada fonte recebe um `id` único.

Preferência editorial:

1. fonte primária;
2. fonte secundária confiável;
3. contexto complementar.

Exemplo:

```json
{
  "id": "src_01",
  "title": "Relatório oficial",
  "url": "https://...",
  "publisher": "Banco Central",
  "source_type": "primary"
}
```

## Claims

Um claim é uma afirmação factual verificável.

```json
{
  "id": "claim_01",
  "text": "A empresa reportou receita de X.",
  "source_ids": ["src_01"],
  "confidence": "high",
  "verification_status": "verified"
}
```

Toda afirmação importante deve apontar para pelo menos uma fonte.

## Cenas

A duração final não é definida no pacote. A narração será sintetizada posteriormente e o áudio determinará o tamanho real de cada cena.

```json
{
  "index": 0,
  "title": "Gancho",
  "narration": "Texto falado...",
  "visual": {
    "type": "BIG_NUMBER",
    "payload": {}
  },
  "claim_ids": ["claim_01"]
}
```

## Bloqueadores editoriais

Estes flags serão tratados como bloqueadores de renderização:

- `RUMOR_NAO_CONFIRMADO`
- `FONTE_INSUFICIENTE`
- `TITULO_NAO_SUPORTADO_PELOS_FATOS`
- `RECOMENDACAO_FINANCEIRA`
- `PROMESSA_DE_GANHO`
- `URGENCIA_ARTIFICIAL`
- `RISCO_COPYRIGHT`
- `DADO_CONFLITANTE`

O projeto pode ser importado com bloqueadores para correção, mas não deverá avançar para render até a revisão.

## Regras de integridade

O painel valida antes de importar:

- versão = 1.0;
- subject obrigatório;
- URLs válidas;
- IDs de fonte únicos;
- IDs de claim únicos;
- claims só podem apontar para fontes existentes;
- índices de cena únicos;
- cenas só podem apontar para claims existentes.

O banco faz a gravação em uma única transação.
