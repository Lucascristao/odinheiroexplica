# Produção por qualquer IA autora

## Pré-requisitos

Checkout deste repositório, Node 22, Python 3.11+, Git e GitHub CLI autenticado. Actions usa os secrets já configurados de Gemini e Drive; não entregue esses valores ao agente nem ao frontend. Qualquer IA precisa poder ler os arquivos, editar o JSON, executar comandos e acompanhar Actions. Somente colar um prompt em uma IA sem essas capacidades não executa o motor.

## Pedido e execução

Leia skills/ode-video/SKILL.md. O pedido reutilizável está em docs/production-prompt.md e pode ser impresso com npm run ode -- prompt. A escolha autônoma de pauta precisa estar autorizada no pedido; use --ask-topic para imprimir a variante com três opções.

1. npm ci e npm run ode -- context mostram contratos, política de voz e recursos disponíveis.
2. Leia histórico, pesquise fontes atuais e registre storyboard antes de escrever daily.json.
3. Leia docs/editorial-learning.md. Novo episódio preenche learning_strategy e usa npm run ode -- preflight --new-episode; retomada histórica usa preflight. O comando valida conteúdo, fontes, pronúncia e contratos HyperFrames. Se o Python do sistema não existir, defina ODE_PYTHON com o caminho do executável.
4. No modo normal, execute npm run typecheck e as suítes relevantes. Faça commit e push na main sem alterar render-trigger/daily.txt; espere CI do mesmo commit.
5. npm run ode -- dispatch solicita workflow_dispatch na main. Compare o headSha do run com o commit enviado.
6. npm run ode -- status; para falha transitória, npm run ode -- resume --run-id NUMERO. Corrigir conteúdo exige novo commit e novo run, que reutiliza cenas de voz compatíveis.
   Se o render e o QA terminaram e a falha ocorreu na conferência auxiliar ou no envio, use npm run ode -- resume --run-id NUMERO --delivery-only. A retomada confere a procedência e reaproveita o MP4 sem sintetizar voz nem renderizar novamente; veja docs/recovery-render.md.
7. Baixe daily-production-review do Actions; revise relatórios e o MP4 completo com áudio. Use npm run ode -- review para repetir a extração local no vídeo real.
8. Confira a pasta Drive, gere a capa completa conforme a skill de embalagem, salve-a em production/ID-DO-EPISODIO/thumbnail.jpg (ou thumbnail.png), faça commit/push e envie para a pasta observada com npm run ode -- deliver --folder-id ID --file production/ID-DO-EPISODIO/thumbnail.jpg --role thumbnail. O workflow verifica pasta, tamanho, formato e readback do arquivo. Registre a revisão em production/ID-DO-EPISODIO/review.md (ou review.json) e use --role editorial-review para entregá-la também. O comando acompanha o envio; quando vídeo, metadados, texto, capa e revisão atuais estão confirmados na pasta, registra final-delivery.json e limpa automaticamente os temporários locais desse episódio.

O estado local em work/production-state.json só organiza a sessão e não é fonte editorial. Os arquivos editáveis, skills, pesquisa, HTML, workflow e relatório final ficam no Git; derivados grandes ficam em artifacts e Drive, com hashes.

## Limpeza após a entrega

Não mantenha MP4, áudio de revisão, quadros, ZIPs e staging HyperFrames locais após a conclusão. Baixe os artifacts do episódio em work/runs/NUMERO-DO-RUN/ mantendo a estrutura original. A limpeza identifica esses downloads pelo projeto, recibo e checksum do vídeo; preflight, revisão e HyperFrames registram os temporários que criam. Somente os arquivos comprovadamente pertencentes ao episódio concluído são removidos. Falhas ou entregas incompletas preservam os caches para retomada.

Se a entrega foi confirmada por um conector em vez de ode deliver, registre em production/ID-DO-EPISODIO/final-delivery.json o project_id, source_project_sha256 (SHA-256 de daily.json com quebras LF), folder_id, complete_package: true e files com id, name e size observados no Drive. Conserve delivery.json com o checksum do MP4. Execute npm run ode -- complete --production production/ID-DO-EPISODIO para finalizar a limpeza. cleanup.json registra caminhos removidos e espaço liberado; uma falha ao remover arquivos deixa status pending e pode ser retomada com o mesmo comando.

A limpeza preserva arquivos versionados, dependências e produções sem entrega comprovada. Não apague work/ ou public/ inteiros. Não remova arquivos manualmente antes de confirmar o pacote completo no Drive.

## Falhas e retomada

