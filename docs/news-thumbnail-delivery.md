# Capa opcional na preparação da notícia automática

Este procedimento pertence ao formato `ode-news-single` autorizado para publicação autônoma. A capa é preparada no começo, depois de fechar a pauta, o título, o roteiro e a embalagem e **antes do commit do episódio que inicia a produção**. O fluxo de vídeos explicativos com entrega manual no Drive permanece em `docs/thumbnail-identity.md`.

## Preparar e conferir

1. Conferir se esta execução dispõe realmente de geração nativa de imagem, acesso aos bytes finais, inspeção visual e escrita binária no GitHub. O conector GitHub oferece `create_blob` com `encoding="base64"`; isso permite enviar PNG/JPEG, mas não garante que a tarefa agendada disponha do gerador ou dos bytes da imagem. Se faltar uma capacidade, registrar qual e seguir com miniatura automática.
2. Fechar o episódio e executar o adaptador canônico `worker/news_single_project.py --input ARQUIVO_DO_EPISODIO --output PROJETO_TEMPORARIO`. O resultado é determinístico. Usar seu `packaging.thumbnails[0].contract` para gerar a arte completa: assunto e promessa verdadeiros, headline exata, 1280x720, identidade do canal e nenhuma exclusão presente. Não gerar antes de definir esses elementos nem trocar o título depois sem rever a auditoria.
3. Inspecionar os pixels da imagem completa e sua leitura em 320x180 segundo `docs/thumbnail-identity.md`. Preencher uma auditoria somente com observações reais. Se não for possível inspecionar ou a arte estiver inadequada, refazer ou seguir sem capa; não aprovar por intenção do prompt.
4. Preparar `production/EPISODIO/thumbnail.jpg` ou `.png` e `production/EPISODIO/thumbnail-audit.json`. Usar `normalized_project_sha256(PROJETO_TEMPORARIO)`, `contract_sha256(contract)` e `file_sha256(IMAGEM)` de `worker/thumbnail_contract.py`. O hash do projeto é dos bytes que o adaptador escreve, normalizados em LF; não é o hash do JSON bruto de `news/episodes`. A serialização canônica é `json.dumps(project, ensure_ascii=False, indent=2) + "\n"`. Não incluir mudanças de captura, áudio ou tempos posteriores nesse hash.
5. Validar a auditoria com `validate_thumbnail_audit(root, project, image, project_source_path=PROJETO_TEMPORARIO)`. Não reutilizar auditoria de outro episódio ou de um projeto alterado. As sete verificações, as observações, as exclusões conferidas e a data real continuam obrigatórias. Este validador confere integridade; a inspeção semântica dos pixels cabe ao agente.

## Gravar o pacote antes do render

Quando o conector GitHub for usado, preparar um único commit com os três arquivos:

- `news/episodes/YYYY-MM-DD-SLOT.json`;
- `production/EPISODIO/thumbnail.jpg` ou `.png`;
- `production/EPISODIO/thumbnail-audit.json`.

Ler a revisão atual de `main` e sua árvore. Criar o blob da imagem com **base64 dos bytes reais** e `encoding="base64"`; criar os blobs UTF-8 dos dois JSONs. Usar `create_tree` com `base_tree_sha` da árvore atual e as três entradas `{path, mode:"100644", type:"blob", sha}`. Criar o commit com `parent_sha` da revisão lida e atualizar `main` com `update_ref`, `expected_sha` da mesma revisão e `force=false`. Se a revisão mudar, ler o novo estado, conferir novamente que o slot continua ausente e reconstruir sobre a árvore atual; não sobrescrever o trabalho concorrente. Em checkout local, o mesmo pacote pode ser adicionado e enviado em um único commit.

Não enviar bytes binários por uma ferramenta que só grava texto. Não publicar o JSON primeiro e acrescentar a capa depois: o render lê a revisão do gatilho e não recebe arquivos de commits futuros. Criar blobs ou uma árvore sem atualizar a branch também não inicia a produção. Se faltar suporte ao pacote completo, registrar a limitação e gravar somente o episódio, sem auditoria fictícia.

## Anexar e publicar

`render-news-single.yml` faz o render e QA, confere a capa presente na revisão inicial, envia o vídeo privado, anexa a imagem validada ao mesmo `video_id` e programa a publicação. Não é necessário esperar o vídeo terminar para criar a arte. Capa ausente, inválida ou erro no anexo são registrados e a publicação segue com a miniatura automática do YouTube; os gates de fatos, canal, autenticação, QA e integridade do vídeo continuam obrigatórios.

Uma capa acrescentada depois do início não tem anexo automático garantido nessa execução. Não iniciar outro render ou upload para incluí-la. Uma eventual entrega posterior deve operar explicitamente sobre o vídeo existente e seus recibos, preservando identidade e autorização.

O relatório deve distinguir `capa gerada`, `capa gravada no GitHub` e `capa anexada ao YouTube`. Só o recibo do anexo confirma a última etapa. A disponibilidade de geração e transferência em uma tarefa agendada e o primeiro pacote completo com capa ainda precisam ser demonstrados em execução real; a existência deste procedimento não é prova de sucesso.
