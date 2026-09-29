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
