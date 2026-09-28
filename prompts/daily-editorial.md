# Prompt diário

## Regra de independência editorial

Arquivos de piloto, testes, demonstrações e exemplos anteriores existem apenas para validar a tecnologia. Nunca use o assunto, a estrutura narrativa, o título, a thumbnail, os visuais ou o enquadramento de um piloto como molde ou preferência para um novo vídeo. Cada pauta deve nascer da solicitação atual e da pesquisa atual. O piloto do Pix é somente um teste técnico e não deve influenciar a seleção ou a forma dos próximos vídeos.


Pesquise profundamente acontecimentos recentes ligados a dinheiro, empresas, economia, bancos, fintechs, tecnologia com impacto econômico e grandes movimentos empresariais relevantes para o público brasileiro.

Não escolha simplesmente a notícia mais importante. Escolha a história com melhor combinação de novidade, impacto, surpresa, curiosidade, dimensão econômica, reconhecimento, narrativa, potencial visual, qualidade das fontes e potencial evergreen.

Priorize fontes primárias. Confirme afirmações relevantes em fontes adicionais quando necessário. Não faça recomendação individual de compra ou venda de investimentos.

Escolha um único assunto forte.

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
- Roberto: voz masculina pt-BR-MacerioMultilingualNeural;
- Luana: voz feminina pt-BR-ThalitaMultilingualNeural.

Roberto e Luana são personagens editoriais fixos do canal. Use seus nomes de forma natural quando houver apresentação no roteiro. A escolha do apresentador deve considerar o assunto, o enquadramento e o público provável do vídeo, sem usar estereótipos simplistas de gênero.

A apresentação do narrador deve variar naturalmente quando fizer sentido. Não use sempre a mesma frase de abertura. É válido começar pelo gancho e só depois o apresentador se identificar. Evite introduções longas que atrasem a entrega da promessa do vídeo.

Inclua pedido de inscrição apenas quando houver um ponto natural de respiro. Varie a formulação e a posição. Não coloque o CTA sempre no mesmo minuto e não use a mesma frase em todos os vídeos. Em alguns vídeos, se o CTA quebrar a narrativa, prefira apenas um elemento visual discreto ou omita a fala.

Antes de fechar o texto da narração, faça uma auditoria explícita de pronúncia. Identifique termos estrangeiros, siglas, nomes próprios, marcas e palavras que possam soar artificiais no TTS. Mantenha sempre a grafia correta no roteiro, no vídeo e na publicação; a adaptação é somente para a fala.

Quando houver risco de pronúncia, preencha no nível raiz do VideoProject:
- speech.pronunciations: mapa "termo escrito" -> "forma falada em português brasileiro";
- speech.ignore_pronunciation_terms: somente para termos que parecem arriscados, mas cuja leitura padrão já foi validada e deve permanecer.

Exemplo: "bets" continua escrito como bets, mas pode receber a forma falada "béts". Não invente pronúncias para palavras que você não consegue justificar. O pipeline executa uma auditoria antes do TTS e interrompe a geração do áudio quando encontra um termo de risco conhecido sem tratamento, evitando descobrir o problema apenas depois do render.

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
- capítulos e fontes serão acrescentados pelo pipeline depois da descrição editorial.

Preencha publication.seo com:
- primary_keyword;
- secondary_keywords;
- search_intent;
- description_strategy.

A descrição em publication.description deve sair pronta para publicação e otimizada para busca, mantendo linguagem natural.

## Dinamismo visual durante a fala

Não trate uma cena como um slide que anima na entrada e depois fica parado. O movimento deve continuar acompanhando o raciocínio da narração.

Regras globais:
- toda cena longa precisa ter microeventos visuais distribuídos ao longo da duração real do áudio;
- entrada, desenvolvimento, mudança de ponto e saída devem ter resposta visual;
- palavras-chave, números, etapas, linhas, cards, barras, setas e destaques devem aparecer ou mudar quando a fala chega naquele ponto;
- animações internas devem usar a duração proporcional da cena, não tempos fixos pensados para uma cena curta;
- evite mais de aproximadamente 5 a 7 segundos sem alguma mudança visual perceptível, salvo quando uma pausa estática for uma escolha editorial intencional;
- movimento de ambiente, câmera sutil e parallax podem manter vida, mas não substituem eventos que acompanham o conteúdo;
- não mexa em tudo ao mesmo tempo; o resultado deve continuar editorial, elegante e fácil de entender;
- processos devem avançar etapa por etapa, timelines devem progredir ao longo da fala, listas devem ser reveladas em sequência e números/alertas devem ganhar foco em momentos diferentes;
- o final da cena deve preparar visualmente a transição para a próxima.

A regra vale para todos os próximos vídeos e para qualquer tipo de cena criado no futuro. O objetivo é evitar sensação de PowerPoint narrado sem transformar o vídeo em edição caótica.

Não determine previamente a duração. O vídeo termina quando a história estiver completa, sem repetição para aumentar tempo.

Audite:
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
