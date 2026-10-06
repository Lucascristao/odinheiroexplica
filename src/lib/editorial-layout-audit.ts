import type {LayoutIssue} from "./editorial-layout";

export type LayoutAuditMode = "geometry-only" | "pre-voice" | "final-timing";

// Only the early composition pass may defer evidence files. Paid production
// still requires the asset-aware pass and the final real-narration pass.
export function partitionLayoutIssues<T extends LayoutIssue>(issues: T[], mode: LayoutAuditMode) {
  return {
    issues: issues.filter(issue => mode !== "geometry-only" || issue.code !== "missing-visual-asset"),
    deferred: mode === "geometry-only" ? issues.filter(issue => issue.code === "missing-visual-asset") : [],
  };
}

export function layoutRepairGuidance(code: string): string {
  switch (code) {
    case "icon-capacity":
      return "Amplie a região do protagonista ou use content_layout column; reserve espaço para ícone e texto sem reduzir a arte apenas para passar no gate.";
    case "text-capacity": case "title-capacity": case "dom-text-capacity": case "signal-capacity":
      return "Amplie a região ou ajuste o texto visual preservando o sentido; mantenha a fonte mínima e o roteiro.";
    case "connection-space": case "operation-space": case "equation-space":
      return "Reposicione os participantes e reserve um corredor livre para a relação/operador; preserve a demonstração e confira o percurso.";
    case "stack-order": case "stack-space":
      return "Organize os itens na ordem vertical declarada, reserve espaço lateral e ajuste moves; preserve a sequência explicada.";
    case "camera-capacity": case "photo-caption-capacity":
      return "Ajuste câmera e composição para manter inteiros todos os fatos já visíveis e suas legendas; confira quadros intermediários.";
    case "animated-node-collision":
      return "Reserve espaço no percurso inteiro e ajuste direção, posições ou tempos da entrada/movimento.";
    case "missing-visual-asset":
      return "Prepare o arquivo real da foto/recorte e refaça o passe pre-voice com o manifest de assets antes do TTS.";
    case "missing-final-timing":
      return "Use o render-input alinhado à narração real; tempos estimados não aprovam o passe final.";
    default:
      return "Revise o elemento indicado com a fonte real e refaça a auditoria; não retire relações ou efeitos só para passar no gate.";
  }
}

export function githubAnnotation(message: string): string {
  return message.replace(/%/g, "%25").replace(/\r/g, "%0D").replace(/\n/g, "%0A");
}
