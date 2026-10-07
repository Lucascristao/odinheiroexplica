# Arquitetura de produção

A IA autora lê o repositório, apura, escreve o VideoProject e acompanha a entrega. Pode ser qualquer agente com leitura/escrita de arquivos e acesso ao GitHub; nenhum SDK de Claude participa do motor. O botão do painel copia esse pedido.

## Caminho executado

Pedido → skills/ode-video → pesquisa e storyboard → video/data/daily.json → contratos editoriais, fontes, pronúncia e layout → Gemini 3.8 Live / Roberto–Charon → alinhamento ao áudio real → arte HyperFrames → Remotion → QA do MP4 → pacote de revisão → Google Drive. A publicação no YouTube é manual.

O JSON é a interface estável entre autoria e execução. Texto, claims, provas, operações, câmera e legendas pertencem ao Stage. HyperFrames renderiza HTML/GSAP local em um objeto do Stage, com envelope explícito. Recebe os frames dos beats depois do alinhamento, produz um clipe mudo por objeto e não cria voz, fatos ou legendas. O compilador valida fps, dimensões, duração e número de frames.

## Onde está cada responsabilidade

- AGENTS.md: autorização, pauta, qualidade e condução até a entrega.
- skills/ e frame.md: procedimentos por função e identidade do canal.
- src/lib/: contratos compartilhados, normalização e geometria.
- video/hyperframes/: arte HTML autoral determinística, sem rede.
- scripts/ode.ts: contexto, prompt, preflight, disparo, acompanhamento e retomada.
- worker/: preparação, voz, alinhamento, QA, embalagem e entrega.
- .github/workflows/render-daily.yml: execução real com secrets do GitHub.

As dependências HyperFrames e GSAP estão fixadas no lockfile. Clipes reutilizam cache por fonte HTML, GSAP, versão do motor, dimensão, duração e tempos; mudanças visuais não alteram o cache de voz. A política de voz continua em worker/voice-policy.json, sem troca automática de modelo.

## Revisão e limites

O motor extrai quadros do MP4 antes/durante/depois dos beats e mede mudança de pixels em regiões. Isso ajuda a localizar vazios e transições; não aprova compreensão, fatos, fala ou retenção. O agente faz essa revisão, registra limitações e corrige cenas preservando o áudio compatível. Os relatórios e seus hashes acompanham a entrega.

O painel também mantém importação transacional e autenticação via Supabase; isso é independente do render em Actions. Chaves privilegiadas permanecem no servidor. Não é necessário consultar ou migrar o banco para gerar um vídeo por Git.

Leia docs/production-portable.md para executar o fluxo.
