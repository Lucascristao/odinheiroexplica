# Prompt diário

## Composição legível no celular

As ilustrações precisam protagonizar o quadro, com informações principais grandes e transformações ligadas à fala. Não usar arte pequena num card com grandes vazios nem reservar espaço para legendas que o motor já posiciona nos vazios reais. Declare `visual_role` e, para objetos cujo rótulo seja só descrição técnica, `show_label: false`. Não exibir “ILUSTRAÇÃO ESQUEMÁTICA”; preserve a identificação de exemplos hipotéticos e condições reais. Confira o tamanho efetivo do clipe/SVG no relatório de produção, além da largura nominal do elemento. Use rótulos curtos em regiões generosas e câmera/estados que mostrem o raciocínio, não apenas foco decorativo.

## Regra de independência editorial e seleção de pauta

1. **Anti-repetição obrigatória**: Antes de sugerir ou iniciar qualquer roteiro, consulte obrigatoriamente `docs/visual-history.md`, os commits recentes e o repositório para verificar os vídeos já produzidos pelo canal. Nunca repita temas, ganchos ou ângulos idênticos aos episódios anteriores.
2. **Apresentação de 3 opções virais ao usuário**: Ao receber o pedido de um novo vídeo diário (ou nova seleção de pauta), pesquise a fundo o cenário do momento e apresente 3 opções qualificadas, distintas e com alta predisposição a viralizar. Cada opção deve conter:
   - **Título Viral de Alto CTR**: Sem jargões técnicos ("marcação a mercado", "juro real", "subvenção"). O título deve ativar curiosidade irresistível ou medo de perder dinheiro.
   - **Thumbnail Magnética**: Conceito visual e texto de 2 a 4 palavras de alto impacto emocional, complementando o título.
   - **Gancho Hipnótico (Primeiros 5s)**: Abertura na tensão máxima, quebrando crenças comuns.
   - **Gatilho Mental Central**: Qual motor psicológico puxa o clique (Aversão à perda, Segredo revelado, Curiosidade oculta, Alerta no bolso).
   - **Fatos e Dados Concretos**: Sustentação real e fontes balanceadas (clickbait ético: alta curiosidade, entrega 100% verdadeira).
   Aguarde a escolha do usuário antes de escrever `video/data/daily.json` e iniciar o render.
3. **Preservação e Potencialização da Pauta Escolhida**: Uma vez que o usuário escolheu ou aprovou uma pauta na conversa, preserve esse assunto e aplique toda essa engenharia viral no título final, na thumbnail, na abertura e no ritmo do roteiro. Não troque de tema sem pedido explícito.

### Conflito concreto antes da seleção

Cada candidata deve conter uma situação reconhecível do bolso, uma crença contrariada por um fato verificável e uma resposta que possa ser demonstrada. Resolva internamente: o que a pessoa acredita, o que acontece de diferente, qual consequência ela sofre e qual prova/conta/objeto torna a descoberta compreensível. Um aviso de serviço, lista de benefícios ou tutorial genérico não basta por ter palavras como "dinheiro" ou "perder".

Referência de qualidade aprovada: **"Supermercado: o aumento de preço que você não vê"**, thumbnail **"CADÊ O RESTO?"**, abertura **"O preço não mudou. Então por que você está pagando mais?"**. A força nasce da contradição entre preço da embalagem e preço por quantidade. Reutilize o critério, nunca o tema ou a fórmula nas próximas pautas.

Prefira assunto reconhecível cedo no título e tensão específica a adjetivos alarmistas. Título, thumbnail e gancho vendem a mesma descoberta, entregue no roteiro. Não transformar hipótese em fato, caso isolado em aumento universal, redução informada em fraude, risco em perda certa ou exemplo numérico em estatística observada. Potencial editorial não é CTR medido nem promessa de viralidade.

Arquivos de piloto, testes, demonstrações e exemplos anteriores existem apenas para validar a tecnologia. Nunca use o assunto, a estrutura narrativa, o título, a thumbnail, os visuais ou o enquadramento de um piloto como molde ou preferência para um novo vídeo. Cada pauta deve nascer da solicitação atual e da pesquisa atual. O piloto do Pix é somente um teste técnico e não deve influenciar a seleção ou a forma dos próximos vídeos.

Pesquise profundamente acontecimentos recentes ligados a dinheiro, empresas, economia, bancos, fintechs, tecnologia com impacto econômico e grandes movimentos empresariais relevantes para o público brasileiro.

Não escolha simplesmente a notícia mais importante. Escolha a história com melhor combinação de novidade, impacto, surpresa, curiosidade, dimensão econômica, reconhecimento, narrativa, potencial visual, qualidade das fontes e potencial evergreen.

Use fontes primárias para confirmar documentos, regras, números e posições institucionais, mas não deixe que elas definam sozinhas o enquadramento da história. Em pautas econômicas, regulatórias ou de interesse público, siga obrigatoriamente `docs/source-neutrality.md`, buscando fontes independentes de linhas editoriais diferentes, análise técnica quando houver e contrapontos sustentados por evidência. Não faça recomendação individual de compra ou venda de investimentos.

Em toda pauta, consulte ao menos uma matéria específica de veículo com linha editorial à direita ou centro-direita e registre `publisher`, URL e resumo em `editorial.source_balance.right_editorial_review.consulted`. Use essa leitura para testar o enquadramento, os custos e os efeitos práticos da narrativa oficial. Não atribua a essa matéria dados que ela não traz; confirme números na fonte primária e cruze as interpretações. A voz do canal pode dar espaço maior a críticas bem sustentadas, mantendo linguagem sóbria e sem militância partidária.

### Atribuição das fontes na fala

Evite nomes de jornais, revistas e portais na narração. Use atribuição natural quando necessária, como "uma reportagem consultada destacou" ou "as reportagens consultadas apontaram". A forma no singular ou no plural precisa corresponder às fontes que realmente sustentam aquela afirmação. Não substitua o nome de um veículo por "o mercado", "a imprensa" ou "os especialistas" para sugerir consenso que a pesquisa não demonstrou. Preserve opiniões e interpretações como posições atribuídas, sem apresentá-las como fatos confirmados.

