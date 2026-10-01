# Narração

## Política e fallback

`worker/voice-policy.json` é a política canônica de modelos, vozes, idioma e direção vocal. O worker, DSP, gates e chave de cache consultam esse arquivo. Roberto usa `Charon`; Luana usa `Autonoe`. A cascata padrão é `gemini-3.8-flash-tts` → `gemini-3.8-flash-lite-tts` → `gemini-3.1-flash-tts-preview`. O modelo seguinte só entra após RPD esgotado, 429 persistente, 5xx persistente ou timeout persistente, conforme as tentativas do worker. Erros de autenticação, configuração, conexão e resposta sem áudio interrompem a geração. Um trecho restaurado do fallback não prova indisponibilidade atual do principal.

As chamadas começam com pelo menos 22 segundos de intervalo. Produções deste workflow entram em fila por repositório; isso evita que dois renders disputem a mesma cota. Essa fila não controla chamadas feitas por outros aplicativos. RPM, RPD e TPM são limites de requisições por minuto, por dia e tokens por minuto, respectivamente; confira os valores atuais do projeto no AI Studio.

3.8 Flash e Lite recebem transcrição literal e `speech_metadata.style` pela API Interactions, com idioma `pt-BR` e voz em `speech_config`. 3.1 preview recebe instruções de leitura separadas da transcrição delimitada pela API GenerateContent. `worker/tts_config.py` adapta cada requisição e calcula o fingerprint dos controles efetivamente enviados. Instruções não entram na narração, no hash do roteiro ou nas âncoras visuais. Campos antigos por cena como `tts.delivery`, `tts.cues`, `rate` e `pitch` continuam sem aplicação. A credencial `GEMINI_API_KEY` fica somente no runner.

## Cache e retomada

Cada MP3 original permanece sem EQ e tem sidecar `.tts.json` com narração, voz, modelo, duração, hash do áudio, versão e fingerprint da política. O cache só é válido se todos conferirem. Alterar voz, endpoint, idioma, direção, formato da requisição ou texto invalida a gravação correspondente. Áudios legados sem fingerprint não são reclassificados como atuais.

Reexecuções aproveitam gravações válidas, inclusive cenas de fallback, mantendo sua proveniência. Ajustes apenas visuais ou de DSP não exigem novas chamadas. Quando solicitado, o workflow restaura um artifact revisado, mas só aceita trechos com a narração e política atuais. A cache v3 prioriza tentativas anteriores do mesmo run. Se a síntese parar, os áudios já concluídos ficam salvos para a retomada.

Regeneração integral exige o input manual `force_fresh_audio` no workflow_dispatch e vale somente no primeiro attempt. Pushes e reruns retomam cache. Um texto antigo `force_fresh_audio=true` em `render-trigger/daily.txt` não ativa regeneração. Não reduza roteiro, quantidade de cenas ou duração por quota.

## Continuidade adaptativa v3

`worker/process_voice_continuity.py` analisa os originais e gera WAVs separados no runner, sem outra API. Prefere a mediana das cenas 3.8 do episódio quando houver pelo menos duas cenas e doze segundos ativos. Se faltar essa referência para Roberto, usa `worker/voice-references/roberto-charon-3.8.json`, derivado da amostra 3.8/Charon aprovada pelo usuário, com origem, hash e método registrados. Esse perfil não é usado para Autonoe; sem referência compatível, a correção espectral é omitida e o motivo é registrado.

Somente o fallback recebe EQ adaptativa: janelas de 5 segundos, passo de 2,5 segundos, limite de ±2,5 dB por faixa e suavização temporal. Atividade vocal, semelhança do perfil e consistência com a cena reduzem a intensidade da correção quando a referência for fraca. Os coeficientes de confiança indicam quanto aplicar, não uma probabilidade de identidade da voz. A síntese não recebe uma EQ fixa prévia.

Episódios inteiros com o mesmo modelo e voz mantêm os MP3s byte por byte, sem efeitos. Em episódios mistos, as cenas do modelo de referência continuam intocadas; apenas o fallback recebe EQ adaptativa e ganho estático para aproximar seu loudness. O ganho respeita a folga de pico sem limiter, compressor ou normalização dinâmica. Diferença acima de 0,8 LU gera aviso explícito no log e manifesto; acima de 1,5 LU interrompe a produção. Não há alteração de pitch ou velocidade, nem sobreposição de falas. Prosódia e interpretação podem continuar diferentes; o tratamento não garante timbre idêntico.

Originais e sidecars ficam preservados. `public/processed-audio/daily` contém MP3s intocados e WAVs do fallback tratado; FFmpeg/ffprobe validam duração e formatos. O manifesto registra modo de entrega, identidade dos bytes, referência, confiança, ganhos por janela, loudness, picos e hashes. Trocas de modelo ficam apenas nos metadados, sem gerar ou inserir pigarro, fala extra ou efeito audível. A troca não aumenta duração ou desloca beats.

## Alinhamento e entrega

Fluxo: roteiro → cache ou Gemini por cena → continuidade v3 → reconhecimento local do WAV processado → âncoras com confiança → timeline → render.

Gemini não fornece bookmarks de palavras neste fluxo. `worker/align_narration.py` usa faster-whisper em CPU para localizar palavras no áudio real, com idioma português, atividade vocal e limiares de cobertura/confiança. Usa os aliases de pronúncia também na comparação. A transcrição reconhecida nunca altera roteiro, fontes ou fatos. Apenas âncoras únicas, confiáveis e compatíveis com a ordem/intervalos são aceitas como `audio-word-alignment`.

Âncoras incertas mantêm estimativas explícitas; entre âncoras localizadas, são interpoladas sem deslocar os pontos confiáveis. Se o reconhecimento ou download do modelo estiver indisponível, o relatório registra o motivo e preserva estimativas. Isso não é alinhamento garantido palavra por palavra: revise o sincronismo no MP4.

Antes do render, o motor confere a narração, o fingerprint da política, o hash do WAV e sua duração medida. Artifacts incluem manifesto bruto, processado, alinhado e relatório de alinhamento. A revisão manual continua necessária para ouvir as trocas e avaliar a execução visual. A publicação no YouTube permanece manual.
