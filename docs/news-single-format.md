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

Comparar no mínimo 3 títulos por pauta e escolher interesse real, conflito, relevância, clareza e comprovação. Scorecard é **avaliação editorial**, não números de busca ou CTR se eles não foram pesquisados. Título e capa complementares e distintos. Cada vídeo requer capa exclusiva em production/EPISODIO/thumbnail.jpg (ou png), criada aqui no ChatGPT e auditada depois de realmente observar a arte.

## Execução e estados

1. Scout coleta notícias candidatas três vezes por dia; NÃO redige, aprova nem publica automaticamente, pois manchetes RSS não bastam para apuração.
2. Agente/editor seleciona UMA pauta, cruza duas fontes de domínios diferentes, registra no mínimo 4 fatos tipados, escreve opinião em seção clara e indica dois recortes documentais com direitos revisados.
3. Adapter normaliza para VideoProject existente e os gatekeepers validam. Workflow captura documentos com navegador, prepara assets, sintetiza voz Charon, combina áudio contínuo, renderiza Remotion e faz QA.
4. Upload direto YouTube PRIVATE, não Drive. Salva recibo e estado waiting_thumbnail, nunca completed só pelo MP4.
5. A capa é gerada no ChatGPT e inserida junto da auditoria no Git. Push do thumbnail-audit.json aciona news-auto-thumbnail.yml: encontra recibo exato do vídeo privado, valida hashes/projeto/canal e anexa imagem; grava recibo real.
6. Após assistir ao vídeo e inspecionar a capa anexada, aprovação humana pode habilitar publish-news.yml. A confirmação pela API é obrigatória, e possível bloqueio de publicação pela auditoria do projeto YouTube Data API não é contornado.

Esta implementação é de PRODUÇÃO PRIVADA e testes reais; não anunciar três vídeos por dia totalmente autônomos ou publicação pública enquanto isso não for comprovado.


## Direção aprovada: comentário com a prova na tela

**Somente para ode-news-single.** A matéria real, fotografia, gráfico ou relatório é protagonista e pode ocupar **100% da resolução 1920×1080**. Sem painel lateral, cabeçalho obrigatório, faixa escura "IMAGEM DE ARQUIVO", texto repetido ou slides de comentários. Roberto narra e opina enquanto a imagem relevante permanece na tela. O bloco editorial *opinion* continua marcado nos metadados e no discurso, mas **não gera uma tela própria**; deve reutilizar a evidência pertinente do bloco anterior, ou outra fonte visual explicitamente referenciada.

**Matéria de portal:** capturar bloco editorial autêntico amplo em viewport de desktop, com manchete e contexto, não apenas um parágrafo isolado. Abrir mostrando o conjunto com o portal perceptível; só depois selecionar, em momentos ancorados na voz, regiões de zoom ou grifo **quando coordenadas forem conferidas no print real**. O motor preserva os pixels autênticos; não recria uma falsa página para "embelezar" capturas bem-sucedidas.

**Fotografias:** podem preencher 100% do quadro em cover, com assunto preservado, sem faixa automática de foto de arquivo e sem títulos decorativos. Créditos/licenças permanecem nos metadados. Cenas com foto e recortes podem permanecer estáveis enquanto a narração comenta; movimento opcional, discreto.

**Relatórios, slides e gráficos:** mostrar documento original grande, depois marcações contextuais (seta, caixa, grifo, foco) sobre regiões verificadas. Duas reportagens podem ser comparadas em composição explícita, desde que ambas estejam verificadas e identificáveis. Nada de valores imaginários ou falsos recortes. Transições funcionais, sem trocar a cada frase.

**Fallback quando a captura falhar:** reconstrução editorial somente se houver título e resumo previamente apurados, vinculação factual, URL, fonte e data. Mostrar "RECONSTRUÇÃO EDITORIAL / NÃO É PRINT DO PORTAL" claramente e salvar procedência. Jamais simular logotipo/layout do jornal, incluir aspas falsas ou apresentar reconstrução como print.

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