Mantenha o nome exato do veículo, o título e a URL específica em `sources` e no pacote técnico. Preserve nomes reais e créditos na seção de fontes da descrição, mantendo seu formato público sem links. A preferência de não falar marcas de veículos não elimina pesquisa, diversidade editorial nem rastreabilidade. Instituições oficiais, como Banco Central, IBGE e TSE, podem ser nomeadas na narração quando isso ajuda a identificar o dado, documento ou metodologia usado; continue separando dados verificáveis de interpretações institucionais.

Escolha um único assunto forte. Se o usuário já definiu a pauta, preserve esse assunto e atualize a pesquisa, os dados e o enquadramento; pedir um vídeo novo ou atualizado não autoriza trocar a pauta.

Antes de fechar o roteiro, resolva a embalagem. Título + thumbnail formam uma única decisão editorial e precisam vender exatamente a história que o vídeo entrega.

Crie somente UMA embalagem principal. Não gere alternativas por obrigação.

A thumbnail final não é renderizada pelo Remotion nem montada a partir de uma imagem-base. Depois que o vídeo terminar e for enviado ao Google Drive, o ChatGPT deve gerar a capa completa, já com composição, imagem, texto e acabamento final, pronta para uso no YouTube, seguindo docs/thumbnail-identity.md. O campo packaging.thumbnails[0].visual_prompt deve descrever essa capa completa. Cada capa deve ser única e magnética, mas manter o DNA visual do canal. Depois de gerar, o ChatGPT deve enviar a capa para a mesma pasta do Google Drive criada para o vídeo. A produção da capa só termina quando o arquivo final estiver nessa pasta.

A embalagem precisa:
- **Ter predisposição viral**: baseada em curiosidade irresistível, aversão à perda, quebra de expectativa ou urgência real no bolso do espectador;
- **Zero jargão no título**: nunca use termos como "marcação a mercado", "juro real recorde", "arcabouço", "subvenção" ou siglas obscuras no título. Ninguém clica nisso no YouTube. Traduza para a dor ou consequência direta: "Renda fixa dando prejuízo?", "O banco pode tirar dinheiro da sua conta?", "Demitido e sem FGTS?";
- **Curiosity gap e tensão**: o título e a thumb abrem uma lacuna mental que a pessoa PRECISA clicar para preencher;
- **Sinergia e não repetição**: o título coloca a dúvida/impacto, a thumbnail traz a imagem chocante e um texto de 2 a 4 palavras de alto contraste emocional (ex.: Título: *Renda fixa dando prejuízo? O erro que faz muita gente perder dinheiro* -> Thumb: *RENDA FIXA NEGATIVA?*);
- comunicar uma ideia central;
- ser entendida rapidamente no feed e no celular;
- ter um elemento visual dominante e reconhecível;
- usar texto curto na thumbnail, preferencialmente 2 a 4 palavras quando isso funcionar;
- criar curiosidade, tensão, contraste ou consequência sem enganar;
- fazer título e thumbnail se complementarem;
- evitar excesso de elementos competindo entre si;
- evitar estética genérica de finanças;
- funcionar mesmo para quem nunca viu o canal;
- não prometer algo que o roteiro não entrega.

Preencha packaging.strategy com:
- click_reason;
- visual_focus;
- curiosity_gap;
- mobile_readability;
- anti_clickbait_check;
- repetition_check.

### Gancho Hipnótico nos Primeiros 5 Segundos (Hook)
Esqueça introduções mornas ("Olá, bem-vindos ao canal", "No vídeo de hoje vamos analisar..."). O vídeo deve começar direto no ponto de maior tensão ou na quebra de paradigma:
- Exemplo fraco: "O Tesouro Direto é um investimento muito conhecido e hoje vamos explicar como funcionam os títulos IPCA+..."
- Exemplo viral: "Você investe na renda fixa acreditando que é o lugar mais seguro do Brasil... e de repente o seu saldo diminui. Como um investimento seguro pode dar prejuízo no extrato?"
O espectador decide ficar ou sair nos primeiros 5 a 10 segundos. O gancho precisa prender pela garganta.

Depois construa uma narrativa original que entregue essa promessa. Não reescreva uma reportagem.

Leia `docs/editorial-learning.md` e preencha `editorial.learning_strategy`. Defina público e hipótese, entregue uma descoberta útil na primeira cena e vincule título e capa a fatos, unidades e trechos de entrega/limite. Faça os blocos avançarem pelas perguntas das unidades explicativas. Não esconda toda a resposta até o fim nem alongue para uma duração arbitrária. Valide novo episódio com `npm run ode -- preflight --new-episode`; revisão semântica inclui a embalagem e confere se a prova realmente sustenta a promessa.

A narração deve soar como uma pessoa explicando algo interessante para outra pessoa. Evite cadência de relatório, frases excessivamente formais e blocos com o mesmo ritmo. Use português brasileiro natural, variação de frases, perguntas pontuais, exemplos concretos e conectores conversacionais quando fizer sentido. Não force gírias.

### Texto escrito para ser falado

O roteiro é texto de boca, não texto de artigo. Antes de aprovar cada cena, leia mentalmente como Roberto ou Luana falariam aquilo numa conversa.

### Não datar o vídeo pela data de publicação

O vídeo deve continuar natural se for publicado no mesmo dia, alguns dias depois ou mais tarde. Na narração, não use a data de produção/publicação como referência com expressões como "hoje", "ontem", "amanhã", "hoje, dia 30", "na manhã de hoje", "nesta tarde" ou equivalentes.

Datas de fatos continuam permitidas e são preferíveis quando ajudam a precisão. Exemplos: "em 30 de setembro o Banco Central divulgou...", "o primeiro turno está marcado para 4 de outubro de 2026" ou "nos dados de agosto". "Atualmente" também pode ser usado quando descreve de fato o estado atual do assunto e não funciona como carimbo da data do vídeo.

