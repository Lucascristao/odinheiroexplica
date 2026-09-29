# Direção editorial: atenção com clareza

Aplicável a todas as pautas. Esta diretriz complementa a continuidade visual e substitui instruções antigas que pedem fonte no rodapé, texto miúdo ou troca ornamental constante.

## Voz e estrutura

Abrir com a consequência concreta para uma pessoa, uma pergunta específica ou uma contradição verificável. Entregar uma primeira resposta cedo. Construir cada bloco como pergunta → explicação → exemplo visual → consequência. A próxima pergunta deve nascer do que acabou de ser explicado. Não guardar todas as respostas para o fim nem fazer promessas vagas de revelação.

Escrever para o ouvido: frases curtas alternadas com explicações, verbos concretos, linguagem cotidiana, siglas explicadas no primeiro uso. Separar fato, hipótese e exemplo. Não imitar bordões, voz ou persona do apresentador de referência. Evitar tom de comunicado e repetição de “agora vamos entender”. A fala conduz; a tela mostra relações, objetos e números em vez de transcrever parágrafos.

Antes de fechar o roteiro, identificar o que o espectador aprende em cada bloco. Trechos sem uma informação, demonstração ou consequência nova devem ser cortados. Usar pergunta retórica com resposta e breve pausa de reflexão como interação; não criar botões falsos ou depender de clique dentro do MP4. A conclusão responde à pergunta inicial e entrega uma ação ou compreensão prática. CTA curta depois da entrega de valor.

## Repertório disponível no motor

`visual.stage.elements` aceita `step`, `label`, `metric`, `note`, `photo` e `object`. Cada elemento ocupa uma região segura; o texto não pode invadir outra região.

- `icon`: bank, wallet, person, search, bell, lock, check, refund, shield, warning, clock, phone, receipt, cart, key, eye-off, route, coins, chart, house, car, document, globe. SVG local, sem serviço pago. Escolher pelo significado; não colocar um ícone em toda frase por obrigação.
- `kind: object` com `object_type: receipt | wallet | bank`: ilustrações vetoriais originais em camadas, para objetos dominantes. `label` é a legenda curta. São esquemas, não documentos ou comprovantes reais.
- `kind: photo` com `asset_id`: fotos e gráficos do manifesto visual. `image_fit: contain | cover`, `focal_x/focal_y: 0..100`, `image_motion: none | push | pan`, `photo_style: clean | paper`. Push/pan são discretos, limitados e calculados pelo frame; usar none para documento que precisa ser lido e contain para preservar recorte.
- Conexões: traço de foco e ponto percorrendo o caminho quando a fala chega ao destino. Não representam valores ou velocidades financeiras reais.
- `reveal_ids`, `retire_ids`, `moves` e `action:update` mudam a explicação sem desmontar o palco. Retirar anotações que perderam função; preservar as relações que ainda ajudam.

Não há suporte novo a B-roll de vídeo, câmera 3D ou J/L cuts nesta revisão. Não inventar campos para essas capacidades. Compor dinamismo com o repertório implementado.

## Cor de identidade

Destaques editoriais, ícones de foco, conexões, objetos e transições usam amarelo `#FFBD19` com preto/carvão e branco. Não substituir o amarelo pela cor do assunto, do Pix, de banco ou de empresa. Fotografias preservam suas cores naturais; cores semânticas em dados só entram quando necessárias à compreensão, não como decoração.

## Texto, imagens e movimento

Uma ideia dominante por momento, com poucos apoios. Preferir rótulos de 2–6 palavras. Texto de apoio é opcional e deve acrescentar algo que a imagem não explica. Fonte mínima do palco: 32 px em 1080p; rótulos normalmente 38–46, métricas até 72. Se não couber, reduzir a redação ou ampliar a região. Não reduzir fonte indefinidamente. Reservar largura para ícones e altura para números antes de escrever.

Alternar escala e recurso quando muda a pergunta: objeto real para reconhecimento, diagrama para mecanismo, número grande para dimensão, contraste para limite. Isso é um repertório, não uma sequência fixa nem uma cota de efeitos por segundo. Preservar momentos de leitura e repouso. Não usar tremor, flash, zoom pulsante ou efeito sonoro em cada palavra. Um foco em movimento por vez.

Pesquisar imagem pelo que ela explica: local, produto, documento ou objeto relacionado à afirmação. Não preencher todas as pautas com o mesmo celular, cédulas e gráfico genérico. Conferir resolução, origem e licença; preferir domínio público, CC0, licença compatível ou material original. Usar recorte só quando o objeto precisa se integrar ao diagrama. Não remover fundo de documentos, ambientes ou fotos em que o contexto é evidência. Evitar texto gerado dentro de imagem para informações factuais.

Não exibir rodapé com nomes de fontes no vídeo. A descrição não contém links: listar apenas títulos das fontes e créditos textuais. URLs ficam somente nos registros internos de pesquisa. Se a licença exigir link público ou crédito sobre a imagem, escolher outro material compatível com esta direção; nunca omitir obrigação de licença. Remover rodapé não autoriza remover referências da pesquisa.

## Título, descrição e descoberta

Escolher internamente uma formulação centrada em busca e outra em curiosidade; entregar apenas a opção final, como exige o contrato atual. Identificar situação/assunto cedo, criar uma pergunta ou consequência específica e assegurar que o roteiro entrega a promessa. Até 100 caracteres, preferencialmente conciso; sem gritaria, urgência falsa ou resultado garantido. Não afirmar que uma formulação possui maior volume de busca sem dados.

Descrição única: primeiras duas linhas dizem para quem é, qual pergunta responde e qual aprendizado entrega. Usar a expressão principal e sinônimos naturalmente, sem lista repetitiva de keywords. Explicar siglas. Depois entram contexto, capítulos, nomes das fontes e créditos textuais, sem links. Reservar espaço dentro dos 5.000 caracteres para tudo isso. O pipeline usa os tempos reais e só publica capítulos que atendem aos limites do YouTube. Tags são apoio; não substituem assunto, título, conteúdo e descrição coerentes.

Para buscas fora do YouTube, a descrição pública deve ser compreensível isoladamente e nomear o assunto com clareza. Não há garantia de indexação ou posição. O painel privado não vira uma página pública de SEO, nem publica projetos sem autorização.

## Referências analisadas em 29/09/2026

- [O Primo Rico](https://www.youtube.com/watch?v=B0IRXCb6NTM): leitura da abertura/transcrição e capítulos; a abertura contrasta potencial econômico com obstáculos concretos (casa, carro, futuro), depois promete explicar causas. Aplicação: consequência humana antes do jargão, contraste e encadeamento causal. Não importar números, conclusões ou CTA longo do vídeo para outras pautas.
- [Marketing Demons](https://www.youtube.com/watch?v=dijLCofg8WE): transcrição completa e amostras visuais. Defende estrutura, edição, equilíbrio sonoro e entrega de valor ao longo da explicação. Aplicação: cada bloco paga uma pequena promessa, texto selecionado, variação com propósito, som sem repetição excessiva. A sugestão de 15 segundos é uma heurística do autor, não regra científica nem cronômetro de efeitos. Não adotamos produto pago patrocinado nem alegações sobre dopamina como fundamento técnico.
- [YouTube: títulos e capas](https://support.google.com/youtube/answer/12340300), [descrições](https://support.google.com/youtube/answer/12948449) e [capítulos](https://support.google.com/youtube/answer/9884579).

A análise dos vídeos é de estrutura/transcrições e amostras, não uma revisão audiovisual integral nem uma medição de retenção dos canais.
