# Benchmark visual e plano de evolução 09/10/2026

## Fontes efetivamente analisadas
- Site oficial https://ancap.su/site/videos, catálogo de 08/10/2026: vídeos com uma notícia central e títulos destacando protagonista, contraste e consequência.
- Identidade do canal: https://ancap.su/links, notícias frequentes com viés libertário.
- Exemplos reais https://www.youtube.com/watch?v=V6l4eCZbPZ4 e https://www.youtube.com/watch?v=JUeTEWsl1rs (fevereiro de 2026): títulos de controvérsia tributária, trechos do evento, desdobramento e reação; pesquisa efetuada sobre títulos, metadados e descrição, NÃO quadro a quadro.
- Referência histórica secundária sobre capas: https://wikilibertaria.fandom.com/pt-br/wiki/ANCAPSU. NÃO confundir fonte secundária com comprovação de cadência real de edição.
- Uso documental/direitos: https://www12.senado.leg.br/manualdecomunicacao/guia-de-direitos-autorais e https://support.google.com/youtube/answer/9783148: crédito e finalidade jornalística NÃO autorizam automaticamente qualquer foto ou vídeo de terceiros.
- Notícia do piloto: https://agenciabrasil.ebc.com.br/economia/noticia/2026-10/durigan-preve-envio-de-mp-do-imposto-seletivo-apos-eleicoes. A data, o pronunciamento e as ressalvas devem corresponder ao texto verificado.

## Limitação da investigação externa
Não foi possível obter quadros internos dos vídeos do ANCAPSU através das ferramentas disponíveis. Nenhuma métrica de cortes/tempo de tela ou proporção de imagens é atribuída ao canal; a direção abaixo é uma hipótese criativa ORIGINAL. Uma análise comparativa frame a frame necessita arquivos de referência acessíveis/licenciados, nunca imagens geradas como se fossem screenshots.

## Diagnóstico observado da nossa produção
- Run 37878336687, versão 1: nas amostras do bloco da notícia, caixa e título fixos durante a maior parte do trecho.
- Run 37879484592, versão 2: palavras mudam, mas ícone do pacote e geometria são praticamente constantes. O MP4 de ambas tem 193,9 s e QA técnico com advertências de âncoras visuais estimadas.
- Nenhuma das duas versões multiassunto contém imagem documental da fonte no palco. A mudança de texto é insuficiente para dar aparência jornalística.
- No novo episódio de assunto único o layout foi bloqueado antes da síntese por Zod: o source_excerpt recebeu surface paper e o contrato proíbe esse acabamento.

## Mudanças propostas e realizadas
1. Uma pauta central, com headline verificada, contraste e comentário opinativo identificável do Roberto. Sem copiar estilo pessoal, voz, scripts ou bordões de outro comunicador.
2. Pelo menos dois recortes documentais reais com URL exata, trecho verificado e atribuição, capturados por Playwright. Não gerar fotos que pareçam provas.
3. Três composições sem repetir o template: abertura/explicação com objeto próprio; evidência em painel documental; opinião em palco aberto só com ideias-chave.
4. Remotion usa a duração e as âncoras da fala. Não forçar número imaginado de cortes a cada 3 segundos.
5. Antes da voz, o adaptador news_single_project e scripts/validate-news-single.ts testam cada cena contra o MESMO schema Zod do Remotion. Mensagens devem apontar cena e propriedade específicas.
6. A arte exclusiva da capa é gerada no ChatGPT, auditada com hash e enviada automaticamente ao YouTube privado quando houver imagem aprovada. Publicação só após revisão, nunca pelo upload privado.

## Pendências e critérios verificáveis
P0: CI e geometry-only aprovados; captura real com Playwright; manifesto contém dois recortes; render completo e revisão de seus pixels.
P1: bibliotecas de fotos com licenças verificáveis e uso contextual, testadas sem cobrança extra; reduzir exposição a ícones repetidos.
P1: ligação automática da capa com o ID correto e readback da API.
P2: solicitar referências em vídeo para comparação visual genuína e medir visuais sem extrapolar para outras épocas do canal.
P2: após alguns vídeos próprios, comparar CTR, retenção e duração no Studio e revisar títulos/capas com dados, não estimativas.


## Evolução 09/10: imagens reais como padrão de edição
- O piloto Imposto Seletivo passou a exigir **cinco visuais de fontes distintas em seis blocos**: dois recortes jornalísticos verificáveis e três fotografias contextuais com licença revista; bloco de opinião mantém palco próprio. Isso é padrão editorial NOSSO, não estatística do ANCAPSU.
- Foto do Congresso de **Leandro Ciuffo** (arquivo 2011, CC BY 2.0): https://commons.wikimedia.org/wiki/File:Congresso_Nacional_Brasil.jpg
- Supermercado brasileiro de **Eduardo Soares** (arquivo 2020, Unsplash License): https://unsplash.com/photos/a-grocery-store-filled-with-lots-of-drinks-ouNWk-_iTmM
- Urna de 2022 de **Pedro França/Agência Senado** (CC BY 2.0, arquivo 2022): https://commons.wikimedia.org/wiki/File:Elei%C3%A7%C3%B5es_2022_-_Segundo_Turno_-_52465029467.jpg
- Verificar que as imagens entram como contextualização **de arquivo**, não como fotografias capturadas na notícia de 2026. O manifesto identifica origem, licença, autor e relação com o bloco; créditos devem constar na descrição produzida pelo motor.
- A validação de roteiro bloqueia fotos não licenciadas, número insuficiente de contextos e cenas genéricas com pouco material jornalístico. O render deve produzir 3 fotos + 2 documentos verificáveis em cena antes da avaliação final. Captura/streaming/MP4 continuam **pendentes** até o GitHub terminar.
