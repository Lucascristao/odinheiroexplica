# Política editorial de fontes

## Objetivo

O canal deve informar com precisão sem transformar comunicado institucional em narrativa pronta.

Fontes primárias continuam importantes para confirmar texto de normas, números oficiais, cronogramas, documentos e posições institucionais. Elas não devem, sozinhas, definir a interpretação ou o efeito prático de uma história.

## Pautas regulatórias, econômicas e de interesse público

Quando a pauta depender de uma regra, decisão regulatória ou medida pública:

- usar pelo menos duas fontes não oficiais, de publicadores diferentes;
- incluir jornalismo independente e, quando disponível, análise técnica, setorial, acadêmica ou checagem;
- separar o que foi anunciado do que a regra efetivamente diz;
- separar expectativa declarada de resultado já observado;
- procurar limitações, gargalos de implementação, críticas técnicas e dados que possam contrariar a narrativa institucional;
- atribuir posições institucionais com expressões como "segundo o Banco Central", "o órgão afirma" ou equivalentes;
- não tratar objetivo declarado de uma medida como efeito comprovado;
- não construir contraponto artificial sem evidência.

O foco do roteiro deve ser mecanismo, evidência, consequência prática e incerteza.

## Campos do VideoProject

Preencher editorial.source_balance:

- requires_diversity
- public_policy_or_regulation
- official_sources_role
- independent_sources_role
- counterpoint_summary
- official_claims_attributed

Classificar cada fonte com publisher_class e editorial_role.

Classificar claims com framing:
- verified_fact
- official_position
- reported_claim
- analysis
- context

Quando framing for official_position, attribution_required deve ser true.

## Auditoria

O pipeline executa uma auditoria antes do TTS. Quando requires_diversity=true, a produção deve ter fontes não oficiais suficientes, publicadores diferentes, contexto independente e contraponto documentado.


## Diversidade de linhas editoriais

Em temas com disputa política, econômica ou regulatória, não concentre as fontes não oficiais em veículos com linha editorial semelhante.

Busque deliberadamente cobertura de linhas editoriais diferentes quando existir material relevante. Revista Oeste e Gazeta do Povo devem entrar no radar de pesquisa junto com outros veículos nacionais, sem que qualquer publicação seja tratada como autoridade por sua orientação editorial.

Regras:
- evitar montar o contexto independente somente com Folha/UOL ou somente com qualquer outro grupo de veículos;
- quando Revista Oeste, Gazeta do Povo ou outro veículo de linha editorial distinta tiver cobertura factual relevante da pauta, considerar essa cobertura na pesquisa;
- separar notícia/reportagem de coluna de opinião;
- opinião pode ser usada para mapear argumentos ou críticas, mas nunca como prova factual por si só;
- fatos importantes devem ser cruzados com documento, dado, fonte técnica ou outra reportagem independente;
- a meta é diversidade de perspectiva, não uma cota ideológica nem compensação artificial;
- quando duas fontes divergem, explicitar a divergência e buscar evidência adicional em vez de escolher uma narrativa por afinidade editorial.
