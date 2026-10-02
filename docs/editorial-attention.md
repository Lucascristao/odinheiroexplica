# Direção editorial: atenção com clareza

Aplicável a todas as pautas. Esta diretriz complementa a continuidade visual e substitui instruções antigas que pedem fonte no rodapé, texto miúdo ou troca ornamental constante.

## Voz e estrutura

Abrir com a consequência concreta para uma pessoa, uma pergunta específica ou uma contradição verificável, nomeando o assunto e a pergunta central. Entregar uma primeira resposta cedo. Desenvolver perguntas, explicações, exemplos visuais e consequências conforme o assunto pedir, sem uma sequência fixa para todas as cenas. A próxima pergunta deve nascer do que acabou de ser explicado. Não guardar todas as respostas para o fim nem fazer promessas vagas de revelação.

Escrever para o ouvido: frases curtas alternadas com explicações, verbos concretos, linguagem cotidiana, siglas explicadas no primeiro uso. Separar fato, hipótese e exemplo. Não imitar bordões, voz ou persona do apresentador de referência. Evitar tom de comunicado e repetição de “agora vamos entender”. A fala conduz; a tela mostra relações, objetos e números em vez de transcrever parágrafos.

Todo vídeo deve ter uma apresentação falada de Roberto ou Luana em uma frase natural logo após o gancho e um único pedido falado breve de inscrição depois de entregar valor, em um respiro ou no encerramento. Variar a formulação conforme a pauta, sem vinheta longa, minuto fixo ou interrupção da explicação.

O contrato `editorial.narrative_contract` deve apontar três trechos literais únicos da narração: `topic_explanation` nas duas primeiras cenas, `presenter_introduction` na primeira cena após o gancho, com o nome do narrador, e `subscription_request` depois da apresentação e da entrega de valor. A validação antes do TTS evita omissões; a revisão do roteiro ainda precisa confirmar que o assunto está compreensível e a conclusão responde à abertura.

Antes de fechar o roteiro, identificar o que o espectador aprende em cada bloco. Trechos sem uma informação, demonstração ou consequência nova devem ser cortados. Usar pergunta retórica com resposta e breve pausa de reflexão como interação; não criar botões falsos ou depender de clique dentro do MP4. A conclusão responde à pergunta inicial e entrega uma ação ou compreensão prática. O assunto deve ser explicado do começo ao fim, com as cenas e a duração necessárias; limites TTS não determinam o conteúdo.

## Repertório disponível no motor

Recortes autênticos, gráficos com dados, marcações de frases/regiões e camadas reservadas seguem o contrato de `docs/editorial-evidence.md`. Consultá-lo durante a pesquisa e antes de construir o VideoProject.

`visual.stage.elements` aceita `step`, `label`, `metric`, `note`, `photo`, `object`, `source_excerpt` e `chart`. Cada elemento ocupa uma região segura; sobreposição de texto só é permitida na região explicitamente reservada de uma foto/objeto.

- `icon`: bank, wallet, person, search, bell, lock, check, refund, shield, warning, clock, phone, receipt, cart, key, eye-off, route, coins, chart, house, car, document, globe. SVG local, sem serviço pago. Escolher pelo significado; não colocar um ícone em toda frase por obrigação.
- `kind: object` com `object_type: receipt | wallet | bank | component | factory | truck | package | atm | cash | branch | hub | data | store | phone | terminal`: ilustrações vetoriais originais em camadas, para participantes dominantes. `label` é o rótulo curto; legendas da fala têm outro contrato. São esquemas, não documentos, instalações ou comprovantes reais de uma instituição.
- `kind: photo` com `asset_id`: fotos e gráficos do manifesto visual. `image_fit: contain | cover`, `focal_x/focal_y: 0..100`, `image_motion: none | push | pan`, `photo_style: clean | paper`. Push/pan são discretos, limitados e calculados pelo frame; usar none para documento que precisa ser lido e contain para preservar recorte.
- Conexões: `motion:once` desenha o percurso e repousa; `flow` ou `pulse` com `period_seconds` sustentam a relação em curso. Não representam valores, frequências ou velocidades financeiras reais.
- `reveal_ids`, `retire_ids`, `moves` e `action:update` mudam a explicação sem desmontar o palco. Retirar anotações que perderam função; preservar as relações que ainda ajudam.
- `beat.actuation:tap|lock|unlock|confirm|signal` faz um alvo SVG compatível atuar conforme a fala. `element.sustain` permite breathe/drift/float/tilt autorais, perceptíveis e determinísticos, com amplitude 0–40 limitada ao envelope de até 12% do objeto e inclinação de até 4°; não movimentar toda cena com a mesma oscilação.
- `element.surface:none|glow|paper|spotlight` escolhe o acabamento. Objeto, número ou texto pode viver diretamente no palco; um painel não é a unidade obrigatória de toda explicação.
- `stage.captions` apresenta a narração em blocos normais de aproximadamente três palavras por linha, com até duas linhas. Só entra se houver uma área livre contígua de pelo menos 30–40% do quadro, segundo o limiar escolhido. A ilustração comanda a composição; não reservar área para a legenda. Ausência conserva o projeto anterior sem legendas adicionadas automaticamente.

