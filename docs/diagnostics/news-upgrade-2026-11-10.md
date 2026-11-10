# Revisão da automação — 10/11/2026

O titular autorizou análise, correções, testes e publicação, com sete vídeos por dia. Leitura autenticada do Studio pela porta local de depuração e de logs do GitHub; nenhum token foi exportado do navegador.

## Evidências

- Canal `@odinheiro.explica`: 141 inscritos e 65 vídeos na leitura. Muitas notícias com 1–12 visualizações, além de casos com 68 e 141. São contagens observadas; não havia CTR/retenção para atribuir causalidade.
- Os 30 uploads mostrados no Studio variavam de 0:58 a 1:34, com vídeos privados e públicos. O redator solicitava 4–9 blocos curtos, sem orçamento total de desenvolvimento.
- Meio-dia [42715062320](https://github.com/Lucascristao/odinheiroexplica/actions/runs/42715062320): terminou perto de 20h em Fortaleza; `Janela de tolerância vencida; preservar vídeo privado`. Monitor [42728125980](https://github.com/Lucascristao/odinheiroexplica/actions/runs/42728125980) confirmou privado no ID `9O7Hybp4WLM`.
- Manhã [42608950319](https://github.com/Lucascristao/odinheiroexplica/actions/runs/42608950319): retentativas esgotadas por divergência literal do Live em número/código com barra. O gate recusou áudio divergente corretamente.
- Noite [42704300725](https://github.com/Lucascristao/odinheiroexplica/actions/runs/42704300725): `publishAt` confirmado no ID `X-QhH5Cmifo`; Studio mostrou público na leitura posterior. Agendamento e publicação são estados diferentes.
- O código de recortes podia substituir texto ausente por outro com palavras em comum; isso não comprovava a afirmação. A substituição foi removida.
- O episódio Pix de 09/11 tratava do recorde de 06/11. Declarar outra data no JSON não demonstra acontecimento novo. A segunda revisão exige prova literal da data do acontecimento/divulgação e examina números, condições e cálculos.

## Melhorias

Agenda 08h/10h30, 13h/16h, 18h/20h/22h (Fortaleza), com produção antecipada, deduplicação, cron nominal e bloqueio antes de consumir voz numa janela vencida. Watchdog distingue redação, render pré-upload e publicação do ID original; não depende exclusivamente de cadeias `workflow_run`, limitadas pelo GitHub.

Oito blocos, alvo 700–950 palavras, desenvolvimento em lotes e segunda revisão com citações por fato/data. Três títulos de ângulos diferentes, promessa demonstrável e abertura direta. Perspectiva liberal explicitamente separada dos fatos. Por orientação posterior do titular, duração/faixa de palavras, estilo e quantidade de recortes viraram avisos, sem bloquear notícia válida. Nenhuma desaceleração ou silêncio para preencher tempo.

Capa composta localmente com identidade oficial e material real, tentativa de revisão multimodal Groq em duas resoluções. Google fica exclusiva na voz. Modelo/quota indisponível ou reprovação visual usa miniatura automática; nenhuma auditoria fictícia. Capa chamativa é hipótese editorial, sem promessa de CTR.

## Limites e verificação

Gemini Live tem limites de sessão, concorrência e tokens dependentes da conta; Groq tem limites por minuto/dia. Chamadas sequenciais, espera entre passes, cache de áudio compatível e retentativas limitadas. Não houve contratação paga nem troca de modelo de voz.

GitHub pode atrasar crons. Prazo de publicação até 180 minutos, mesmo dia, QA sem falhas e identidade/recibos obrigatórios. Privados antigos não serão liberados em lote: podem estar vencidos ou ter falhado em apuração/QA.

Testes offline, avaliação de APIs reais, configuração implantada e publicação confirmada serão registrados separadamente após execução.
