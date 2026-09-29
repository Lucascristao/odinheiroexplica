# Identidade de thumbnails — O Dinheiro Explica

## Princípio

Cada thumbnail deve ser única para a história do vídeo. A identidade do canal vem de sinais visuais recorrentes, não de repetir o mesmo layout.

A capa precisa funcionar primeiro como peça de clique e depois como peça de marca. Nunca sacrificar força editorial para manter um template.

## DNA visual fixo

- base escura em preto/carvão profundo;
- dourado O Dinheiro Explica como cor de assinatura: #FFBD19;
- branco quente para texto principal: #F6F7F8;
- vermelho apenas como cor de tensão/alerta quando o assunto justificar;
- contraste alto e iluminação cinematográfica;
- acabamento editorial/fotográfico;
- evitar aparência genérica de IA, mockup barato ou interface montada;
- não usar nome do canal, logotipo, ícone ou selo de marca na thumbnail por padrão;
- a identidade deve vir de tipografia, paleta, contraste e acabamento editorial, não de branding explícito;
- tipografia pesada, limpa e muito legível em celular;
- espaçamento confortável entre letras, sem compressão agressiva;
- um foco visual dominante e, no máximo, um apoio secundário.

## O que deve variar em toda capa

A composição, o enquadramento, o objeto ou personagem central, a direção da luz, a escala do assunto, a cor secundária, a posição do texto, a metáfora visual e o recurso de tensão devem nascer da história atual.

Não repetir automaticamente fórmulas de capas anteriores, como celular à direita + texto à esquerda, seta amarela, card bancário, gráfico, dinheiro flutuando ou rosto recortado.

## Regra magnética

Antes de gerar a thumbnail, resolver internamente:
1. qual pergunta, consequência ou tensão faz alguém querer clicar;
2. qual imagem comunica isso em menos de um segundo;
3. como texto e imagem se complementam sem repetir a mesma informação;
4. se a capa continua compreensível reduzida ao tamanho de um celular;
5. quais elementos podem ser removidos sem perder a ideia;
6. se o conceito parece genérico de finanças;
7. se está parecido demais com alguma capa anterior do canal.

Se parecer genérica ou repetitiva, refazer o conceito antes de gerar.

## Texto

- preferir 2 a 4 palavras;
- até 5 somente quando necessário;
- headline curta, concreta e legível;
- título do YouTube e thumbnail se complementam;
- evitar subtítulos pequenos;
- evitar duas frases concorrentes;
- evitar letter-spacing negativo agressivo;
- nenhuma palavra pode ficar espremida ou com letras visualmente coladas.

## Decisão de clique e precisão

Escolher um instante visual de tensão relacionado ao que o vídeo realmente entrega. Pensar título e capa como uma única promessa: título identifica o assunto e a dúvida, capa torna o conflito visível. Não repetir a frase do título na imagem. Usar 2–4 palavras e um objeto dominante; segundo objeto só quando estabelece relação indispensável. Nenhum rodapé, fonte jornalística, dado miúdo ou subtítulo.

Conferir mentalmente a composição em 320 × 180: foco reconhecível, texto imediato, respiro nas bordas e canto inferior direito livre para a duração. Não gerar interface bancária falsa, saldo fictício, documento forjado ou pessoa pública associada a afirmação que o vídeo não faz. Ilustração deve ser reconhecível como ilustração. Não usar cadeado aberto ou dinheiro retornando como garantia quando o assunto é recuperação incerta.

No MED, a tensão é seguir o dinheiro versus conseguir recuperá-lo. Uma trilha interrompida pode comunicar esse limite; não converter automaticamente o conceito em celular + vários nós pequenos. A regra geral é buscar a metáfora mais simples da pauta, sem tornar essa composição um template. O prompt final deve especificar foco, posição e escala do texto, contraste, metáfora, elementos a excluir e exata headline aprovada.

Gerar a capa final completa no ChatGPT após o render, como abaixo. Sem contratar ferramenta paga, fazer testes A/B ou inventar desempenho de clique.

## Entrega

A thumbnail não faz parte do render do Remotion.

1. O vídeo é roteirizado, narrado, renderizado e enviado ao Google Drive.
2. O render termina sem gerar thumbnail automática.
3. Na etapa seguinte da mesma produção no ChatGPT, o ChatGPT confere a pasta criada para o vídeo, usa a embalagem aprovada e este DNA visual e gera a CAPA FINAL COMPLETA.
4. A imagem já deve sair com fotografia/ilustração, texto, composição e identidade visual final. Não é uma imagem-base e não deve incluir nome do canal, logotipo ou ícone, salvo pedido explícito.
5. O ChatGPT envia a capa para a MESMA pasta do Google Drive criada para o vídeo.
6. A capa entregue no Drive é o arquivo final usado no YouTube.

A capa só é considerada concluída depois de estar na mesma pasta do vídeo.

Importante: a geração da capa pelo ChatGPT não acontece dentro do GitHub Actions. Ela é uma segunda etapa da produção conduzida pelo próprio ChatGPT. Não usar polling/monitoramento periódico como parte normal do fluxo; quando a etapa de render já tiver concluído, o ChatGPT deve apenas conferir o resultado e executar a etapa da capa.