Não há suporte novo a B-roll de vídeo, câmera 3D ou J/L cuts nesta revisão. Não inventar campos para essas capacidades. Compor dinamismo com o repertório implementado.

## Cor de identidade

Destaques editoriais, ícones de foco, conexões, objetos e transições usam amarelo `#FFBD19` com preto/carvão e branco. Não substituir o amarelo pela cor do assunto, do Pix, de banco ou de empresa. Fotografias preservam suas cores naturais; cores semânticas em dados só entram quando necessárias à compreensão, não como decoração.

## Texto, imagens e movimento

Uma ideia dominante por momento, com poucos apoios. Preferir rótulos de 2–6 palavras. Texto de apoio é opcional e deve acrescentar algo que a imagem não explica. Fonte mínima do palco: 32 px em 1080p; rótulos normalmente 38–46 e métricas com escala adequada à sua área. Legendas usam fonte de 48–96, normalmente 64, com bloco completo e sem sublinhado ou animação palavra a palavra. Se um rótulo não couber, reduzir a redação ou ampliar sua região; se a legenda não tiver espaço livre suficiente, omiti-la. Não reduzir fonte indefinidamente. Reservar largura para ícones e altura para números antes de escrever; nunca reservar faixa para legenda.

Textos, números e unidades da informação em foco devem aparecer inteiros. Informações futuras começam ocultas e são reveladas quando a fala chega a elas; não antecipar o próximo conteúdo parcialmente cortado na borda. Durante movimentos de câmera, verificar também os quadros intermediários e manter legível o conteúdo que está sendo explicado. Objetos de contexto podem permanecer quando contribuem para a compreensão, sem concorrer com o foco ou sugerir dados incompletos.

Alternar escala e recurso quando muda a pergunta: objeto real para reconhecimento, diagrama para mecanismo, número grande para dimensão, contraste para limite. Isso é um repertório, não uma sequência fixa nem uma cota de efeitos por segundo. Preservar momentos de leitura e repouso. Não usar tremor, flash, zoom pulsante ou efeito sonoro em cada palavra. Um foco em movimento por vez.

Planejar também os intervalos entre as entradas: um participante pode atuar, o fluxo pode continuar, a relação pode se transformar ou a câmera repousar para ler. Um desenho de contorno e um brilho inicial não satisfazem uma demonstração de abrir, confirmar, sacar ou aproximar. Sustentação discreta preserva presença; a atuação e as transformações precisam entregar o significado da fala. Não preencher todo o vídeo com listas reveladas item a item.

As legendas acompanham trechos literais da narração em blocos completos e estáveis, aproximadamente três palavras por linha e até duas linhas. Usar somente a área livre contígua que já existe e atinge o limiar de 30–40% do vídeo; não somar vazios separados, promover áreas pequenas ou mover ilustrações para acomodar texto. Os campos antigos de região/lado não podem forçar exibição. Evitar posição fixa no rodapé de todas as cenas e duplicação do rótulo em foco. Sem karaoke, palavra destacada individualmente ou sublinhado. Tempos estimados continuam identificados no pacote técnico; conferir sincronismo do bloco no MP4.

Ao retirar um elemento, decidir o papel do vazio durante a fala restante: pausa, foco no objeto presente ou nova relação. Uma legenda pode acompanhar esse momento somente se a área livre contígua suficiente surgir naturalmente. A decisão nasce da história, e o vazio não precisa ser preenchido. No renderer persistente, manter objetos não preserva automaticamente as composições expressivas antigas; escolher recursos executáveis e uma interação autoral quando necessária.

A revisão de produção assiste ao MP4 com áudio, inclusive depois do último reveal. Avaliar movimento percebido, progressão da explicação, legibilidade, sincronismo e uso do espaço. Diagnósticos de segundos sem eventos e número de transformações ajudam a localizar trechos; não são cotas, aprovação de originalidade ou medição de atenção do público. Uma pausa pode ser correta, e muitos efeitos podem continuar contando pouco.

