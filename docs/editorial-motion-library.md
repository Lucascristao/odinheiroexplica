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

`stage.camera_mode: manual` (também usado quando omitido) preserva câmeras explícitas; `static` mantém o quadro estável. `auto` é uma opção autoral que acompanha alvos e operações, limitada pelo enquadramento completo da informação visível. Não é ativada automaticamente para todos os vídeos. `beat.camera_mode: hold` mantém o enquadramento; uma câmera explícita continua tendo prioridade. Use `initial_camera`, câmeras nos beats e `moves` para percursos próprios da história.

`beat.entrance` escolhe `fade`, `slide`, `scale` ou `wipe`, com `direction: left | right | up | down` quando aplicável. Wipe mascara somente a arte de objetos/ícones; rótulos, números e documentos entram inteiros, sem cortar letras ou dados. A entrada deve ter relação com a ideia, respeitar a região reservada e terminar antes da leitura. `stage.motion_profile: static` permite um trecho sem efeitos; não elimina alterações informativas declaradas.

SVGs locais têm desenho de traços, entrada de camadas e destaque interno finito. O foco não desmonta um objeto que já foi apresentado. `element.svg_motion` escolhe `assemble`, `trace` ou `none`; montagem por partes pertence aos objetos e ícones usam traçado ou nenhum efeito. Escolha o movimento das partes quando ele ajuda a reconhecer ou explicar o objeto; não use pulsação contínua.

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

### bloom — transição legada

Transition: bloom.

Expansão curta de luz/cor usada como revelação ou mudança de estado. É pontual, não é fundo contínuo. Não usar em toda transição.

## Princípios

- toda animação é determinística por frame;
- a âncora alinhada ao áudio real define a entrada do beat; tempos sem confiança continuam explicitamente estimados;
- cada mudança termina e deixa tempo de leitura; não impor entrada, desenvolvimento e saída a toda frase;
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
