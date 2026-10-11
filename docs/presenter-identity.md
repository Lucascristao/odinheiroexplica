# Roberto consistente nas capas das notícias

O usuário autorizou um apresentador virtual original e consistente nas capas. Desde a data `news_enabled_since` de `worker/presenter-identity.json`, o adaptador de notícias inclui `presenter_identity` no contrato. Projetos históricos conservam os contratos e caches anteriores. A voz continua Roberto/Charon, exclusivamente Gemini 3.8 Live; esta mudança não cria avatar falante no vídeo.

## Identidade no motor

A referência é `video/public/presenters/roberto/roberto-v1.png`, gerada nativamente no ChatGPT, transparente, sem copiar pessoa real. O registro associa ID, caminho e SHA-256. O compositor usa diretamente esses pixels: não pede ao gerador outra pessoa, não espelha, não recolore, não altera traços ou expressões. O tamanho uniforme e a posição podem variar; novas poses e expressões exigem referências próprias previamente conferidas, sem substituição silenciosa da identidade.

O gerador nativo cria somente o **fundo da notícia**, sem texto e sem pessoas. A headline e o retrato são compostos pelo Remotion. Reserve espaço para a notícia e o rosto inteiro; não transforme o retrato em obstáculo para o objeto principal. As novas capas personalizadas usam esse mesmo Roberto. A política de publicação mantém capa opcional: falha de capa não impede vídeo válido de usar a miniatura automática do YouTube.

O catálogo inclui `roberto-v1-engaged.png`, uma edição nativa conferida contra a referência original, com expressão atenta, sobrancelhas inquisitivas e boca discretamente entreaberta. O motor escolhe essa referência fixa para notícias revisadas a partir de `2026-10-11T05:00:00Z`; contratos anteriores conservam o retrato original. `thumbnail_presenter_expression` pode selecionar somente uma das referências registradas. A expressão varia pelo catálogo, sem recriar o rosto a cada edição. O hash verifica o arquivo; a continuidade percebida foi inspecionada visualmente, sem reconhecimento facial automático.

## Variações de pose e roupa autorizadas em 11/10/2026

O usuário pediu variações de posição e roupas mantendo o Roberto. Três novas edições nativas foram comparadas com a referência original em tamanho integral e no catálogo com largura de 320 px. São retratos PNG transparentes fixos, com prompts e auditorias próprios no mesmo diretório:

| ID em `thumbnail_presenter_expression` | Pose e roupa | Uso de composição |
| --- | --- | --- |
| `roberto-v1-navy-left` | Blazer azul-marinho, camisa azul-clara, três quartos olhando à esquerda do observador | Retrato à direita, olhando para o assunto à esquerda |
| `roberto-v1-blue-right` | Camisa azul, três quartos olhando à direita do observador | Retrato à esquerda, olhando para o assunto à direita |
| `roberto-v1-burgundy-front` | Polo vinho, frontal com leve inclinação e sorriso discreto | Qualquer lado, conforme a prova e o texto |

Para próximas notícias revisadas desde `variants_enabled_after_utc`, o editor escolhe a referência conforme o layout e o tom factual da pauta, consultando a última capa para evitar repetição imediata. Sem escolha explícita, as janelas canônicas usam uma distribuição estável por data e janela entre as três novas referências. A escolha explícita prevalece. A retomada do mesmo episódio conserva a mesma referência; revisões anteriores ao corte não recebem as variantes. Os contratos históricos permanecem idênticos. A voz Roberto/Charon não varia com a roupa.

Abra `video/public/presenters/roberto/catalog-preview.html` para comparar os retratos. Essa inspeção é da biblioteca de referências; cada capa final ainda exige inspeção e auditoria próprias. O gerador de fundo continua sem pessoas, e o compositor usa os pixels registrados, sem espelhamento ou alteração do rosto.

## Execução local

Depois de apurar e fechar o episódio, adaptar o JSON a um projeto temporário. Não alterar `video/data/daily.json`:

```powershell
python worker/news_single_project.py --input news/preparations/AAAA-MM-DD-slot.json --output video/generated/thumbnail-project.json
npm run ode -- thumbnail-spec --project video/generated/thumbnail-project.json
npm run ode -- thumbnail-compose --project video/generated/thumbnail-project.json --background production/EPISODIO/thumbnail-background.png --portrait-side right --headline-position lower --portrait-size close
```

Lado do retrato: `left` ou `right`, contrário ao texto; posição da headline: `upper`, `middle`, `lower`; escala: `compact`, `standard`, `close`. A escala padrão é `close`, com o rosto em primeiro plano. Enquadre cabeça e rosto inteiros, mantenha expressão legível no celular e luz natural; evite aparência de foto publicitária ou retrato pequeno. Escolha posição e fundo pelo assunto real. Não há espelhamento para mudar o lado. `--replace` é necessário para sobrescrever uma capa existente após revisão.

O resultado é `production/EPISODIO/thumbnail.jpg`, acompanhado de `thumbnail-composition.json`. O recibo vincula referência, contrato, imagem final, fundo e escolhas de composição. Depois, **inspecione os pixels finais e 320x180** e escreva `thumbnail-audit.json` conforme `docs/news-thumbnail-delivery.md`. O recibo de composição não é avaliação de rosto, legibilidade ou promessa. O validador confirma os hashes e a procedência declarada, sem reconhecimento facial ou detecção automática de objetos.

## Execução da tarefa ChatGPT com GitHub

O agendamento editorial existente continua sendo o único. Não criar outra tarefa nem cron editorial.

1. Conferir se o slot ainda está ausente; pesquisar, escrever e validar o rascunho, sem iniciar o vídeo.
2. Gerar nativamente e inspecionar o **fundo** sem headline/rostos. No mesmo commit, gravar os bytes PNG em `production/EPISODIO/thumbnail-background.png` e o rascunho em `news/preparations/AAAA-MM-DD-slot.json`. Os opcionais `thumbnail_text_side`, `thumbnail_headline_position` e `thumbnail_portrait_size` escolhem a composição. Esses caminhos não disparam voz, render de vídeo nem YouTube.
3. O workflow `news-prepare-thumbnail.yml` adapta o projeto e compõe a capa usando a referência oficial. Seu único produto é o artefato `news-thumbnail-preparation`. Ele tem acesso de leitura, sem chaves de voz ou publicação. Conferir conclusão, baixar os bytes e **inspecionar a capa composta**, inteira e pequena.
4. Criar a auditoria verdadeira dos bytes e do projeto adaptado. Depois conferir novamente o slot e o SHA de `main` e gravar em **um commit**: o JSON final em `news/episodes`, `thumbnail.jpg`, `thumbnail-composition.json`, `thumbnail-audit.json` e o fundo correspondente, caso ainda não esteja na árvore atual. Preservar trabalho concorrente. O projeto final precisa ser idêntico ao usado na composição; mudanças de roteiro/título/contrato exigem nova composição/revisão.
5. O render valida a auditoria e o recibo com os hashes reais antes do anexo ao mesmo vídeo. Arquivo alterado, identidade diferente ou recibo ausente rejeita a capa, registrando a causa; não duplica upload.

Se a tarefa não tiver geração nativa, transferência binária, acesso ao artefato ou inspeção dos pixels, registrar a limitação e publicar o episódio sem capa personalizada. Não inventar aprovação, esperar indefinidamente ou usar Gemini para imagem. O sucesso desse caminho em uma execução assistida não comprova, por si, que todas as capacidades estarão disponíveis na ativação agendada do ChatGPT.
