import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  ExternalLink,
  FileText,
  HardDrive,
  SearchCheck,
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
};

type PackageData = {
  editorial?: {
    youtube_suitability?: {
      risk_level?: "low" | "medium" | "high";
      sensitive_topics?: string[];
      context_notes?: string;
      title_thumbnail_safe?: boolean;
      monetization_notes?: string;
    };
  };
  script?: {
    hook?: string;
    closing?: string;
  };
  packaging?: {
    strategy?: {
      click_reason?: string;
      visual_focus?: string;
      curiosity_gap?: string;
      mobile_readability?: string;
      anti_clickbait_check?: string;
      repetition_check?: string;
      youtube_safety_check?: string;
    };
    titles?: Array<{ id?: string; text?: string; rationale?: string }>;
    thumbnails?: Array<{
      id?: string;
      headline?: string;
      concept?: string;
      visual_prompt?: string;
    }>;
  };
  publication?: {
    description?: string;
    seo?: {
      primary_keyword?: string;
      secondary_keywords?: string[];
      search_intent?: string;
      description_strategy?: string;
    };
    tags?: string[];
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
    IDEA: "Pauta",
    RESEARCHED: "Pesquisa pronta",
    IMPORTED: "Projeto criado",
    VALIDATING: "Validando",
    READY_TO_RENDER: "Pronto para produzir",
    RENDERING: "Em produção",
    READY_TO_REVIEW: "Vídeo pronto",
    APPROVED: "Vídeo pronto",
    UPLOADED: "No Drive",
    PUBLISHED: "Publicado",
    ANALYZING: "Analisando",
    ARCHIVED: "Arquivado",
    ERROR: "Erro",
  };

  return labels[status] ?? status;
}

