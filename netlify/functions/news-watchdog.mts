import {getStore} from "@netlify/blobs";
import settings from "../../config/news-autonomy.json" with {type: "json"};
import {tickNewsClock} from "../lib/news-clock.ts";

declare const Netlify: {env: {get(name: string): string | undefined}};

export default async () => {
  const now = new Date();
  let result: Record<string, unknown>;
  try {
    result = await tickNewsClock({now, settings,
      token: Netlify.env.get("ODE_NEWS_TRIGGER_GITHUB_TOKEN")});
  } catch (error) {
    // Only our own fixed error codes are logged; never a provider body/header.
    const message = error instanceof Error ? error.message : "";
    result = {status: "error", code: /^news_clock_[a-z0-9_]+$/.test(message) ? message : "news_clock_transport_error"};
  }
  const report = {checked_at: now.toISOString(), source: "netlify_schedule", ...result};
  console.info("ODE_NEWS_EXTERNAL_CLOCK", JSON.stringify(report));
  try {
    await getStore({name: "ode-news-clock", consistency: "strong"}).setJSON("latest", report);
  } catch {
    console.warn("ODE_NEWS_EXTERNAL_CLOCK_HEARTBEAT_STORAGE_UNAVAILABLE");
  }
  if (result.status === "error") throw new Error(String(result.code));
  return new Response(null, {status: 204});
};

// UTC, every half hour. Window calculations use the shared Fortaleza config.
// Scheduled functions have no public invocation URL and run on production only.
export const config = {schedule: "11,41 * * * *"};
