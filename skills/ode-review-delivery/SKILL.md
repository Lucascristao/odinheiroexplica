---
name: ode-review-delivery
description: Revisar MP4, localizar falhas visuais/temporais e concluir entrega do vídeo e embalagem no Drive.
---

# ode-review-delivery

Leia [revisão](../../docs/production-portable.md) e pacote render-output/visual-review. O relatório de ritmo descreve eventos; QA mede integridade/áudio; pixel-diff diagnostica movimento. Nenhum deles comprova compreensão sozinho.

Confira quadros de prova, intermediários e emendas; números/unidades, visibilidade de condições, sincronismo, relações e leitura. Assista com áudio para julgar ritmo e naturalidade. Use tempos/quadros e findings concretos; registre limitações de observação. Movimento de fundo/legenda não demonstra mudança do protagonista.

Bloqueie defeitos concretos de conteúdo ou integridade. Avisos de pausas, pitch e movimento são diagnósticos; não exigem novas animações ou narração apenas para cumprir métricas. A extração auxiliar de provas não bloqueia o envio de um MP4 aprovado pelo QA; registre eventual falha sem declarar revisão concluída. Se o render já terminou e somente a entrega falhou, use `resume --run-id NUMERO --delivery-only` conforme [retomada](../../docs/recovery-render.md).

Corrija causa e retome com cache; não remover recursos apenas para passar gate. Arquivos do pacote permanecem nos artifacts e no Drive. Confirme delivery.json e a pasta real, incluindo vídeo, título/descrição e capa. Produção só termina após essa conferência; postagem manual.
