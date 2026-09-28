import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  ChevronRight,
  LogOut,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { supabase } from "../lib/supabase";
import type { VideoProjectRow } from "../lib/database.types";
import { ImportProject } from "./ImportProject";
import { ProjectDetail } from "./ProjectDetail";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export function Dashboard() {
  const [projects, setProjects] = useState<VideoProjectRow[]>([]);
  const [selectedProject, setSelectedProject] =
    useState<VideoProjectRow | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadProjects = useCallback(async () => {
    if (!supabase) return;

    setLoading(true);
    setLoadError(null);

    const {
      data: { user },
      error: userError,
    } = await supabase.auth.getUser();

    if (userError || !user) {
      setLoadError(userError?.message ?? "Usuário não encontrado.");
      setLoading(false);
      return;
    }

    const { data, error } = await supabase
      .from("video_projects")
      .select("*")
      .eq("owner_id", user.id)
      .order("created_at", { ascending: false })
      .limit(50);

    if (error) {
      setLoadError(error.message);
    } else {
      setProjects(data ?? []);

      if (selectedProject) {
        const refreshed = data?.find(
          (project) => project.id === selectedProject.id,
        );
        if (refreshed) setSelectedProject(refreshed);
      }
    }

    setLoading(false);
  }, [selectedProject]);

  useEffect(() => {
    void loadProjects();
  }, [loadProjects]);

  async function signOut() {
    await supabase?.auth.signOut();
  }

  function handleProjectUpdated(updatedProject: VideoProjectRow) {
    setSelectedProject(updatedProject);
    setProjects((current) =>
      current.map((project) =>
        project.id === updatedProject.id ? updatedProject : project,
      ),
    );
  }

  if (selectedProject) {
    return (
      <main className="app-shell">
        <header className="topbar">
          <div>
            <div className="brand-title">
              <span className="brand-dot" />
              O Dinheiro Explica
            </div>
            <span className="muted small">Redação automatizada</span>
          </div>

          <button className="secondary-button" onClick={signOut}>
            <LogOut size={17} />
            Sair
          </button>
        </header>

        <ProjectDetail
          project={selectedProject}
          onBack={() => setSelectedProject(null)}
          onProjectUpdated={handleProjectUpdated}
        />
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand-title">
            <span className="brand-dot" />
            O Dinheiro Explica
          </div>
          <span className="muted small">Redação automatizada</span>
        </div>

        <button className="secondary-button" onClick={signOut}>
          <LogOut size={17} />
          Sair
        </button>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">MVP editorial</p>
          <h1>Da pauta ao vídeo, com controle humano.</h1>
          <p className="muted hero-copy">
            Importe a pesquisa produzida no ChatGPT, revise as evidências e
            ajuste o roteiro antes de liberar o vídeo para produção.
          </p>
        </div>

        <div className="hero-stat">
          <Sparkles size={20} />
          <strong>{projects.length}</strong>
          <span>projetos no painel</span>
        </div>
      </section>

      <ImportProject onImported={loadProjects} />

      <section className="panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Produção</p>
            <h2>Projetos</h2>
          </div>
          <button
            className="secondary-button"
            onClick={() => void loadProjects()}
            disabled={loading}
          >
            <RefreshCw size={17} />
            Atualizar
          </button>
        </div>

        {loadError && (
          <div className="validation-box error">
            <AlertTriangle size={18} />
            <span>{loadError}</span>
          </div>
        )}

        {loading ? (
          <p className="muted">Carregando...</p>
        ) : projects.length === 0 ? (
          <div className="empty-state">
            <strong>Nenhum projeto importado ainda.</strong>
            <span>
              Use o pacote de exemplo acima para testar o fluxo sem depender de
              uma pauta real.
            </span>
          </div>
        ) : (
          <div className="project-grid">
            {projects.map((project) => (
              <article className="project-card" key={project.id}>
                <div className="project-card-top">
                  <span className="status-chip">{project.status}</span>
                  {project.viral_score !== null && (
                    <span className="score">
                      potencial {project.viral_score}/100
                    </span>
                  )}
                </div>

                <h3>{project.subject}</h3>
                {project.angle && <p>{project.angle}</p>}

                {project.risk_flags.length > 0 && (
                  <div className="risk-row">
                    <AlertTriangle size={15} />
                    {project.risk_flags.join(", ")}
                  </div>
                )}

                <footer className="project-card-footer">
                  <div>
                    <span>{project.category ?? "sem categoria"}</span>
                    <span>{formatDate(project.created_at)}</span>
                  </div>
                  <button
                    className="card-link-button"
                    onClick={() => setSelectedProject(project)}
                  >
                    Abrir revisão
                    <ChevronRight size={16} />
                  </button>
                </footer>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
