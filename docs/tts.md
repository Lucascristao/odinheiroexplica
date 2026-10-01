# Narração

## Política canônica

`worker/voice-policy.json` é a política canônica da narração. Roberto usa a voz Gemini `Charon`; Luana usa `Autonoe`. O único modelo de produção é `gemini-3.8-live`.

Não existe mais cascata de 3.8 Flash, Flash-Lite e 3.1. Se o Live falhar, a produção para e pode ser retomada pelo cache. O motor não troca de modelo nem de voz no meio do vídeo.

A direção vocal continua centralizada na política: português brasileiro, leitura humana e conversacional, ritmo moderado, articulação clara, ênfase variada sem exagero, pausas curtas entre pensamentos completos e sem cadência de locutor ou leitura robótica.

## Leitura literal e pronúncia

A narração é enviada ao Live como texto literal. A instrução de sistema proíbe introduções, comentários, resumos, reformulações ou qualquer palavra extra. `speech.pronunciations` continua sendo respeitado como instrução de fala, preservando a grafia correta no roteiro e na tela.

A Live API devolve também a transcrição da própria saída. Cada cena só é aceita quando essa transcrição alcança a similaridade mínima definida em `worker/voice-policy.json` com o roteiro original. O manifesto registra a transcrição e a pontuação de fidelidade. Isso reduz o risco de um modelo conversacional improvisar ou alterar a narração.

## Áudio bruto

O Gemini Live devolve PCM mono de 16 bits a 24 kHz. O worker apenas encapsula esses bytes em WAV. Não aplica EQ, ganho, limiter, compressor, normalização, pitch, velocidade ou resample.

`worker/process_voice_continuity.py` deixou de fazer match de timbre. Ele agora é apenas um gate de integridade: confere que todas as cenas usam `gemini-3.8-live` e a mesma voz e copia cada WAV byte por byte para o diretório de entrega. O manifesto registra `byte_identical: true` e `effects_applied: false`.

## Cache e retomada

Cada WAV tem um sidecar `.tts.json` com texto, modelo, voz, duração, hash do áudio, versão da política, fingerprint da direção vocal, fingerprint das pronúncias do projeto e transcrição de saída. A direção por cena em `tts.delivery` e `tts.cues` também integra o cache. Mudança de roteiro, voz, política, pronúncias ou direção invalida apenas as cenas correspondentes.

Regeneração integral continua exigindo o input manual `force_fresh_audio` no primeiro attempt de um `workflow_dispatch`. Pushes e reruns retomam cache válido.

`tts.delivery` aceita hook, explain, contrast, question ou closing. Os cues identificam até seis trechos literais e únicos com intenção de emphasis, number ou contrast; são enviados em instruções separadas da leitura. Pausas são intenções aproximadas, não tempos garantidos. Rate e pitch não alteram o áudio bruto. Não inserir marcações de atuação no texto narrado.

## Alinhamento e entrega

Fluxo: roteiro → auditoria de pronúncia → Gemini 3.8 Live → verificação de fidelidade → passthrough byte-idêntico → alinhamento local das âncoras → timeline → render.

`worker/align_narration.py` continua usando o áudio real para melhorar o sincronismo visual. A transcrição do Live valida o conteúdo falado; o alinhamento local continua responsável por localizar as palavras no tempo. Revise o MP4 final para ritmo, dicção e sincronização visual.
