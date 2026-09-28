import { getStore } from "@netlify/blobs";

export default async (request: Request) => {
  if (request.method !== "GET") {
    return Response.json(
      {ok: false, error: "Método não permitido."},
      {status: 405, headers: {"Cache-Control": "no-store"}},
    );
  }

  const store = getStore({name: "ode-render-jobs", consistency: "strong"});
  const job = await store.get("latest", {type: "json"});

  return Response.json(
    {ok: true, job: job ?? null},
    {status: 200, headers: {"Cache-Control": "no-store"}},
  );
};