export function ProjectDetail({project, onBack}: Props) {
  const [sources, setSources] = useState<ProjectSourceRow[]>([]);
  const [claims, setClaims] = useState<ProjectClaimRow[]>([]);
  const [scenes, setScenes] = useState<ProjectSceneRow[]>([]);
  const [loading, setLoading] = useState(true);
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
      data: {user},
      error: userError,
    } = await supabase.auth.getUser();

    if (userError || !user) {
      setMessage(userError?.message ?? "Usuário não encontrado.");
      setLoading(false);
      return;
    }

    const [sourceResult, claimResult, sceneResult] = await Promise.all([
      supabase
        .from("project_sources")
        .select("*")
        .eq("project_id", project.id)
        .eq("owner_id", user.id)
        .order("created_at", {ascending: true}),
      supabase
        .from("project_claims")
        .select("*")
        .eq("project_id", project.id)
        .eq("owner_id", user.id)
        .order("created_at", {ascending: true}),
      supabase
        .from("project_scenes")
        .select("*")
        .eq("project_id", project.id)
        .eq("owner_id", user.id)
        .order("scene_index", {ascending: true}),
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
  const verifiedClaims = claims.filter(
    (claim) =>
      claim.verification_status === "verified" && claim.source_keys.length > 0,
  ).length;
  const suitability = packageData.editorial?.youtube_suitability;
  const seo = packageData.publication?.seo;

  return (
    <section className="project-detail">
      <div className="detail-toolbar">
        <button className="text-icon-button" onClick={onBack}>
          <ArrowLeft size={18} />
          Histórico
        </button>
        <span className="status-chip">{statusLabel(project.status)}</span>
      </div>

      <header className="detail-header">
        <div>
          <p className="eyebrow">Projeto do vídeo</p>
          <h1>{project.subject}</h1>
          {project.angle && <p className="muted hero-copy">{project.angle}</p>}
        </div>
        {project.drive_file_id && (
          <a
            className="primary-button project-drive-link"
            href={`https://drive.google.com/file/d/${project.drive_file_id}/view`}
            target="_blank"
            rel="noreferrer"
          >
            <HardDrive size={17} />
            Abrir no Drive
          </a>
        )}
      </header>

      {message && <div className="notice">{message}</div>}

      <section className="readiness-grid production-summary-grid">
        <article className={`readiness-card ${blockers.length === 0 ? "ok" : "bad"}`}>
          <span>Bloqueadores</span>
          <strong>{blockers.length}</strong>
          <small>
            {blockers.length === 0
              ? "Nenhum bloqueio crítico"
              : blockers.join(", ")}
          </small>
        </article>
        <article className="readiness-card ok">
          <span>Fatos com fonte</span>
          <strong>
            {verifiedClaims}/{claims.length}
          </strong>
          <small>Afirmações verificadas no pacote editorial</small>
        </article>
        <article className="readiness-card">
          <span>Cenas</span>
          <strong>{scenes.length}</strong>
          <small>
            {project.duration_seconds
              ? `Vídeo com ${Math.round(project.duration_seconds)}s`
              : "Timeline definida pela narração"}
          </small>
        </article>
      </section>

      {loading ? (
        <section className="panel">
          <p className="muted">Carregando projeto...</p>
        </section>
      ) : (
        <>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Embalagem</p>
                <h2>Título e thumbnail</h2>
              </div>
            </div>

            {packageData.script?.hook && (
              <div className="hook-box">
                <span>Gancho</span>
                <strong>{packageData.script.hook}</strong>
              </div>
            )}

            {packageData.packaging?.strategy?.click_reason && (
              <div className="hook-box">
                <span>Por que clicar</span>
                <strong>{packageData.packaging.strategy.click_reason}</strong>
                <small>
                  Foco: {packageData.packaging.strategy.visual_focus ?? "não informado"}
                </small>
              </div>
            )}

            <div className="packaging-grid">
              <div>
                <h3>Título</h3>
                <div className="stack-list">
                  {(packageData.packaging?.titles ?? []).map((title, index) => (
                    <article className="compact-card" key={title.id ?? index}>
                      <span className="option-index">1</span>
                      <div>
                        <strong>{title.text ?? "Sem título"}</strong>
                        {title.rationale && <small>{title.rationale}</small>}
                      </div>
                    </article>
                  ))}
                </div>
              </div>

              <div>
                <h3>Thumbnail</h3>
                <div className="stack-list">
                  {(packageData.packaging?.thumbnails ?? []).map((thumb, index) => (
                    <article className="compact-card" key={thumb.id ?? index}>
                      <span className="option-index">1</span>
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
                <p className="eyebrow">YouTube</p>
                <h2>Adequação e SEO</h2>
              </div>
              <ShieldCheck size={20} />
            </div>

            <div className="youtube-grid top-gap">
              <article className="youtube-card">
                <span>Adequação</span>
                <strong>
                  {suitability?.risk_level === "high"
                    ? "Atenção alta"
                    : suitability?.risk_level === "medium"
                      ? "Atenção moderada"
                      : "Baixo risco"}
                </strong>
                <p>
                  {suitability?.context_notes ??
                    "Sem observação especial de adequação para este vídeo."}
                </p>
                {packageData.packaging?.strategy?.youtube_safety_check && (
                  <small>
                    {packageData.packaging.strategy.youtube_safety_check}
                  </small>
                )}
              </article>

              <article className="youtube-card">
                <span>SEO principal</span>
                <strong>{seo?.primary_keyword ?? "Não informado"}</strong>
                <p>{seo?.search_intent ?? "Intenção de busca não informada."}</p>
                {seo?.secondary_keywords && seo.secondary_keywords.length > 0 && (
                  <div className="keyword-row">
                    {seo.secondary_keywords.map((keyword) => (
                      <em key={keyword}>{keyword}</em>
                    ))}
                  </div>
                )}
              </article>
            </div>

            {packageData.publication?.description && (
              <div className="description-preview">
                <span>Descrição preparada para publicação</span>
                <p>{packageData.publication.description}</p>
              </div>
            )}
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Pesquisa</p>
                <h2>Fontes e evidências</h2>
              </div>
              <SearchCheck size={20} />
            </div>

            <div className="evidence-summary">
              <strong>{claims.length}</strong>
              <span>afirmações verificáveis</span>
              <strong>{sources.length}</strong>
              <span>fontes utilizadas</span>
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
                    <span className="source-type">
                      {source.source_type ?? "fonte"}
                    </span>
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
                <article className="scene-readonly" key={scene.id}>
                  <div className="scene-number">{scene.scene_index + 1}</div>
                  <div>
                    <div className="scene-readonly-heading">
                      <strong>{scene.title ?? `Cena ${scene.scene_index + 1}`}</strong>
                      <span className="visual-chip">
                        {scene.visual_type ?? "VISUAL"}
                      </span>
                    </div>
                    <p>{scene.narration}</p>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="panel compact-summary">
            <FileText size={20} />
            <div>
              <strong>Fluxo automático</strong>
              <p className="muted">
                Este painel é para acompanhar e consultar. Pesquisa, embalagem,
                roteiro, narração e produção avançam pelo fluxo automático sem
                exigir revisão manual etapa por etapa.
              </p>
            </div>
          </section>
        </>
      )}
    </section>
  );
}
