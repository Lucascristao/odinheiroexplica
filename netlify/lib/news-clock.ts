export const repository = "Lucascristao/odinheiroexplica";
const workflow = "news-trigger-watchdog.yml";
const activeStates = new Set(["queued", "pending", "waiting", "requested", "in_progress"]);

export type ClockConfig = {
  enabled: boolean; timezone: string; publish_if_late: boolean;
  late_tolerance_minutes: number; minimum_production_budget_minutes: number;
  slots: {production: string; publication: string}[];
  recovery_policy?: {effective_from: string; same_day_no_deadline: boolean};
};

export function withinNewsWindow(now: Date, settings: ClockConfig) {
  if (!settings.enabled) return false;
  const parts = new Intl.DateTimeFormat("en-CA", {timeZone: settings.timezone,
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23"}).formatToParts(now);
  const minutes = Number(parts.find(p => p.type === "hour")!.value) * 60 +
    Number(parts.find(p => p.type === "minute")!.value);
  const minuteOf = (time: string) => Number(time.slice(0, 2)) * 60 + Number(time.slice(3, 5));
  const grace = settings.publish_if_late ? settings.late_tolerance_minutes : 0;
  const localDay = ["year", "month", "day"].map(type=>parts.find(p=>p.type===type)!.value).join("-");
  const noDeadline = settings.recovery_policy?.same_day_no_deadline === true &&
    localDay >= settings.recovery_policy.effective_from;
  return settings.slots.some(slot => minutes >= minuteOf(slot.production) &&
    minutes <= (noDeadline ? 1439 : Math.min(1440-settings.minimum_production_budget_minutes,
      minuteOf(slot.publication)+grace-settings.minimum_production_budget_minutes)));
}

export async function tickNewsClock(options: {
  now: Date; settings: ClockConfig; token?: string; fetcher?: typeof fetch;
}) {
  const {now, settings, token, fetcher=fetch} = options;
  if (!withinNewsWindow(now, settings)) return {status: "outside_window"};
  if (!token) throw new Error("news_clock_missing_dispatch_credential");
  const endpoint = `https://api.github.com/repos/${repository}/actions/workflows/${workflow}`;
  const headers = {Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"};
  const response = await fetcher(`${endpoint}/runs?branch=main&per_page=8`,
    {headers, signal: AbortSignal.timeout(8000)});
  if (!response.ok) throw new Error(`news_clock_read_http_${response.status}`);
  const payload = await response.json() as {workflow_runs?: {status: string; created_at: string; id: number}[]};
  if (!Array.isArray(payload.workflow_runs)) throw new Error("news_clock_invalid_run_inventory");
  if (payload.workflow_runs.some(run => activeStates.has(run.status))) return {status: "guard_active"};
  const recent = payload.workflow_runs.find(run => {
    const age = now.getTime()-Date.parse(run.created_at);
    return Number.isFinite(age) && age >= 0 && age < 20*60*1000;
  });
  if (recent) return {status: "guard_recent", run_id: recent.id};
  const dispatched = await fetcher(`${endpoint}/dispatches`, {method: "POST", headers,
    signal: AbortSignal.timeout(8000),
    body: JSON.stringify({ref: "main", inputs: {dry_run: "false", trigger_source: "netlify"}})});
  if (dispatched.status !== 204) throw new Error(`news_clock_dispatch_http_${dispatched.status}`);
  return {status: "guard_dispatched", repository, workflow};
}
