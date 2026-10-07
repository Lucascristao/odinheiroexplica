# Direção de cena executável

O storyboard decide como a informação será demonstrada. A paleta identifica o canal; geometria, metáfora, protagonistas e montagem nascem da pauta. Consulte a última produção no Git para comparar a composição real, além do histórico de temas em `visual-history.md`.

Antes de preencher `visual.stage`, registre para cada cena: pergunta/afirmação, protagonista, relação demonstrada, dados ou asset de origem, mudança visual na âncora da fala, percurso da câmera e saída. Converta o plano em elementos e eventos implementados. Não basta declarar uma intenção em `visual_direction`.

## Escolher a demonstração

- Quantidades e evolução usam `kind: chart` com dados verificáveis, fonte, unidade e escala explícita. Um ícone chamado chart não é um gráfico. O gráfico ocupa pelo menos 60% × 50% do palco.
- Contas usam `beat.operation` com os valores e participantes reais. Em `equation`, declare `input_ids`, `operator` e `result_id`; ligue a conta ao exemplo revisado em `editorial.explanation`.
- Um número central pode dominar o quadro com `kind: metric`, `value_size`, `surface: none` e `treatment: giant_number`. O Stage exibe valores exatos; atualizações não são contadores progressivos.
- Ações físicas ou digitais usam objetos SVG compatíveis e `actuation`. Uma aproximação da câmera e um contorno traçado não demonstram apertar, bloquear ou devolver.
- Uma regra ou afirmação documental pode usar um recorte autêntico com contexto, unidade e condições preservados. Fotografias precisam de função narrativa e de crédito.
- Fluxos usam conexões quando origem, destino e percurso ajudam a explicar. Uma comparação não exige seta. Um protagonista único e `connections: []` são válidos.

Essas escolhas não formam um catálogo obrigatório nem uma sequência fixa. Cada mudança de relação deve ter uma resposta visual; repetir o diagrama de dois textos conectados em todas as cenas pede revisão, mesmo com zoom, cascata e fluxo.

## Arte protagonista e texto

A ilustração ocupa a maior parte útil do quadro quando comanda a explicação. Não reserve o terço inferior para legendas nem prenda toda cena num retângulo baixo. Componha pela relação: arte ampla com título curto, comparação grande ou protagonista lateral com informação grande. Texto principal normalmente usa 64–96 px, com região suficiente, sem diminuir a arte para caber legendas.

Objetos aceitam `show_label: false`: `label` continua como metadado sem aparecer ou reservar uma faixa. Não escreva “ILUSTRAÇÃO ESQUEMÁTICA” ou outro nome de técnica na tela. Condições necessárias, como “EXEMPLO HIPOTÉTICO”, continuam nos rótulos explicativos; não confundir isso com aviso sobre o formato da arte. Quando o rótulo do objeto estiver visível, o motor mede sua altura real, sem rodapé fixo de 90 px.

Declare `visual_role: protagonist | support` nas artes. O relatório de produção mede a área efetiva do SVG/clipe após o encaixe `contain`, com fonte e câmera reais; uma região larga e baixa pode produzir arte muito pequena. `small-protagonist` avisa quando a maior ocupação conferida fica abaixo de 12% do quadro. É diagnóstico para recompor, não cota de efeitos nem autorização para cortar o desenho. A medida cobre o envelope da arte; transparências e vazios internos do SVG exigem direção e revisão visual.

Elementos de texto com `icon` aceitam `icon_size: 48..500` em pixels. Use 250–500 quando o SVG comandar a cena. O tamanho explícito é preservado; o auditor informa falta de capacidade em vez de reduzir a arte silenciosamente. A ausência mantém os tamanhos dos episódios antigos.

`content_layout: row | column` organiza ícone e texto na mesma região. Em coluna, reserve altura para ambos; em linha, reserve largura. Os mínimos de texto, entradas e câmera continuam valendo. `surface: none` remove também a bolha atrás do ícone. Fotos, recortes, gráficos e `kind: object` usam sua própria região, sem `icon_size` ou `content_layout`.

`sustain` aceita `breathe`, `drift`, `float` e `tilt`. `flow` e `pulse` são movimentos de conexões; `actuation: count` movimenta moedas/cédulas compatíveis e não interpola valores monetários. `kinetic_type` atua no rótulo; `giant_number` dá presença ao valor. `push-in`, `pan` e `reframe` são intenções de câmera, implementadas com `camera`; não são actions. As actions são `focus`, `reveal`, `update` e `retire`.

## Material visual chega ao runner

Durante a pesquisa, declare fotos utilizáveis em `visual_assets` com URL HTTPS de imagem, procedência e crédito. O worker baixa e prepara o arquivo em `public/generated-assets/`.

Para `source_excerpt`, escolha a página específica e o trecho literal em `source_page_url` e `expected_text`. O runner pode capturar esse trecho antes da voz; uma captura real já salva em `research/captures/` também pode ser usada conforme `editorial-evidence.md`. Não invente data de captura, dimensões, pixels ou marcações. Vincule o `asset_id` ao elemento do palco. URL de notícia não é `image_url`.

Leia os relatórios de captura e confira o contexto. Uma falha de acesso pede outra fonte legítima ou captura real, preservando a afirmação e seus limites. Não deixe assets vazios apenas para evitar preparação. Quando imagens não ajudarem, registre essa decisão editorial e use uma demonstração adequada.

## Segurança e revisão

Reserve regiões inclusive para participantes inicialmente ocultos; use updates do mesmo participante e movimentos compatíveis para transformações. Composições que exigem sobreposições ou interações além do contrato precisam de implementação autoral, preservando os dados e a voz. Não afrouxe colisões ou enquadramento para simular liberdade.

Os diagnósticos `repeated-two-node-flow` e `repeated-composition` sinalizam estrutura repetida mesmo quando há câmera. São avisos para revisão, sem quantidade obrigatória de formatos. A geometria comprova capacidade e enquadramento; o MP4 com áudio decide clareza e ritmo percebido.

## Produção direta

Quando o usuário pedir produção sem testes, use `[production direct]` na mensagem do commit. O CI ignora seu job de testes nesse push; os testes permanentes continuam disponíveis para outras execuções e pull requests. O Netlify continua publicando o painel. Não use `[skip ci]` para deploy via Git, pois ele também suprime Netlify.

Esse modo não elimina preparação de produção: compilação/typecheck, contratos, fontes, assets reais, fidelidade de voz, alinhamento e auditoria do render real permanecem. Não execute prévias, suítes ou renders demonstrativos. Registre o que não foi executado e avalie o resultado no fluxo real autorizado.
