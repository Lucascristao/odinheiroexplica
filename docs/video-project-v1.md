# VideoProject v1.0

> Nota histórica: as seções abaixo que descrevem SSML e bookmarks do Azure pertencem ao fluxo antigo. O render diário atual usa somente Gemini TTS e estimativas de tempo por âncora; consulte `docs/tts.md` e `docs/editorial-voice.md` para a produção vigente.

O `VideoProject` é o contrato entre o ChatGPT e o sistema.

## Objetivo

O pacote precisa ser suficiente para identificar a história, auditar fontes e claims, escolher uma única embalagem principal, construir o roteiro, gerar cenas, preparar publicação e renderizar sem reinterpretar texto livre.

## Embalagem

Título e thumbnail são uma decisão editorial única e devem ser resolvidos antes do roteiro final.

O sistema entrega exatamente:
- 1 título principal;
- 1 thumbnail principal;
- 1 estratégia de embalagem.

`packaging.strategy` registra:
- `click_reason`: por que alguém clicaria;
- `visual_focus`: elemento visual dominante;
- `curiosity_gap`: pergunta aberta;
- `mobile_readability`: por que funciona pequeno;
- `anti_clickbait_check`: como o vídeo entrega a promessa;
- `repetition_check`: padrão que deve ser evitado para não repetir capas anteriores.

Uma segunda embalagem só deve ser criada depois da publicação quando CTR ou outro dado justificar um novo teste.

## Narração

A escrita deve soar natural em português brasileiro. O roteiro evita tom de relatório e usa variação de frases, perguntas pontuais, exemplos concretos e conectores conversacionais quando fizer sentido.

A duração não é definida no pacote. A voz é sintetizada por cena e o áudio real define a timeline.

## Fontes e claims

Cada fonte recebe um ID único. Claims factuais relevantes precisam apontar para fontes existentes. Prioridade editorial:
1. fonte primária;
2. fonte secundária confiável;
3. contexto complementar.

## Bloqueadores

- `RUMOR_NAO_CONFIRMADO`
- `FONTE_INSUFICIENTE`
- `TITULO_NAO_SUPORTADO_PELOS_FATOS`
- `RECOMENDACAO_FINANCEIRA`
- `PROMESSA_DE_GANHO`
- `URGENCIA_ARTIFICIAL`
- `RISCO_COPYRIGHT`
- `DADO_CONFLITANTE`

## Integridade

O sistema valida versão, URLs, IDs, vínculos entre claims e fontes, índices de cena, narração, uma única embalagem principal e ausência de bloqueadores críticos antes de produção.


## Pronúncia da narração

O VideoProject pode declarar ajustes de fala no nível raiz sem alterar a grafia publicada:

```json
{
  "speech": {
    "pronunciations": {
      "bets": "bétes"
    },
    "ignore_pronunciation_terms": []
  }
}
```

`speech.pronunciations` é aplicado somente ao TTS. Texto de tela, título, descrição e roteiro mantêm a escrita original. Antes da síntese, o pipeline executa uma auditoria de termos com maior risco de leitura artificial. Em modo estrito, a etapa de áudio é interrompida quando um termo de risco conhecido não possui alias nem validação explícita.


## Sound design

O render diário possui uma camada global de sound design editorial. Ela não depende de o VideoProject escolher sons manualmente.

Princípios:
- a voz do apresentador é a faixa principal;
- efeitos são curtos e discretos;
- os eventos sonoros acompanham marcos visuais relevantes, como entrada de número, avanço de processo, alerta e transição;
- o sistema evita colocar som em cada movimento para não deixar a edição cansativa;
- não há música contínua por padrão;
- o encerramento reserva uma pequena cauda depois da narração e toca uma assinatura sonora curta;
- os efeitos são gerados proceduralmente dentro do próprio projeto durante o workflow, evitando dependência de arquivos externos e problemas de licença.

