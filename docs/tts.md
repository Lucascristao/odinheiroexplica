# Narração

## Fluxo atual

O render diário usa somente Gemini TTS e preserva a mesma voz do apresentador em toda a cascata. Para o apresentador masculino, solicita `Charon`; para o feminino, `Autonoe`. A ordem padrão é `gemini-3.8-flash-tts` → `gemini-3.8-flash-lite-tts` → `gemini-3.1-flash-tts-preview`. O próximo modelo só é acionado quando o anterior devolve RPD esgotado, 429 persistente após três tentativas espaçadas, 5xx persistente ou timeout persistente após as tentativas. Cada pedido pode aguardar até 180 segundos pela resposta. Erro de autenticação, configuração, modelo inexistente, resposta sem áudio ou erro de conexão não avança silenciosamente a cascata.

O worker espaça o início das chamadas por pelo menos 22 segundos para respeitar a cota Free de 3 RPM mostrada no AI Studio. Em 429, registra os detalhes estruturados de cota sem expor a chave; RPM transitório espera e tenta novamente no 3.8. Ao entrar em um nível de fallback, as cenas novas dessa execução continuam no nível ativo; se ele também ficar indisponível, o motor desce para o próximo mantendo a mesma voz. Um fallback restaurado do cache não prova indisponibilidade atual do principal e, por isso, não força cenas novas a permanecerem nele. Se os três modelos falharem, o render para e preserva o que já foi gerado. Não existe Azure nem troca automática para outra voz.

O manifesto de TTS registra `engine`, `voice`, `model`, `voice_treatment` e `fallback_reason` por cena, além de `models_used` e `fallback_scene_ids` no resumo. `requested_voice` guarda a voz solicitada. A credencial `GEMINI_API_KEY` pertence apenas ao worker e não deve aparecer no frontend, no repositório ou em logs.

Cada arquivo de áudio tem um sidecar `.tts.json` com hash da narração, modelo, voz, tratamento, hash do áudio e duração medida. Ao reexecutar, o worker só reutiliza o MP3 se esses dados e a duração conferirem. Assim, uma execução que parou por quota retoma das cenas faltantes sem repetir chamadas já concluídas. Uma mudança de texto, modelo, voz, tratamento ou áudio invalida o cache daquela cena. Um trecho já gravado pelo 3.1 continua como 3.1 na retomada, sem ser confundido com o 3.8.

## Semelhança de voz no fallback

As três amostras de Charon enviadas pelo usuário em 30/09/2026 têm nível médio muito próximo: 3.8 Flash a −18,42 dBFS e 3.1 a −18,26 dBFS. A amostra 3.1 apresentou cerca de 6 dB a mais na faixa de 4–8 kHz e menos presença em 1–2 kHz. Só no trecho 3.1, o worker aplica EQ fixa e leve: graves abaixo de 160 Hz −1 dB, região de 1,5 kHz +1,5 dB, agudos acima de 4,2 kHz −2,5 dB. O tratamento não muda velocidade ou altura de voz e não promete timbre idêntico: interpretação e prosódia ainda podem variar. O vídeo final é entregue para escuta e aprovação manual.

## Continuidade de voz por episódio

Após obter os áudios, `worker/process_voice_continuity.py` processa os arquivos localmente no runner, sem chamadas de API. O perfil de referência vem das cenas 3.8 do próprio episódio. Nas cenas 3.8 Flash-Lite e 3.1, a versão `adaptive-voice-continuity-v2` analisa janelas lentas de 5 segundos com sobreposição de 2,5 segundos. Cada janela calcula uma correção residual limitada; as correções são suavizadas entre janelas e têm limite de variação entre uma janela e outra. O objetivo é evitar a sensação de o tratamento entrar e sair durante a fala.

O match espectral usa no máximo ±2,5 dB por faixa, com transições interpoladas no tempo. O Charon 3.1 pode já conter a EQ fixa inicial; nesse caso a correção por janela continua sendo apenas residual. O 3.8 Flash principal não recebe correção de timbre e serve de referência quando há pelo menos duas cenas e doze segundos ativos.

A versão v2 remove compressor e normalização dinâmica do caminho de entrega. O loudness é medido, mas o áudio recebe **ganho estático por cena** para se aproximar da mediana das cenas 3.8, com limiter apenas como proteção de pico. Não há pitch, mudança de velocidade, crossfade de fala ou `loudnorm` dinâmico aplicado ao sinal. O teto permanece em −1 dBTP.

MP3s originais e sidecars do cache são preservados. A saída fica separada em `public/processed-audio/daily`, em WAV mono de 48 kHz e 24 bits. A validação usa FFmpeg/ffprobe, inclusive para WAVE_FORMAT_EXTENSIBLE. `video/generated/daily-processed-tts-manifest.json` registra as janelas, ganhos, loudness, pico, duração e hashes. O render usa esse manifesto e os WAVs processados.

Ao refazer um vídeo revisado, o workflow pode restaurar seus áudios de um artefato anterior. Uma cena só é reutilizada se o hash da narração for o mesmo e os dados do cache, hash do áudio e duração forem válidos. Cenas com narração alterada ou cache inválido geram novo TTS; ajustes apenas de processamento ou visual reutilizam a gravação. Restaurar um trecho 3.1 não o identifica como 3.8 e não transforma o fallback em modelo principal.

## Timeline

A divisão em cenas e a extensão do roteiro são decisões editoriais: use o necessário para explicar a história inteira. Os limites da API controlam o agendamento da síntese, não a quantidade de cenas nem o conteúdo. Em caso de quota, use cache, espera, retomada e o fallback autorizado; preserve o roteiro completo se a síntese precisar continuar depois.

roteiro por cena → cache válido ou TTS por cena → continuidade de voz offline → duração medida do WAV → estimativa de posição das âncoras → timeline → render.

O Gemini usado aqui entrega áudio, sem offsets de palavras ou bookmarks. `compute_beat_timings` distribui cada âncora pela duração real do áudio segundo os caracteres e a pontuação da narração. Esses tempos têm `timing_source: estimated-text-alignment`; uma âncora não encontrada recebe `estimated-distributed` e não serve para um palco persistente. O render verifica que as âncoras de palcos persistentes existem uma única vez e aparecem na ordem da fala. Manifestos antigos com `gemini-bookmark` são lidos como estimativas textuais. Ajuste fino de sincronismo precisa de alinhamento forçado ou eventos de TTS realmente medidos.

Cada cena tem arquivo próprio para permitir regeneração isolada. A entrega completa usa um único motor e uma única voz; o modelo pode descer pela cascata 3.8 Flash → 3.8 Flash-Lite → 3.1 quando houver fallback documentado no manifesto.

Na captura da conta Free em 30/09/2026, cada um dos modelos TTS testados tinha 10 RPD e 10 mil TPM. Com sete cenas separadas, um vídeo usa ao menos sete chamadas; tentativas que recebam 429 podem aumentar esse número. Os valores `4/3` e `24/10` do painel representam máximos históricos de uso frente às cotas, não a capacidade restante no momento. As cotas por modelo podem variar; confirme os limites atuais no AI Studio. O fallback pode completar um vídeo mesmo quando a cota do 3.8 acabar, desde que haja cota e disponibilidade no 3.1.


## Execução sem cache

Para validar uma chave/API nova, o trigger pode conter `force_fresh_audio=true`. Nessa execução o workflow não restaura o cache do GitHub nem o artifact revisado, limpa o diretório de áudio antes da síntese e força chamadas novas ao Gemini. O áudio recém-gerado volta a ser salvo no cache para as próximas execuções.
