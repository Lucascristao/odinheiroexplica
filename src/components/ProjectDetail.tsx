import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  FileText,
  Save,
  ShieldCheck,
} from "lucide-react";
import type {
  Json,
  ProjectClaimRow,
  ProjectSceneRow,
  ProjectSourceRow,
  VideoProjectRow,
} from "../lib/database.types";
import { supabase } from "../lib/supabase";
import { hardRiskFlags } from "../lib/video-project-schema";

type Props = {
  project: VideoProjectRow;
  onBack: () => void;
  onProjectUpdated: (project: VideoProjectRow) => void;
};

type PackageData = {
  script?: {
    hook?: string;
    closing?: string;
  };
  packaging?: {
    titles?: Array<{ id?: string; text?: string; rationale?: string }>;
    thumbnails?: Array<{
      id?: string;
      headline?: string;
      concept?: string;
      visual_prompt?: string;
    }>;
  };
};

function asPackageData(value: Json): PackageData {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    return value as unknown as PackageData;
  }

  return {};
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    IMPORTED: "Importado",
    VALIDATING: "Em revisão",
    READY_TO_RENDER: "Pronto para render",
    RENDERING: "Renderizando",
    READY_TO_REVIEW: "Pronto para assistir",
    APPROVED: "Aprovado",
    UPLOADED: "Enviado",
    PUBLISHED: "Publicado",
    ANALYZING: "Em análise",
    ARCHIVED: "Arquivado",
    ERROR: "Erro",
  };

  return labels[status] ?? status;
}

function transitionError(message: string) {
  if (message.includes("editorial_blockers_present")) {
    return "Ainda existem bloqueadores editoriais no projeto.";
  }
  if (message.includes("claims_not_ready")) {
    return "Todos os claims precisam estar verificados e ligados a pelo menos uma fonte.";
  }
  if (message.includes("scenes_required")) {
    return "O projeto precisa ter pelo menos uma cena.";
  }
  if (message.includes("scene_narration_required")) {
    return "Todas as cenas precisam ter texto de narração.";
  }
  if (message.includes("state_changed")) {
    return "O estado do projeto mudou em outra operação. Atualize e tente novamente.";
  }
  if (message.includes("transition_not_allowed")) {
    return "Essa mudança de etapa não é permitida.";
  }

  return message;
}

