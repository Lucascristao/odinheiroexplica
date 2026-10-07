# Produção por qualquer IA autora

## Pré-requisitos

Checkout deste repositório, Node 22, Python 3.11+, Git e GitHub CLI autenticado. Actions usa os secrets já configurados de Gemini e Drive; não entregue esses valores ao agente nem ao frontend. Qualquer IA precisa poder ler os arquivos, editar o JSON, executar comandos e acompanhar Actions. Somente colar um prompt em uma IA sem essas capacidades não executa o motor.

## Pedido e execução

Leia skills/ode-video/SKILL.md. O pedido reutilizável está em docs/production-prompt.md e pode ser impresso com npm run ode -- prompt. A escolha autônoma de pauta precisa estar autorizada no pedido; use --ask-topic para imprimir a variante com três opções.

1. npm ci e npm run ode -- context mostram contratos, política de voz e recursos disponíveis.
2. Leia histórico, pesquise fontes atuais e registre storyboard antes de escrever daily.json.
3. npm run ode -- preflight valida conteúdo, fontes, pronúncia e contratos HyperFrames. Se o Python do sistema não existir, defina ODE_PYTHON com o caminho do executável.
4. No modo normal, execute npm run typecheck e as suítes relevantes. Faça commit e push na main sem alterar render-trigger/daily.txt; espere CI do mesmo commit.
5. npm run ode -- dispatch solicita workflow_dispatch na main. Compare o headSha do run com o commit enviado.
6. npm run ode -- status; para falha transitória, npm run ode -- resume --run-id NUMERO. Corrigir conteúdo exige novo commit e novo run, que reutiliza cenas de voz compatíveis.
7. Baixe daily-production-review do Actions; revise relatórios e o MP4 completo com áudio. Use npm run ode -- review para repetir a extração local no vídeo real.
8. Confira a pasta Drive, gere a capa completa conforme a skill de embalagem, salve-a em production/ID-DO-EPISODIO/, faça commit/push e envie para a pasta observada com npm run ode -- deliver --folder-id ID --file production/ID-DO-EPISODIO/thumbnail.jpg --role thumbnail. O workflow verifica pasta, tamanho, formato e readback do arquivo. Registre a revisão em production/ e use --role editorial-review para entregá-la também.

O estado local em work/production-state.json só organiza a sessão e não é fonte editorial. Os arquivos editáveis, skills, pesquisa, HTML, workflow e relatório final ficam no Git; derivados grandes ficam em artifacts e Drive, com hashes.

## Falhas e retomada

Não encurte o roteiro para quota de voz. Respeite retry/backoff do mesmo modelo e use cache por cena. Não peça regeneração total no gatilho: force_fresh_audio é input manual do workflow e só vale na primeira tentativa. Se o agente não puder assistir/escutar, registre essa limitação; métricas e transcrição não equivalem a revisão perceptual.

Produção direta sem testes é uma opção somente quando explicitamente pedida; o prompt --direct registra o modo e o commit usa [production direct]. Os gates necessários da produção continuam.
