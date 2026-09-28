import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Clock3, Film, LoaderCircle, RefreshCw } from "lucide-react";

type RenderJob = {
  runId: string;
  title: string;
  status: "queued" | "running" | "completed" | "error";
  stage: string;
  detail: string;
  percent: number;
  etaSeconds: number | null;
  videoDurationSeconds: number | null;
  createdAt: string;
  updatedAt: string;
};

function timeLabel(seconds: number | null | undefined) {
  if (seconds == null || !Number.isFinite(seconds)) return "—";
  const rounded = Math.max(0, Math.round(seconds));
  const minutes = Math.floor(rounded / 60);
  const secs = rounded % 60;
  return `${minutes}:${String(secs).padStart(2, "0")}`;
}

function stageLabel(stage: string) {
  const labels: Record<string, string> = {
    fila: "Na fila",
    preparando: "Preparando",
    audio: "Gerando narração",
    timeline: "Montando timeline",
    dependencias: "Preparando render",
    render: "Renderizando vídeo",
    thumbnail: "Gerando thumbnail",
    publicando: "Publicando arquivos",
    concluido: "Vídeo pronto",
    erro: "Erro no processamento",
  };
  return labels[stage] ?? stage;
}

export function RenderStatusPanel() {
  const [job, setJob] = useState<RenderJob | null>(null);
  const [fallbackReady, setFallbackReady] = useState(false);
  const [fallbackDuration, setFallbackDuration] = useState<number | null>(null);
  const [checking, setChecking] = useState(true);
  const [now, setNow] = useState(Date.now());

  async function refresh() {
    try {
      const response = await fetch("/.netlify/functions/render-status", {
        cache: "no-store",
      });
      const payload = await response.json();
      if (response.ok && payload?.job) {
        setJob(payload.job);
        setFallbackReady(false);
      } else {
        const fallback = await fetch("/render-tests/pix-med-youtube.json", {
          cache: "no-store",
        });
        if (fallback.ok) {
          const metadata = await fallback.json();
          setFallbackReady(true);
          setFallbackDuration(Number(metadata.duration_seconds) || null);
        }
      }
    } catch {
      // O painel não deve impedir o restante do sistema de carregar.
    } finally {
      setChecking(false);
    }
  }

  useEffect(() => {
    void refresh();
    const poll = window.setInterval(() => void refresh(), 12000);
    const clock = window.setInterval(() => setNow(Date.now()), 1000);
    return () => {
      window.clearInterval(poll);
      window.clearInterval(clock);
    };
  }, []);

  const elapsed = useMemo(() => {
    if (!job?.createdAt) return null;
    return Math.max(0, (now - new Date(job.createdAt).getTime()) / 1000);
  }, [job, now]);

  if (checking && !job) {
    return (
      <section className="panel render-status-panel">
        <div className="render-status-main">
          <LoaderCircle className="spin" size={20} />
          <span>Consultando produção...</span>
        </div>
      </section>
    );
  }

  if (!job && fallbackReady) {
    return (
      <section className="panel render-status-panel ready">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Produção automática</p>
            <h2>Último vídeo pronto</h2>
          </div>
          <CheckCircle2 size={22} />
        </div>
        <div className="render-ready-row">
          <div>
            <strong>O Pix Agora Rastreia o Dinheiro do Golpe</strong>
            <span>Duração {timeLabel(fallbackDuration)}</span>
          </div>
          <a className="primary-button render-link" href="/render-tests/">
            Assistir
          </a>
        </div>
      </section>
    );
  }

  if (!job) return null;

  const running = job.status === "running" || job.status === "queued";
  const done = job.status === "completed";

  return (
    <section className={`panel render-status-panel ${done ? "ready" : ""}`}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Produção automática</p>
          <h2>{stageLabel(job.stage)}</h2>
        </div>
        <button className="secondary-button" onClick={() => void refresh()}>
          <RefreshCw size={16} />
          Atualizar
        </button>
      </div>

      <div className="render-title-row">
        <Film size={19} />
        <strong>{job.title}</strong>
      </div>

      <div className="render-progress-track" aria-valuenow={Math.round(job.percent)}>
        <div
          className="render-progress-bar"
          style={{width: `${Math.max(0, Math.min(100, job.percent))}%`}}
        />
      </div>

      <div className="render-metrics">
        <div>
          <span>Progresso</span>
          <strong>{Math.round(job.percent)}%</strong>
        </div>
        <div>
          <span>Duração do vídeo</span>
          <strong>{timeLabel(job.videoDurationSeconds)}</strong>
        </div>
        <div>
          <span>Tempo decorrido</span>
          <strong>{timeLabel(elapsed)}</strong>
        </div>
        <div>
          <span>{running ? "Estimativa restante" : "Status"}</span>
          <strong>
            {running
              ? job.etaSeconds == null
                ? "calculando..."
                : timeLabel(job.etaSeconds)
              : done
                ? "concluído"
                : "verificar erro"}
          </strong>
        </div>
      </div>

      {job.detail && <p className="muted render-detail">{job.detail}</p>}

      {done && (
        <a className="primary-button render-link" href="/render-tests/">
          Assistir vídeo pronto
        </a>
      )}

      {running && (
        <div className="render-live">
          <Clock3 size={15} />
          Atualiza automaticamente. Não precisa abrir o GitHub Actions.
        </div>
      )}
    </section>
  );
}
