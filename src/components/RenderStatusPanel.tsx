import { useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  Clock3,
  Film,
  HardDrive,
  LoaderCircle,
  RefreshCw,
} from "lucide-react";

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

const productionStages = [
  {key: "editorial", label: "Editorial"},
  {key: "audio", label: "Narração"},
  {key: "timeline", label: "Timeline"},
  {key: "render", label: "Render"},
  {key: "drive", label: "Drive"},
];

function timeLabel(seconds: number | null | undefined) {
  if (seconds == null || !Number.isFinite(seconds)) return "n/d";
  const rounded = Math.max(0, Math.round(seconds));
  const minutes = Math.floor(rounded / 60);
  const secs = rounded % 60;
  return `${minutes}:${String(secs).padStart(2, "0")}`;
}

function stageLabel(stage: string) {
  const labels: Record<string, string> = {
    fila: "Na fila",
    preparando: "Preparando produção",
    audio: "Gerando narração",
    timeline: "Montando timeline",
    dependencias: "Preparando render",
    render: "Renderizando vídeo",
    thumbnail: "Gerando thumbnail",
    publicando: "Enviando para o Drive",
    concluido: "Vídeo pronto",
    erro: "Erro no processamento",
  };
  return labels[stage] ?? stage;
}

function stagePosition(job: RenderJob) {
  if (job.status === "completed") return productionStages.length;
  if (job.status === "error") return -1;

  const map: Record<string, number> = {
    fila: 0,
    preparando: 0,
    audio: 1,
    timeline: 2,
    dependencias: 2,
    render: 3,
    thumbnail: 3,
    publicando: 4,
    concluido: 5,
  };

  return map[job.stage] ?? 0;
}

export function RenderStatusPanel() {
  const [job, setJob] = useState<RenderJob | null>(null);
  const [checking, setChecking] = useState(true);
  const [now, setNow] = useState(Date.now());

  async function refresh() {
    try {
      const response = await fetch("/.netlify/functions/render-status", {
        cache: "no-store",
      });
      const payload = await response.json();
      setJob(response.ok && payload?.job ? payload.job : null);
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

  if (!job) {
    return (
      <section className="panel render-status-panel idle">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Produção</p>
            <h2>Aguardando o próximo vídeo</h2>
          </div>
          <Film size={22} />
        </div>
        <p className="muted render-detail">
          Quando um pedido feito no chat entrar na fábrica, o andamento aparece
          aqui automaticamente.
        </p>
        <div className="production-stage-strip">
          {productionStages.map((stage) => (
            <div className="production-stage" key={stage.key}>
              <span />
              <strong>{stage.label}</strong>
            </div>
          ))}
        </div>
      </section>
    );
  }

  const running = job.status === "running" || job.status === "queued";
  const done = job.status === "completed";
  const currentPosition = stagePosition(job);

  return (
    <section
      className={`panel render-status-panel ${done ? "ready" : ""} ${
        job.status === "error" ? "failed" : ""
      }`}
    >
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Produção em tempo real</p>
          <h2>{stageLabel(job.stage)}</h2>
        </div>
        {done ? (
          <CheckCircle2 size={22} />
        ) : (
          <button className="secondary-button" onClick={() => void refresh()}>
            <RefreshCw size={16} />
            Atualizar
          </button>
        )}
      </div>

      <div className="render-title-row">
        <Film size={19} />
        <strong>{job.title}</strong>
      </div>

      <div className="production-stage-strip active-strip">
        {productionStages.map((stage, index) => {
          const completed = done || index < currentPosition;
          const active = !done && index === currentPosition;
          return (
            <div
              className={`production-stage ${completed ? "done" : ""} ${
                active ? "active" : ""
              }`}
              key={stage.key}
            >
              <span />
              <strong>{stage.label}</strong>
            </div>
          );
        })}
      </div>

      <div
        className="render-progress-track"
        aria-valuenow={Math.round(job.percent)}
      >
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
        <div className="drive-ready">
          <HardDrive size={17} />
          <span>
            Produção concluída. As novas produções são entregues no Google Drive.
          </span>
        </div>
      )}

      {running && (
        <div className="render-live">
          <Clock3 size={15} />
          Atualiza automaticamente a cada poucos segundos.
        </div>
      )}
    </section>
  );
}
