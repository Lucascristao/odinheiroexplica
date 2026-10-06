export function productionChatRequest(request: string): string {
  return `${request}

Use o repositório https://github.com/Lucascristao/odinheiroexplica. Antes de escrever o episódio, leia AGENTS.md, prompts/daily-editorial.md, docs/editorial-scene-design.md, docs/editorial-motion-library.md e os documentos editoriais exigidos por eles. O pedido abaixo contém as decisões essenciais; os arquivos completam os contratos técnicos.

MODO DE PRODUÇÃO DIRETA:
- Produza na main sem suítes de testes locais ou no CI, prévias silenciosas, amostras de voz ou renders demonstrativos. Mantenha compilação/typecheck de produção, contratos, preparação de assets, fontes, fidelidade vocal e alinhamento necessários ao vídeo real.
- Nos commits desta produção, use o marcador [production direct], que suprime o job de testes do CI e conserva o deploy do painel. Não use [skip ci] para publicar o painel pelo Git, pois também suprime o deploy Netlify.
- Não gere vídeo antes da decisão de pauta. Se ainda não houver tema aprovado, consulte o histórico completo de vídeos e apresente três opções virais fundamentadas, com título, thumbnail, gancho, gatilho e fontes; aguarde minha escolha. Se o tema já foi aprovado, preserve-o.

PAUTA E TÍTULO COM CONFLITO CONCRETO:
- Escolha uma história que faça a pessoa reconhecer uma situação do próprio bolso e querer descobrir uma resposta: preço igual com menos produto, dinheiro garantido que fica indisponível, custo novo cuja responsabilidade está em disputa. A tensão precisa nascer de um mecanismo verificável, não de adjetivos alarmistas.
- Evite propostas com cara de aviso de serviço, lista de benefícios ou tutorial genérico. Antes de apresentar as três opções, resolva para cada uma: o que a pessoa acredita, qual fato contraria essa crença, qual consequência concreta ela sofre e qual demonstração entrega a resposta.
- Nomeie cedo um assunto reconhecível e abra uma pergunta ou contradição específica. Referência de qualidade aprovada: "Supermercado: o aumento de preço que você não vê", com thumbnail "CADÊ O RESTO?" e gancho "O preço não mudou. Então por que você está pagando mais?". Use o princípio, sem repetir o tema, a frase ou a composição nas próximas produções.
- Título, thumbnail e abertura precisam vender a mesma descoberta. Não prometa valor encontrado, aumento universal, fraude, perda ou urgência que as fontes não sustentam. Diferencie caso real, hipótese e risco; números ilustrativos não viram manchete factual. Não afirme CTR ou viralidade medidos sem dados.

DIREÇÃO VISUAL QUE EXPLICA A HISTÓRIA:
1. Antes do JSON, construa um storyboard: para cada cena registre a afirmação/pergunta, o protagonista, a demonstração visual, os dados/asset, a transformação ligada à fala, a câmera e a saída. Compare a composição com o episódio anterior no Git, além de consultar docs/visual-history.md.
2. Escolha a composição pela relação explicada: quantidade pede escala/gráfico verificável; uma conta pede operation; uma regra pode pedir recorte autêntico; uma ação pede objeto que atua; um valor pode ocupar o quadro com tipografia livre. Não use dois blocos com uma seta como solução universal. Conexões só entram quando o percurso explica uma relação real. Não imponha uma sequência fixa de formatos.
3. Faça os recursos existir no caminho EditorialStage: declare kind: chart com dados e escala; beat.operation com participantes/operador/resultado; photo/source_excerpt com asset_id e visual_assets; números protagonistas com value_size e surface: none; entradas/revelações, updates e moves nas âncoras pertinentes. Texto em visual_direction e nomes em treatment não executam uma demonstração.
4. SVGs protagonistas precisam de região grande. Em elementos com icon, use icon_size explícito de 250 a 500 px e content_layout: column ou row quando a composição pedir; reserve espaço para arte e texto. Objetos SVG usam kind: object e a própria região. surface: none remove o suporte e a bolha do ícone. Não reduzir a arte a um ícone decorativo para passar na geometria.
5. Diferencie efeitos de explicação: trace desenha o contorno; sustain aceita breathe, drift, float ou tilt; flow/pulse pertencem às conexões. Eles sustentam a cena, mas a nova afirmação precisa de uma mudança informativa. giant_number destaca um valor exato; kinetic_type anima o rótulo. O Stage não cria contadores numéricos; actuation: count é atuação de moedas/cédulas, não interpolação de dinheiro.
6. Dê o primeiro acontecimento nos primeiros 2 a 3 segundos e faça a explicação avançar durante a fala, com micro-beats a cada nova afirmação e intervalos de até 4 a 5 segundos. Trocar o foco entre os mesmos dois textos não substitui uma conta, uma comparação ou a ação prometida. Câmera é declarada por camera e reposicionamento por moves conforme a função; push-in, pan e reframe não são valores de action. Actions válidas: focus, reveal, update e retire.
7. Pesquise também materiais visuais utilizáveis. O pipeline já baixa imagens de image_url HTTPS e captura source_excerpt declarado com source_page_url e expected_text literal. Cadastre fonte, crédito, papel narrativo e asset real; não invente recortes, dimensões ou pontos de gráfico. Vincule o asset ao palco. Se imagens não ajudarem a pauta, registre a razão editorial e entregue demonstrações visuais adequadas.
8. Preserve geometria, enquadramento completo, texto legível e regiões dos elementos ocultos. Corrija colisões reorganizando a composição, nunca removendo a conta, o gráfico, a mídia ou o movimento para obter aprovação. Leia os avisos de repetição de composição mesmo quando há câmera e animação.

IDENTIDADE, VOZ E ENTREGA:
- Paleta #FFBD19, grafite e branco; composição própria para esta história. Legendas sincronizadas em blocos limpos e secundários à ilustração.
- Roberto/Charon com Gemini 3.8 Live é o padrão. Luana/Autonoe somente para pauta dirigida ao público feminino. Preserve o roteiro completo, as fontes verificadas e os contratos de explicação; não encurte para economizar TTS.
- Conduza o render real até a entrega: acompanhe Actions, corrija falhas preservando a explicação e retome cache compatível. Confira o MP4 completo com áudio e vídeo/título/descrição na pasta do Drive antes de anunciar conclusão; informe limitações reais.
- As correções necessárias encontradas durante esta geração estão autorizadas: ajuste o conteúdo, o motor ou o pipeline conforme a falha comprovada, publique na main e retome a produção preservando o tema, os gates e o cache válido.
- Depois da entrega do vídeo, gere a thumbnail final 16:9 de alta conversão, com imagem, composição, acabamento e texto de 2 a 4 palavras que complemente o título. Envie a capa para a mesma pasta do Drive. Publicação no YouTube é manual.`;
}