## Descrição para YouTube

O pipeline acrescenta automaticamente capítulos e a seção `Bases do vídeo:`.

Essa seção lista somente os títulos das fontes que sustentaram o roteiro. As URLs continuam preservadas dentro do VideoProject para auditoria e verificação, mas não são colocadas automaticamente na descrição pública.


## Beats informativos

Cada cena pode declarar `visual.beats` para que novas informações da narração recebam uma microcena visual própria sem quebrar o bloco narrativo em dezenas de cenas.

Exemplo:

```json
{
  "visual": {
    "type": "TIMELINE",
    "payload": {
      "eyebrow": "Preço dos combustíveis"
    },
    "beats": [
      {
        "anchor": "o petróleo voltou a subir",
        "kind": "trend_up",
        "headline": "Petróleo em alta",
        "value": "+...",
        "sound": "impact"
      },
      {
        "anchor": "o governo anunciou novas medidas",
        "kind": "process",
        "headline": "Novas medidas anunciadas",
        "sound": "none"
      }
    ]
  }
}
```

O campo `anchor` deve ser um trecho literal da própria narração. Na montagem da timeline, o pipeline localiza esse trecho no texto e converte sua posição em um frame aproximado dentro do áudio real da cena. Se um beat usar `at` explicitamente, o valor é uma proporção entre 0 e 1 e tem prioridade.

O Remotion apresenta cada beat como uma microcena editorial em primeiro plano. Os tipos disponíveis são `fact`, `number`, `date`, `money`, `bank`, `flow`, `process`, `warning`, `compare`, `trend_up`, `trend_down`, `fuel` e `block`.

Objetivo editorial: quando a fala muda de informação, o foco visual também deve mudar. Em cenas longas, a referência é uma nova informação visual aproximadamente a cada 4 a 7 segundos, sem criar movimento gratuito.


## Direção visual por pauta

O VideoProject deve definir um `visual_direction` próprio para cada história. A marca permanece consistente em tipografia, contraste, preto/carvão, branco, dourado e acabamento editorial, mas composição, metáfora, movimento, cor secundária e objetos devem nascer da pauta atual.

Campos:
- `concept`: ideia visual central;
- `world`: minimal, digital, industrial, documentary, market, network ou paper;
- `secondary_color`: cor secundária específica da pauta;
- `motifs`: objetos/formas que pertencem à história;
- `motion_language`: decisões de movimento e corte;
- `avoid`: soluções que fariam o vídeo parecer repetição de outro.

O histórico em `docs/visual-history.md` serve somente como lista anti-repetição. Nunca deve influenciar seleção de pauta ou estrutura narrativa.

## Microcenas narrativas

`visual.beats` não é uma camada de cards sobre a cena. Cada beat representa uma nova unidade visual capaz de substituir, transformar ou reenquadrar a composição.

Campos de edição:
- `behavior`: cut, transform, reframe ou overlay;
- `treatment`: kinetic_type, giant_number, flow_diagram, timeline, split_compare, meter, spotlight, equation, stack ou signal;
- `transition`: cut, fade, slide_left, slide_up, zoom ou wipe;
- `placement`: left, center, right ou full.

Overlay é exceção e deve existir apenas com área segura. O sistema valida no máximo um por cena e bloqueia repetição do mesmo tratamento em três beats consecutivos.

## Sincronização de fala e imagem

Beats com `anchor` usam bookmarks SSML inseridos exatamente antes do trecho literal da narração. O Azure Speech SDK devolve o `audio_offset` real do bookmark durante a síntese. O pipeline converte esse timestamp para frame e inicia a microcena naquele ponto.

O método anterior de estimar o tempo pela posição proporcional do texto continua apenas como fallback para projetos antigos ou beats que usem `at`.

Com isso, um número, diagrama, corte ou mudança de composição entra quando o apresentador realmente chega à informação correspondente, e não em um ponto aproximado da cena.
