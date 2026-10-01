# Voz editorial

## Política de produção

`worker/voice-policy.json` é a referência canônica. O único modelo é `gemini-3.8-live`: Roberto usa `Charon` e Luana usa `Autonoe`. Não existe cascata de fallback. Uma falha preserva o cache e permite retomada com o mesmo modelo e voz.

A direção vocal é instrução separada da narração: português brasileiro, conversa natural, ritmo moderado, articulação clara, ênfase variada sem exagero e pausas entre pensamentos completos. O texto falado precisa continuar fiel ao roteiro. A Live API devolve uma transcrição de saída, exigida pelo gate de fidelidade; ela também pode conter erros de transcrição e não substitui a escuta.

O worker encapsula PCM mono 16-bit/24 kHz em WAV, sem EQ, ganho, normalização, compressor, limiter, resample, pitch ou mudança de velocidade. A etapa de continuidade verifica modelo/voz/integridade e copia o arquivo byte por byte. Não há ajuste de timbre ou efeitos sonoros nas trocas de modelo, pois o modelo não muda.

## Texto para falar e explicar

Escreva frases naturais, varie comprimentos e conecte ideia, demonstração e consequência. Evite relatório burocrático e bordões obrigatórios. Perguntas e conectores entram quando ajudam o raciocínio. Não imite a persona ou voz de um canal de referência.

Siga `docs/editorial-explanation.md`: explique conceitos essenciais e use exemplos ou analogias quando resolvem uma dificuldade concreta. Preserve condições e limites; não substitua precisão por informalidade. Não há obrigação de analogia em cada conceito nem quota de exemplos.

Apresente Roberto ou Luana naturalmente depois do gancho; inclua um único convite breve de inscrição depois de entregar valor. A conclusão responde à pergunta inicial. Cenas e duração seguem a explicação, sem redução para caber em quota.

## Pronúncias, sincronização e revisão

Registre aliases em `speech.pronunciations`, preservando a grafia correta da narração e da tela. O Live recebe essas pronúncias como instruções de leitura. Por cena, `tts.delivery` e até seis `tts.cues` literais e únicos orientam interpretação fora do roteiro; a direção entra no fingerprint do cache. Pausas descritas são intenções aproximadas, não controles exatos. Não use SSML ou rate/pitch para manipular a voz bruta.

A transcrição de saída verifica conteúdo; o alinhamento local do áudio real localiza as âncoras no tempo. Tempos confirmados e estimados permanecem distinguidos no manifesto. Mudanças visuais não invalidam voz válida; mudanças no texto, pronúncias ou política precisam corresponder ao cache atual.

Ouça o MP4 inteiro para naturalidade, dicção, fidelidade, pausas e sincronização. WPM, picos e duração são diagnósticos; não aceleram automaticamente a fala nem provocam nova síntese por aviso isolado. Consulte `docs/tts.md` para o protocolo de cache, fidelidade e entrega.
