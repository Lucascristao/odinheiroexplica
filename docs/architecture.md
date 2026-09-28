# Arquitetura revisada

## Objetivo

Criar uma redação semiautomatizada para o canal O Dinheiro Explica. A automação cuida do trabalho mecânico, enquanto pauta e aprovação continuam sob controle humano.

## Princípios editoriais

1. Um assunto forte por vídeo.
2. Duração definida pela história, não por meta artificial.
3. Título e thumbnail chamativos, mas sustentados pelo conteúdo.
4. Claims importantes precisam apontar para fontes.
5. Conteúdo informativo, sem recomendação individual de compra ou venda.
6. Bloqueadores editoriais impedem renderização futura, mas podem ser importados para correção.
7. Estrutura e visuais devem variar para não produzir conteúdo repetitivo em escala.

## Fluxo do MVP

ChatGPT
→ VideoProject v1.0
→ validação Zod
→ RPC transacional do Supabase
→ projeto + fontes + claims + cenas
→ revisão no painel

A renderização ainda não faz parte desta primeira entrega.

## Por que o import é uma RPC

O pacote contém várias entidades. Fazer inserts separados pelo navegador permitiria estados parciais em caso de falha.

A função `import_video_project` executa a importação em uma transação do Postgres. Se qualquer fonte, claim ou cena falhar, o projeto inteiro volta ao estado anterior.

## Segurança

Todas as tabelas públicas usam RLS.

Cada registro carrega `owner_id` e as tabelas filhas usam uma foreign key composta `(project_id, owner_id)`. Isso impede que um usuário associe dados próprios a um projeto pertencente a outro usuário.

A chave `service_role` nunca entra no frontend.

## Fases

### Fase 1, em andamento

- Auth
- painel
- schema VideoProject
- importação atômica
- listagem de projetos

### Fase 2

- página de revisão do projeto
- edição de roteiro por cena
- claims e fontes lado a lado
- guardas de transição de status

### Fase 3

- Kokoro TTS
- cache de áudio por cena
- duração calculada pelo áudio

### Fase 4

- Remotion
- biblioteca de componentes visuais
- render parcial por cena
- render final

### Fase 5

- GitHub Actions
- Google Drive
- thumbnails A/B/C

### Fase 6

- YouTube
- analytics
- retenção ligada às cenas
- aprendizado editorial
