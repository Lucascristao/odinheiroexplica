export type ProductionRequestOptions = {mode?: "normal" | "direct"; chooseTopic?: boolean};
export function productionChatRequest(request: string, options: ProductionRequestOptions = {}): string {
  const mode = options.mode ?? "normal";
  return `${request}

Produza no repositório https://github.com/Lucascristao/odinheiroexplica, na main, até entregar vídeo, título, descrição e capa na mesma pasta do Google Drive. A publicação no YouTube é manual.

Leia AGENTS.md e skills/ode-video/SKILL.md. Se sua IA não descobrir skills automaticamente, leia os arquivos indicados diretamente. Execute npm ci e npm run ode -- context para descobrir os contratos, capacidades e estado. Todo o procedimento está no Git; não depende de Claude nem da memória deste chat.

Modo: ${mode === "direct" ? "produção direta sem suítes de testes, prévias silenciosas, demos ou amostras de voz; use [production direct] nos commits e preserve os gates da produção real" : "normal, com contratos, auditorias, typecheck e verificações relevantes; aguarde o CI do mesmo commit antes de disparar"}.
${options.chooseTopic ? "Autorizo você a escolher uma pauta inédita após pesquisar e conferir o histórico. Preserve uma pauta aprovada e não peça nova confirmação para etapas autorizadas." : "Sem pauta aprovada nem autorização para você escolher, apresente três opções fundamentadas e aguarde a escolha antes de escrever daily.json."}

Use as skills por função. Registre um storyboard próprio antes do JSON. Faça objetos, contas e documentos demonstrarem a fala; nomes de efeitos não comprovam execução. HyperFrames é opcional por protagonista e recebe tempos reais após o alinhamento; texto, relações, câmera e legendas continuam auditados no Stage. A voz segue worker/voice-policy.json.

Execute npm run ode -- preflight. Registre alterações no Git e envie à main. Dispare npm run ode -- dispatch e acompanhe npm run ode -- status. Leia falhas e corrija preservando cache compatível; npm run ode -- resume --run-id ID retoma etapas falhas.

Leia os relatórios e o pacote visual extraído do MP4. Confira o vídeo real com áudio, corrija o necessário e gere a capa completa conforme docs/thumbnail-identity.md. Confirme todos os arquivos no Drive antes de anunciar conclusão. Registre limitações de observação; relatório automático não substitui revisão editorial.`;
}