Pesquisar imagem pelo que ela explica: local, produto, documento ou objeto relacionado à afirmação. Não preencher todas as pautas com o mesmo celular, cédulas e gráfico genérico. Conferir resolução, origem e licença; preferir domínio público, CC0, licença compatível ou material original. Usar recorte só quando o objeto precisa se integrar ao diagrama. Não remover fundo de documentos, ambientes ou fotos em que o contexto é evidência. Evitar texto gerado dentro de imagem para informações factuais.

Dar acabamento autoral às fotos e recortes com suporte, moldura, profundidade, luz e entrada pertinentes à cena, sem deixar um retângulo branco solto no palco. Preservar os pixels, textos, fontes e contexto da evidência; o tratamento apresenta o material, sem recriar ou alterar seus fatos. Não impor a mesma moldura a todas as pautas nem enfraquecer a prova para favorecer a legenda.

Não exibir rodapé com nomes de fontes no vídeo. A descrição não contém links: listar apenas títulos das fontes e créditos textuais. URLs ficam somente nos registros internos de pesquisa. Se a licença exigir link público ou crédito sobre a imagem, escolher outro material compatível com esta direção; nunca omitir obrigação de licença. Remover rodapé não autoriza remover referências da pesquisa.

## Título, descrição e descoberta

A regra canônica de embalagem está em `docs/youtube-packaging.md` e deve ser aplicada em toda nova produção.

Escolher internamente uma formulação centrada em busca e outra em curiosidade; entregar apenas a opção final. Front-load do assunto: sempre que soar natural, a palavra-chave principal ou o tema reconhecível entra nas primeiras 3 a 5 palavras. Depois vem a consequência ou dúvida concreta que justifica o clique. Usar como referência editorial cerca de 45 a 65 caracteres, preservando o limite técnico de 100. Evitar abrir com jargão burocrático, número de norma ou "Entenda/Saiba/Veja" quando o assunto puder aparecer primeiro. Não afirmar volume de busca sem dados e não prometer resultado que o roteiro não entrega.

Título e thumbnail formam uma única promessa e precisam se complementar. Se a thumbnail apenas repete o título, a embalagem ainda não está resolvida.

`publication.description` contém somente o corpo editorial: 2 a 3 frases curtas de gancho e 3 ou 4 bullets de respostas concretas. A palavra-chave principal aparece naturalmente logo no começo. Capítulos, fontes, créditos, pergunta de comentários e hashtags são acrescentados pelo pipeline e não podem ser duplicados no corpo. Toda produção preenche também `publication.engagement_question` e exatamente 3 itens em `publication.hashtags`.

O pacote final usa os tempos reais e só publica capítulos tecnicamente válidos, consolida as fontes uma única vez e mantém URLs apenas nos metadados internos. Tags continuam sendo apoio e não substituem assunto, título, conteúdo e descrição coerentes.

Para buscas fora do YouTube, a descrição pública deve ser compreensível isoladamente e nomear o assunto com clareza. Não há garantia de indexação ou posição. O painel privado não vira uma página pública de SEO, nem publica projetos sem autorização.

## Referências analisadas em 29/09/2026

- [O Primo Rico](https://www.youtube.com/watch?v=B0IRXCb6NTM): leitura da abertura/transcrição e capítulos; a abertura contrasta potencial econômico com obstáculos concretos (casa, carro, futuro), depois promete explicar causas. Aplicação: consequência humana antes do jargão, contraste e encadeamento causal. Não importar números, conclusões ou CTA longo do vídeo para outras pautas.
- [Marketing Demons](https://www.youtube.com/watch?v=dijLCofg8WE): transcrição completa e amostras visuais. Defende estrutura, edição, equilíbrio sonoro e entrega de valor ao longo da explicação. Aplicação: cada bloco paga uma pequena promessa, texto selecionado, variação com propósito, som sem repetição excessiva. A sugestão de 15 segundos é uma heurística do autor, não regra científica nem cronômetro de efeitos. Não adotamos produto pago patrocinado nem alegações sobre dopamina como fundamento técnico.
- [YouTube: títulos e capas](https://support.google.com/youtube/answer/12340300), [descrições](https://support.google.com/youtube/answer/12948449) e [capítulos](https://support.google.com/youtube/answer/9884579).

A análise dos vídeos é de estrutura/transcrições e amostras, não uma revisão audiovisual integral nem uma medição de retenção dos canais.
