# Explicação editorial e exemplos

Contrato geral para todas as pautas. Novas produções usam `editorial.explanation`, versão `1.0`, definida em `src/lib/editorial-explanation.ts`. Projetos antigos continuam legíveis; a migração exige revisar o conteúdo. `src/lib/editorial-project.ts` normaliza `scenes` e `script.scenes`; se ambos existirem, seus conteúdos precisam ser iguais.

## Conceitos

Registre os conceitos indispensáveis em `concepts`: `id`, `terms`, `explanation:{scene_id,quote}`, `claim_ids`, `first_use` quando aplicável e `boundary` quando houver condição relevante. O trecho é literal e único na cena. A primeira utilização declarada que depende do conceito vem após sua explicação. Explique função e significado das siglas; expandi-las pode não bastar.

Explique cada conceito quando ele se torna necessário. O gancho apresenta consequência ou contradição compreensível; a conclusão responde à pergunta inicial. Não transforme a abertura em glossário.

## Exemplos

Use exemplos quando demonstram uma relação que a definição não esclareceu. Não há quota ou obrigação de analogia para todo conceito. Em `examples`, registre finalidade, tipo, claims, participantes, hipóteses, entradas com unidade/origem, conta, limites, trechos de fala e bindings para elementos reais do palco.

- `observed`: valores reais com fontes específicas.
- `derived`: resultado de entradas verificadas, operação e unidades compatíveis.
- `illustrative`: valores hipotéticos identificados por `identification` na fala e `visual_identification` na tela. A placa permanece durante a demonstração; o resultado não pode parecer cotação, alíquota ou economia observada.
- `analogy`: preserva a relação relevante e registra onde deixa de representar o assunto. Explique na fala o limite que evita uma conclusão falsa.

`calculation` aceita `operation:add|subtract|multiply|divide`, `input_ids`, `result`, `unit` e tolerância. Respeite participantes, tributos, períodos e unidades. Valores em reais não são automaticamente compensáveis. Uma hipótese numérica não suspende regras legais.

Não atribua fonte factual a número inventado. Claims sustentam a regra do mecanismo; entradas hipotéticas permanecem hipóteses. Um exemplo favorável não demonstra que uma opção é melhor para todos.

## Unidades explicativas e storyboard

Cada `learning_units` registra pergunta, resposta nova literal, conceitos/claims/exemplos e função visual com `bindings`. Uma unidade pode ocupar várias cenas; uma cena pode conter várias unidades. Cenas e duração seguem a explicação completa.

Planeje participantes, estado inicial, mudança e consequência. A tela demonstra a fala: guia se divide, parcela elegível reduz uma conta, custos diferentes mudam a comparação, situação identifica prazo. Mantenha explícito o beneficiário de créditos e fluxos.

Contas usam `operation:{kind:'equation',input_ids,operator,result_id}`; comparações usam `operation:{kind:'compare',element_ids}`. Os IDs precisam existir no palco. `treatment` sozinho não demonstra uma conta. Reserve corredores para operadores e setas. Relação não representa automaticamente pagamento ou transferência.

Escolha documento, objeto, número, foto, gráfico ou comparação conforme sua função. Preserve objetos quando ajudam a continuidade; retire o que perdeu função. Imagens são pesquisadas pela evidência que oferecem, sem repetir símbolos financeiros em todas as pautas.

## Revisão com evidências

`review.findings` contém perguntas de compreensão, trechos e conclusões específicas. Verifique se o público entende a mudança, os participantes, beneficiários, hipóteses, condições, exceções e limites. A conclusão entrega a promessa do título e da abertura. Evite notas arbitrárias ou um `approved:true` sem evidência.

`review.content_sha256` é SHA-256 de `stableJson(explanationReviewContent(normalizeEditorialProject(project)))`. Inclui story, fontes, claims, cenas, assets visuais e conceitos/exemplos/unidades, excluindo a própria revisão e o `captured_at` gerado pelo runner. A frase esperada, a fonte, o papel e a região autoral da prova pertencem à revisão; a hora técnica de captura não muda seu significado. Em Python, normalize IDs/índices das cenas, exclua `captured_at` dos assets e use `json.dumps(...,ensure_ascii=False,sort_keys=True,separators=(',',':'))`. Refaça revisão e hash quando o conteúdo abrangido mudar.

Automação confirma referências, trechos, ordem declarada, unidades, conta, proveniência e correspondência da revisão. Não confirma sozinha verdade da fonte, suficiência da definição ou compreensão do público.

## Produção portátil

O chat com acesso ao GitHub lê o contrato, pesquisa, escreve e revisa o projeto. Fontes e capturas ficam no repositório ou acessíveis ao runner. Execute `npm run validate:editorial -- video/data/daily.json`, auditorias de fontes/pronúncia e verificações pertinentes antes do TTS. Os workflows usam o mesmo contrato.

A produção autorizada usa `main`, sem PR obrigatório ou integração adicional de IA. O Actions fornece vídeo real e relatórios; mudanças visuais reaproveitam voz válida. Quotas TTS não determinam conteúdo, cenas ou duração.
