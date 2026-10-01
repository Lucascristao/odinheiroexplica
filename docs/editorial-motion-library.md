# Biblioteca de movimento editorial

> Para a produção atual, siga primeiro [editorial-continuity.md](editorial-continuity.md). Texto por palavra, grifos, SVGs em camadas e operações agora participam do palco persistente. Recursos de montagem fotográfica e transição do renderer antigo continuam identificados como legados.

Esta biblioteca existe para ampliar a linguagem do canal, não para criar um novo template fixo.

Cada vídeo tem composição e direção próprias. Escolha recursos conforme o que precisa ser explicado; não percorra esta biblioteca como uma lista obrigatória. O diagnóstico de direção mostra decisões executáveis e aponta repetições para revisão, sem exigir quantidade mínima de efeitos ou mudanças por segundo.

Ela foi desenhada a partir de três referências técnicas estudadas em setembro de 2026:
- composição por camadas/máscaras em React + Remotion, com texto atrás de fotografia recortada;
- Curvable Motion, especialmente seus princípios de animação determinística por frame, cascade de palavras, sweep de texto, bloom e paleta derivada;
- Remotion Bits, especialmente AnimatedText, AnimatedCounter, StaggeredMotion, Ken Burns, barras animadas e reframing.

A implementação do projeto é própria e usa apenas os conceitos úteis para o canal.

## Capacidades atuais

### Operações do palco persistente

Para produções novas, a matriz implementada está em `visualCapabilities`, no módulo `src/lib/editorial-layout.ts`. As operações têm dados próprios em `beat.operation`; escolher apenas um nome em `treatment` não constrói uma demonstração.

| Operação | Dados e função |
|---|---|
| `equation` | `input_ids`, `operator`, `result_id`: liga valores declarados aos operadores; os números e a conta são conferidos em `editorial.explanation`. |
| `compare` | `element_ids`: destaca os participantes da comparação, sem escolher automaticamente um vencedor. |
| `stack` | `element_ids`: conecta itens em ordem vertical; reserve o corredor lateral. |
| `meter` | `value`, `min`, `max`, `unit`: representa uma escala explícita, sem limitar silenciosamente um valor inválido. |
| `signal` | `status`, `message`: revela uma condição textual, com seu significado declarado. |

Conexões reservam espaço para suas legendas e acompanham a geometria dos objetos. `semantic: transfer` precisa representar uma transferência real; sem `token_label` explícito, o token é neutro. O motor não infere dinheiro por palavras da narração. Preserve as relações e deixe o conteúdo futuro oculto até o beat correspondente.

A composição compartilhada usa a fonte de produção no Chromium e verifica estados de entrada, movimento, atualização e câmera. Falta de espaço produz diagnóstico antes da voz; aumentar a área, reorganizar blocos ou dividir a explicação é uma decisão editorial. Não reduzir indefinidamente a fonte nem esconder palavras.

O Actions executa uma verificação antes da narração e outra com o relógio do áudio real, salvando quadros e relatórios. Textos em imagens documentais ainda exigem conferência visual: geometria válida não comprova legibilidade raster.

### Conferir o que será executado

O diagnóstico de direção separa erros de execução de alertas editoriais. Uma escolha explícita sem os dados exigidos interrompe o plano antes da voz: `flow_diagram` precisa de uma conexão do alvo, `equation`/`split_compare`/`stack`/`meter`/`signal` precisam de uma operação correspondente, `kinetic_type` precisa de `reveal`/`update` de texto, `giant_number` precisa de `value`, e `masked_emphasis` precisa de um rótulo de texto. Uma operação já declarada pode continuar visível nos beats seguintes; não duplicar dados para simular continuidade.

No palco persistente, `behavior: reframe` sozinho não move câmera. Declare `camera` ou selecione `camera_mode: auto` conscientemente; em uma prova documental, `view` ou `mark_ids` executam a aproximação ou o destaque regional. Um nome de tratamento, `transition` ou uma frase em `visual_direction` não substitui esses dados.

