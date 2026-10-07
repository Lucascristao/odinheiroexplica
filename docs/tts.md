# Narração

## Política canônica

`worker/voice-policy.json` é a política canônica da narração. Roberto usa a voz Gemini `Charon`; Luana usa `Autonoe`. O único modelo de produção é `gemini-3.8-live`.

Não existe mais cascata de 3.8 Flash, Flash-Lite e 3.1. O motor não troca de modelo nem de voz no meio do vídeo. A integração usa `google-genai==2.26.0`, temperatura padrão do Gemini 3 e uma sessão WebSocket isolada para cada tentativa de cada cena, conforme `live_runtime.session_strategy`. A sessão é encerrada antes da próxima cena, sem carregar contexto conversacional da cena anterior. A mesma voz e direção mantêm a coerência vocal; quedas e rejeições são refeitas apenas na cena afetada, preservando o cache válido.

A direção vocal continua centralizada na política: português brasileiro de conversa, voz presente e calorosa, articulação clara, ritmo e entonação que variam com o raciocínio e pausas entre pensamentos completos. Cada vídeo recebe interpretação própria pelo significado de suas frases, preservando a identidade do apresentador. A política orienta presença e intenção; não impõe uma sequência de emoções ou uma curva repetida de pergunta, explicação e conclusão.

## Leitura literal e pronúncia

A narração é enviada ao Live como texto literal. A instrução de sistema proíbe introduções, comentários, resumos, reformulações ou qualquer palavra extra. `speech.pronunciations` continua sendo respeitado como instrução de fala, preservando a grafia correta no roteiro e na tela.

A Live API devolve também a transcrição da própria saída. Cada cena só é aceita quando essa transcrição corresponde lexicalmente ao roteiro depois de normalizações seguras. Anos de quatro dígitos entre 1900 e 2099 recebem automaticamente orientação de pronúncia em português brasileiro sem alterar o texto do roteiro. O validador aceita representações equivalentes do mesmo ano que apareça no roteiro, como `2027`, `dois mil e vinte e sete` ou a forma de ASR `vinte vinte e sete`; um ano diferente continua sendo erro. Qualquer divergência literal, numérica ou lexical, rejeita o áudio daquela tentativa e permite refazer somente a mesma cena em uma sessão nova, mantendo voz, modelo e roteiro. O gate continua estrito: o áudio divergente não é escrito nem cacheado, mesmo com similaridade alta. A produção para se as quatro tentativas da cena forem rejeitadas. Os diagnósticos distinguem divergência apenas numérica de lexical; o manifesto das cenas aceitas registra a transcrição, as equivalências e a pontuação de fidelidade.

## Áudio bruto

O Gemini Live devolve PCM mono de 16 bits a 24 kHz. O worker apenas encapsula esses bytes em WAV. Não aplica EQ, ganho, limiter, compressor, normalização, pitch, velocidade ou resample.

`worker/process_voice_continuity.py` deixou de fazer match de timbre. Ele agora é apenas um gate de integridade: confere que todas as cenas usam `gemini-3.8-live` e a mesma voz e copia cada WAV byte por byte para o diretório de entrega. O manifesto registra `byte_identical: true` e `effects_applied: false`.

## Cache e retomada

Cada WAV tem um sidecar `.tts.json` com texto, modelo, voz, duração, hash do áudio, versão da política, fingerprint da direção vocal, fingerprint das pronúncias do projeto e transcrição de saída. A direção por cena em `tts.delivery` e `tts.cues`, incluindo intenção, arco e palavra-chave, também integra o cache. O fingerprint usa a direção validada e o texto de instrução enviado ao Live: mudar somente um cue invalida a cena correspondente; uma alteração da política global invalida as cenas que usam a política anterior. Mudanças apenas visuais preservam o áudio válido.

Regeneração integral continua exigindo o input manual `force_fresh_audio` no primeiro attempt de um `workflow_dispatch`. Pushes e reruns retomam cache válido.

Falhas transitórias do Live, incluindo fechamento 1011/1012/1013, Resource Exhausted temporário, timeout ou conexão interrompida, e rejeições de fidelidade da saída são repetidas na mesma cena em uma sessão nova com backoff de 5 s, 15 s e 30 s, dentro do limite de quatro tentativas. Não existe fallback para outro modelo. Formato de áudio ou configuração inválida continuam fatais, assim como fidelidade rejeitada depois de esgotar as tentativas. As cenas já aceitas preservam seu cache.

