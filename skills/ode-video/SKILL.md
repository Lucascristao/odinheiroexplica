---
name: ode-video
description: Produzir e retomar vídeos do O Dinheiro Explica até entregar o pacote no Drive; usar para pedidos completos de produção neste repositório.
---

# ode-video

Leia AGENTS.md. Execute npm run ode -- context. Preserve pauta, modo e autorizações da conversa; só peça a decisão editorial quando ela faltar. Se o usuário autorizou escolher, pesquise uma pauta inédita e registre a escolha.

Escolha skills por necessidade: editorial para pesquisa/roteiro, direction para storyboard, motion para execução, evidence para mídia, voice-sync para voz/tempos, review-delivery para revisão/entrega, packaging para título/capa. Leia apenas as referências da etapa.

Leia [aprendizado editorial](../../docs/editorial-learning.md) para público, hipótese e prova da embalagem. Em episódio novo, execute npm run ode -- preflight --new-episode; em retomada histórica, use preflight. Registre mudanças no Git. Em modo normal, aguarde CI do mesmo commit; em modo direto, preserve gates reais e use [production direct], sem testes/demos. npm run ode -- dispatch inicia o Actions. Acompanhe npm run ode -- status --run-id ID; leia logs de falhas, corrija e retome cache compatível. Nunca declarar entrega pelo simples disparo.

O executor gera áudio, tempos, clipes HyperFrames, mix, MP4, revisão e upload. O agente continua responsável por fatos, explicação e direção. Confira o MP4 e seus relatórios; gere/upload a capa completa e confirme vídeo/título/descrição/capa na mesma pasta. Publicação é manual.

Referências: [fluxo](../../docs/production-portable.md), [arquitetura](../../docs/architecture.md), [prompt](../../docs/production-prompt.md).


Capa: use a skill `ode-packaging` e `npm run ode -- thumbnail-spec`. Novo episódio exige `packaging.thumbnails[0].contract`; inspeção da imagem final exige `production/EPISODIO/thumbnail-audit.json` antes de `ode deliver`. Nenhuma composição genérica deve substituir os protagonistas e as exclusões aprovados.


Para o destino alternativo de notícias YouTube, reutilize a preparação editorial, narração, composição e QA do motor existente, mas use `ode dispatch --youtube-private` quando essa entrega for explicitamente solicitada. O upload é privado, não passa pelo Drive e exige confirmação da identidade @odinheiro.explica. A imagem é gerada neste chat e anexada depois de auditoria via workflow de capa com `target=youtube`. Não considere o vídeo publicado só porque o upload privado concluiu. Consulte `docs/production-portable.md`.
