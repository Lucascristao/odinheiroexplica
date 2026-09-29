import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  ChevronRight,
  Copy,
  Lightbulb,
  LogOut,
  MessageSquareText,
  Newspaper,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { supabase } from "../lib/supabase";
import type { VideoProjectRow } from "../lib/database.types";
import { ProjectDetail } from "./ProjectDetail";
import { RenderStatusPanel } from "./RenderStatusPanel";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
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

function categoryLabel(category: string | null) {
  const labels: Record<string, string> = {
    news: "notícia",
    company: "empresa",
    economy: "economia",
    money: "dinheiro",
    evergreen: "tema",
  };

  return category ? labels[category] ?? category : "vídeo";
}

export function Dashboard() {
  const [projects, setProjects] = useState<VideoProjectRow[]>([]);
  const [selectedProject, setSelectedProject] =
    useState<VideoProjectRow | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  async function copyRequest(text: string) {
    try {await navigator.clipboard.writeText(text); setCopied(text);}
    catch {setCopied("Não foi possível copiar. Selecione o pedido abaixo.");}
  }

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

  if (selectedProject) {
    return (
      <main className="app-shell">
        <header className="topbar">
          <div>
            <div className="brand-title">
              <span className="brand-dot" />
              O Dinheiro Explica
            </div>
            <span className="muted small">Central de produção</span>
          </div>

          <button className="secondary-button" onClick={signOut}>
            <LogOut size={17} />
            Sair
          </button>
        </header>

        <ProjectDetail
          project={selectedProject}
          onBack={() => setSelectedProject(null)}
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
          <span className="muted small">Central de produção</span>
        </div>

        <button className="secondary-button" onClick={signOut}>
          <LogOut size={17} />
          Sair
        </button>
      </header>

      <section className="hero production-hero">
        <div>
          <p className="eyebrow">Produção diária</p>
          <h1>Crie no chat. Acompanhe por aqui.</h1>
          <p className="muted hero-copy">
            Pesquisa, roteiro e direção visual começam no ChatGPT. Este painel
            acompanha narração, render e entrega no Drive. A capa final continua
            sendo uma etapa conduzida no chat.
          </p>
        </div>

        <div className="hero-stat">
          <Sparkles size={20} />
          <strong>{projects.length}</strong>
          <span>vídeos no histórico</span>
        </div>
      </section>

      <RenderStatusPanel />

      <section className="panel request-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Como iniciar</p>
            <h2>Leve o próximo pedido ao ChatGPT</h2>
          </div>
          <div className="chat-origin">
            <MessageSquareText size={16} />
            Começa no ChatGPT
          </div>
        </div>

        <div className="request-grid">
          <article className="request-card">
            <div className="request-icon">
              <Newspaper size={20} />
            </div>
            <div>
              <span className="request-kicker">Assuntos do dia</span>
              <h3>Vídeo do dia</h3>
              <p>
                Eu pesquiso notícias e movimentos recentes em dinheiro,
                empresas, economia, bancos, fintechs e finanças e escolho uma
                história forte para o canal.
              </p>
              <div className="request-command">“Gerar o vídeo de hoje.”</div>
              <button className="card-link-button" onClick={() => void copyRequest("Gerar o vídeo de hoje.")}><Copy size={15}/>{copied === "Gerar o vídeo de hoje." ? "Copiado" : "Copiar pedido"}</button>
            </div>
          </article>

          <article className="request-card">
            <div className="request-icon">
              <Lightbulb size={20} />
            </div>
            <div>
              <span className="request-kicker">Tema específico</span>
              <h3>Vídeo por assunto</h3>
              <p>
                Você escolhe o tema. Eu pesquiso o melhor ângulo, fontes,
                exemplos, título, thumbnail e roteiro antes de enviar para
                produção.
              </p>
              <div className="request-command">
                “Faça um vídeo sobre como organizar suas finanças e guardar dinheiro.”
              </div>
              <button className="card-link-button" onClick={() => void copyRequest("Faça um vídeo sobre [assunto], seguindo as regras atuais do O Dinheiro Explica.")}><Copy size={15}/>{copied?.startsWith("Faça um vídeo") ? "Copiado" : "Copiar modelo"}</button>
            </div>
          </article>
        </div>

        {copied && <p className="muted small" role="status">{copied.startsWith("Não foi") ? copied : "Pedido copiado. Cole na conversa do projeto no ChatGPT."}</p>}

        <div className="production-flow">
          <span>Pesquisa</span>
          <i />
          <span>Embalagem</span>
          <i />
          <span>Roteiro</span>
          <i />
          <span>Narração</span>
          <i />
          <span>Render</span>
          <i />
          <span>Drive</span>
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Histórico</p>
            <h2>Vídeos e projetos</h2>
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
          <p className="muted top-gap">Carregando...</p>
        ) : projects.length === 0 ? (
          <div className="empty-state">
            <strong>Nenhum projeto salvo neste histórico.</strong>
            <span>
              O andamento da execução mais recente aparece no acompanhamento
              acima. Projetos salvos no painel aparecem nesta lista.
            </span>
          </div>
        ) : (
          <div className="project-grid">
            {projects.map((project) => (
              <article className="project-card" key={project.id}>
                <div className="project-card-top">
                  <span className="status-chip">{statusLabel(project.status)}</span>
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
                    <span>{categoryLabel(project.category)}</span>
                    <span>{formatDate(project.created_at)}</span>
                  </div>
                  <button
                    className="card-link-button"
                    onClick={() => setSelectedProject(project)}
                  >
                    Ver detalhes
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
