# Prompt diário

## Regra de independência editorial

Preserve a pauta aprovada pelo usuário ao atualizar datas, dados ou visuais de um episódio em andamento. Só selecione outro assunto quando a solicitação pedir essa nova escolha.

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

Depois construa uma narrativa original que entregue essa promessa. Não reescreva uma reportagem.

A narração deve soar como uma pessoa explicando algo interessante para outra pessoa. Evite cadência de relatório, frases excessivamente formais e blocos com o mesmo ritmo. Use português brasileiro natural, variação de frases, perguntas pontuais, exemplos concretos e conectores conversacionais quando fizer sentido. Não force gírias.

### Texto escrito para ser falado

O roteiro é texto de boca, não texto de artigo. Antes de aprovar cada cena, leia mentalmente como Roberto ou Luana falariam aquilo numa conversa.

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

O render diário usa somente Gemini TTS. Escolha o apresentador antes da síntese e mantenha a mesma voz predefinida em todas as cenas. O modelo principal é `gemini-3.8-flash-tts`, configurável por `GEMINI_TTS_MODEL` antes do início do vídeo. Primeiro aguarde e tente novamente quando a falha for temporária. Se o principal continuar indisponível, o worker pode completar as cenas pendentes com `gemini-3.1-flash-tts-preview` como fallback, aplicando o tratamento leve e registrando modelo e tratamento por cena. O mesmo nome de voz em modelos diferentes não garante timbre idêntico: escute o vídeo completo e ajuste a continuidade vocal antes de aprová-lo.

Roberto e Luana são personagens editoriais fixos do canal. Todo vídeo deve ter uma apresentação falada breve do apresentador escolhido. A escolha do apresentador deve considerar o assunto, o enquadramento e o público provável do vídeo, sem usar estereótipos simplistas de gênero.

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

## Direção visual própria para cada pauta

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

### Plano visual persistente — obrigatório para cenas com beats

Aplicar `docs/editorial-evidence.md`: durante a pesquisa, selecionar e salvar recortes reais que demonstrem as afirmações. Planejar quando apresentar, destacar, aproximar e retirar cada trecho durante a fala. Usar `source_excerpt`, marcações por região, `emphasis` por frase, gráficos com dados verificados e números dominantes conforme a necessidade da pauta. Capturas precisam estar disponíveis no repositório antes do render. Não basta informar a URL de uma notícia esperando que o motor encontre e capture o trecho sozinho. Não copiar a estrutura dos vídeos de referência.

Siga também `docs/editorial-attention.md` para roteiro falado, escolha de imagens, objetos e ícones, texto legível, título e descrição. Essa diretriz vale para todas as próximas pautas. Não mostrar fontes no rodapé; manter fontes e créditos no pacote da descrição. O campo `icon` e `kind: object` estão disponíveis no palco; usar conforme o significado. Uma imagem relevante ou um objeto dominante deve substituir parágrafos quando explica melhor. Não transformar todo bloco em lista de texto.

Siga docs/editorial-continuity.md. O motor usa visual.stage com objetos identificáveis e visual.beats como eventos sobre eles. Cada evento tem anchor literal, target_id, action e prominence. O padrão é contextual. reveal_ids/retire_ids controlam elementos auxiliares em regiões reservadas; moves permite reposicionar mantendo identidade.

Quando a relação pedir um percurso espacial, defina `visual.stage.initial_camera` e câmeras nos beats relevantes como `{x, y, zoom, motion_seconds}`. `x` e `y` são percentuais do palco seguro (0–100), `zoom` vai de 1 a 1,6 e o movimento dura 0,2–2 segundos. Enquadre o objeto alvo inteiro, incluindo rótulo, dado e unidade; a validação rejeita câmera que o corte. Informações que só serão explicadas depois começam com `initially_visible:false` e aparecem por `action:reveal` ou `reveal_ids` no beat correspondente. Não use texto ou dado cortado na borda para antecipar o próximo conteúdo. A câmera deve seguir a informação narrada e parar para leitura. Revise a prévia descrita em `docs/visual-preview.md`, incluindo quadros intermediários dos movimentos, antes do render final.

Não copiar a composição do MED. Definir palco e relações conforme a informação da pauta. Usar fotografia, fluxo, comparação ou texto quando explicam melhor, com identidade do canal preservada.

