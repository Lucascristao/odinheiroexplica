# Recortes, gráficos e marcações durante a narração

Este é o contrato do motor para as próximas produções. Complementa `editorial-attention.md` e `editorial-continuity.md`. A identidade permanece carvão, branco e amarelo #FFBD19. Usar estes recursos conforme a explicação, sem impor sequência ou quantidade por vídeo.

## Pesquisa que produz material visual

Durante a leitura das fontes, escolher uma manchete, trecho ou gráfico que ajude a demonstrar uma afirmação do roteiro. Capturar a página real pelo navegador disponível e guardar a imagem em `research/captures/`, no repositório usado pelo render. Não gerar uma imitação de notícia com IA. Registrar a fonte em `sources`, a data real da captura e o papel do recorte na explicação. Uma página inteira com texto minúsculo não serve como recorte final.

O chat escolhe a fonte e o trecho durante a pesquisa. O runner pode executar `worker/auto_capture_sources.py` com `source_page_url` e `expected_text` para capturar a passagem real antes da voz. Ele verifica o texto na página, salva o bloco completo e registra `captured_at` com o UTC real. Não preencher uma data fictícia de captura no projeto planejado. Uma captura existente pode ser versionada ou fornecida por URL HTTPS de imagem; caminhos temporários do computador não servem ao Actions. Não usar URL HTML como `image_url`.

Escolher `expected_text` e, quando necessário, `target_selector` para preservar quem, qual opção, período, unidade e condição sustentam a fala. Uma data isolada ou um cabeçalho não comprovam uma regra. A revisão compara o recorte com a passagem exata em que será mostrado. O capturador valida presença de texto; a suficiência do contexto exige revisão editorial.

Em `visual_assets`, usar:

- `type: source_excerpt`, `id`, `source_id` existente e `expected_text` literal; `captured_at` em ISO UTC depois da captura;
- `capture_file: research/captures/nome.png` **ou** `image_url`, nunca ambos;
- `source_page_url`, `subject`, `narrative_role`, `country_context`, `license` e atribuição quando aplicável;
- `needs_cutout: false`;
- `crop: {x, y, width, height}` opcional, em percentuais da captura original.

O worker guarda a captura original, o recorte, dimensões, região escolhida e hash SHA-256 no manifesto. Não remove fundo de recortes documentais. URLs permanecem nos registros internos; a descrição pública continua sem links. Escolher materiais compatíveis com essa forma de uso e crédito.

## Recorte no palco

Criar elemento `kind: source_excerpt` com `asset_id`, região do palco e `label` identificador. Dimensões e caminho da imagem são preenchidos pelo compilador; não inventar `asset_width`, `asset_height` ou `asset_file` no roteiro. A identificação que já pertence ao recorte autêntico é preservada. O renderer utiliza somente a imagem real preparada; não substitui o documento por texto predefinido nem imprime selo de verificação.

`annotations` é uma lista de `{id, style, region}`. Estilos: `highlight`, `underline`, `strike`, `circle`. A região usa porcentagens **do recorte preparado**, não da página original ou da tela inteira. Definir regiões separadas para linhas de uma manchete. O destaque não pode ocultar ressalvas nem alterar a interpretação da fonte.

No beat direcionado ao recorte:

- `mark_ids` define a lista de marcações visíveis. `[]` limpa; omitir mantém. Marcações já visíveis não reiniciam ao acrescentar outra.
- `view: {x, y, width, height}` aproxima uma região; `{x:0,y:0,width:100,height:100}` retorna ao conjunto. A imagem e as marcações compartilham as mesmas coordenadas, sem esticar o conteúdo.
- `motion_seconds` define a duração da transição, entre 0,1 e 2 segundos; padrão 0,45. O início vem do bookmark real da fala.

Mostrar contexto antes de aproximar. Não cortar unidade, período ou ressalva essencial. Capturar em resolução suficiente para o maior enquadramento. Não há OCR automático que garanta leitura; selecionar e conferir o trecho durante a pesquisa.

## Texto com marcação

Nos elementos de texto (`label`, `note`, `step`, `metric`), o beat pode usar `emphasis: {phrase, style}`. A frase deve ocorrer exatamente uma vez no `label` vigente. Estilos: highlight, underline, strike. A marcação acompanha as linhas medidas da fonte, inclusive quando o trecho quebra de linha. `emphasis: null` remove. `action: update` troca o rótulo e limpa a marcação antiga, salvo nova marcação explícita.

Riscar somente uma hipótese que a narração está descartando, deixando claro o que está sendo corrigido. Evitar destacar o parágrafo inteiro. Entrada, alteração e saída usam beats próprios com âncoras literais e únicas. Não inventar timestamps proporcionais para frases.

## Gráficos próprios baseados em dados

Elemento `kind: chart`, com `label` curto como título e `chart`:

- `type: line | bar`;
- `source_id` existente, `unit`, `x_label`;
- `y_min`, `y_max` explícitos; barras começam em zero;
- `points: [{x, label, value}]`, de 2 a 40 pontos. X numérico crescente, sem duplicatas, preserva espaçamentos reais de períodos. Não tratar anos irregulares como intervalos iguais.

Reservar pelo menos 60% da largura e 50% da altura do palco; preferir gráfico dominante. Escala permanece fixa durante a cena. O motor não inventa valores, não suaviza séries e não anima contagens que poderiam parecer dados reais. Rótulos do eixo são espaçados para evitar colisões; os pontos continuam representados.

Beat com `chart_focus: {from, to}` destaca um ponto (`from === to`) ou intervalo por índices, começando em zero. O último ponto selecionado mostra seu valor. `chart_focus: null` limpa. Narrar a unidade e o período. Não reconstruir um gráfico sem dados confiáveis: usar recorte autêntico quando apropriado.

## Composição livre e números grandes

`visual.stage.show_title: false` libera a faixa superior. A área segura e a marca do canal permanecem. O padrão true preserva projetos existentes.

`label_size` permite 32–120 px; `value_size` permite 48–260 px. O texto é medido e só reduz até o mínimo legível. A região precisa comportar o número e o rótulo; não aumentar a fonte dentro de um bloco pequeno.

Para um número sobre uma foto/objeto, o elemento de base declara `text_region` em percentuais de sua própria região. O elemento superior usa `overlay_on` com o ID da base e ocupa somente essa região reservada. Somente label ou metric sem ícone/detalhe podem ocupar essa camada. O renderer fornece base escura de contraste, e outras colisões continuam proibidas. Não usar overlay para escrever sobre texto ou dados de um recorte. Ao mover o conjunto, mover base e sobreposição juntos; as posições e o corredor continuam sujeitos à verificação de limites.

## Ritmo e permanência

O motor mantém a marcação e o enquadramento até um novo evento alterá-los. Planejar: apresentar → marcar no termo relevante → permitir leitura → retirar ou mudar foco na próxima frase. `reveal_ids` e `retire_ids` podem acompanhar o mesmo beat. Animação não ocupa necessariamente todo o tempo de exposição. Agrupar mudanças simultâneas no mesmo evento, preservando o contrato de bookmarks.

Usar repouso visual entre destaques. Evitar múltiplas regiões se movendo enquanto o espectador lê. Alternar recorte, objeto, número e gráfico porque mudou a necessidade de explicação, não para cumprir uma cadência artificial.