O relatório compara câmeras e posições declaradas com as mudanças planejadas pelo mesmo resolver do renderer. Uma câmera idêntica, `hold`, movimento para a mesma posição, entrada sem mudança de visibilidade ou efeito suprimido por `motion_profile: static` recebe um alerta específico. Todas as cenas com câmera e objetos parados também pedem revisão do storyboard. Esses alertas não exigem uma cota de efeitos: explique por que o quadro estável ajuda a ler a prova e verifique onde uma relação precisa de percurso, transformação ou contraste. A revisão final usa o relógio do áudio e os quadros reais.

### Corrigir layout preservando a explicação

Use a mensagem da auditoria para identificar o elemento, conexão, operação e frame que falharam. Reserve mais área para o texto, reorganize participantes, crie o corredor da relação ou separe um momento de leitura quando necessário. Uma pilha usa `element_ids` em ordem vertical e espaço lateral para sua espinha; uma comparação preserva os dois lados reais; uma conexão mantém origem, destino e significado.

Não troque uma demonstração por `spotlight` nem apague setas, câmera ou operações apenas para obter validação verde. Se a composição precisar mudar, confira que o espectador continua vendo a relação que a fala explica e que cada intenção do storyboard virou uma ação executável. Refaça a auditoria completa dos estados de entrada, movimento e leitura antes da síntese. Depois do áudio, confira novamente as mesmas relações com os tempos finais.

### Câmera e entradas autorais no palco

`stage.camera_mode: manual` (também usado quando omitido) preserva câmeras explícitas; `static` mantém o quadro estável. `auto` é uma opção autoral que acompanha alvos e operações, limitada pelo enquadramento completo da informação visível. Não é ativada automaticamente para todos os vídeos. `beat.camera_mode: hold` mantém o enquadramento; não combine `hold` e uma câmera explícita no mesmo beat, pois são instruções contraditórias. Use `initial_camera`, câmeras nos beats e `moves` para percursos próprios da história.

`beat.entrance` escolhe `fade`, `slide`, `scale` ou `wipe`, com `direction: left | right | up | down` quando aplicável. Wipe mascara somente a arte de objetos/ícones; rótulos, números e documentos entram inteiros, sem cortar letras ou dados. A entrada deve ter relação com a ideia, respeitar a região reservada e terminar antes da leitura. `stage.motion_profile: static` permite um trecho sem efeitos; não elimina alterações informativas declaradas.

SVGs locais têm desenho de traços, entrada de camadas e destaque interno. O foco não desmonta um objeto que já foi apresentado. `element.svg_motion` escolhe `assemble`, `trace` ou `none`; montagem por partes pertence aos objetos e ícones usam traçado ou nenhum efeito. Traçar o contorno não equivale a fazer o objeto atuar. Escolha uma atuação semântica ou sustentação quando a explicação continua depois da entrada; reserve repouso para leitura e não aplique o mesmo pulso a todo elemento.

### Movimento durante a fala e atuação dos objetos

A entrada apresenta o assunto; o desenvolvimento precisa continuar mostrando o processo, contraste ou consequência. Planeje o que acontece entre as âncoras e depois do último reveal. Uma lista com três entradas e nenhum desenvolvimento pode ocupar quase toda a fala com o mesmo quadro. A estabilidade é adequada quando dá tempo de ler uma prova; não deve resultar apenas do esgotamento dos eventos.

| Contrato autoral | Uso |
|---|---|
| `element.sustain` | `{kind: breathe | drift | float | tilt, amplitude: 0..12, period_seconds: 2..12, phase?: number}`: movimento pequeno, determinístico, reservado com o objeto. A amplitude é limitada pelo contrato; não deslocar dados para fora da região nem fazê-los oscilar para sugerir valores. |
| `connection.motion` | `once` desenha o percurso e repousa; `flow` mantém o percurso ativo; `pulse` destaca a ligação periodicamente. `period_seconds` controla o ciclo. Escolher continuidade só quando há relação/processo em curso, sem inferir velocidade, frequência ou volume financeiro. |
| `beat.actuation` | `tap`, `lock`, `unlock`, `confirm` ou `signal`: ação das partes do SVG ligada à âncora da fala. Usar com um alvo compatível; desenhar um cadeado não demonstra abrir/fechar, e aproximar o bloco inteiro não demonstra tocar a tela. |
| `element.surface` | `none`, `glow`, `paper` ou `spotlight`: acabamento escolhido pela função. Uma escolha explícita retira painel, borda e regra lateral legados; `none` mostra arte/tipografia limpa, `glow` e `spotlight` são luz, sem cartão obrigatório. `paper` fica no suporte de photo/object, separado do rótulo branco; documentos preservam os pixels e podem usar iluminação no fundo. |

