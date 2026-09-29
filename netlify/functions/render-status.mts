import { getStore } from "@netlify/blobs";
import {createClient} from "@supabase/supabase-js";

declare const Netlify: {env: {get(name: string): string | undefined}};

export default async (request: Request) => {
  if (request.method !== "GET") {
    return Response.json(
      {ok: false, error: "Método não permitido."},
      {status: 405, headers: {"Cache-Control": "no-store"}},
    );
  }

  const authorization = request.headers.get("authorization") ?? "";
  if (!authorization.startsWith("Bearer ")) return Response.json({error: "Entre no painel para acompanhar a produção."}, {status: 401, headers: {"Cache-Control": "no-store"}});
  const url = Netlify.env.get("VITE_SUPABASE_URL");
  const key = Netlify.env.get("VITE_SUPABASE_PUBLISHABLE_KEY");
  if (!url || !key) return Response.json({error: "Acompanhamento temporariamente indisponível."}, {status: 503, headers: {"Cache-Control": "no-store"}});
  // Same trusted admin role used by the app. No service role or database query.
  const client = createClient(url, key, {auth: {persistSession: false, autoRefreshToken: false}});
  const {data, error} = await client.auth.getUser(authorization.slice(7));
  if (error || data.user?.app_metadata?.role !== "admin") return Response.json({error: "Acesso restrito ao administrador."}, {status: 403, headers: {"Cache-Control": "no-store"}});
  const store = getStore({name: "ode-render-jobs", consistency: "strong"});
  const job = await store.get("latest", {type: "json"});

  return Response.json(
    {ok: true, job: job ?? null},
    {status: 200, headers: {"Cache-Control": "no-store"}},
  );
};