Evite contagens relativas ligadas à publicação, como "faltam quatro dias para a eleição", quando a mesma informação pode ser dada por uma data objetiva. Diferencie sempre a data do acontecimento da data em que o espectador apertou play.

Regras:
- prefira frases que uma pessoa realmente diria em voz alta;
- misture frases curtas com frases médias; evite sequência de períodos com a mesma estrutura;
- use conectores naturais como "olha só", "na prática", "só que", "agora", "e aqui tem um detalhe", "então", "aí" quando couber, sem transformar isso em bordão;
- "pra" pode ser usado no lugar de "para" quando soar mais natural;
- é permitido começar frase com "e", "mas", "só que" ou uma pergunta curta quando isso melhorar a fala;
- quebre construções burocráticas em duas ou três frases mais simples;
- evite expressões de relatório como "cumpre destacar", "dessa forma", "conforme mencionado", "no que diz respeito", "por conseguinte" e equivalentes;
- não tente deixar toda frase gramaticalmente perfeita se a forma falada brasileira for mais natural e continuar clara;
- não use erros propositais, caricatura regional, excesso de gíria ou vícios repetidos;
- apresentações e CTAs também precisam parecer espontâneos, nunca texto publicitário lido;
- se uma frase estiver correta no papel, mas soar como locução de telejornal ou leitura de prompt, reescreva.

Faça uma última auditoria de oralidade: se o apresentador provavelmente não falaria a frase daquele jeito numa conversa explicativa, ela não está pronta.

## Apresentadores do canal

O canal trabalha com dois apresentadores fixos:
- Roberto: voz predefinida Gemini `Charon`;
- Luana: voz predefinida Gemini `Autonoe`.

O render diário usa somente Gemini 3.8 Live, conforme `worker/voice-policy.json`. Escolha o apresentador antes da síntese e mantenha a mesma voz em todas as cenas: Charon para Roberto ou Autonoe para Luana. Não existe fallback para outro modelo. Cada cena usa uma sessão Live isolada e falhas transitórias podem ser repetidas na mesma cena sem mudar a voz. A direção vocal comum, `tts.delivery`, `tts.cues` e as pronúncias ficam em instruções separadas do roteiro; a saída só é aceita após conferir a transcrição devolvida pelo próprio Live. O WAV bruto é preservado sem EQ, limiter, compressor, normalização ou alteração de pitch/velocidade. Escute o vídeo completo antes de aprová-lo. Regeneração integral exige o input manual do workflow.

Roberto e Luana são personagens editoriais fixos do canal. Priorize sempre Roberto/Charon; Luana/Autonoe só entra quando o assunto for dirigido ao público feminino. Escolher pelo público da pauta, sem alternância estética/automática nem estereótipos simplistas de gênero. Todo vídeo deve ter uma apresentação falada breve do apresentador escolhido. Uma troca de apresentador exige apresentação e contrato coerentes, nova narração com a voz correta e cache compatível; nunca reutilizar o áudio de Luana em um episódio apresentado por Roberto.

### Estabilidade e Coerência Vocal Entre Cenas
Mantenha estilo vocal conversacional consistente (`explain` prioritário) entre todas as cenas. Evite mudanças drásticas de entonação entre cenas consecutivas (ex.: alternar entre `contrast` agressivo e sussurrado), garantindo estabilidade de afinação fundamental (pitch), presença e calor conversacional contínuos. O pipeline equaliza ativamente o loudness em -18.0 dBFS RMS na faixa contínua master, mas a consistência de delivery no roteiro é indispensável para evitar quebras perceptíveis.

### Ritmo Visual e Latência de Abertura das Cenas
- **Beat 0 nos primeiros 2 a 3 segundos**: O primeiro evento visual de cada cena DEVE ser ancorado nas primeiras 5 a 10 palavras do texto (dentro dos primeiros 2 a 3 segundos). Nenhuma tela ou título deve ficar parado por 7 a 16 segundos antes do primeiro acontecimento no palco.
- **Cadência Contínua de Micro-beats (Máximo 4 a 5 segundos)**: Nenhum gráfico, texto ou ilustração pode ficar estático por mais de 4 a 5 segundos enquanto o narrador fala. Divida trechos longos de raciocínio em micro-beats (`focus`, `reveal`, `update`, `reframe` ou `push-in`), mantendo o espectador visualmente engajado a cada nova frase.

A abertura deve nomear o assunto e deixar clara a pergunta que o vídeo vai responder. Explique siglas e conceitos no primeiro uso, com linguagem comum e um exemplo quando necessário. Logo após o gancho, apresente Roberto ou Luana em uma frase natural integrada à explicação. Varie a formulação; não reserve uma cena ou vinheta longa para a apresentação.

Todo vídeo deve incluir um pedido falado breve de inscrição depois de uma primeira entrega de valor, em um respiro natural ou no encerramento. Faça apenas um pedido, ligado ao benefício de acompanhar o canal. Varie a formulação e a posição conforme a narrativa, sem determinar um minuto fixo e sem interromper uma explicação pela metade.

Preencha `editorial.narrative_contract` com três strings copiadas literalmente da narração, cada uma com uma ocorrência única no roteiro:
- `topic_explanation`: trecho que explica o assunto com linguagem comum, nas duas primeiras cenas;
- `presenter_introduction`: apresentação com o nome do narrador escolhido, na primeira cena, depois do gancho;
- `subscription_request`: pedido de inscrição, depois da apresentação e de uma entrega de valor.

O validador exige esse contrato antes da síntese. Os campos identificam trechos do roteiro, sem gerar falas ou inserir conteúdo automaticamente. Revise também o sentido: uma sigla solta não explica o assunto, mencionar Roberto fora de uma apresentação não identifica o narrador, e um CTA não substitui a conclusão. Não há frase pronta, layout ou duração obrigatória para esses momentos.

