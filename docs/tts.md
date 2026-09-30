# Narração

## Fluxo atual

O render diário usa somente Gemini TTS e preserva a mesma voz do apresentador em toda a cascata. Para o apresentador masculino, solicita `Charon`; para o feminino, `Autonoe`. A ordem padrão é `gemini-3.8-flash-tts` → `gemini-3.8-flash-lite-tts` → `gemini-3.1-flash-tts-preview`. O próximo modelo só é acionado quando o anterior devolve RPD esgotado, 429 persistente após três tentativas espaçadas, 5xx persistente ou timeout persistente após as tentativas. Cada pedido pode aguardar até 180 segundos pela resposta. Erro de autenticação, configuração, modelo inexistente, resposta sem áudio ou erro de conexão não avança silenciosamente a cascata.

O worker espaça o início das chamadas por pelo menos 22 segundos para respeitar a cota Free de 3 RPM mostrada no AI Studio. Em 429, registra os detalhes estruturados de cota sem expor a chave; RPM transitório espera e tenta novamente no 3.8. Ao entrar em um nível de fallback, as cenas novas dessa execução continuam no nível ativo; se ele também ficar indisponível, o motor desce para o próximo mantendo a mesma voz. Um fallback restaurado do cache não prova indisponibilidade atual do principal e, por isso, não força cenas novas a permanecerem nele. Se os três modelos falharem, o render para e preserva o que já foi gerado. Não existe Azure nem troca automática para outra voz.

O manifesto de TTS registra `engine`, `voice`, `model`, `voice_treatment` e `fallback_reason` por cena, além de `models_used` e `fallback_scene_ids` no resumo. `requested_voice` guarda a voz solicitada. A credencial `GEMINI_API_KEY` pertence apenas ao worker e não deve aparecer no frontend, no repositório ou em logs.

Cada arquivo de áudio tem um sidecar `.tts.json` com hash da narração, modelo, voz, tratamento, hash do áudio e duração medida. Ao reexecutar, o worker só reutiliza o MP3 se esses dados e a duração conferirem. Assim, uma execução que parou por quota retoma das cenas faltantes sem repetir chamadas já concluídas. Uma mudança de texto, modelo, voz, tratamento ou áudio invalida o cache daquela cena. Um trecho já gravado pelo 3.1 continua como 3.1 na retomada, sem ser confundido com o 3.8.

## Semelhança de voz no fallback

O cache guarda o áudio bruto devolvido pelo Gemini. Nenhuma EQ fixa é aplicada durante a síntese. Qualquer correção existe somente no pós-processamento e apenas quando o manifesto comprova que houve mais de um modelo no mesmo episódio.

Quando o modelo muda entre duas cenas, o worker registra a fronteira exata no manifesto, mas **não insere nenhum marcador audível**. A troca fica auditável tecnicamente sem acrescentar pigarro, fala extra ou efeito sonoro.

## Continuidade de voz por episódio

A versão `adaptive-voice-continuity-v3` usa uma regra rígida: **mesmo modelo + mesma voz do começo ao fim = áudio intocado**. Nesse caso, cada MP3 é copiado byte por byte para a pasta usada no render. Não há EQ, ganho, limiter, compressor, normalização, resample nem re-encode.

Se o episódio mistura modelos, o modelo de referência, normalmente `gemini-3.8-flash-tts`, permanece intocado. Somente as cenas de outro modelo recebem aproximação espectral lenta em janelas de 5 segundos com sobreposição de 2,5 segundos. O volume do fallback usa apenas ganho estático, limitado pela folga de pico. Não há compressor, limiter nem normalização dinâmica.

A troca de modelo não altera a duração da cena nem desloca os beats visuais. O registro fica apenas nos metadados.

Se o vídeo inteiro sair em Flash-Lite ou 3.1 desde a primeira cena, também não há tentativa de transformar aquela voz em outro modelo, porque não existe transição interna. A correção existe apenas para episódios mistos.

O manifesto registra `model_transition_count`, as cenas onde a troca aconteceu, o modelo anterior, o novo modelo e o modo de pós-processamento. Em modo homogêneo, `effects_applied` fica falso e cada cena registra `byte_identical: true`.

## Timeline

A divisão em cenas e a extensão do roteiro são decisões editoriais: use o necessário para explicar a história inteira. Os limites da API controlam o agendamento da síntese, não a quantidade de cenas nem o conteúdo. Em caso de quota, use cache, espera, retomada e o fallback autorizado; preserve o roteiro completo se a síntese precisar continuar depois.

roteiro por cena → cache válido ou TTS por cena → continuidade de voz offline → duração medida do WAV → estimativa de posição das âncoras → timeline → render.

O Gemini usado aqui entrega áudio, sem offsets de palavras ou bookmarks. `compute_beat_timings` distribui cada âncora pela duração real do áudio segundo os caracteres e a pontuação da narração. Esses tempos têm `timing_source: estimated-text-alignment`; uma âncora não encontrada recebe `estimated-distributed` e não serve para um palco persistente. O render verifica que as âncoras de palcos persistentes existem uma única vez e aparecem na ordem da fala. Manifestos antigos com `gemini-bookmark` são lidos como estimativas textuais. Ajuste fino de sincronismo precisa de alinhamento forçado ou eventos de TTS realmente medidos.

Cada cena tem arquivo próprio para permitir regeneração isolada. A entrega completa usa um único motor e uma única voz; o modelo pode descer pela cascata 3.8 Flash → 3.8 Flash-Lite → 3.1 quando houver fallback documentado no manifesto.

Na captura da conta Free em 30/09/2026, cada um dos modelos TTS testados tinha 10 RPD e 10 mil TPM. Com sete cenas separadas, um vídeo usa ao menos sete chamadas; tentativas que recebam 429 podem aumentar esse número. Os valores `4/3` e `24/10` do painel representam máximos históricos de uso frente às cotas, não a capacidade restante no momento. As cotas por modelo podem variar; confirme os limites atuais no AI Studio. O fallback pode completar um vídeo mesmo quando a cota do 3.8 acabar, desde que haja cota e disponibilidade no 3.1.


## Execução sem cache

Para validar uma chave/API nova, o trigger pode conter `force_fresh_audio=true`. Nessa execução o workflow não restaura o cache do GitHub nem o artifact revisado, limpa o diretório de áudio antes da síntese e força chamadas novas ao Gemini. O áudio recém-gerado volta a ser salvo no cache para as próximas execuções.