export function ProjectDetail({
  project,
  onBack,
  onProjectUpdated,
}: Props) {
  const [sources, setSources] = useState<ProjectSourceRow[]>([]);
  const [claims, setClaims] = useState<ProjectClaimRow[]>([]);
  const [scenes, setScenes] = useState<ProjectSceneRow[]>([]);
  const [ownerId, setOwnerId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyStatus, setBusyStatus] = useState(false);
  const [savingSceneId, setSavingSceneId] = useState<string | null>(null);
  const [savingClaimId, setSavingClaimId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const packageData = useMemo(
    () => asPackageData(project.raw_payload),
    [project.raw_payload],
  );

  const loadData = useCallback(async () => {
    if (!supabase) return;

    setLoading(true);
    setMessage(null);

    const {
      data: { user },
      error: userError,
    } = await supabase.auth.getUser();

    if (userError || !user) {
      setMessage(userError?.message ?? "Usuário não encontrado.");
      setLoading(false);
      return;
    }

    setOwnerId(user.id);

    const [sourceResult, claimResult, sceneResult] = await Promise.all([
      supabase
        .from("project_sources")
        .select("*")
        .eq("project_id", project.id)
        .eq("owner_id", user.id)
        .order("created_at", { ascending: true }),
      supabase
        .from("project_claims")
        .select("*")
        .eq("project_id", project.id)
        .eq("owner_id", user.id)
        .order("created_at", { ascending: true }),
      supabase
        .from("project_scenes")
        .select("*")
        .eq("project_id", project.id)
        .eq("owner_id", user.id)
        .order("scene_index", { ascending: true }),
    ]);

    const firstError =
      sourceResult.error ?? claimResult.error ?? sceneResult.error;

    if (firstError) {
      setMessage(firstError.message);
    } else {
      setSources(sourceResult.data ?? []);
      setClaims(claimResult.data ?? []);
      setScenes(sceneResult.data ?? []);
    }

    setLoading(false);
  }, [project.id]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const blockers = project.risk_flags.filter((flag) => hardRiskFlags.has(flag));
  const claimsReady =
    claims.length > 0 &&
    claims.every(
      (claim) =>
        claim.verification_status === "verified" &&
        claim.source_keys.length > 0,
    );
  const scenesReady =
    scenes.length > 0 && scenes.every((scene) => scene.narration.trim().length > 0);
  const editorialReady =
    blockers.length === 0 && claimsReady && scenesReady;

  async function transition(nextStatus: string) {
    if (!supabase) return;

    setBusyStatus(true);
    setMessage(null);

    const { data, error } = await supabase.rpc(
      "transition_video_project_status",
      {
        p_project_id: project.id,
        p_expected_status: project.status,
        p_new_status: nextStatus,
      },
    );

    if (error) {
      setMessage(transitionError(error.message));
    } else if (data) {
      onProjectUpdated(data);
    }

    setBusyStatus(false);
  }

  async function saveScene(scene: ProjectSceneRow) {
    if (!supabase || !ownerId) return;

    setSavingSceneId(scene.id);
    setMessage(null);

    const { data, error } = await supabase
      .from("project_scenes")
      .update({
        title: scene.title,
        narration: scene.narration,
      })
      .eq("id", scene.id)
      .eq("project_id", project.id)
      .eq("owner_id", ownerId)
      .select("*")
      .single();

    if (error) {
      setMessage(error.message);
    } else if (data) {
      setScenes((current) =>
        current.map((item) => (item.id === data.id ? data : item)),
      );
      setMessage(`Cena ${scene.scene_index + 1} salva.`);
    }

    setSavingSceneId(null);
  }

  async function setClaimVerification(
    claim: ProjectClaimRow,
    verificationStatus: "verified" | "unverified",
  ) {
    if (!supabase || !ownerId) return;

    setSavingClaimId(claim.id);
    setMessage(null);

    const { data, error } = await supabase
      .from("project_claims")
      .update({ verification_status: verificationStatus })
      .eq("id", claim.id)
      .eq("project_id", project.id)
      .eq("owner_id", ownerId)
      .select("*")
      .single();

    if (error) {
      setMessage(error.message);
    } else if (data) {
      setClaims((current) =>
        current.map((item) => (item.id === data.id ? data : item)),
      );
    }

    setSavingClaimId(null);
  }

  function updateScene(
    sceneId: string,
    field: "title" | "narration",
    value: string,
  ) {
    setScenes((current) =>
      current.map((scene) =>
        scene.id === sceneId ? { ...scene, [field]: value } : scene,
      ),
    );
  }

  function renderStatusAction() {
    if (project.status === "IMPORTED") {
      return (
        <button
          className="primary-button"
          disabled={busyStatus}
          onClick={() => void transition("VALIDATING")}
        >
          <ShieldCheck size={17} />
          Iniciar revisão
        </button>
      );
    }

    if (project.status === "VALIDATING") {
      return (
        <button
          className="primary-button"
          disabled={busyStatus || !editorialReady}
          onClick={() => void transition("READY_TO_RENDER")}
          title={
            editorialReady
              ? "Liberar projeto para a etapa de renderização"
              : "Resolva os itens da revisão antes de avançar"
          }
        >
          <CheckCircle2 size={17} />
          Marcar pronto para render
        </button>
      );
    }

    if (project.status === "READY_TO_RENDER") {
      return (
        <button
          className="secondary-button"
          disabled={busyStatus}
          onClick={() => void transition("VALIDATING")}
        >
          Reabrir revisão
        </button>
      );
    }

    return null;
  }

  return (
    <section className="project-detail">
      <div className="detail-toolbar">
        <button className="text-icon-button" onClick={onBack}>
          <ArrowLeft size={18} />
          Projetos
        </button>
        <span className="status-chip">{statusLabel(project.status)}</span>
      </div>

      <header className="detail-header">
        <div>
          <p className="eyebrow">Revisão editorial</p>
          <h1>{project.subject}</h1>
          {project.angle && <p className="muted hero-copy">{project.angle}</p>}
        </div>
        <div className="detail-actions">{renderStatusAction()}</div>
      </header>

      {message && <div className="notice">{message}</div>}

      <section className="readiness-grid">
        <article className={`readiness-card ${blockers.length === 0 ? "ok" : "bad"}`}>
          <span>Bloqueadores</span>
          <strong>{blockers.length}</strong>
          <small>
            {blockers.length === 0 ? "Nenhum bloqueio crítico" : blockers.join(", ")}
          </small>
        </article>
        <article className={`readiness-card ${claimsReady ? "ok" : "bad"}`}>
          <span>Claims</span>
          <strong>
            {claims.filter((claim) => claim.verification_status === "verified").length}/
            {claims.length}
          </strong>
          <small>Verificados e com fonte</small>
        </article>
        <article className={`readiness-card ${scenesReady ? "ok" : "bad"}`}>
          <span>Cenas</span>
          <strong>{scenes.length}</strong>
          <small>{scenesReady ? "Narração completa" : "Há cena sem narração"}</small>
        </article>
      </section>

      {loading ? (
        <section className="panel">
          <p className="muted">Carregando revisão...</p>
        </section>
      ) : (
        <>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Embalagem</p>
                <h2>Títulos e thumbnail</h2>
              </div>
            </div>

            {packageData.script?.hook && (
              <div className="hook-box">
                <span>Gancho</span>
                <strong>{packageData.script.hook}</strong>
              </div>
            )}

            <div className="packaging-grid">
              <div>
                <h3>Títulos</h3>
                <div className="stack-list">
                  {(packageData.packaging?.titles ?? []).map((title, index) => (
                    <article className="compact-card" key={title.id ?? index}>
                      <span className="option-index">{String.fromCharCode(65 + index)}</span>
                      <div>
                        <strong>{title.text ?? "Sem título"}</strong>
                        {title.rationale && <small>{title.rationale}</small>}
                      </div>
                    </article>
                  ))}
                </div>
              </div>

              <div>
                <h3>Thumbnails</h3>
                <div className="stack-list">
                  {(packageData.packaging?.thumbnails ?? []).map((thumb, index) => (
                    <article className="compact-card" key={thumb.id ?? index}>
                      <span className="option-index">{String.fromCharCode(65 + index)}</span>
                      <div>
                        <strong>{thumb.headline ?? "Sem headline"}</strong>
                        <small>{thumb.concept ?? "Sem conceito"}</small>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Evidências</p>
                <h2>Claims</h2>
              </div>
              <span className="muted small">
                {claims.length} afirmações verificáveis
              </span>
            </div>

            <div className="stack-list top-gap">
              {claims.map((claim) => {
                const linkedSources = sources.filter((source) =>
                  claim.source_keys.includes(source.source_key ?? ""),
                );
                const canVerify = linkedSources.length > 0;
                const isVerified = claim.verification_status === "verified";

                return (
                  <article className="claim-card" key={claim.id}>
                    <div className="claim-main">
                      <div className="claim-meta">
                        <span className={`verification-dot ${isVerified ? "verified" : ""}`} />
                        <span>{claim.claim_key ?? "claim"}</span>
                        <span>{claim.confidence}</span>
                      </div>
                      <p>{claim.claim_text}</p>

                      <div className="source-links">
                        {linkedSources.length === 0 ? (
                          <span className="risk-row">
                            <AlertTriangle size={14} />
                            Sem fonte vinculada
                          </span>
                        ) : (
                          linkedSources.map((source) => (
                            <a
                              key={source.id}
                              href={source.url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <ExternalLink size={13} />
                              {source.publisher ?? source.title ?? "Fonte"}
                            </a>
                          ))
                        )}
                      </div>
                    </div>

                    <button
                      className={isVerified ? "secondary-button" : "primary-button"}
                      disabled={savingClaimId === claim.id || (!isVerified && !canVerify)}
                      onClick={() =>
                        void setClaimVerification(
                          claim,
                          isVerified ? "unverified" : "verified",
                        )
                      }
                    >
                      {isVerified ? "Reabrir" : "Verificar"}
                    </button>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Pesquisa</p>
                <h2>Fontes</h2>
              </div>
              <span className="muted small">{sources.length} fontes</span>
            </div>

            <div className="source-grid top-gap">
              {sources.map((source) => (
                <a
                  className="source-card"
                  key={source.id}
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  <div>
                    <span className="source-type">{source.source_type ?? "fonte"}</span>
                    <strong>{source.title ?? source.publisher ?? source.url}</strong>
                    <small>{source.publisher ?? source.url}</small>
                  </div>
                  <ExternalLink size={16} />
                </a>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Roteiro</p>
                <h2>Cenas</h2>
              </div>
              <span className="muted small">{scenes.length} cenas</span>
            </div>

            <div className="scene-list top-gap">
              {scenes.map((scene) => (
                <article className="scene-editor" key={scene.id}>
                  <div className="scene-number">{scene.scene_index + 1}</div>
                  <div className="scene-fields">
                    <div className="scene-heading-row">
                      <input
                        className="scene-title-input"
                        value={scene.title ?? ""}
                        placeholder="Título interno da cena"
                        onChange={(event) =>
                          updateScene(scene.id, "title", event.target.value)
                        }
                      />
                      <span className="visual-chip">
                        {scene.visual_type ?? "VISUAL"}
                      </span>
                    </div>

                    <textarea
                      className="scene-narration"
                      value={scene.narration}
                      placeholder="Texto de narração"
                      onChange={(event) =>
                        updateScene(scene.id, "narration", event.target.value)
                      }
                    />

                    <div className="scene-footer">
                      <span className="muted small">
                        {scene.claim_keys.length > 0
                          ? `Claims: ${scene.claim_keys.join(", ")}`
                          : "Sem claim factual vinculado"}
                      </span>
                      <button
                        className="secondary-button"
                        disabled={savingSceneId === scene.id}
                        onClick={() => void saveScene(scene)}
                      >
                        <Save size={16} />
                        {savingSceneId === scene.id ? "Salvando..." : "Salvar cena"}
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="panel compact-summary">
            <FileText size={20} />
            <div>
              <strong>Próxima etapa</strong>
              <p className="muted">
                Quando o projeto estiver pronto para render, entraremos na geração
                de voz por cena. A duração do áudio passará a determinar a timeline
                do vídeo.
              </p>
            </div>
          </section>
        </>
      )}
    </section>
  );
}