Antes de fechar o texto da narração, faça uma auditoria explícita de pronúncia. Identifique termos estrangeiros, siglas, nomes próprios, marcas e palavras que possam soar artificiais no TTS. Mantenha sempre a grafia correta no roteiro, no vídeo e na publicação; a adaptação é somente para a fala.

Quando houver risco de pronúncia, preencha no nível raiz do VideoProject:
- speech.pronunciations: mapa "termo escrito" -> "forma falada em português brasileiro";
- speech.ignore_pronunciation_terms: somente para termos que parecem arriscados, mas cuja leitura padrão já foi validada e deve permanecer.

Exemplo: "bets" continua escrito como bets, mas pode receber a forma falada "bétes". Não invente pronúncias para palavras que você não consegue justificar. O pipeline executa uma auditoria antes do TTS e interrompe a geração do áudio quando encontra um termo de risco conhecido sem tratamento, evitando descobrir o problema apenas depois do render.

O início precisa criar interesse imediatamente. Use curiosidade, contraste, consequência e especificidade quando forem sustentados pelos fatos.

Não use falsa urgência, promessa de ganho, previsão tratada como certeza ou título que o vídeo não entrega.

Faça também uma auditoria de adequação ao YouTube antes de fechar a embalagem e o texto final. Não trate isso como uma lista mágica de "palavras proibidas" ou "shadowban". O risco depende do tema, do contexto, do foco, do tom e de como título, thumbnail, descrição e vídeo apresentam o assunto.

Regras editoriais para adequação ao YouTube:
- evite palavrões e linguagem obscena em título e thumbnail; no roteiro, só use se forem realmente necessários ao contexto;
- temas sensíveis como medicamentos, drogas, violência, sexo, morte, golpes, crimes, armas e saúde podem ser cobertos quando houver finalidade informativa, documental, científica ou econômica, mas sem promoção, instrução de abuso, glorificação ou sensacionalismo;
- nomes de medicamentos ou marcas não são automaticamente proibidos. Se forem essenciais ao assunto, use-os de forma factual e contextualizada, sem promessa de resultado, indicação médica ou alegação de tratamento não sustentada;
- em saúde, não faça diagnóstico, prescrição ou alegação que contradiga autoridades de saúde;
- em finanças, não faça promessa de lucro, enriquecimento ou recomendação individual de investimento;
- evite imagens chocantes, sangue, drogas em uso, nudez, armas em destaque ameaçador e outras representações desnecessariamente gráficas na thumbnail;
- se um termo sensível for importante para busca e compreensão, prefira contexto claro a censura artificial. Não substitua automaticamente palavras por símbolos;
- se a embalagem aumentar desnecessariamente risco de monetização ou política, reformule título, texto da thumbnail e conceito visual sem perder a verdade da história.

Preencha editorial.youtube_suitability com:
- risk_level: low, medium ou high;
- sensitive_topics;
- context_notes;
- title_thumbnail_safe;
- monetization_notes.

Preencha também packaging.strategy.youtube_safety_check explicando por que título e thumbnail estão adequados ao tema e ao contexto.

SEO da publicação:
- produza uma descrição única para cada vídeo;
- identifique uma palavra-chave principal e termos secundários realmente relacionados;
- use a palavra-chave principal naturalmente no título quando fizer sentido e nas primeiras linhas da descrição;
- as primeiras duas linhas devem explicar com clareza o que o espectador vai encontrar no vídeo, sem enrolação;
- inclua sinônimos e termos relacionados de modo natural, nunca como bloco de palavras-chave;
- não faça keyword stuffing;
- não encha a descrição de tags; tags têm importância secundária e só devem existir quando forem úteis, por exemplo para grafias alternativas;
- a descrição não pode conter links. Capítulos válidos e uma seção `Bases do vídeo:` serão acrescentados pelo pipeline com apenas os títulos das fontes; créditos de imagens são textuais, sem URLs. Manter URLs somente nos registros internos de pesquisa. Escolher imagens cuja licença permita esse formato de crédito.

Preencha publication.seo com:
- primary_keyword;
- secondary_keywords;
- search_intent;
- description_strategy.

A descrição em publication.description deve sair pronta para publicação e otimizada para busca, mantendo linguagem natural.

## Embalagem de descoberta: título e descrição

Leia e siga obrigatoriamente `docs/youtube-packaging.md` antes de fechar `packaging` e `publication`.

Para o título:
- front-load: coloque a palavra-chave principal ou o assunto reconhecível nas primeiras 3 a 5 palavras sempre que soar natural;
- mire em cerca de 45 a 65 caracteres, preservando o limite técnico de 100;
- traduza jargão para impacto real: custo, prazo, limite, segurança, imposto, bloqueio, risco ou consequência quando houver suporte factual;
- use a lógica `Fato/tema: consequência ou dúvida` quando ela deixar o título mais claro, sem transformar a fórmula em template;
- evite começar com "Entenda", "Saiba", "Veja", número de norma ou nome burocrático quando o assunto puder abrir o título diretamente;
- título e thumbnail devem se complementar. A thumbnail não repete a frase do título.

Para a descrição:
- `publication.description` contém somente 2 a 3 frases curtas de gancho + 3 ou 4 bullets didáticos;
- a palavra-chave principal aparece naturalmente logo no começo;
- não escreva capítulos, fontes, créditos, pergunta de comentários ou hashtags dentro de `publication.description`;
- preencha `publication.engagement_question` com uma pergunta simples ligada ao conteúdo;
- preencha `publication.hashtags` com exatamente 3 hashtags;
- capítulos são calculados pelo tempo real do render;
- o pacote final consolida as fontes uma única vez, sem links.

O validador bloqueia descrições duplicadas ou sem essa estrutura. O pacote final do YouTube monta corpo, capítulos, fontes, créditos, pergunta e hashtags nessa ordem.

## Direção visual própria para cada pauta

Leia `docs/editorial-scene-design.md` antes de preencher o palco. Registre a função, demonstração, dados/assets, transformação e saída de cada cena; compare a composição com a última produção no Git. Zoom, seta em loop e troca de rótulos não substituem a demonstração. Os avisos de composição repetida pedem revisão mesmo quando os beats têm câmera.

