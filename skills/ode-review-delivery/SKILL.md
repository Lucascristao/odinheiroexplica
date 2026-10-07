---
name: ode-review-delivery
description: Revisar MP4, localizar falhas visuais/temporais e concluir entrega do vídeo e embalagem no Drive.
---

# ode-review-delivery

Leia [revisão](../../docs/production-portable.md) e pacote render-output/visual-review. O relatório de ritmo descreve eventos; QA mede integridade/áudio; pixel-diff diagnostica movimento. Nenhum deles comprova compreensão sozinho.

Confira grupos antes/durante/depois/intervalo, cobertura de cena e timing_source do pacote de prova, além das emendas; números/unidades, condições, sincronismo, relações e leitura. Registre o segundo real da primeira descoberta e confira sua relação com a promessa conforme [aprendizado](../../docs/editorial-learning.md). Assista com áudio para julgar ritmo e naturalidade. Use tempos/quadros e findings concretos; registre limitações de observação. Movimento de fundo/legenda não demonstra mudança do protagonista.

Bloqueie defeitos concretos de conteúdo ou integridade. Avisos de pausas, pitch e movimento são diagnósticos; não exigem novas animações ou narração apenas para cumprir métricas. A extração auxiliar de provas não bloqueia o envio de um MP4 aprovado pelo QA; registre eventual falha sem declarar revisão concluída. Se o render já terminou e somente a entrega falhou, use `resume --run-id NUMERO --delivery-only` conforme [retomada](../../docs/recovery-render.md).

Corrija causa e retome com cache; não remover recursos apenas para passar gate. Arquivos do pacote permanecem nos artifacts e no Drive. Confirme delivery.json e a pasta real, incluindo vídeo, título/descrição e capa. Produção só termina após essa conferência; postagem manual.

Baixe artifacts em work/runs/ID mantendo a estrutura original. Salve os definitivos em production/ID-DO-EPISODIO/ com capa thumbnail.jpg ou thumbnail.png e revisão review.md ou review.json. Envie ambos com `ode deliver`; o fechamento confirmado limpa os temporários locais do episódio e registra cleanup.json. Se usar o conector Drive, registre final-delivery.json conforme o documento de produção e execute `ode complete --production production/ID-DO-EPISODIO`. Não deixe cópias locais de MP4, áudio de revisão, quadros, ZIPs ou staging após a entrega. Preserve caches durante falhas/entrega incompleta e preserve código, arquivos versionados e outras produções; nunca apague work/ inteiro.
