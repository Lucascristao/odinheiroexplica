# Direção de voz editorial

O render diário usa apenas Gemini TTS. Roberto solicita a voz `Charon` e Luana solicita `Autonoe`. O modelo principal é Gemini 3.8 Flash TTS. Para Roberto, se o 3.8 esgotar a cota, mantiver HTTP 429 após as tentativas espaçadas ou ficar indisponível com 5xx persistente, o motor pode completar as cenas faltantes com Gemini 3.1 Flash TTS preview, ainda com Charon. Se o 3.8 funcionar, não há chamada ao 3.1. Uma EQ leve aproxima o timbre do trecho complementar, mas não garante identidade perfeita; escute a transição no MP4 final. O manifesto informa o modelo e tratamento de cada cena. Para Luana, o fallback ainda não foi calibrado e fica desativado.

## O que o motor aplica de fato

O worker envia o texto da `narration` e a voz predefinida ao Gemini. `speech.pronunciations` substitui termos de risco **somente na fala**, preservando a grafia em tela. Campos antigos de `tts.delivery`, `tts.cues`, `rate` ou `pitch` ainda podem estar no contrato, mas o worker Gemini atual não os aplica ao áudio; não os use como prova de que houve direção de atuação. SSML, `prosody`, `break` e bookmarks do Azure não fazem parte deste fluxo.

Escreva a intenção na própria narração: frases com uma ideia, pontuação que ajude a leitura, perguntas naturais e contraste claro. Ouça o áudio pronto antes da aprovação. Se a interpretação variar entre cenas, revise o roteiro e considere blocos contínuos de narração após testar duração e sincronização. Evite alternar modelos manualmente; o fallback automático documentado acima é a única exceção.

## Sincronização

O Gemini usado no projeto devolve áudio sem instantes medidos de cada palavra. O pipeline mede a duração real de cada cena e **estima** as posições dos eventos visuais a partir das âncoras literais do texto. Revise a entrada dos números, fotos e gráficos no MP4 pronto. Ao alterar a narração, gere novamente o áudio da cena; o cache valida o hash do texto, modelo e voz.

Escrever frases com uma ideia, variar comprimentos e conectar dado, exemplo e consequência. Dar espaço à compreensão dos recortes e gráficos. Não ler o texto inteiro da tela; a voz explica enquanto os elementos demonstram. Referências técnicas e fontes de pesquisa ficam nos arquivos internos, sem links na descrição do YouTube.


## Tom de conversa, analogias e linguagem brasileira (Estilo Didático)

- **Conversa direta e informal:** O apresentador deve soar como um brasileiro autêntico explicando finanças para um amigo (estilo Primo Rico / canais didáticos de economia), sem afetação acadêmica ou jargão jurídico distante.
- **Analogias e exemplos do cotidiano:** Todo conceito complexo (ex: segregação na liquidação, IBS dual, split payment) deve ser acompanhado de uma analogia simples e prática (ex: a compra na padaria, a maquininha de cartão separando o valor do café, o fluxo de caixa do pequeno comerciante).
- **Gatilhos de conexão:** Usar frases de engajamento natural: *"Pensa comigo"*, *"Repara no detalhe"*, *"Na prática, o que acontece?"*, *"Imagina a seguinte cena..."*.
- **Dicção brasileira natural:** Evitar fechamento exagerado de vogais ou palavras com sonoridade truncada. Se a voz neural fechar vogais de forma estranha (ex: soar "ue" ou travar em ditongos), aplicar alias fonético direto em `GLOBAL_PRONUNCIATIONS`.

## Datas e abertura

- Diga a data quando ela identifica o dado ou evento que está sendo explicado; omiti-la pode tirar contexto de uma notícia econômica. Evite repetir o calendário sem função narrativa.
- Comece com uma pergunta ou consequência concreta. A saudação e o nome do apresentador entram depois, quando ajudarem a relação com o público. Não reserve automaticamente segundos vazios antes de mostrar o assunto.
- Varie a abertura conforme a pauta. A primeira imagem deve tornar a pergunta visível, não apenas apresentar uma frase num cartão.