Cada vídeo precisa ser único. O motor oferece capacidades de atuação, câmera, texto, SVGs e operações; ele não escolhe a montagem da história. Crie o percurso a partir da pergunta, participantes, relações e consequências da pauta atual. Não aplique a mesma sequência de zoom, cascata, comparação e fechamento a todos os temas. Identidade de voz, paleta e tipografia permanecem reconhecíveis; composição, ritmo e intenção nascem da história.

Converta cada decisão relevante de `visual_direction.motion_language` em um acontecimento executável no palco: `camera`, `moves`, `entrance`, relações, `operation`, grifo, recorte ou `kinetic_type`. Planeje também o desenvolvimento durante a fala: `actuation` faz um objeto compatível agir, `sustain` conserva movimento discreto com função e conexões `flow`/`pulse` mantêm uma relação ativa. Texto descrevendo movimento não anima a cena; contorno desenhado não demonstra uma ação. Uma pausa também é uma decisão: manter a câmera e dar tempo de leitura quando a informação pede. Câmera automática e movimento sustentado só entram quando explicitamente escolhidos; não servem como substituto de storyboard.

Consulte o diagnóstico de direção emitido por `validate:editorial`. Ele identifica o que será executado e avisa sobre repetição de spotlight, durações uniformes e ausência de atuação específica. Use esses avisos como perguntas de revisão, sem cotas de efeitos ou obrigação de mudar um movimento que ainda explica bem a mesma relação.

Antes de escolher cenas e microcenas, crie uma direção visual específica para a história atual. A identidade do canal é o DNA, não um template. Consulte `docs/visual-history.md` somente para identificar padrões recentes que NÃO devem ser repetidos; nunca use esse histórico como molde de pauta, roteiro ou estrutura.

Consulte também `docs/editorial-motion-library.md` e `docs/photography-narrative.md`. Eles descrevem capacidades disponíveis, não uma sequência obrigatória. Escolha só o que melhora a explicação daquela pauta.

Preencha `visual_direction` com:
- `concept`: a ideia visual que traduz esta história;
- `world`: minimal, digital, industrial, documentary, market, network ou paper;
- `secondary_color`: usar sempre `#FFBD19`, o amarelo do canal. Destaques, ícones, linhas e transições não mudam de cor conforme a pauta; preservar preto/carvão e branco como base;
- `motifs`: 2 a 6 objetos, formas ou símbolos próprios desta história;
- `motion_language`: 2 a 6 decisões de movimento/corte que combinam com a narrativa;
- `avoid`: padrões visuais que fariam este vídeo parecer uma cópia dos anteriores.

Regras:
- dois vídeos do canal podem compartilhar paleta, tipografia e acabamento, mas não devem parecer o mesmo projeto com texto e áudio trocados;
- não usar sempre o mesmo fundo, grade, cards, posição de texto, setas, timelines ou entrada;
- linha do tempo não é o formato padrão: use-a somente quando datas ou sequência temporal explicam o assunto; escolha a composição de cada trecho pela relação que a fala precisa mostrar, e compare o storyboard com o episódio anterior;
- não criar uma biblioteca de “templates fixos” e simplesmente escolher um deles;
- a composição nasce da informação: número pode dominar a tela, fluxo pode virar diagrama espacial, comparação pode dividir o quadro, processo pode transformar a própria cena;
- use o quadro inteiro como espaço narrativo. Card flutuante é exceção, não padrão;
- anotações precisam de região reservada; nunca cobrir informação essencial;
- por padrão, preservar objetos no palco e destacar ou atualizar o alvo da fala;
- não alternar tratamentos apenas para produzir variedade; continuidade da mesma explicação pode repetir a operação;
- cortes e transições precisam ter função narrativa. Hard cut é válido e muitas vezes melhor que um efeito ornamental;
- quando dois momentos tiverem forma, direção, objeto ou ideia em comum, prefira continuidade visual, match de forma ou movimento;
- preserve eye-trace quando isso ajuda a compreensão: o novo foco deve nascer perto de onde o espectador já estava olhando, salvo quando a intenção for provocar ruptura;
- o som pode fazer ponte entre mudanças visuais, mas não deve mascarar uma composição fraca.

Antes de fechar o VideoProject, faça uma auditoria de repetição: se o vídeo puder ser descrito como “o anterior com outro texto”, a direção visual ainda não está pronta.

Confira a execução, além dos nomes: no palco, `behavior: reframe` exige `camera`/`camera_mode: auto` ou `view`/`mark_ids` em uma prova documental; `flow_diagram` exige conexão do alvo; operações exigem dados próprios; `kinetic_type` atua sobre texto em `reveal`/`update` ou `focus` autoral; `depth_photo` exige foto com movimento interno, não um recorte de fonte. A cascata do rótulo editorial é um tratamento pontual e não se aplica à legenda da narração, que entra em bloco completo. A operação pode persistir entre beats. O diagnóstico mostra câmeras/posições declaradas e mudanças planejadas; `hold` e repetir a mesma posição não contam como movimento.

Leia todos os erros e alertas do diagnóstico. Um plano totalmente estático pode servir à leitura documental, mas precisa ser uma escolha consciente do storyboard: confira onde a estabilidade ajuda e onde a relação pede movimento. Não distribua efeitos para cumprir uma cota e não preencha tratamentos diferentes para aparentar variedade. A revisão se apoia no que é renderizado, com tempo de leitura.

### Plano visual persistente — obrigatório para cenas com beats

