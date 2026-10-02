# Voz editorial

## Política de produção

`worker/voice-policy.json` é a referência canônica. O único modelo é `gemini-3.8-live`: Roberto usa `Charon` e Luana usa `Autonoe`. Não existe cascata de fallback. Uma falha preserva o cache e permite retomada com o mesmo modelo e voz.

Priorize sempre Roberto/Charon. Luana/Autonoe é escolhida somente quando o assunto for dirigido ao público feminino; a escolha depende do público da pauta, sem alternância estética ou automática nem estereótipos simplistas de gênero. Defina antes da síntese e mantenha a mesma pessoa e voz em todas as cenas, com apresentação falada e contrato coerentes.

A direção vocal é instrução separada da narração: português brasileiro, presença, calor, articulação clara e variação natural de ritmo e entonação conforme o raciocínio. A pergunta, a descoberta, o contraste e a resposta precisam ter intenção audível; não aplique uma curva idêntica a todas as frases. A identidade do apresentador permanece, mas cada vídeo recebe direção própria, escolhida pelo sentido das suas frases, sem sequência obrigatória de emoções ou quota de ênfases. O texto falado precisa continuar fiel ao roteiro. A Live API devolve uma transcrição de saída, exigida pelo gate de fidelidade; ela também pode conter erros de transcrição e não substitui a escuta.

O worker encapsula PCM mono 16-bit/24 kHz em WAV, sem EQ, ganho, normalização, compressor, limiter, resample, pitch ou mudança de velocidade. A etapa de continuidade verifica modelo/voz/integridade e copia o arquivo byte por byte. Não há ajuste de timbre ou efeitos sonoros nas trocas de modelo, pois o modelo não muda.

## Texto para falar e explicar

Escreva frases naturais, varie comprimentos e conecte ideia, demonstração e consequência. Evite relatório burocrático e bordões obrigatórios. Perguntas e conectores entram quando ajudam o raciocínio. Não imite a persona ou voz de um canal de referência.

Siga `docs/editorial-explanation.md`: explique conceitos essenciais e use exemplos ou analogias quando resolvem uma dificuldade concreta. Preserve condições e limites; não substitua precisão por informalidade. Não há obrigação de analogia em cada conceito nem quota de exemplos.

Apresente Roberto ou Luana naturalmente depois do gancho; inclua um único convite breve de inscrição depois de entregar valor. A conclusão responde à pergunta inicial. Cenas e duração seguem a explicação, sem redução para caber em quota.

## Pronúncias, sincronização e revisão

Registre aliases em `speech.pronunciations`, preservando a grafia correta da narração e da tela. O Live recebe essas pronúncias como instruções de leitura. Por cena, `tts.delivery` oferece uma orientação flexível e até seis `tts.cues` literais e únicos dirigem os pontos em que a intenção precisa ficar clara. Cada cue permanece dentro de uma frase; pode acrescentar `intent`, `arc` e `emphasis_word` para escolher intenção, percurso da frase e uma palavra-chave literal do trecho. Esses campos são opcionais e autorais: o motor não inventa cues nem atribui curvas automaticamente ao roteiro. Os cues antigos continuam válidos, com suas instruções traduzidas em direção de fala em português. A direção entra no fingerprint do cache.

Escolha o que merece atuação pelo significado: uma condição pode pedir atenção, uma pergunta pode pedir curiosidade e uma consequência pode pedir resolução. Preserve hipóteses e limites mesmo quando a fala ganha convicção. Pausas descritas são intenções aproximadas, não controles exatos. Não use SSML ou rate/pitch para manipular a voz bruta. Consulte `docs/tts.md` para os valores aceitos e um exemplo.

A transcrição de saída verifica conteúdo; o alinhamento local do áudio real localiza as âncoras no tempo. Tempos confirmados e estimados permanecem distinguidos no manifesto. Mudanças visuais não invalidam voz válida; mudanças no texto, pronúncias, apresentador, voz ou política precisam corresponder ao cache atual. Trocar Luana/Autonoe por Roberto/Charon exige nova narração com a voz correta, nova apresentação quando necessário e alinhamento correspondente; não reaproveitar WAV da voz anterior como se fosse o novo apresentador. A política de modelo permanece Gemini 3.8 Live e o WAV continua bruto, sem DSP.

Ouça o MP4 inteiro para presença, intenção das frases, naturalidade, dicção, fidelidade, pausas e sincronização. O gate lexical não avalia interpretação nem exige ritmo neutro. Se houver uma dúvida concreta de direção, compare um trecho curto antes da síntese completa; isso é uma ferramenta de decisão, sem obrigação de produzir amostras em cada execução. WPM, picos e duração são diagnósticos; não aceleram automaticamente a fala nem provocam nova síntese por aviso isolado. Consulte `docs/tts.md` para o protocolo de cache, fidelidade e entrega.
