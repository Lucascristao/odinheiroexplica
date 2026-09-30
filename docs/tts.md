# Narração

## Fluxo atual

O render diário usa somente Gemini TTS. Para o apresentador masculino, solicita a voz `Charon`; para o feminino, `Autonoe`. Todas as cenas de um vídeo usam o mesmo modelo, configurado por `GEMINI_TTS_MODEL` (padrão: `gemini-3.8-flash-tts`). O worker espaça o início das chamadas por pelo menos 22 segundos para respeitar a cota Free de 3 RPM mostrada no AI Studio. Se o serviço responder HTTP 429, registra os detalhes de cota disponíveis sem expor a chave, e tenta novamente com espera exponencial. Se o Google identificar RPD esgotado, interrompe as tentativas. Se a síntese não completar todas as cenas, o render falha; não troca o modelo nem o motor de voz.

O manifesto de TTS registra `engine`, `voice` e modelo efetivos em cada cena e `engine` e `voice` no resumo do vídeo. `requested_voice` guarda a voz solicitada. A credencial `GEMINI_API_KEY` pertence apenas ao worker e não deve aparecer no frontend, no repositório ou em logs.

Cada arquivo de áudio tem um sidecar `.tts.json` com hash da narração, modelo, voz, hash do áudio e duração medida. Ao reexecutar, o worker só reutiliza o MP3 se esses dados e a duração conferirem. Assim, uma execução que parou por quota retoma das cenas faltantes sem repetir chamadas já concluídas. Uma mudança de texto, modelo, voz ou áudio invalida o cache daquela cena.

## Timeline

roteiro por cena → TTS por cena → duração medida do áudio → estimativa de posição das âncoras → timeline → render.

O Gemini usado aqui entrega áudio, sem offsets de palavras ou bookmarks. `compute_beat_timings` distribui cada âncora pela duração real do áudio segundo os caracteres e a pontuação da narração. Esses tempos têm `timing_source: estimated-text-alignment`; uma âncora não encontrada recebe `estimated-distributed` e não serve para um palco persistente. O render verifica que as âncoras de palcos persistentes existem uma única vez e aparecem na ordem da fala. Manifestos antigos com `gemini-bookmark` são lidos como estimativas textuais. Ajuste fino de sincronismo precisa de alinhamento forçado ou eventos de TTS realmente medidos.

Cada cena tem arquivo próprio para permitir regeneração isolada, mas a entrega completa usa um único motor e uma única voz.

Na captura da conta Free em 30/09/2026, `gemini-3.8-flash-tts` tinha 10 RPD e 10 mil TPM. Com sete cenas separadas, um vídeo usa sete chamadas; um segundo vídeo no mesmo dia ultrapassaria a cota nominal se não houvesse áudio válido em cache. Os valores `4/3` e `24/10` do painel representam máximos históricos de uso frente às cotas, não a capacidade restante no momento. Um modelo TTS alternativo pode ter cota separada, mas o mesmo nome de voz não garante áudio idêntico entre modelos; a produção nunca alterna modelo durante um episódio.