Aplicar `docs/editorial-evidence.md`: durante a pesquisa, selecionar recortes reais que demonstrem as afirmações. Planejar quando apresentar, destacar, aproximar e retirar cada trecho durante a fala. Usar `source_excerpt`, marcações por região, `emphasis` por frase, gráficos com dados verificados e números dominantes conforme a necessidade da pauta. O runner já captura fontes declaradas com `source_page_url` e `expected_text` literal antes da voz; também aceita capturas reais disponíveis em `research/captures/`. Fotos usam `image_url` HTTPS utilizável e são baixadas pelo worker. Cadastre o material em `visual_assets` e vincule ao palco; uma URL de notícia solta não seleciona uma prova nem é URL de imagem. Não inventar dimensões ou datas de captura. Não copiar a estrutura dos vídeos de referência.

Siga também `docs/editorial-attention.md` para roteiro falado, escolha de imagens, objetos e ícones, texto legível, título e descrição. Essa diretriz vale para todas as próximas pautas. Não mostrar fontes no rodapé; manter fontes e créditos no pacote da descrição. O campo `icon` e `kind: object` estão disponíveis no palco; usar conforme o significado. Uma imagem relevante ou um objeto dominante deve substituir parágrafos quando explica melhor. Não transformar todo bloco em lista de texto.

Siga docs/editorial-continuity.md. O motor usa visual.stage com objetos identificáveis e visual.beats como eventos sobre eles. Cada evento tem anchor literal, target_id, action e prominence. O padrão é contextual. reveal_ids/retire_ids controlam elementos auxiliares em regiões reservadas; moves permite reposicionar mantendo identidade.

Quando a relação pedir um percurso espacial, defina `visual.stage.initial_camera` e câmeras nos beats relevantes como `{x, y, zoom, motion_seconds}`. `x` e `y` são percentuais do palco seguro (0–100), `zoom` vai de 1 a 1,6 e o movimento dura 0,2–2 segundos. Enquadre o objeto alvo inteiro, incluindo rótulo, dado e unidade; a validação rejeita câmera que o corte. Informações que só serão explicadas depois começam com `initially_visible:false` e aparecem por `action:reveal` ou `reveal_ids` no beat correspondente. Não use texto ou dado cortado na borda para antecipar o próximo conteúdo. A câmera deve seguir a informação narrada e parar para leitura. Revise o vídeo real e os quadros intermediários dos movimentos conforme `docs/visual-preview.md`. A prévia silenciosa é opcional; a produção autorizada ocorre na main, sem PR obrigatório.

Não copiar a composição do MED. Definir palco e relações conforme a informação da pauta. Usar fotografia, fluxo, comparação ou texto quando explicam melhor, com identidade do canal preservada.

Headline é intenção editorial; só action:update substitui o label. Evitar duplicar a mesma frase como título e anotação. Não repetir informação já compreendida só para criar outro evento. Permitir pausa de leitura.

Escolha `stage.captions` para acompanhar a fala em blocos normais: aproximadamente três palavras por linha, até duas linhas, com o bloco completo exibido de uma vez e sem sublinhado, karaoke ou animação palavra a palavra. Use os padrões `max_words:6`, `words_per_line:3`, `max_lines:2`, `font_size:64` e `min_free_area_ratio:0.30`, adaptando o limiar entre 0.30 e 0.40 conforme a composição. O contrato aceita `max_words:1..8`, `words_per_line:1..4`, `max_lines:1|2` e `font_size:48..140` por compatibilidade; o renderer limita a legenda a 96 px e agrupa ao menos três palavras quando há fala contínua, sem retomar a palavra isolada dos projetos antigos. A produção gera `scene.audio_captions` e `scene.caption_timing` a partir da narração/áudio; não escrever tempos finais em `daily.json`. Tempos reconhecidos e estimados permanecem distinguidos.

As ilustrações comandam a composição. A legenda só entra numa área livre contígua que já atinja 30–40% do quadro, considerando câmera, entradas, rotas, operadores, objetos, números e documentos. Vazios separados não somam essa área. Não reservar faixa para legenda, promover uma região pequena ou reduzir/mover ilustrações para acomodar texto. Se faltar área suficiente, omitir a legenda naquele momento. `region` e `preferred_side` antigos são aceitos apenas para importar projetos e não podem forçar entrada. Legenda não substitui a relação visual; desabilitá-la quando a prova exigir silêncio visual.

Use `element.surface:none|glow|paper|spotlight` pela função visual, sem envolver tudo no mesmo bloco. Objetos dominantes, mapas de relação, texto grande, provas e composições espaciais devem variar com a pergunta da cena, sem alternância obrigatória. O vazio deixado por um objeto retirado pode servir ao foco, à pausa de leitura ou a uma nova transformação. Uma legenda em bloco só acompanha quando a área livre contígua suficiente já existe; não criar espaço para ela nem preencher toda região por obrigação. `sustain` tem amplitude autoral 0–40, com movimento perceptível limitado ao envelope de até 12% do objeto e tilt de até 4°.

Ícones protagonistas usam `icon_size` explícito de 250–500 px e `content_layout: row | column` conforme o espaço de arte e texto. A geometria preserva o tamanho pedido; reorganize a composição se não couber. `surface: none` também remove a bolha do ícone. `kind: object`, fotos e gráficos usam sua própria região. No Stage, `giant_number` não é contador progressivo e `actuation: count` atua sobre moedas/cédulas; não prometa interpolação numérica. `sustain` aceita breathe/drift/float/tilt; flow/pulse pertencem às conexões.

Fotos e recortes recebem acabamento autoral com suporte, moldura, profundidade, luz e entrada relacionados à pauta. Evitar retângulo branco solto. Preservar pixels, textos, fontes e contexto da evidência; aplicar o acabamento à apresentação sem recriar fatos, encobrir condições ou impor a mesma moldura a todas as cenas.

Não usar treatment como catálogo a alternar. Repetir operações sobre o mesmo objeto é continuidade, não repetição de template. Usar takeover somente com takeover_reason e nunca em sequência. Não criar medidor sem dado real nem comparações ANTES/AGORA quando a relação for outra.

A síntese Gemini não devolve bookmarks de palavras. O runner localiza âncoras no áudio processado com reconhecimento local e critérios de confiança. Cada evento registra `audio-word-alignment` ou uma estimativa explícita quando o reconhecimento não for suficiente. Revise o sincronismo depois do render; nenhuma âncora pode estar ausente, repetida ou fora da ordem da narração.

