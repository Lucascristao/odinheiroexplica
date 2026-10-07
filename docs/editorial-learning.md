# Aprender com cada publicação

O diagnóstico está em [análise de 07/10/2026](analise-crescimento-youtube-2026-10-07.md). `research/youtube-analytics-2026-10-07.json` contém observações agregadas manuais dos prints, não dados individuais nem integração com a conta. CTR de 2,4% e retenção de 37% aos 30s das bets orientam hipóteses; não explicam sozinhos todos os vídeos.

## Antes do roteiro

Defina situação concreta, crença anterior e descoberta que a pessoa levará. Hipótese inicial: brasileiros tentando entender cobranças, contratos e decisões que afetam seu dinheiro. Não deduza gênero, idade ou renda de relatórios indisponíveis. Escolha pautas inéditas relacionadas por essa necessidade, após conferir histórico e commits.

Registre uma mudança observável e uma hipótese antes da publicação. Entregar a primeira distinção útil na abertura pode reduzir abandono; isso não é garantia. Não mude tudo e depois atribua o resultado a uma só variável. Pesquise referências fortes e fracas com a mesma necessidade do público, registrando URL, data, idade e limite de comparação. Views públicas não revelam CTR ou retenção. Extraia princípios sem copiar roteiro, thumbnail ou conclusão.

## Contrato do próximo episódio

Gancho apresenta a pergunta; abertura entrega uma descoberta ou demonstração, além de suspense. Apresente Roberto depois do gancho. Conceito entra quando necessário. Inscrição vem depois de valor. Cada unidade responde uma pergunta e abre a próxima. Corte repetição; não imponha 20 minutos, duplique parágrafos ou esconda toda a resposta.

Preencha `editorial.learning_strategy`, conforme `src/lib/editorial-learning.ts`:

- `version: "1.0"`;
- `audience`: `situation`, `prior_belief`, `desired_understanding`;
- `hypothesis`: `change`, `expected_effect`, `evaluation`;
- `first_value`: `{scene_id, quote}` literal e único na primeira cena;
- `promises`: exatamente duas entradas (`surface: "title"` e `"thumbnail"`). `text` reproduz a embalagem. `kind` é `explanation`, `conditional_result` ou `quantitative_generalization`. Declare `claim_ids`, `learning_unit_ids`, `example_ids`, `delivery` e `boundary` com referências literais;
- `progression`: uma entrada por unidade existente, com `learning_unit_id`, `new_information`, `next_question`. A última pode convidar a conferir a própria situação, sem suspense artificial.

Promessa quantitativa geral exige demonstração factual: hipótese isolada não prova resultado universal. Condições aparecem na fala e tela. Validador verifica referências e proveniência, não decide se a prova sustenta a conclusão. A revisão semântica justifica isso. O hash de projetos com estratégia inclui estratégia e embalagem.

Para novo episódio, execute `npm run ode -- preflight --new-episode`: exige o contrato antes do TTS. Retomadas históricas continuam compatíveis e não invalidam voz só para preencher contrato novo.

## Revisão do vídeo real

Contatos mostram antes/durante/depois/intervalo por evento, mais início, quartos e fim da cena. Não pulam o estado final por um stride entre entradas. `completed_before_next_event` refere-se à duração nominal, não à compreensão nem à ausência de outros movimentos. Tempos e `timing_source` continuam explícitos.

Assista e escute: registre segundo real da primeira descoberta, apresentação, correspondência com a imagem, prova e condições da promessa, conclusão e legibilidade no celular. Confira âncoras estimadas nos eventos críticos. Pixels em movimento e vazio no instante de entrada não demonstram ritmo percebido. Mudança visual não exige ressíntese integral.

## Medição após publicação manual

Registre snapshots do Studio em 72h, 7 e 28 dias. Compare formato, idade, janela e origem semelhantes. Salve impressões, CTR, duração média, retenção inicial, watch time e funil disponíveis. Ausência é `null`, diferente de zero. Pouca amostra: “inconclusivo”. Frequência deve ser sustentável; não sacrifique revisão por suposta quota diária.

Importação local de CSV do modo avançado (ID e título obrigatórios; português ou inglês):

```powershell
npm run ode -- analytics --input research/export-studio.csv --start 2026-10-07 --end 2026-10-10 --locale pt-BR --format long --output research/youtube/snapshot-2026-10-10.json
npm run ode -- analytics --input research/youtube/snapshot-2026-10-10.json
```

JSON canônico usa `record_type: "video_performance_snapshot"`, schema em `src/lib/youtube-analytics.ts`. CSV mantém `published_at: null`; preencha ISO com fuso a partir de fonte verificada para comparar idade. Retenção aos 30s e watch time de impressões podem exigir preenchimento manual por vídeo. Não associar vídeos por título nem misturar totais. Não há coleta automática, previsão ou vencedor automático.

Desde 24/08/2026, views e denominadores engajados exigem cuidado. Não reconstrua duração média engajada dividindo watch time agregado por views gerais. O importador deriva somente `watch_seconds_per_impression`, quando existem watch time **de impressões** e impressões da mesma janela/origem. Teste nativo de título/capa, quando escolhido para uma publicação, precisa de amostra e avalia tempo de exibição; trocas sequenciais não são prova causal.

Fontes: [métricas](https://support.google.com/youtube/answer/12220281?hl=en), [CTR](https://support.google.com/youtube/answer/7628154?hl=pt-BR), [retenção](https://support.google.com/youtube/answer/9314415?hl=pt-BR), [teste nativo](https://support.google.com/youtube/answer/16391400?hl=pt-BR), [frequência](https://support.google.com/youtube/answer/141805?hl=pt-br).