Headline é intenção editorial; só action:update substitui o label. Evitar duplicar a mesma frase como título e anotação. Não repetir informação já compreendida só para criar outro evento. Permitir pausa de leitura.

Não usar treatment como catálogo a alternar. Repetir operações sobre o mesmo objeto é continuidade, não repetição de template. Usar takeover somente com takeover_reason e nunca em sequência. Não criar medidor sem dado real nem comparações ANTES/AGORA quando a relação for outra.

A síntese Gemini não devolve bookmarks de palavras. O pipeline estima os instantes pelas âncoras do texto; revisar o sincronismo depois do render e não prometer alinhamento exato. Nenhuma âncora pode estar ausente, repetida ou fora da ordem da narração.

Palcos não podem ter colisão, nem mesmo nas posições de anotações que ainda vão surgir. O renderer mede texto com fonte fixa; ampliar a região ou reduzir o texto quando não houver espaço. Letras espremidas não são uma solução.

Som é none por padrão. Escolher poucos eventos com função audível. A foto com papel rasgado é uma variação opcional; recorte limpo continua disponível.

## Ritmo durante a fala

Use âncoras literais para as mudanças de significado e janelas curtas de animação. Não alongar uma entrada até ocupar quase toda a fala. Não animar cada palavra por obrigação nem exigir uma mudança a cada número fixo de segundos. Conferir manualmente o alinhamento estimado da voz Gemini.

O fluxo deve avançar junto com a explicação, o mesmo objeto pode mudar de posição e as anotações devem aparecer junto do elemento relevante. Estados anteriores continuam presentes enquanto ajudam a compreensão. Retire informação quando deixar de ser útil.

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

A quantidade de cenas deve ser a necessária para explicar o assunto do começo ao fim. Quotas de voz, número de chamadas TTS e tempo de render não são critérios para cortar explicações, reduzir cenas ou encurtar o roteiro. Resolva restrições de produção com cache, espera, retomada e o fallback autorizado; se elas impedirem concluir a síntese, preserve o roteiro completo para a retomada.

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

Escrever intenção, contraste e pausas na própria narração. O worker Gemini não aplica `tts.delivery`, `tts.cues`, `rate` ou `pitch`; esses campos antigos não comprovam direção de atuação. Associar a entrada de número, recorte ou grifo a uma âncora literal única de `visual.beats`. Os tempos são estimados a partir do texto e da duração real, sem bookmarks medidos por palavra; revisar a sincronização no MP4. Reservar tempo de leitura durante a explicação e manter a voz do apresentador e o destaque amarelo da marca.


### Direção de motion design por episódio

- Abra com uma consequência concreta ou uma pergunta específica, nomeie o assunto e mostre um elemento visual pertinente desde o início. Logo após o gancho, identifique o apresentador em uma frase curta integrada à explicação. Não reservar segundos de tela vazia para uma saudação fixa.
- Desenhe um percurso visual para a ideia central: o mesmo objeto pode deslocar-se, mudar de escala ou de função enquanto a relação causal se revela. Indique o que permanece na tela, o que muda e o que o espectador entende em cada beat.
- Faça cada corte, movimento de câmera, linha desenhada, gráfico progressivo ou recorte ter uma função na explicação. Pausas estáveis são úteis para ler uma prova; movimento constante de cartões não substitui progressão narrativa.
- Use os tipos visuais exigidos pela história, sem cota de formatos e sem proibir a repetição de uma composição que mantém a mesma explicação. Evite a sequência mecânica de título no topo mais cartões em todas as cenas.
- Para gráficos, registre valores observados, datas de cada ponto e uma fonte específica que sustente a série. Nunca invente pontos para dias ou meses futuros. Distinguir PTAX, fechamento comercial e máxima intradiária.
- Recortes de fonte exigem uma URL da página específica, `expected_text` verificável e captura legível. Homepage, índice de notícias ou substituto sintético não são prova documental. Se a evidência não estiver disponível, troque o tratamento visual ou suspenda o plano.
- O palco JSON resolve posição, revelação e atualização. Quando a história exigir morph, travelling, mapa animado ou montagem com ritmo próprio, especifique essa necessidade para uma composição Remotion autoral; não simule a capacidade com vários cartões iguais.