Palcos não podem ter colisão, nem mesmo nas posições de anotações que ainda vão surgir. O renderer mede texto com fonte fixa; ampliar a região ou reduzir o texto quando não houver espaço. Letras espremidas não são uma solução.

Corrija cada falha de layout preservando a relação explicada. Reorganize os participantes, amplie a região de texto, reserve corredores para setas/operadores e replaneje o intervalo quando necessário. Não apague conexões, câmera ou operações nem substitua uma demonstração por destaque genérico apenas para passar o gate. Verifique que a nova composição ainda mostra origem, destino, condição, comparação ou conta prevista na fala; execute a auditoria completa antes da voz e novamente com o tempo final do áudio.

Som é none por padrão. Escolher poucos eventos com função audível. A foto com papel rasgado é uma variação opcional; recorte limpo continua disponível.

## Ritmo durante a fala

Use âncoras literais para as mudanças de significado e entradas curtas. Depois da entrada, sustente o processo pertinente ou transforme a relação enquanto a fala o desenvolve; dê repouso quando a prova precisar ser lida. Não deixar a explicação inteira sem acontecimentos apenas porque terminou a animação de entrada. Não animar todo elemento nem exigir uma mudança a cada número fixo de segundos. A legenda em bloco normal acompanha o trecho falado somente quando a composição já oferece área livre contígua suficiente; não usar palavra a palavra ou reservar espaço para texto. Conferir a origem dos tempos no alinhamento e o sincronismo no MP4 real.

O fluxo deve avançar junto com a explicação, o mesmo objeto pode mudar de posição e as anotações devem aparecer junto do elemento relevante. Estados anteriores continuam presentes enquanto ajudam a compreensão. Retire informação quando deixar de ser útil.

Use os diagnósticos de transformações e segundos sem eventos como perguntas editoriais. Segundos só existem depois de resolver duração/âncoras; antes disso o relatório não inventa um relógio de fala. Respiração, fluxo e palavras podem conservar atividade sem entregar nova explicação. Aprovação de layout e quantidade de câmeras não demonstram ritmo: assista com áudio ao trecho depois da última entrada e ao vídeo inteiro, observando ação do objeto, progressão da ideia, leitura e uso dos vazios. Pausas não são reprovadas por um limite automático.

Uma comparação deve revelar seus lados reais, não usar placeholders. Números mostram valores verificados; prazos podem permanecer estáveis enquanto recebem destaque. Nenhuma barra ou gráfico pode sugerir uma quantidade inventada.

## Sound design editorial

O render diário usa efeitos sonoros discretos para reforçar alguns eventos visuais sem disputar espaço com Roberto ou Luana.

Regras globais:
- a narração é sempre a prioridade e deve permanecer claramente acima dos efeitos;
- usar sons pontuais, não um efeito para cada movimento;
- entradas relevantes podem receber tick, impacto suave ou whoosh curto;
- alertas podem receber um sinal discreto, sem dramatização exagerada;
- processos, listas e timelines podem receber sons apenas nos marcos mais importantes;
- não usar música contínua como padrão;
- evitar repetição mecânica do mesmo efeito em todas as cenas;
- o encerramento recebe uma assinatura sonora curta depois do fim da narração, com cauda visual suficiente para não terminar de forma seca;
- os efeitos do fluxo são gerados internamente pelo projeto, sem depender de arquivos aleatórios ou material externo;
- sound design deve reforçar clareza, ritmo e acabamento, nunca virar protagonista;
- efeitos precisam ser perceptíveis em reprodução comum, mesmo em celular, mas sempre abaixo da narração;
- mudanças visuais importantes podem ter um segundo ponto sonoro discreto durante seu desenvolvimento, não apenas na entrada;
- se o efeito ficar inaudível sob a voz, aumente presença seletivamente em vez de colocar mais efeitos.

Não determine previamente a duração. O vídeo termina quando a história estiver completa, sem repetição para aumentar tempo.

A quantidade de cenas deve ser a necessária para explicar o assunto do começo ao fim. Quotas de voz, número de chamadas TTS e tempo de render não são critérios para cortar explicações, reduzir cenas ou encurtar o roteiro. Resolva restrições de produção com cache, espera e retomada; se elas impedirem concluir a síntese, preserve o roteiro completo para a retomada sem trocar de modelo.

Audite:
- assunto e pergunta central claros desde a abertura, com siglas e conceitos explicados no primeiro uso;
- apresentação breve do narrador logo após o gancho e um pedido de inscrição após a entrega de valor;
- resposta à pergunta inicial na conclusão e explicação completa do assunto;
- textos e dados inteiros no enquadramento, sem antecipação recortada de informações futuras;
- afirmações sem fonte;
- números conflitantes;
- exageros;
- falsa urgência;
- promessa não entregue;
- recomendação financeira;
- risco de copyright;
- repetição de estruturas e hooks;
- linguagem artificial ou excessivamente formal;
- trechos que enfraquecem retenção;
- embalagem confusa em tamanho pequeno;
- adequação de título, thumbnail, descrição e roteiro às políticas do YouTube;
- risco de monetização causado por linguagem ou visual sensacionalista;
- descrição fraca para busca, genérica ou com excesso de palavras-chave.

Ao final, entregue somente um JSON válido seguindo o schema VideoProject v1.0 do projeto.


## Branding da thumbnail

Não usar nome do canal, logotipo, ícone ou selo de marca por padrão. A identidade deve vir de tipografia, paleta, contraste e acabamento editorial. Só incluir branding explícito se o usuário pedir.


## Direção da narração e edição em conjunto

Seguir `docs/editorial-voice.md`. Escrever para o ouvido: frases curtas com uma ideia, exemplos concretos e alternância natural entre pergunta, explicação e consequência. Evitar listas lidas, introduções burocráticas e suspense sem resposta. Não copiar bordões ou imitar a voz dos vídeos de referência.

