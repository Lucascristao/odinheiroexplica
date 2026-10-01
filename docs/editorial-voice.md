# Voz editorial

O render diário usa apenas Gemini 3.8 Live, seguindo `worker/voice-policy.json`. Roberto usa `Charon`; Luana usa `Autonoe`. O modelo não muda no meio do vídeo e não existe cascata de fallback para outro modelo.

O Live recebe uma instrução de leitura literal, português brasileiro e a direção vocal comum do canal: natural, conversacional, ritmo moderado, articulação clara, ênfase variada sem exagero e pausas curtas entre ideias completas. `speech.pronunciations` continua orientando termos de risco somente na fala, preservando a grafia do roteiro e da tela.

A transcrição de saída do próprio Live é obrigatória e funciona como gate de fidelidade ao roteiro. Se a leitura divergir além do limite da política, a cena é rejeitada em vez de ser aceita com improvisação.

O áudio sai como PCM 24 kHz/16-bit mono e é encapsulado em WAV sem DSP. Não há EQ, limiter, compressor, loudness matching, pitch, velocidade, resample ou efeito de transição. O worker de continuidade agora apenas comprova que o modelo e a voz são homogêneos e copia os bytes sem alteração.

Escreva a intenção na própria narração: uma ideia por frase quando possível, pontuação que ajude a leitura, perguntas naturais e contraste claro. A direção da API melhora a interpretação, mas não substitui um roteiro falável. Ouça o áudio final antes da aprovação.

## O que o motor aplica de fato

O worker envia a direção vocal comum da política à API: metadata de estilo no 3.8/Lite e instruções separadas da transcrição no 3.1. `speech.pronunciations` substitui termos de risco **somente na fala**, preservando a grafia em tela. Campos antigos por cena de `tts.delivery`, `tts.cues`, `rate` ou `pitch` continuam sem aplicação; não os use como prova de direção de atuação. SSML, `prosody`, `break` e bookmarks do Azure não fazem parte deste fluxo.

Escreva a intenção na própria narração: frases com uma ideia, pontuação que ajude a leitura, perguntas naturais e contraste claro. Ouça o áudio pronto antes da aprovação. Se a interpretação variar entre cenas, revise o roteiro e considere blocos contínuos de narração após testar duração e sincronização. Evite alternar modelos manualmente; o fallback automático documentado acima é a única exceção.

## Continuidade entre cenas

O runner aplica continuidade adaptativa v3 sem API adicional apenas em episódios mistos; voz homogênea e cenas do modelo de referência ficam byte por byte intocadas. Prefere cenas principais suficientes do próprio episódio; para Roberto/Charon, usa a amostra aprovada no GitHub quando faltar essa referência. O fallback recebe correção espectral limitada, suavizada e reduzida em trechos pouco confiáveis, mais ganho estático com folga de pico. Não há EQ prévia, limiter, compressor, mudança de velocidade ou pitch, nem sobreposição de falas. Meta de loudness: 0,8 LU; aviso acima dela e falha acima de 1,5 LU. Isso não garante timbre idêntico nem corrige prosódia ou emoção. As trocas são registradas sem pigarro ou outros sons extras.

O processamento gera WAVs de 48 kHz em diretório separado, preservando os originais e o cache. O manifesto informa referência, confiança, ganhos, loudness, picos e modelo original. Retomadas aceitam apenas narração e política atuais, com fingerprints, hashes e duração válidos; áudio legado não é reclassificado. Mudanças visuais e de processamento aproveitam as gravações válidas. Veja os parâmetros e o pedido explícito de regeneração em `docs/tts.md`.

## Sincronização

O Gemini devolve áudio sem bookmarks de palavras. O runner localiza âncoras no WAV processado com reconhecimento local e limiares de confiança. Os eventos confirmados registram `audio-word-alignment`; os demais permanecem estimativas explícitas. O relatório não altera a narração ou cria dados. Revise a entrada de números, fotos e gráficos no MP4. Ao alterar a narração ou política vocal, o cache invalida o áudio correspondente.

Escrever frases com uma ideia, variar comprimentos e conectar dado, exemplo e consequência. Dar espaço à compreensão dos recortes e gráficos. Não ler o texto inteiro da tela; a voz explica enquanto os elementos demonstram. Referências técnicas e fontes de pesquisa ficam nos arquivos internos, sem links na descrição do YouTube.


## Tom de conversa, analogias e linguagem brasileira (Estilo Didático)

- **Conversa direta e informal:** O apresentador deve soar como um brasileiro autêntico explicando finanças para um amigo (estilo Primo Rico / canais didáticos de economia), sem afetação acadêmica ou jargão jurídico distante.
- **Analogias e exemplos do cotidiano:** Todo conceito complexo (ex: segregação na liquidação, IBS dual, split payment) deve ser acompanhado de uma analogia simples e prática (ex: a compra na padaria, a maquininha de cartão separando o valor do café, o fluxo de caixa do pequeno comerciante).
- **Gatilhos de conexão:** Usar frases de engajamento natural: *"Pensa comigo"*, *"Repara no detalhe"*, *"Na prática, o que acontece?"*, *"Imagina a seguinte cena..."*.
- **Dicção brasileira natural:** Evitar fechamento exagerado de vogais ou palavras com sonoridade truncada. Se uma pronúncia validada precisar de ajuste, registre o alias no `speech.pronunciations` do projeto; preserve a grafia correta em tela.

## Datas e abertura

- Diga a data quando ela identifica o dado ou evento que está sendo explicado; omiti-la pode tirar contexto de uma notícia econômica. Evite repetir o calendário sem função narrativa.
- Comece com uma pergunta ou consequência concreta e nomeie o assunto. Explique siglas e conceitos no primeiro uso, sem presumir conhecimento prévio; acrescente um exemplo simples quando a definição não bastar.
- Todo vídeo deve apresentar Roberto ou Luana em uma frase falada natural logo após o gancho, integrada à explicação. Não reserve uma cena, vinheta longa ou segundos vazios para a apresentação.
- Varie a abertura conforme a pauta. A primeira imagem deve tornar a pergunta visível, não apenas apresentar uma frase num cartão.
- Todo vídeo deve incluir um único pedido falado breve de inscrição após entregar valor, em um respiro da narrativa ou no encerramento. Relacione o convite ao benefício de acompanhar o canal, sem interromper uma explicação nem repetir a mesma frase entre vídeos.
- A conclusão responde à pergunta inicial. Duração e número de cenas seguem a explicação necessária; a quota da voz é tratada pela produção, sem cortar o roteiro.

Antes do TTS, registre em `editorial.narrative_contract` as strings `topic_explanation`, `presenter_introduction` e `subscription_request`, copiadas literalmente de trechos com ocorrência única na narração. A explicação está nas duas primeiras cenas, a apresentação com nome na primeira cena após o gancho, e o pedido depois da apresentação e de uma entrega de valor. O validador confere o contrato; a revisão editorial confere se os trechos realmente explicam, apresentam e convidam. As falas continuam sendo escritas para cada pauta.