Não encurte o roteiro para quota de voz. Respeite retry/backoff do mesmo modelo e use cache por cena. Não peça regeneração total no gatilho: force_fresh_audio é input manual do workflow e só vale na primeira tentativa. Se o agente não puder assistir/escutar, registre essa limitação; métricas e transcrição não equivalem a revisão perceptual.

A conferência automática de entrega bloqueia falhas concretas de integridade. A extração de quadros e as métricas de movimento são auxiliares: uma falha nessa ferramenta não impede enviar um MP4 aprovado pelo QA. Pausas, variação de pitch e avisos de ritmo orientam a revisão editorial, sem exigir nova produção por si só. A duração do contêiner pode incluir cauda de áudio; os quadros seguem a duração da trilha de vídeo.

Produção direta sem testes é uma opção somente quando explicitamente pedida; o prompt --direct registra o modo e o commit usa [production direct]. Os gates necessários da produção continuam.


## Auditoria da thumbnail antes de enviar

Na pauta nova, declarar `packaging.thumbnails[0].contract` e rodar `npm run ode -- thumbnail-spec --check --new-episode` (também incluído em `ode preflight --new-episode`). O CI roda `npm run ode -- thumbnail-spec --check` e exige contrato atual; episódios antigos podem manter `production/EPISODIO/thumbnail-contract.json` explícito sem alterar a origem do MP4. A headline e o SHA vinculam o snapshot a um único episódio.

Depois do render, executar `npm run ode -- thumbnail-spec` e usar a instrução resultante sem acrescentar elementos. Inspecionar a imagem completa e a redução a 320×180; se falhar, regenerar e revisar. Persistir `production/EPISODIO/thumbnail-audit.json` conforme a estrutura documentada em `docs/thumbnail-identity.md`, com hashes e observações **realmente verificadas**. O comando de entrega compara `project_sha256`, `contract_sha256`, `image_sha256`, texto, sete verificações e todas as restrições antes do upload, registra também um segundo arquivo `thumbnail-audit-HASH.json` no Drive e verifica seu readback. Isso evita omitir a revisão ou aprovar um arquivo posteriormente alterado, mas não detecta visualmente rostos via código: a inspeção da imagem não pode ser simulada.


## Entrega direta ao YouTube para a linha de notícias (sem Drive)

O fluxo explicativo anterior permanece com Drive por padrão. Para um episódio destinado ao YouTube, use `npm run ode -- dispatch --youtube-private` após os gates do projeto. Esse comando dispara o MESMO motor, porém com `delivery_target=youtube_private`. Nesse caso **o MP4 não passa pelo Drive**: `worker/youtube_publication.py` identifica a conta OAuth e confere ID, nome e @handle do O Dinheiro Explica, consulta a playlist recente para evitar uploads duplicados, valida metadados e envia o vídeo **sempre em modo privado** com `youtube.upload`. O arquivo `daily-youtube-private-receipt` do Actions guarda ID, URL e checksum do MP4; não contém credenciais. `YOUTUBE_REFRESH_TOKEN` é separado do token do Drive; reutilizamos `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` sem alterar `worker/drive.py`.

A capa não é produzida pelo Actions: gere-a **neste chat** de acordo com `docs/thumbnail-identity.md`, confira a imagem real e salve `production/EPISODIO/thumbnail.jpg/png`, com o relatório `thumbnail-audit.json` correspondente no Git. Para anexar ao vídeo privado já enviado, execute manualmente **Upload Thumbnail to Google Drive** no Actions com `target=youtube`, `project_id` igual ao episódio, `video_id` recuperado do recibo e `thumbnail_path` apontando para o arquivo canônico. Apesar do nome legado desse workflow, nesse modo ele **não chama o Google Drive**. O backend exige auditoria íntegra e confere novamente o canal e a privacidade privada antes de usar `thumbnails.set`. A capa só pode ser enviada para o vídeo indicado; nenhuma etapa faz publicação pública.

**Limite da autorização:** as permissões já concedidas `youtube.upload` e `youtube.readonly` bastam para upload privado, associação da miniatura e leitura da identidade do canal; **não bastam para mudar o status de privado para público depois**, pois `videos.update` exige `youtube` ou `youtube.force-ssl`. Até que essa permissão seja concedida explicitamente e se construa um gate de publicação, libere manualmente a visibilidade do vídeo pelo YouTube Studio. Não prometa publicação autônoma. A criação automática de três pautas diárias e o agendamento de notícias são outra etapa, ainda não implementada; este desvio de entrega apenas reutiliza o motor já existente com um destino novo.
