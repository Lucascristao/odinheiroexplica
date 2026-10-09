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


Notícias usam a skill do motor mas têm **contrato separado** em `docs/news-format.md`, `news/editions` e `worker/news_project.py`. Cada edição contém múltiplas matérias verificadas, apresentador Roberto e conclusão sintética. Reutilizar Live/Remotion/QA, sem mexer em `video/data/daily.json`. O workflow de notícias entrega somente como vídeo privado, aguardando inspeção do MP4, capa feita no chat e liberação pública permitida pelo YouTube.


No formato de notícias, o roteiro é também **comentado pelo Roberto**: ponto de vista editorial de direita/liberal na economia, críticas fundamentadas a medidas estatais e empresariais, reações humanas, ironia e sarcasmo na dose apropriada, sempre distinguindo informação apurada de opinião. Não imitar Piter/ANCAPSU literalmente nem alterar os vídeos explicativos por essa preferência. Conferir exemplos e limites em `docs/news-format.md`.


NOVO FORMATO CANÔNICO (09/10/2026): cada notícia é um vídeo exclusivo. `news/episodes/*.json`, `worker/news_single_project.py`, `.github/workflows/render-news-single.yml`. Processo completo e referência ANCAPSU em `docs/news-single-format.md`. A meta de três edições diárias significa três notícias distintas, NÃO um giro com três matérias. Dizer status real e nunca tratar `uploaded_private` como entrega completa. Recortes documentais devem vir de URLs verificadas com contexto; sem autorização explícita, não copiar fotos de imprensa. Capas geradas aqui, encaminhadas para o Git com auditoria real. O anexo ao YouTube após aprovação é automático por `news-auto-thumbnail.yml`.
