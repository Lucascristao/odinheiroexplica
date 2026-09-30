# Narração

## Fluxo atual

O render diário usa somente Gemini TTS. Para o apresentador masculino, solicita a voz `Charon`; para o feminino, `Autonoe`. O modelo principal é `gemini-3.8-flash-tts`. Para `Charon`, `gemini-3.1-flash-tts-preview` fica disponível **somente como fallback** quando o principal devolve RPD esgotado, 429 persistente após três tentativas espaçadas, 5xx persistente ou timeout persistente após as tentativas. Cada pedido pode aguardar até 180 segundos pela resposta para evitar repetir a síntese enquanto o servidor ainda trabalha. O 3.1 não recebe nenhuma chamada se o 3.8 concluir as cenas. Erro de autenticação, configuração, modelo inexistente, resposta sem áudio ou erro de conexão não aciona troca automática. Para `Autonoe`, a produção permanece no modelo principal até que haja uma calibração específica.

O worker espaça o início das chamadas por pelo menos 22 segundos para respeitar a cota Free de 3 RPM mostrada no AI Studio. Em 429, registra os detalhes estruturados de cota sem expor a chave; RPM transitório espera e tenta novamente no 3.8. Ao entrar no fallback, não testa o 3.8 de novo nas cenas ainda sem áudio dessa execução. Se o 3.1 também falhar, o render para e preserva as cenas já geradas no cache. Não existe Azure nem terceiro modelo.

O manifesto de TTS registra `engine`, `voice`, `model`, `voice_treatment` e `fallback_reason` por cena, além de `models_used` e `fallback_scene_ids` no resumo. `requested_voice` guarda a voz solicitada. A credencial `GEMINI_API_KEY` pertence apenas ao worker e não deve aparecer no frontend, no repositório ou em logs.

Cada arquivo de áudio tem um sidecar `.tts.json` com hash da narração, modelo, voz, tratamento, hash do áudio e duração medida. Ao reexecutar, o worker só reutiliza o MP3 se esses dados e a duração conferirem. Assim, uma execução que parou por quota retoma das cenas faltantes sem repetir chamadas já concluídas. Uma mudança de texto, modelo, voz, tratamento ou áudio invalida o cache daquela cena. Um trecho já gravado pelo 3.1 continua como 3.1 na retomada, sem ser confundido com o 3.8.

## Semelhança de voz no fallback

As três amostras de Charon enviadas pelo usuário em 30/09/2026 têm nível médio muito próximo: 3.8 Flash a −18,42 dBFS e 3.1 a −18,26 dBFS. A amostra 3.1 apresentou cerca de 6 dB a mais na faixa de 4–8 kHz e menos presença em 1–2 kHz. Só no trecho 3.1, o worker aplica EQ fixa e leve: graves abaixo de 160 Hz −1 dB, região de 1,5 kHz +1,5 dB, agudos acima de 4,2 kHz −2,5 dB. O tratamento não muda velocidade ou altura de voz e não promete timbre idêntico: interpretação e prosódia ainda podem variar. O vídeo final é entregue para escuta e aprovação manual.

## Timeline

A divisão em cenas e a extensão do roteiro são decisões editoriais: use o necessário para explicar a história inteira. Os limites da API controlam o agendamento da síntese, não a quantidade de cenas nem o conteúdo. Em caso de quota, use cache, espera, retomada e o fallback autorizado; preserve o roteiro completo se a síntese precisar continuar depois.

roteiro por cena → TTS por cena → duração medida do áudio → estimativa de posição das âncoras → timeline → render.

O Gemini usado aqui entrega áudio, sem offsets de palavras ou bookmarks. `compute_beat_timings` distribui cada âncora pela duração real do áudio segundo os caracteres e a pontuação da narração. Esses tempos têm `timing_source: estimated-text-alignment`; uma âncora não encontrada recebe `estimated-distributed` e não serve para um palco persistente. O render verifica que as âncoras de palcos persistentes existem uma única vez e aparecem na ordem da fala. Manifestos antigos com `gemini-bookmark` são lidos como estimativas textuais. Ajuste fino de sincronismo precisa de alinhamento forçado ou eventos de TTS realmente medidos.

Cada cena tem arquivo próprio para permitir regeneração isolada. A entrega completa usa um único motor e um único preset de voz; o modelo pode mudar uma vez para o 3.1 em condição de fallback documentada no manifesto.

Na captura da conta Free em 30/09/2026, cada um dos modelos TTS testados tinha 10 RPD e 10 mil TPM. Com sete cenas separadas, um vídeo usa ao menos sete chamadas; tentativas que recebam 429 podem aumentar esse número. Os valores `4/3` e `24/10` do painel representam máximos históricos de uso frente às cotas, não a capacidade restante no momento. As cotas por modelo podem variar; confirme os limites atuais no AI Studio. O fallback pode completar um vídeo mesmo quando a cota do 3.8 acabar, desde que haja cota e disponibilidade no 3.1.
