import {createHash, timingSafeEqual} from "node:crypto";
import { getStore } from "@netlify/blobs";

const allowedStatus = new Set(["queued", "running", "completed", "error"]);
const allowedStages = new Set([
  "fila",
  "preparando",
  "audio",
  "timeline",
  "dependencias",
  "render",
  "thumbnail",
  "publicando",
  "concluido",
  "erro",
]);

function json(status: number, body: unknown) {
  return Response.json(body, {
    status,
    headers: {"Cache-Control": "no-store"},
  });
}

function safeText(value: unknown, max: number) {
  return String(value ?? "").trim().slice(0, max);
}

function authorized(request: Request) {
  const secret = (process.env.GOOGLE_CLIENT_SECRET || "").trim();
  if (!secret) return false;

  const expected = createHash("sha256")
    .update(`ode-progress-v1:${secret}`)
    .digest("hex");
  const received = (request.headers.get("x-ode-progress-token") || "").trim();

  if (received.length !== expected.length) return false;
  return timingSafeEqual(Buffer.from(received), Buffer.from(expected));
}

export default async (request: Request) => {
  if (request.method !== "POST") {
    return json(405, {ok: false, error: "Método não permitido."});
  }
  if (!authorized(request)) {
    return json(401, {ok: false, error: "Não autorizado."});
  }

  let body: Record<string, unknown>;
  try {
    body = await request.json();
    if (!body || typeof body !== "object" || Array.isArray(body)) {
      throw new Error("invalid");
    }
  } catch {
    return json(400, {ok: false, error: "JSON inválido."});
  }

  const runId = safeText(body.run_id, 40);
  const status = safeText(body.status, 20);
  const stage = safeText(body.stage, 30);
  const title = safeText(body.title, 180);
  const detail = safeText(body.detail, 500);

  if (!/^\d+$/.test(runId)) {
    return json(400, {ok: false, error: "run_id inválido."});
  }
  if (!allowedStatus.has(status) || !allowedStages.has(stage)) {
    return json(400, {ok: false, error: "Estado inválido."});
  }

  const percent = Math.max(0, Math.min(100, Number(body.percent) || 0));
  const etaSeconds =
    body.eta_seconds == null
      ? null
      : Math.max(0, Math.round(Number(body.eta_seconds) || 0));
  const videoDurationSeconds =
    body.video_duration_seconds == null
      ? null
      : Math.max(0, Number(body.video_duration_seconds) || 0);

  const store = getStore({name: "ode-render-jobs", consistency: "strong"});
  const previous =
    (await store.get(`job/${runId}`, {type: "json"})) as
      | Record<string, unknown>
      | null;

  const now = new Date().toISOString();
  const job = {
    runId,
    title: title || previous?.title || "Vídeo em produção",
    status,
    stage,
    detail,
    percent,
    etaSeconds,
    videoDurationSeconds:
      videoDurationSeconds ?? previous?.videoDurationSeconds ?? null,
    createdAt: previous?.createdAt || now,
    updatedAt: now,
  };

  await store.setJSON(`job/${runId}`, job);

  const latest =
    (await store.get("latest", {type: "json"})) as
      | Record<string, unknown>
      | null;
  const latestRunId = Number(latest?.runId ?? 0);
  const incomingRunId = Number(runId);

  // GitHub run IDs crescem ao longo do tempo. Um callback atrasado de uma
  // execução antiga pode atualizar seu próprio histórico, mas nunca deve
  // substituir no painel a execução mais nova.
  if (!latest || incomingRunId >= latestRunId) {
    await store.setJSON("latest", job);
  }

  return json(200, {ok: true});
};
