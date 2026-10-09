# ODE Notícias, execução agendada comandada pelo ChatGPT

## Escopo e autorização
Somente novas notícias únicas `ode-news-single`. O titular autorizou operação recorrente integral, sem pedir pauta nem aprovação por episódio, inclusive publicação **sem capa personalizada**, usando a miniatura automática do YouTube. Esta autorização não se aplica a vídeos explicativos evergreen. O ChatGPT seleciona e edita as pautas; o GitHub executa somente o motor de vídeo, QA e publicação. Gemini API é reservada EXCLUSIVAMENTE à voz Gemini 3.8 Live Roberto/Charon. Não chamar o editor Gemini `worker/news_autonomous_editor.py`, o gerador Gemini `worker/news_autonomous_thumbnail.py` nem criar cron editorial no GitHub.

## Horários e IDs (America/Fortaleza / Brasília, UTC-3)
| Início | Slot | Arquivo | ID | Publicação |
|---|---|---|---|---|
| 06h | manha | `news/episodes/YYYY-MM-DD-manha.json` | `noticia-YYYY-MM-DD-manha` | 08h |
| 10h | meio-dia | `news/episodes/YYYY-MM-DD-meio-dia.json` | `noticia-YYYY-MM-DD-meio-dia` | 12h |
| 18h | noite | `news/episodes/YYYY-MM-DD-noite.json` | `noticia-YYYY-MM-DD-noite` | 20h |

Os horários exatos são agendados por ChatGPT Tasks. Cada ativação é uma execução nova e independente; não esperar em loop e não depender do chat original permanecer aberto. Descobrir data/hora local em tempo real, identificar slot pela execução planejada (não por atraso do runner); se o horário já passou, não produzir matéria antiga para compensar. As verificações tardias são separadas.

## Passos que devem ser realmente executados em cada ativação
1. **Fonte de verdade:** conferir `config/news-autonomy.json` (enabled), `AGENTS.md`, `docs/news-single-format.md`, `worker/news_single_project.py`, `.github/workflows/render-news-single.yml`, notícias anteriores e GitHub Actions. Se `enabled=false`, não produzir. Nunca confiar no contexto antigo para estado recente.
2. **Idempotência:** antes de preparar algo, verificar se o arquivo do slot já existe; se existir, conferir execução/YouTube associada e NÃO criar outro `episode_id`. Se o vídeo já foi publicado/programado, apenas informar. Não iniciar duas produções do mesmo slot.
3. **Pesquisa original do ChatGPT:** consultar a web atual, ler matérias reais, cruzar NO MÍNIMO duas editoras diferentes, conferir eventos/datas, ao menos 4 fatos com `source_ids`, dois materiais documentais HTTPS com trechos textuais efetivamente presentes na página e direitos registrados. Não depender de manchetes RSS como evidência; não inventar URL, aspas, fonte, busca, autorizações ou CTR.
4. **Roteiro/SEO:** escolher só UM assunto atual novo, com relevância para o público brasileiro, sem repetir notícias anteriores. Para opinião crítica do Roberto, marcar claramente `opinion` e dar contrapontos fiéis. Preencher 3 opções reais de título, `scorecard`, `discovery_strategy`, descrição natural, metadata SEO, `publication_target_local=YYYY-MM-DDTHH:00:00-03:00`, 4-9 blocos narrativos coerentes, recortes ligados a segmentos, `thumbnail_headline`, `thumbnail_primary`, `thumbnail_tension` e `thumbnail_composition`. Ler e satisfazer de verdade todas as validações do adaptador.
5. **Marcação factual:** `editorial_status=autonomous_fact_checked` somente depois de conferir fatos, trechos e fontes; `reviewed_at` é o horário real da revisão. Não apresentar verificação feita por Gemini nem fingir revisão humana. Se não for possível conferir, parar e registrar o bloqueio.
6. **Capa OPCIONAL:** se geração de imagem nativa do ChatGPT estiver efetivamente disponível nessa execução e for possível transferir arquivos ao GitHub, produzir 1280x720 conforme `docs/thumbnail-identity.md`, inspecionar pixels e registrar auditoria fiel vinculada ao projeto em `production/EPISODIO/thumbnail.jpg` ou `.png`. Só anexar com auditoria completa, imagens e hashes reais. **Se a imagem não puder ser gerada, verificada ou enviada, NÃO bloquear nem usar Gemini API: o vídeo deve ser publicado com miniatura gerada automaticamente pelo YouTube.**
7. **Escrita real:** criar exatamente o JSON do slot em `main` usando as ferramentas GitHub conectadas. Evitar sobrescrever arquivo existente e commits de outros agentes; trabalhar com o SHA corrente. A criação/alteração de um único `news/episodes/*.json` deve disparar `render-news-single.yml`; conferir se ocorreu. Se o gatilho não vier e houver suporte a `workflow_dispatch`, disparar com `edition_path` do mesmo JSON. Não simular uma execução quando o conector não fornecer escrita/dispatch.
8. **Render e publicação:** o GitHub valida e captura as fontes, gera apenas a narração com Gemini 3.8 Live, renderiza Remotion, executa QA, envia privado ao canal O Dinheiro Explica, anexa a capa opcional e programa `publishAt` para o horário autorizado com o `worker/news_autonomous_schedule.py`. Canal, autenticação, QA `pass`, recibo do vídeo e horário futuro são obrigatórios; capa não. Se a janela de programação perder o prazo ou houver erro real, **não publicar fora de hora**.
9. **Comprovar estado:** consultar runs e recibos. Sucesso de uma etapa não equivale à confirmação de publicação pública. Enviar no relatório o ID do episódio, assunto, link real da execução, vídeo (se confirmado), capa anexada ou miniatura automática, status agendado/publicado/falhou e impedimento. Não inventar sucesso. Se necessário, verificação pública posterior é feita por workflow independente.

## Princípios e limites
- A tarefa ChatGPT é o único cron editorial. `news-autonomous-editor.yml` e `news-scout.yml` são legados sem agendamento e não devem ser reativados.
- A imagem não tem garantia de disponibilidade em Tasks. Não afirmar suporte inexistente nem trocar silenciosamente por Gemini.
- Uso de `GEMINI_API_KEY` nos workflows de notícias deve estar restrito ao step `Narração Live Roberto`.
- Uma tentativa que falha não cancela as execuções das próximas janelas; nunca repetir com tema antigo apenas para completar quota de três vídeos.
- Só afirmar publicação pública depois de retorno do YouTube API confirmando status `public`, ou dizer explicitamente que foi somente programada.