Esses campos são opcionais e autorais. Projetos anteriores conservam o caminho existente quando omitidos; não ativar sustentação, câmera ou ciclos genericamente em todas as cenas. `motion_profile: static` desativa a atuação e os movimentos do palco para uma leitura estável. Legendas seguem seu contrato próprio e podem ser desabilitadas quando interferirem na prova.

Os objetos esquemáticos incluem `receipt`, `wallet`, `bank`, `component`, `factory`, `truck`, `package`, `atm`, `cash`, `branch`, `hub`, `data`, `store`, `phone` e `terminal`. Escolha o participante que a história realmente usa; esquema de terminal ou banco não é foto/documento de uma empresa real. Combinar objeto dominante, informação espacial, documento ou comparação conforme a ideia, sem impor entrada/meio/saída iguais.

Um foco dominante pode atuar enquanto apoios permanecem legíveis. Fluxo e movimento secundário sustentam contexto, mas não devem disputar atenção com uma palavra, número ou ação principal. Repetir o ciclo enquanto a fala explica uma relação é diferente de movimentar todo cartão como decoração.

### Legendas editoriais curtas em espaços adaptativos

`stage.captions` é uma escolha explícita para aquela cena: `{enabled, max_words: 1 | 2, font_size: 72..140, preferred_side: auto | left | right | center, region?: {x, y, width, height}}`. A região usa percentuais do palco. Ausência não adiciona legenda automaticamente aos projetos anteriores.

As palavras acompanham a narração em grupos curtos, com presença tipográfica grande e legível. A posição considera os objetos e a câmera apresentados naquele momento; `auto` procura espaço disponível, e uma região autoral pode reservar lugar para o texto. Quando um objeto sai, o vazio pode receber a próxima palavra ou uma nova função visual; quando a prova ocupa a região, preservar seu texto, valor e unidade. Não fixar toda legenda no rodapé nem cobrir elementos essenciais para cumprir uma escolha de lado.

O worker prepara `scene.audio_captions` no input gerado: `text`, `start_frame`, `end_frame` e `timing_source`. `scene.caption_timing` registra origem, palavras correspondidas e hashes de áudio/narração. Palavras reconhecidas usam `audio-word-alignment`; interpolação entre âncoras ou atividade do áudio permanece identificada como estimativa. Nunca apresentar uma estimativa como sincronismo confirmado. Não escrever tokens ou tempos finais manualmente em `daily.json`.

Legendas seguem palavras literais da fala, sem inventar termos, quantias ou condições. Elas ajudam a ocupar e conduzir o olhar; não substituem a demonstração de uma transferência, comparação ou condição. Rótulos persistentes e legendas da fala têm papéis diferentes: evitar duplicá-los no mesmo foco. Desabilitar legendas quando leitura documental ou uma conta completa exigir o quadro.

### word cascade no palco

Aplicado dentro de kinetic_type. Palavras não aparecem como um bloco único: entram em sequência, com deslocamento e blur discreto. A sequência precisa caber no intervalo real do beat.

No palco persistente, o label mantém suas linhas e sua região medida; os dados numéricos permanecem exatos. Use o tratamento nos reveals/updates pertinentes, sem aplicá-lo a toda frase.

### Números no palco e renderer legado

No palco persistente, os valores são exibidos exatamente como declarados. `giant_number` amplia a presença do valor dentro da região reservada; não cria um contador nem interpola quantias. Atualizações de valores precisam de `action: update` e dados verificados. O contador progressivo existe somente no renderer legado e não deve ser prometido por um `treatment` do palco.

