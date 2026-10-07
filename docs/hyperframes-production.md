# HyperFrames no motor diário

A integração acrescenta arte HTML a elementos kind: object. O Stage continua dono da posição, visibilidade, câmera e texto. Isso mantém a auditoria de layout e a relação dos dados com os claims. Não há migração geral de cenas para um renderer sem os contratos atuais.

## Contrato

O elemento declara hyperframes.entry em video/hyperframes/NOME/index.html, initial_state, width/height pares e states com anchor literal de um beat da mesma cena. O HTML declara estados suportados em data-ode-states, composição ode, marcadores __ODE_DURATION__, __ODE_WIDTH__, __ODE_HEIGHT__ e <!--ODE_DATA-->. window.ODE entrega duração e states com frame/timing_source alinhados. A timeline GSAP é pausada e exposta em window.__timelines.

A preparação antes da voz verifica caminho, fonte local e anchors. Depois do áudio real, o compilador injeta dados, faz lint, renderiza e verifica 30 fps, dimensão, duração e contagem de frames. O Stage usa clip_file gerado. Não escreva clip_file manualmente em daily.json.

## Autoria

Use car-gate e group-pool como exemplos autorais, não como layout universal. Desenhos são esquemas, sem marcas ou representação de dados reais. Texto, contas, recortes documentais e grifos permanecem nos elementos auditáveis do Stage. Proíba relógio de parede, aleatoriedade e recursos de rede no runtime. SVGs podem usar namespace padrão local; isso não autoriza busca externa.

Não suponha que um nome de estado comprova animação. Confira o clipe e o MP4 real. Não imponha movimento decorativo sobre uma demonstração que exige leitura.

Cache: SHA-256 da fonte e assets, versão de HyperFrames e GSAP, dimensões, duração e frames dos estados. A execução registra daily-hyperframes-manifest.json e entrega o relatório de revisão do MP4.

