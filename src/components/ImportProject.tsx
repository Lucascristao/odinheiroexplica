import { useMemo, useState } from "react";
import { ClipboardPaste, FileCheck2, FlaskConical } from "lucide-react";
import { exampleVideoProject } from "../lib/example-project";
import type { Json } from "../lib/database.types";
import { supabase } from "../lib/supabase";
import {
  hardRiskFlags,
  type VideoProject,
  videoProjectSchema,
} from "../lib/video-project-schema";

type Props = {
  onImported: () => void;
};

function formatIssues(error: unknown) {
  if (
    typeof error === "object" &&
    error !== null &&
    "issues" in error &&
    Array.isArray((error as { issues: unknown[] }).issues)
  ) {
    return (error as { issues: Array<{ path?: unknown[]; message?: string }> }).issues
      .slice(0, 8)
      .map((issue) => {
        const path = issue.path?.join(".") || "payload";
        return `${path}: ${issue.message ?? "valor inválido"}`;
      });
  }

  return ["JSON inválido ou fora do schema VideoProject v1.0."];
}

export function ImportProject({ onImported }: Props) {
  const [raw, setRaw] = useState("");
  const [busy, setBusy] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);

  const validation = useMemo(() => {
    if (!raw.trim()) return null;

    try {
      const json = JSON.parse(raw);
      const result = videoProjectSchema.safeParse(json);
      return result.success
        ? ({ ok: true, project: result.data } as const)
        : ({ ok: false, issues: formatIssues(result.error) } as const);
    } catch {
      return {
        ok: false,
        issues: ["JSON inválido. Verifique vírgulas, aspas e chaves."],
      } as const;
    }
  }, [raw]);

  const blockerFlags =
    validation?.ok
      ? validation.project.editorial.risk_flags.filter((flag) =>
          hardRiskFlags.has(flag),
        )
      : [];

  async function importProject(project: VideoProject) {
    if (!supabase) return;

    setBusy(true);
    setResultMessage(null);

    const { data, error } = await supabase.rpc("import_video_project", {
      payload: project as unknown as Json,
    });

    if (error) {
      setResultMessage(`Falha ao importar: ${error.message}`);
      setBusy(false);
      return;
    }

    setResultMessage(`Projeto importado com sucesso. ID: ${data}`);
    setRaw("");
    setBusy(false);
    onImported();
  }

  return (
    <section className="panel import-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Novo vídeo</p>
          <h2>Importar pacote editorial</h2>
        </div>
        <button
          type="button"
          className="secondary-button"
          onClick={() =>
            setRaw(JSON.stringify(exampleVideoProject, null, 2))
          }
        >
          <FlaskConical size={17} />
          Carregar exemplo
        </button>
      </div>

      <p className="muted">
        Cole aqui o JSON VideoProject v1.0 produzido no ChatGPT. A validação
        acontece antes da gravação e o banco importa tudo em uma única transação.
      </p>

      <textarea
        className="json-input"
        spellCheck={false}
        placeholder={'{\n  "version": "1.0",\n  "story": { ... }\n}'}
        value={raw}
        onChange={(event) => {
          setRaw(event.target.value);
          setResultMessage(null);
        }}
      />

      {validation?.ok && (
        <div className="validation-box success">
          <FileCheck2 size={19} />
          <div>
            <strong>{validation.project.story.subject}</strong>
            <span>
              {validation.project.sources.length} fontes ·{" "}
              {validation.project.claims.length} claims ·{" "}
              {validation.project.script.scenes.length} cenas
            </span>
          </div>
        </div>
      )}

      {validation && !validation.ok && (
        <div className="validation-box error">
          <div>
            <strong>O pacote ainda não pode ser importado.</strong>
            <ul>
              {validation.issues.map((issue) => (
                <li key={issue}>{issue}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {blockerFlags.length > 0 && (
        <div className="validation-box warning">
          <div>
            <strong>Há bloqueadores editoriais no pacote.</strong>
            <span>{blockerFlags.join(", ")}</span>
          </div>
        </div>
      )}

      {resultMessage && <div className="notice">{resultMessage}</div>}

      <div className="import-actions">
        <span className="muted small">
          Importar não renderiza nem publica nada.
        </span>
        <button
          type="button"
          className="primary-button"
          disabled={!validation?.ok || busy}
          onClick={() =>
            validation?.ok ? importProject(validation.project) : undefined
          }
        >
          <ClipboardPaste size={17} />
          {busy ? "Importando..." : "Importar projeto"}
        </button>
      </div>
    </section>
  );
}
