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

Confira a execução, além dos nomes: no palco, `behavior: reframe` exige `camera`/`camera_mode: auto` ou `view`/`mark_ids` em uma prova documental; `flow_diagram` exige conexão do alvo; operações exigem dados próprios; `kinetic_type` executa cascata somente em `reveal`/`update` de texto; `depth_photo` exige foto com movimento interno, não um recorte de fonte. A operação pode persistir entre beats. O diagnóstico mostra câmeras/posições declaradas e mudanças planejadas; `hold` e repetir a mesma posição não contam como movimento.

Leia todos os erros e alertas do diagnóstico. Um plano totalmente estático pode servir à leitura documental, mas precisa ser uma escolha consciente do storyboard: confira onde a estabilidade ajuda e onde a relação pede movimento. Não distribua efeitos para cumprir uma cota e não preencha tratamentos diferentes para aparentar variedade. A revisão se apoia no que é renderizado, com tempo de leitura.

### Plano visual persistente — obrigatório para cenas com beats

Aplicar `docs/editorial-evidence.md`: durante a pesquisa, selecionar e salvar recortes reais que demonstrem as afirmações. Planejar quando apresentar, destacar, aproximar e retirar cada trecho durante a fala. Usar `source_excerpt`, marcações por região, `emphasis` por frase, gráficos com dados verificados e números dominantes conforme a necessidade da pauta. Capturas precisam estar disponíveis no repositório antes do render. Não basta informar a URL de uma notícia esperando que o motor encontre e capture o trecho sozinho. Não copiar a estrutura dos vídeos de referência.

Siga também `docs/editorial-attention.md` para roteiro falado, escolha de imagens, objetos e ícones, texto legível, título e descrição. Essa diretriz vale para todas as próximas pautas. Não mostrar fontes no rodapé; manter fontes e créditos no pacote da descrição. O campo `icon` e `kind: object` estão disponíveis no palco; usar conforme o significado. Uma imagem relevante ou um objeto dominante deve substituir parágrafos quando explica melhor. Não transformar todo bloco em lista de texto.

Siga docs/editorial-continuity.md. O motor usa visual.stage com objetos identificáveis e visual.beats como eventos sobre eles. Cada evento tem anchor literal, target_id, action e prominence. O padrão é contextual. reveal_ids/retire_ids controlam elementos auxiliares em regiões reservadas; moves permite reposicionar mantendo identidade.

Quando a relação pedir um percurso espacial, defina `visual.stage.initial_camera` e câmeras nos beats relevantes como `{x, y, zoom, motion_seconds}`. `x` e `y` são percentuais do palco seguro (0–100), `zoom` vai de 1 a 1,6 e o movimento dura 0,2–2 segundos. Enquadre o objeto alvo inteiro, incluindo rótulo, dado e unidade; a validação rejeita câmera que o corte. Informações que só serão explicadas depois começam com `initially_visible:false` e aparecem por `action:reveal` ou `reveal_ids` no beat correspondente. Não use texto ou dado cortado na borda para antecipar o próximo conteúdo. A câmera deve seguir a informação narrada e parar para leitura. Revise o vídeo real e os quadros intermediários dos movimentos conforme `docs/visual-preview.md`. A prévia silenciosa é opcional; a produção autorizada ocorre na main, sem PR obrigatório.

Não copiar a composição do MED. Definir palco e relações conforme a informação da pauta. Usar fotografia, fluxo, comparação ou texto quando explicam melhor, com identidade do canal preservada.

Headline é intenção editorial; só action:update substitui o label. Evitar duplicar a mesma frase como título e anotação. Não repetir informação já compreendida só para criar outro evento. Permitir pausa de leitura.

Escolha `stage.captions` quando palavras da fala ajudarem a conduzir o olhar: `enabled`, `max_words:1|2`, `font_size:72..140`, `preferred_side:auto|left|right|center` e uma `region` percentual opcional. A produção gera `scene.audio_captions` e `scene.caption_timing` a partir da narração/áudio; não escrever tempos finais em `daily.json`. Palavras reconhecidas e estimadas permanecem distinguidas. A tipografia curta adapta-se aos espaços livres conforme câmera, entradas, rotas e operadores; preserva objetos, números e documentos. Legenda não é um parágrafo nem substitui a relação visual. Se a cena exigir silêncio visual para uma prova, desabilite-a por decisão autoral.

