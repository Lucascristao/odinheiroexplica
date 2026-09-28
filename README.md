# O Dinheiro Explica

Painel editorial para produção semiautomatizada de vídeos do canal **O Dinheiro Explica**.

## MVP atual

O primeiro ciclo implementa:

1. autenticação com Supabase;
2. importação de um pacote editorial `VideoProject v1.0`;
3. validação local com Zod;
4. gravação transacional no Supabase;
5. painel com projetos importados;
6. base pronta para render jobs, narração, Remotion, Google Drive e YouTube.

## Stack

- React + Vite + TypeScript
- Supabase Auth + Postgres
- Zod
- Remotion e TTS entram na próxima etapa

## Variáveis locais

Copie `.env.example` para `.env.local`:

```bash
VITE_SUPABASE_URL=
VITE_SUPABASE_PUBLISHABLE_KEY=
```

Nunca exponha `service_role` no frontend.

## Desenvolvimento

```bash
npm install
npm run dev
```

## Banco

As migrations ficam em `supabase/migrations`.

O importador usa a função RPC `import_video_project(payload jsonb)`, assim um pacote inválido não deixa projeto parcialmente gravado.

## Próximas etapas

- editor/revisão por cenas;
- render jobs;
- Kokoro TTS;
- Remotion;
- GitHub Actions;
- Google Drive;
- publicação e analytics do YouTube.
