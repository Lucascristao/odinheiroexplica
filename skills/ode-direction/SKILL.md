---
name: ode-direction
description: Criar storyboard executável próprio da pauta, escolhendo demonstrações, protagonistas e transformações.
---

# ode-direction

Leia [direção](../../docs/editorial-scene-design.md), [continuidade](../../docs/editorial-continuity.md), [atenção](../../docs/editorial-attention.md), [identidade](../../frame.md) e última produção no Git.

Antes do JSON, registre pergunta, protagonista, relação, dados/assets, estado inicial, prova e estado final; ligue transformação a trecho literal único da fala. Não usar dois textos com seta como solução universal. Escolha conta, documento, foto, objeto ou gráfico pela relação.

Reserve regiões inclusive para participantes ocultos; entradas e câmera não cortam informação. Stage oferece geometria e eventos auditados. HyperFrames pode substituir a arte interna de um protagonista via element.hyperframes sem trocar texto, relações ou relógio. Registre por que a técnica explica a afirmação.

Arte protagonista ocupa o quadro útil, com `visual_role: protagonist` e escala efetiva conferida após contain. `show_label: false` preserva o label como metadado e libera toda a região da arte; não exibir nomes de técnica. Use texto principal grande e conciso, mantenha condições e exemplos identificados e não reserve faixa para legenda. O motor mede a área efetiva e avisa sobre protagonistas pequenos; confira também vazios internos da fonte HTML/SVG.

Bom: uma carta se divide em lance e crédito disponível, com conta identificada. Inadequado: títulos saltam enquanto nada mostra de onde sai o lance. Entrega: research/storyboard-<tema>.md e bindings coerentes no projeto.
