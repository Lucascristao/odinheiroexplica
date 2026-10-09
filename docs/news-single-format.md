# Novo formato: notícia única e comentada (09/10/2026)

**Vigente:** até três vídeos por dia, cada vídeo com UMA notícia central; não um giro. Contratos: news/episodes/*.json, worker/news_single_project.py, render-news-single.yml. O multiassunto news/editions é histórico, não produzir novos episódios nesse padrão. Nunca modificar o explanatory video/data/daily.json.

## Pesquisa da referência ANCAPSU / Peter Turguniev

Fontes consultadas:
- https://ancapsu.com/site/videos e https://ancap.su/links, site oficial: notícias frequentes com comentário libertário e manchete específica por vídeo.
- https://ancapsu.substack.com/p/geracao-de-novos-empregos-na-area (14/09/2026): introdução coloquial, notícia, reação própria, interpretação e exemplos.
- https://ancapsu.substack.com/p/elite-aristocratica-socialista-descobre (22/09/2026): debate sobre decisão pública, sarcasmo e consequências alegadas.
- https://ancapsu.substack.com/p/e-a-economia-estupido-crescimento (15/09/2026): argumentos em forma de conversa, comparações, perguntas retóricas e opinião explícita.
- https://wikilibertaria.fandom.com/pt-br/wiki/ANCAP.SU_(Canal) como fonte SECUNDÁRIA da evolução de múltiplas notícias para matéria central e de estilos de thumbnails.

Modelar **princípios do gênero**: um acontecimento, título com tensão verificável, narrador com leitura própria, argumento e evidência. Não copiar bordões, trejeitos, voz, identidade, fotos, insultos ou textos do Peter. Não houve análise quadro a quadro do interior dos vídeos; o tratamento audiovisual abaixo é uma direção ORIGINAL para O Dinheiro Explica, não medição da cadência ANCAPSU.

## Roteiro e opinião

O Roberto (Charon / Gemini Live) fala como brasileiro conversando, com comentários fundamentados e uma perspectiva econômica à direita, especialmente liberal. Estrutura não mecânica: gancho verdadeiro; prova; explicação concreta; leitura crítica/sarcasmo quando convier; contrapontos e incertezas; conclusão. Distinguir fatos, projeções e opinião em todos os casos. Não concluir que proposta de imposto = imposto já cobrado. Sarcasmo não substitui prova e não precisa aparecer em todas as frases. Perspectivas relevantes contrárias merecem representação fiel.

## Identidade visual e direitos

Pelo menos dois materiais documentais por pauta, com URL HTTPS, frase esperada no documento, atribuição e verificação de uso. Priorizar comunicados, manchetes e recortes curtos contextualizados. Não copiar fotos inteiras de imprensa sem licença. Worker com Playwright captura trechos, falha caso fonte não seja localizada e prepara os recortes para Remotion. Visual documental acompanha a voz e intercala gráficos e elementos próprios; proibir slides estáticos de texto como substituto da notícia. Fundo carvão, amarelo #FFBD19 e tipografia branca #F6F7F8; preservar identidade sem imitar concorrente. Sem textos falsos ou fotografias geradas apresentadas como prova.

## Títulos, capa e audiência

Comparar no mínimo 3 títulos **realmente distintos** para cada notícia, e escolher a alternativa com maior avaliação editorial registrada (1 a 5). O título deve ser jornalístico, compreensível e com curiosidade específica, jamais uma manchete burocrática: identificar o acontecimento cedo e provocar uma pergunta ou contraste cuja resposta esteja demonstrada no próprio roteiro. Explorar a diferença entre aparência e realidade, a consequência prática, a decisão inesperada ou um detalhe verificável, sem fabricar segredo, fraude, urgência, impacto ou números. Evitar aberturas frias como "Entenda", "Saiba mais" e "Análise de", quando não acrescentarem tensão. Variar a estrutura de um assunto para o seguinte para que o canal não repita fórmulas. Registrar no scorecard por que a vencedora é mais clara, concreta e atraente e onde o roteiro comprova sua promessa. Scorecard é **avaliação editorial**, não números de busca ou CTR se eles não foram pesquisados. Título e capa complementares e distintos. Capa personalizada é OPCIONAL nas notícias autônomas: se a tarefa do ChatGPT conseguir criá-la, inspecioná-la e versioná-la, anexar ao vídeo. Se não conseguir, publicar com miniatura automática do YouTube. Não usar Gemini API para a capa.

## Execução e estados

1. ChatGPT Tasks inicia às 06h, 10h e 18h America/Fortaleza; pesquisa e redige com suas próprias ferramentas, sem Gemini API editorial. Os antigos crons `news-autonomous-editor.yml` e `news-scout.yml` não devem ser agendados.
2. Agente/editor seleciona UMA pauta, cruza duas fontes de domínios diferentes, registra no mínimo 4 fatos tipados, escreve opinião em seção clara e indica dois recortes documentais com direitos revisados.
3. Adapter normaliza para VideoProject existente e os gatekeepers validam. Workflow captura documentos com navegador, prepara assets, sintetiza voz Charon, combina áudio contínuo, renderiza Remotion e faz QA.
4. Upload direto YouTube PRIVATE, não Drive. Salva recibo. Para `autonomous_fact_checked`, o QA e a publicação programada são obrigatórios; capa é opcional. MP4 isolado nunca comprova publicação.
5. Se uma capa nativa do ChatGPT estiver disponível, validada e enviada antes do render, a Action pode anexá-la com recibo. Sem capa válida, não gerar por Gemini nem atrasar a edição; usar a miniatura automática do YouTube.
6. Com autorização permanente já concedida, `worker/news_autonomous_schedule.py` programa publicação sem aprovação por episódio, somente após apuração factual real, QA `pass`, canal validado e recibo do vídeo. A confirmação pela API é obrigatória; bloqueios OAuth/YouTube não são contornados. Edições manuais/pilotos preservam seus próprios gates.

Esta implementação busca produção autônoma; não afirmar que a publicação pública ocorreu até que o vídeo esteja confirmado `public` pelo YouTube. Consulte `docs/news-chatgpt-task.md`. Gemini API é exclusiva da voz Gemini 3.8 Live.


## Direção aprovada: comentário com a prova na tela

**Somente para ode-news-single.** A matéria real, fotografia, gráfico ou relatório é protagonista e pode ocupar **100% da resolução 1920×1080**. Sem painel lateral, cabeçalho obrigatório, faixa escura "IMAGEM DE ARQUIVO", texto repetido ou slides de comentários. Roberto narra e opina enquanto a imagem relevante permanece na tela. O bloco editorial *opinion* continua marcado nos metadados e no discurso, mas **não gera uma tela própria**; deve reutilizar a evidência pertinente do bloco anterior, ou outra fonte visual explicitamente referenciada.

**Acabamento visual de recortes:** no renderizador do formato `ode-news-single`, colocar cada imagem documental capturada dentro de uma moldura editorial discreta, com sombra, contorno fino, cantos suaves e fundo de apoio desfocado/escurecido derivado do próprio recorte. O documento original é preservado, sem redesenhar seu texto, sem tarjas explicativas e sem cabeçalho falso; zoom e grifos só sobre coordenadas efetivamente verificadas. O tratamento deve se adaptar a imagens estreitas ou largas, sem letras cortadas nem grandes faixas pretas vazias. Fotografias de notícia continuam em quadro limpo, sem moldura obrigatória. Para texto AUTORAL que seja sobreposto futuramente (não parte de um print), usar fundo/padding/sombra e conferir contraste, sem encobrir documentos.

**Matéria de portal:** capturar bloco editorial autêntico amplo em viewport de desktop, com manchete e contexto, não apenas um parágrafo isolado. Abrir mostrando o conjunto com o portal perceptível; só depois selecionar, em momentos ancorados na voz, regiões de zoom ou grifo **quando coordenadas forem conferidas no print real**. O motor preserva os pixels autênticos; não recria uma falsa página para "embelezar" capturas bem-sucedidas.

**Fotografias:** podem preencher 100% do quadro em cover, com assunto preservado, sem faixa automática de foto de arquivo e sem títulos decorativos. Créditos/licenças permanecem nos metadados. Cenas com foto e recortes podem permanecer estáveis enquanto a narração comenta; movimento opcional, discreto.

**Relatórios, slides e gráficos:** mostrar documento original grande, depois marcações contextuais (seta, caixa, grifo, foco) sobre regiões verificadas. Duas reportagens podem ser comparadas em composição explícita, desde que ambas estejam verificadas e identificáveis. Nada de valores imaginários ou falsos recortes. Transições funcionais, sem trocar a cada frase.

**Fallback quando a captura falhar:** reconstrução editorial somente se houver título e contexto previamente apurados, vinculação factual, URL, fonte e data. O quadro deve usar identidade própria do O Dinheiro Explica (não o layout do portal), com crédito de fonte discreto, sem tarjas técnicas, sem os dizeres "RECONSTRUÇÃO EDITORIAL", "NÃO É PRINT DO PORTAL" ou "Resumo editorial, não reprodução da página". A procedência detalhada e a identificação inequívoca como reconstrução ficam no arquivo `.provenance.json` e nos metadados/fontes do episódio. Jamais inventar print, logotipo/layout do veículo, aspas ou evidência documental; preferir a captura autêntica sempre que possível.

**Não herdar layout de outros formatos:** o modo de tela inteira é ativado apenas nos palcos de notícia. O motor evergreen mantém sua identidade e margens tradicionais.

**Direitos de citação, sem licença aberta obrigatória:** o print de matéria usado em contexto de notícia, citação ou crítica pode ser apropriado em certas condições da Lei 9.610/1998, art. 46, III, dependendo da extensão necessária, da identificação de autor e origem e do contexto. Não interpretar como licença automática para reutilização de fotos inteiras, vídeos ou matéria completa. Capturar o trecho mínimo efetivamente comentado, guardar URL, data/crédito e objetivo editorial. **Fotografias de contexto são opcionais:** quando usadas apenas para ilustrar, preferir licenças verificadas; fotos não licenciadas só se a própria imagem for indispensável ao comentário/crítica específica, com justificativa. Nunca exigir quota fixa de fotos. O gate principal é variedade visual relevante, não quantidade de imagens licenciadas.


## Cadência visual de comentário jornalístico

Narrador e mídia são uma única cena contínua. Os pontos da narração disparam apenas operações úteis sobre o material em exibição; sem tela de "Análise do Roberto" e sem troca da prova por frases soltas. Segurar uma fonte durante o comentário é melhor que cortes artificiais. O texto da fonte pode ser legível por enquadramento aberto/zoom autorado e controlado, mas não há zoom automático que corte evidência. Fotos não precisam de rótulos de arquivo; créditos e direitos continuam obrigatórios no manifesto. Use outras fontes ou gráficos quando o assunto pedir. Para prints inacessíveis, aplicar fallback claramente identificado sem inventar matéria.

## Descoberta e retenção no YouTube (obrigatório para notícia única)

Foco na pessoa que assiste, **não** em manipular métricas: investigar qual pergunta concreta move a pauta, qual fato novo responde à pergunta e qual contexto rende valor em tela. O YouTube descreve recomendações como personalização + satisfação + performance entre os espectadores, enquanto títulos/miniaturas/descrições ajudam o público a decidir clicar. Tags são secundárias; não investir tempo em stuffing ou hashtags genéricas.

**Antes da produção**, preencher `discovery_strategy` no episódio: `viewer_intent`, `search_query`, `recommendation_angle`, `first_payoff` (trecho literal da abertura), `promise_proof`, `audience_hypothesis`, `thumbnail_complement`, `verification_limits`. Escrever `publication_description` em linguagem natural com palavra-chave relevante, promessa entregue e bullets úteis. Registre termos secundários apenas se pertinentes. Três títulos com ângulos editoriais distintos, capa magnética complementar e auditoria de promessa. O motor deve bloquear descrições ou promessas não sustentadas. **Não inventar** volume de busca, CTR, tendência, ranking de assuntos ou dados do Studio.

**Primeiros segundos**: uma pergunta de interesse real e uma primeira resposta concreta antes de alongar a análise. O roteiro entrega a promessa, prova antes de opinião e mantém continuidade visual para favorecer compreensão. Nada de exposição repetitiva, vinheta longa ou pedido de inscrição antes de entregar valor.

**Após publicação humana**: medir impressões e CTR por origem de tráfego (Home, sugeridos, pesquisa), duração média e retenção inicial no mesmo recorte temporal. Verificar 72h, 7 e 28 dias se houver dados do Studio; não atribuir melhora a uma única mudança nem usar visões públicas de concorrentes como se fossem seus dados privados. Mudar embalagem só quando a hipótese for verificável. **Viralidade nunca é garantida.**

Referências oficiais: https://support.google.com/youtube/answer/16533387?hl=pt-BR e https://support.google.com/youtube/answer/146402?hl=pt-BR.

## Evolução de automação autorizada em 09/10/2026

O piloto de notícia única foi aprovado pelo usuário. A autorização permanente para edições futuras é sem aprovação humana por vídeo, somente para o formato ode-news-single. A regra histórica de revisão/publicação manual acima descreve o piloto anterior e continua disponível apenas para episódios de modo manual. Para edições futuras, a fonte operacional de autorização é config/news-autonomy.json.

A tarefa ChatGPT é o único agendamento de redação às 06h, 10h e 18h (America/Fortaleza), produzindo no GitHub no máximo um arquivo news/episodes/AAAA-MM-DD-{manha,meio-dia,noite}.json por janela. O workflow news-autonomous-editor.yml está aposentado e não deve ser reativado. Toda pauta deve ser apurada por ferramentas do ChatGPT e registrada com evidências reais.

render-news-single.yml faz o render, QA, upload PRIVADO e programa a publicação com worker/news_autonomous_schedule.py às 08h, 12h ou 20h, se os recibos, a identidade do canal, o QA e a janela forem válidos. A capa personalizada do ChatGPT é opcional; em sua ausência, usa a miniatura automática do YouTube. A API Gemini é reservada à narração. Não interpretar upload privado ou agendamento como confirmação de vídeo público.

news-verify-publication.yml verifica o status público observado 15 minutos após cada janela; agendamento aceito pela API não é confirmação de publicação pública, especialmente quando a auditoria do projeto YouTube API estiver pendente. O primeiro ciclo real ainda precisa demonstrar sucesso para que se afirme que a rotina foi validada ponta a ponta.
