# Apresentação de notícias: referências e aplicação

Revisão iniciada em 10/10/2026, aplicada às notícias futuras em 11/10. Pedido do titular: manter o formato aprovado, melhorar comentário, notícias e dados a partir de Peter/ANCAPSU e Fernando Ulrich, além de título/capa e crescimento do canal.

## Evidência e limites

Foram consultadas as páginas dos canais, títulos e metadados públicos, transcrições publicadas pelo ANCAPSU e descrições/capítulos publicados por Ulrich. Também foram lidas transcrições indexadas de dois episódios de Ulrich. Não houve reprodução integral com áudio dos vídeos de referência. Os anúncios e a conexão do navegador impediram essa escuta. Em 11/10 houve inspeção visual da grade oficial de capas de Ulrich no navegador, inclusive “Vitória histórica!”, “Tem que acabar no primeiro turno!” e “Mais um gol contra de Lula”; isso permite analisar composição, sem atribuir resultados de audiência a seus elementos. Visualizações públicas não são CTR, impressão, retenção ou teste controlado. Os dados do Studio do O Dinheiro Explica não foram recuperados nesta revisão; a causa dos poucos cliques continua uma hipótese.

## Peter / ANCAPSU

- [Clientes de BB e Bradesco relatam problemas com cartão, 04/10](https://ancapsu.substack.com/p/clientes-do-banco-do-brasil-e-bradesco), associado ao [vídeo](https://youtu.be/DbEYt4ecZ9I): abre com uma leitura e uma tensão concreta, passa ao acontecimento e discute implicações para quem usa o serviço. Perguntas coloquiais dão continuidade. Aplicação: uma questão central, comentário próximo da prova e consequência reconhecível. Não adotar automaticamente a ligação causal sugerida entre discurso político e mudanças bancárias.
- [Economia e crescimento, 15/09](https://ancapsu.substack.com/p/e-a-economia-estupido-crescimento), associado ao [vídeo](https://youtu.be/t9NNFNYBjWk): conecta política econômica a compras, comida, crédito e impostos com exemplos e perguntas. Aplicação: explicar o mecanismo e voltar ao bolso. As afirmações políticas da referência não foram incorporadas como fatos do canal.

Na [página do canal](https://www.youtube.com/@ancap_su/videos), títulos observados enfatizam ação, conflito e reação. Aprender a concretude, sem importar caixa alta em excesso, insultos, bordões, voz ou identidade.

## Fernando Ulrich

- [Querem repetir a crise de 2008 agora com IA?](https://youtu.be/BJPogOG1b-0): a [descrição e capítulos publicados pelo criador](https://podcasts.apple.com/br/podcast/querem-repetir-a-crise-de-2008-agora-com-ia/id1508282898?i=1000783101319) organizam anúncio, ativos, financiamento, custo, quem suporta o risco e comparação histórica. A [transcrição indexada](https://podscan.fm/podcasts/fernando-ulrich/episodes/querem-repetir-a-crise-de-2008-agora-com-ia) distingue intenção de investimento e dinheiro efetivamente comprometido. Aplicação: não converter anúncio em resultado; explicar quem recebe, paga e assume risco. Não afirmar que assistimos aos quadros mencionados na transcrição.
- [Sensação de inflação e custo de vida](https://youtu.be/OGl6VcYVu9I): a [transcrição indexada](https://podscan.fm/podcasts/fernando-ulrich/episodes/sensacao-de-inflacao-nada-e-custo-de-vida-alto-pra-miriam) parte da diferença entre taxa e nível de preços, contextualiza uma fala e passa a comparações mensais/anuais. Aplicação: definir unidade, base e período antes de comentar o número; confrontar a frase com o mecanismo, preservando contexto. O áudio completo não foi conferido.

Na [página do canal](https://www.youtube.com/@FernandoUlrichCanal/videos), observamos perguntas, contrastes e condições nos títulos. Esse padrão ajuda a formular hipóteses de embalagem, sem comprovar qual elemento causou as visualizações. Na grade visual conferida, rostos são grandes e a expressão é legível, texto branco/amarelo ou vermelho fica em faixa inferior escura, e personagens/objeto da notícia dividem o quadro. Aplicação ao Roberto: foto com luz suave e expressão atenta, enquadramento próximo e destaque real do rosto; preservar a identidade própria e a paleta do canal, sem copiar faces, capas ou afirmações políticas da referência. A primeira composição pequena e com luz dourada forte foi rejeitada pelo titular antes de publicação e substituída.

## Decisões para o O Dinheiro Explica

1. **Abertura:** nomear a notícia e entregar uma primeira descoberta, seguida da pergunta que a análise vai responder. Roberto se apresenta naturalmente depois desse valor; sem vinheta longa ou inscrição antecipada.
2. **Comentário:** usar somente o trecho relevante da reportagem/documento; explicar causa, mecanismo e consequência. Opinião identificada no discurso e nos metadados, com contraponto e condições. Evitar repetir o mesmo resumo em todas as cenas.
3. **Dados:** separar porcentagem de contas, de pessoas e de dinheiro; identificar data, universo e origem. Comparações entre períodos exigem bases compatíveis. Exemplo hipotético explica, sem fingir dado observado. Gráficos futuros precisam dos dados e escalas reais.
4. **Prova em tela:** preservar o documento grande durante a explicação. Zoom e grifo devem nascer de coordenadas conferidas na captura e de trechos literais da fala. O motor aceita `visual_cues`; capturas usadas nessas marcações ficam vinculadas por `capture_sha256` e proveniência. Não existe cota de cortes ou movimentos para simular dinamismo.
5. **Voz:** manter Roberto/Charon em `explain`, com fraseado conversacional, transições de argumento claras e pausas úteis. Não imitar os apresentadores; diagnóstico de ASR e pitch não substitui escuta subjetiva.
6. **Embalagem:** avaliar três ângulos editoriais diferentes e uma promessa comprovável; a capa complementa o título. O rosto fixo do Roberto é hipótese de reconhecimento, implementada em `docs/presenter-identity.md`. Fundo e objeto principal variam conforme a notícia; não reproduzir a mesma grade em todas as capas.

## Medição antes de concluir por que há poucos cliques

| Sinal observado em recortes comparáveis | Hipótese a investigar |
|---|---|
| Poucas impressões | Alcance e adequação da pauta/público; CTR sozinho não explica |
| Impressões suficientes e CTR menor na mesma origem | Clareza e interesse da combinação título/capa |
| Clique razoável e saída inicial forte | Promessa, abertura e entrega de valor |
| Retenção e retornos fracos após a abertura | Explicação, progressão, ritmo e utilidade |

Importar somente números reais do Studio para snapshots de 72h, 7 e 28 dias, conforme `docs/editorial-learning.md`, comparando formato, idade e origem semelhantes. Não preencher dados ausentes como zero nem atribuir causalidade a um vídeo. O [YouTube explica a variação do CTR e cautelas de comparação](https://support.google.com/youtube/answer/7628154?hl=pt-BR). O [teste nativo de títulos/capas](https://support.google.com/youtube/answer/16391400?hl=pt-BR) usa tempo de exibição para escolher resultado e pode ser inconclusivo; nenhum teste A/B foi ativado nesta revisão.

O objetivo de monetização reforça o valor de apuração, explicação e comentário próprios. [A política do YouTube](https://support.google.com/youtube/answer/1311392?hl=pt-BR) avalia originalidade e conteúdo autêntico; não garantir elegibilidade ou receita por adicionar um rosto ou voz de IA.