Escrever intenção, contraste e pausas na própria narração. A direção comum de `worker/voice-policy.json`, `tts.delivery` e `tts.cues` são enviados ao Gemini Live como instruções que não fazem parte do roteiro falado. `rate` e `pitch` continuam sem processamento direto no áudio bruto. Associar a entrada de número, recorte ou grifo a uma âncora literal única de `visual.beats`. O alinhamento local usa o áudio real quando houver confiança suficiente, mantendo estimativas explícitas nos demais eventos. Revisar a sincronização no MP4. Reservar tempo de leitura durante a explicação e manter a voz do apresentador e o destaque amarelo da marca.

Dirija a atuação das frases essenciais em `tts.cues`, conforme `docs/editorial-voice.md`: `intent` transmite curiosidade, descoberta, acolhimento, cautela ou convicção; `arc` descreve pergunta, construção, resolução ou contraste; `emphasis_word` escolhe uma palavra literal única do próprio trecho. Selecione essas intenções pelas frases reais deste vídeo, sem distribuí-las como uma sequência obrigatória. A pergunta, a explicação, a ressalva e a conclusão podem ter ritmo e energia diferentes. Preserve todas as palavras do roteiro e a identidade do apresentador.

Cada `tts.cues[].text` é um trecho literal único da narração, com no máximo 160 caracteres e sem atravessar duas frases. Selecione a oração essencial para dirigir a atuação; não copie um parágrafo inteiro. `emphasis_word` deve ser uma única palavra literal do trecho, com grafia e maiúsculas iguais. Corrija uma cue longa mantendo o roteiro completo: encurte apenas o trecho selecionado para a direção, sem truncar a narração.


### Direção de motion design por episódio

- Abra com uma consequência concreta ou uma pergunta específica, nomeie o assunto e mostre um elemento visual pertinente desde o início. Logo após o gancho, identifique o apresentador em uma frase curta integrada à explicação. Não reservar segundos de tela vazia para uma saudação fixa.
- Desenhe um percurso visual para a ideia central: o mesmo objeto pode deslocar-se, mudar de escala ou de função enquanto a relação causal se revela. Indique o que permanece na tela, o que muda e o que o espectador entende em cada beat.
- Faça cada corte, movimento de câmera, linha desenhada, gráfico progressivo ou recorte ter uma função na explicação. Use atuação das partes do SVG e sustentação seletiva quando a relação continua durante a fala. Pausas estáveis são úteis para ler uma prova; movimento constante de cartões não substitui progressão narrativa.
- Use os tipos visuais exigidos pela história, sem cota de formatos e sem proibir a repetição de uma composição que mantém a mesma explicação. Evite a sequência mecânica de título no topo mais cartões em todas as cenas.
- Para gráficos, registre valores observados, datas de cada ponto e uma fonte específica que sustente a série. Nunca invente pontos para dias ou meses futuros. Distinguir PTAX, fechamento comercial e máxima intradiária.
- Recortes de fonte exigem uma URL da página específica, `expected_text` verificável e captura legível. Homepage, índice de notícias ou substituto sintético não são prova documental. Se a evidência não estiver disponível, troque o tratamento visual ou suspenda o plano.
- O palco JSON resolve posição, revelação e atualização. Quando a história exigir morph, travelling, mapa animado ou montagem com ritmo próprio, especifique essa necessidade para uma composição Remotion autoral; não simule a capacidade com vários cartões iguais.


## Contrato de compreensão e produção na main

Leia `docs/editorial-explanation.md` antes de construir o roteiro. Novas produções preenchem `editorial.explanation`: conceitos definidos no momento necessário, exemplos observados/derivados/ilustrativos/analogias com origem e limites, unidades explicativas ligadas a claims e elementos reais, e revisão com trechos correspondentes ao hash do conteúdo atual. Quantidade de strings presentes não demonstra compreensão.

Comece pela pergunta e pelo que muda para o público. Construa o storyboard a partir de participantes, operações e consequências. Demonstre a relação difícil com objetos, conta ou comparação quando útil. Não imponha quantidade de cenas, duração, exemplos ou efeitos. Uma conta hipotética precisa de identificação na fala e na tela; não invente alíquotas ou resultados reais. Regras de unidades, elegibilidade e compensação continuam válidas no exemplo.

Use operações implementadas no beat quando a tela demonstra uma equação ou comparação. Tratamentos com nomes diferentes não substituem acontecimentos visuais. Reserve espaço para SVGs, rótulos das relações e operadores, com fontes mínimas legíveis; não reservar área para a legenda da narração. No palco JSON, as regiões base de elementos distintos não podem se sobrepor mesmo que um comece oculto e o outro seja retirado antes de sua entrada. Se a montagem exigir reutilização de uma região, use transformação do mesmo participante quando o contrato permitir ou implemente uma composição autoral; não declare uma sobreposição que o palco rejeita. A mudança visual acompanha a ideia narrada e preserva o beneficiário quando há mais de um crédito ou fluxo.

Valide antes da voz e revise o significado com evidências: o público identifica a mudança, os participantes, o beneficiário, as condições e o limite? A conclusão entrega o que a abertura e o título prometeram? A automação verifica integridade, proveniência e aritmética; não certifica compreensão ou verdade das fontes por campos preenchidos.

A produção real está autorizada na main. Não exigir PR, integração direta com outra IA, acesso ao PC ou amostras de voz a cada execução. Se o usuário pedir produção direta sem testes, não executar suítes locais/CI, prévias silenciosas ou demos; registrar o que não foi executado e preservar as suítes permanentes. Compilação/typecheck, contratos, assets/fontes e integridade necessários ao render real continuam; não prometer bypass dos gates de produção. O chat com acesso ao GitHub aplica o mesmo contrato; o Actions entrega o MP4 e os relatórios. Corrija os problemas necessários e retome usando o áudio válido. Voz segue exclusivamente `worker/voice-policy.json`: Gemini 3.8 Live, sem fallback ou DSP. Publicação manual.
