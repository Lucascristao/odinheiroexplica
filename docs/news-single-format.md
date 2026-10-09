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


## Composição principal atualizada: notícia domina a tela

**Matéria, print ou fotografia ocupa cerca de 80% a 95% da área total do vídeo**, usando um palco próprio com margens reduzidas sem alterar os explicativos. Roberto explica pela voz, sem painel lateral fixo. Uma pequena faixa superior contextual pode existir, mas não disputa com o documento. Alternar materiais jornalísticos, imagens reais e gráficos somente quando a narrativa ganhar informação. Movimento suave de câmera ou destaque deve acompanhar a fala, sem cortes frenéticos, palavras cortadas ou distorção do texto.

**Fallback documental seguro:** tentar a captura autêntica antes. Se houver falha de portal, carregamento, extração ou qualidade visual, gerar uma composição editorial SOMENTE quando o episódio já contiver manchete e resumo revisados, ligados a uma fonte e a fatos verificados. Mostrar claramente “RECONSTRUÇÃO EDITORIAL” e “NÃO É PRINT DO PORTAL”, editoria, fonte e data. Gerar registro de procedência separado com URL, data e erro. Não copiar layout/logotipo original, não inventar aspas e não reproduzir matéria inteira. Sem resumo verificado o render deve falhar.

**Fotos não saem do fluxo.** Continuam disponíveis com créditos e licenças; URLs alternativas só podem representar a mesma foto. Nunca substituir por foto de outro evento sem atualização editorial.

**Direitos de citação, sem licença aberta obrigatória:** o print de matéria usado em contexto de notícia, citação ou crítica pode ser apropriado em certas condições da Lei 9.610/1998, art. 46, III, dependendo da extensão necessária, da identificação de autor e origem e do contexto. Não interpretar como licença automática para reutilização de fotos inteiras, vídeos ou matéria completa. Capturar o trecho mínimo efetivamente comentado, guardar URL, data/crédito e objetivo editorial. **Fotografias de contexto são opcionais:** quando usadas apenas para ilustrar, preferir licenças verificadas; fotos não licenciadas só se a própria imagem for indispensável ao comentário/crítica específica, com justificativa. Nunca exigir quota fixa de fotos. O gate principal é variedade visual relevante, não quantidade de imagens licenciadas.


## Cadência visual aprovada: notícia ≠ vídeo explicativo

**Não forçar muitas trocas visuais.** Um print, reconstrução identificada ou fotografia ocupa quase toda a área útil enquanto Roberto comenta o acontecimento. A narração guia a compreensão; não existe obrigação de painel lateral, de alternar esquerda/direita nem de atualizar texto a cada frase. As frases curtas podem surgir discretamente na faixa superior, sem cobrir a prova. Capturas documentais são estáveis para leitura, com aproximações discretas e intencionais; imagens fotográficas podem receber um leve movimento de câmera. Alternar documento, fotografia licenciada e gráficos quando a narrativa acrescentar contexto ou dados, não por uma cota visual. O comentário opinativo pode usar palco editorial aberto, distinto da evidência documental. **Duas fontes visuais independentes** são exigidas para a mesma pauta; não usar duas capturas do mesmo veículo como se fossem confirmação externa. Se portal bloquear captura, buscar recorte autêntico por outro meio permitido; só usar reconstrução editorial **claramente rotulada** com resumo pré-verificado e fonte, sem simular a página original. Este formato pertence apenas à linha ode-news-single.

**Recortes muito rasos:** quando um print original é largo e baixo demais para ocupar o vídeo sem distorcer ou cortar a manchete, o motor preserva o PNG original e incorpora seus pixels intactos numa apresentação editorial identificada, com título e contexto já verificados e fonte/data legíveis. Os arquivos de origem permanecem verificáveis por SHA-256. Essa composição não é um print do site, e o rótulo precisa dizer “LEITURA EDITORIAL DA MATÉRIA / COM RECORTE ORIGINAL”.