### masked emphasis

Treatment: masked_emphasis.

Uma faixa de destaque percorre a frase sem trocar a composição inteira. Use para uma conclusão, ressalva ou contraste curto. Não repetir várias vezes na mesma cena e não usar em texto longo.

### Foto em movimento e montagem legada

No palco persistente, `depth_photo` exige um alvo `kind: photo` com `image_motion: push | pan`; o movimento fica dentro da região da imagem. Um `source_excerpt` preserva a evidência documental e usa `view`/`mark_ids`, sem receber essa animação fotográfica.

A montagem com uma fotografia recortada entre texto de fundo e primeiro plano (`depth_photo` com `medium: photo_cutout`) pertence ao renderer legado. O palco não cria essa profundidade apenas pelo nome do tratamento. Quando a história exigir essa interação espacial, crie e valide uma composição autoral que a execute.

### Compatibilidade com o repertório expressivo

Ao existir `visual.stage`, a produção usa o renderer persistente em lugar de `Visual` e `EditorialMicroScene`. Portanto, preservar identidade de objetos não conserva automaticamente títulos gigantes, cascatas extensas ou montagens fotográficas do caminho antigo. `beat.headline` descreve a intenção; no palco só `action: update` o transforma em rótulo. A legenda da fala é outro recurso, com relógio próprio. As transições implementadas em `SceneTransitionAccent` também acompanham o caminho Stage; escolha-as pela mudança de ideia.

Planeje a expressividade no caminho realmente executado: atuação, sustentação, superfície, legenda sincronizada, escala e mudanças de relação. Se a cena precisar de uma composição que o palco não representa, implemente a interação autoral mantendo o contrato de dados/voz; não reduza o pedido a vários blocos e não prometa um efeito apenas pelo nome legado. A compatibilidade é preservar a função narrativa, não copiar um template do vídeo anterior.

### Diagnóstico de pausas e revisão percebida

O diagnóstico informa transformações, escolhas de sustentação/atuação/superfície, legendas pedidas e intervalos sem eventos visuais. Segundos só são calculados com `duration_frames` e `resolved_frame`; antes disso o ritmo fica `pending-audio`, sem simular o relógio da fala. Uma sustentação, fluxo ou legenda pode preencher atividade sem produzir nova explicação, por isso os intervalos entre transformações aparecem separadamente.

Esses números descrevem o contrato declarado, não medem movimento dos pixels nem retenção do público. Um intervalo longo gera pergunta editorial, não cota ou reprovação automática. Assista ao MP4 com áudio para julgar se a pausa está ajudando a ler, se o movimento é perceptível e se a explicação ainda progride. Aprovar geometria, contar câmeras ou examinar screenshots não aprova o ritmo.

### bloom — transição legada

Transition: bloom.

Expansão curta de luz/cor usada como revelação ou mudança de estado. É pontual, não é fundo contínuo. Não usar em toda transição.

## Princípios

- toda animação é determinística por frame;
- a âncora alinhada ao áudio real define a entrada do beat; tempos sem confiança continuam explicitamente estimados;
- a entrada termina e deixa tempo de leitura; atuação e relações podem continuar durante a fala quando têm função, sem impor entrada, desenvolvimento e saída a toda frase;
- movimento estrutural vale mais que movimento decorativo;
- fotografia, texto, número e diagrama podem ocupar camadas diferentes;
- profundidade não significa 3D: z-index, recorte, escala, máscara e parallax 2D são suficientes;
- não transformar os recursos em catálogo obrigatório;
- no máximo um efeito de destaque especial por trecho curto;
- o vídeo deve parecer editado para a história atual, não uma demonstração de biblioteca.

## Recursos que não entram no padrão

- cenas 3D;
- cubos, carrosséis 3D e UI inclinada apenas por estética;
- partículas decorativas;
- fundos WebGL pesados;
- confete, Matrix e efeitos de demo;
- gradiente ornamental permanente.

Esses recursos só podem ser considerados se tiverem função editorial clara e passarem por revisão específica.