O worker registra `daily-live-diagnostics.json` com versão do SDK, tentativa por cena, latência até o primeiro áudio, bytes PCM, duração, `usage_metadata`, `go_away`, updates de retomada recebidos e código/motivo de fechamento quando houver. Session Resumption fica desativado porque cada cena é independente.

Há também watchdogs para primeiro áudio, silêncio durante geração e duração anormal calculada a partir do tamanho do roteiro. Depois que o servidor envia `generationComplete`, o worker muda de estado: espera uma graça curta por `turnComplete`, mas não usa mais o timeout de geração. Para este TTS offline, se já existem PCM e transcrição válidos, `generationComplete` é aceito mesmo que `turnComplete` não chegue; a fidelidade literal continua sendo validada antes de salvar a cena. Isso evita descartar áudio completo só porque o servidor ainda está aguardando o encerramento lógico do turno.

`tts.delivery` aceita hook, explain, contrast, question ou closing como orientações flexíveis, escolhidas para a cena. Os cues identificam até seis trechos literais e únicos, sem sobreposição ou corte de palavra e sem atravessar frases, com `kind` de emphasis, number ou contrast. O motor traduz esses tipos em direção de fala em português, mantendo compatibilidade com cues anteriores. Além de `pause_before_ms` entre 0 e 300, cada cue pode ter:

- `intent`: curiosity, discovery, reassurance, caution ou conviction; define a intenção da fala sem alterar sua certeza factual.
- `arc`: question, build, resolve ou contrast; orienta o percurso do trecho de forma natural, sem pitch, velocidade ou duração exatos.
- `emphasis_word`: uma palavra literal formada por letras ou números, presente exatamente uma vez como palavra inteira no próprio cue, respeitando maiúsculas e acentos.

Exemplo de direção autoral para uma frase específica:

```json
{
  "narration": "Parece contraditório? A empresa continua no Simples.",
  "tts": {
    "delivery": "hook",
    "cues": [
      {
        "text": "Parece contraditório?",
        "kind": "emphasis",
        "intent": "curiosity",
        "arc": "question",
        "emphasis_word": "contraditório"
      },
      {
        "text": "A empresa continua no Simples.",
        "kind": "contrast",
        "intent": "reassurance",
        "arc": "resolve",
        "emphasis_word": "continua",
        "pause_before_ms": 180
      }
    ]
  }
}
```

O autor escolhe esses campos pelo sentido do vídeo; não há inferência automática de emoções ou cues, quantidade mínima ou obrigação de repetir o exemplo. Toda a direção é enviada em instruções separadas da leitura. Pausas são intenções aproximadas, não tempos garantidos; uma pausa de zero mantém a fluidez sem pedir uma pausa artificial. Rate e pitch não alteram o áudio bruto. Não inserir marcações de atuação no texto narrado.

## Alinhamento e entrega

Fluxo: roteiro → auditoria de pronúncia → Gemini 3.8 Live → verificação de fidelidade → passthrough byte-idêntico → alinhamento local das âncoras → timeline → render.

`worker/align_narration.py` continua usando o áudio real para melhorar o sincronismo visual. A transcrição do Live valida o conteúdo falado; o alinhamento local continua responsável por localizar as palavras no tempo. O gate lexical não aprova presença ou prosódia e não exige ritmo neutro: revise o MP4 final para intenção, naturalidade, ritmo, dicção e sincronização visual. Uma comparação curta de direções pode ajudar quando houver uma dúvida concreta, sem ser uma etapa obrigatória de cada produção.

## Constância entre cenas · 07/10/2026

A política 2026-10-07.1 orienta todas as sessões como a mesma conversa, com registro médio, timbre e energia estáveis. Cues mudam articulação e intenção, sem pedir troca de registro ou volume.

O alinhador mede active_rms_dbfs em janelas de 20 ms acima de −45 dBFS; RMS do arquivo inteiro permanece como diagnóstico separado. A faixa contínua planeja um alvo comum de −18 dBFS de fala ativa, reduzido para todos se necessário para respeitar pico 0,975. Não há clamp de ganho de 0,5–1,5 nem limitação independente que mude só uma cena. Se os picos impedirem alvo adequado, a montagem falha e exige revisão. WAVs brutos permanecem byte-idênticos; só o master aplica ganho e envelopes de 5 ms.

O daily-voice-master-report.json registra ganhos, alvo, hash do master e estimativas de registro por autocorrelação. O QA mede novamente cada trecho do master. Pitch é diagnóstico incerto: entonação, voz crepitante e erros de oitava pedem escuta; nenhuma mudança artificial de pitch é aplicada. Essas medições não garantem naturalidade.