Use `element.surface:none|glow|paper|spotlight` pela função visual, sem envolver tudo no mesmo bloco. Objetos dominantes, mapas de relação, texto grande, provas e composições espaciais devem variar com a pergunta da cena, sem alternância obrigatória. O vazio deixado por um objeto retirado precisa continuar tendo função durante a fala: foco, pausa de leitura, palavra sincronizada ou nova transformação, conforme a história. Não preencher toda região apenas porque há espaço.

Não usar treatment como catálogo a alternar. Repetir operações sobre o mesmo objeto é continuidade, não repetição de template. Usar takeover somente com takeover_reason e nunca em sequência. Não criar medidor sem dado real nem comparações ANTES/AGORA quando a relação for outra.

A síntese Gemini não devolve bookmarks de palavras. O runner localiza âncoras no áudio processado com reconhecimento local e critérios de confiança. Cada evento registra `audio-word-alignment` ou uma estimativa explícita quando o reconhecimento não for suficiente. Revise o sincronismo depois do render; nenhuma âncora pode estar ausente, repetida ou fora da ordem da narração.

Palcos não podem ter colisão, nem mesmo nas posições de anotações que ainda vão surgir. O renderer mede texto com fonte fixa; ampliar a região ou reduzir o texto quando não houver espaço. Letras espremidas não são uma solução.

Corrija cada falha de layout preservando a relação explicada. Reorganize os participantes, amplie a região de texto, reserve corredores para setas/operadores e replaneje o intervalo quando necessário. Não apague conexões, câmera ou operações nem substitua uma demonstração por destaque genérico apenas para passar o gate. Verifique que a nova composição ainda mostra origem, destino, condição, comparação ou conta prevista na fala; execute a auditoria completa antes da voz e novamente com o tempo final do áudio.

Som é none por padrão. Escolher poucos eventos com função audível. A foto com papel rasgado é uma variação opcional; recorte limpo continua disponível.

## Ritmo durante a fala

Use âncoras literais para as mudanças de significado e entradas curtas. Depois da entrada, sustente o processo pertinente ou transforme a relação enquanto a fala o desenvolve; dê repouso quando a prova precisar ser lida. Não deixar a explicação inteira sem acontecimentos apenas porque terminou a animação de entrada. Não animar todo elemento nem exigir uma mudança a cada número fixo de segundos. Legendas de uma ou duas palavras podem acompanhar a fala por escolha da cena, sem tornar o vídeo uma transcrição de parágrafos. Conferir a origem dos tempos no alinhamento e o sincronismo no MP4 real.

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

Use operações implementadas no beat quando a tela demonstra uma equação ou comparação. Tratamentos com nomes diferentes não substituem acontecimentos visuais. Reserve espaço para SVGs, legendas, operadores e relações, com fontes mínimas legíveis. No palco JSON, as regiões base de elementos distintos não podem se sobrepor mesmo que um comece oculto e o outro seja retirado antes de sua entrada. Se a montagem exigir reutilização de uma região, use transformação do mesmo participante quando o contrato permitir ou implemente uma composição autoral; não declare uma sobreposição que o palco rejeita. A mudança visual acompanha a ideia narrada e preserva o beneficiário quando há mais de um crédito ou fluxo.

Valide antes da voz e revise o significado com evidências: o público identifica a mudança, os participantes, o beneficiário, as condições e o limite? A conclusão entrega o que a abertura e o título prometeram? A automação verifica integridade, proveniência e aritmética; não certifica compreensão ou verdade das fontes por campos preenchidos.

A produção real está autorizada na main. Não exigir PR, integração direta com outra IA, acesso ao PC ou amostras de voz a cada execução. Se o usuário pedir produção direta sem testes, não executar suítes locais/CI, prévias silenciosas ou demos; registrar o que não foi executado e preservar as suítes permanentes. Compilação/typecheck, contratos, assets/fontes e integridade necessários ao render real continuam; não prometer bypass dos gates de produção. O chat com acesso ao GitHub aplica o mesmo contrato; o Actions entrega o MP4 e os relatórios. Corrija os problemas necessários e retome usando o áudio válido. Voz segue exclusivamente `worker/voice-policy.json`: Gemini 3.8 Live, sem fallback ou DSP. Publicação manual.
