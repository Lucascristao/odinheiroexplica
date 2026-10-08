---
name: ode-packaging
description: Criar título, descrição e capa completos que entreguem a promessa do episódio sem sensacionalismo.
---

# ode-packaging

Leia [embalagem](../../docs/youtube-packaging.md), [aprendizado](../../docs/editorial-learning.md) e [capa](../../docs/thumbnail-identity.md). Assunto reconhecível cedo, consequência concreta, título e thumbnail complementares. Vincule cada promessa aos claims, unidades e trechos que a entregam; um exemplo hipotético não prova resultado universal. Não prometer CTR medido.

Descrição editorial curta para celular; pipeline acrescenta capítulos reais, fontes, créditos, pergunta e três hashtags uma vez. URLs ficam nos metadados internos.

Após vídeo entregue, gere a capa completa conforme visual_prompt, verifique texto/composição, proporção e limite do YouTube e envie à mesma pasta. Não substituir a capa final por screenshot automático. Registre o arquivo, dimensões e entrega. Preserve a pauta no título e imagem.


## Procedimento obrigatório de thumbnail

Use `npm run ode -- thumbnail-spec` para produzir a instrução de geração exclusivamente a partir do contrato estruturado. Em novos episódios registre `packaging.thumbnails[0].contract` antes da renderização. Não transfira livremente um modelo de thumbnail do YouTube para dentro da arte: pessoas, números, setas, documentos e qualquer apoio só são permitidos se aprovados no contrato do episódio.

Após gerar a imagem, **inspecione os pixels reais** e a redução 320x180, seguindo `docs/thumbnail-identity.md`. Se não puder observá-la ou algo divergir, pare e refaça; nunca marque como aprovado por suposição. Salve `thumbnail.jpg/png` e `thumbnail-audit.json` em `production/EPISODIO/`, registrando SHA-256 do projeto, contrato e imagem, observações específicas, lista de exclusões checadas e responsável. O workflow bloqueia upload sem registro íntegro e entrega a auditoria ao lado da capa. O registro não equivale a inspeção automática dos objetos da imagem.
