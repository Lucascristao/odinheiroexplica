import assert from "node:assert/strict";
import settings from "../config/news-autonomy.json" with {type: "json"};
import {tickNewsClock, withinNewsWindow} from "../netlify/lib/news-clock.ts";

const now = new Date("2026-11-10T11:41:00Z"); // 08:41 Fortaleza
const run = {id: 123, created_at: "2026-11-10T11:00:00Z", status: "completed"};
assert.equal(withinNewsWindow(now, settings), true);
assert.equal(withinNewsWindow(new Date("2026-11-10T07:00:00Z"), settings), false);
assert.equal(withinNewsWindow(now, {...settings, enabled: false}), false);
assert.equal(withinNewsWindow(new Date("2026-11-11T02:59:00Z"), settings), true);
await assert.rejects(tickNewsClock({now, settings}), /missing_dispatch_credential/);

for (const status of ["pending", "in_progress", "queued"]) {
  let calls=0;
  const fetcher=(async()=>{calls++; return Response.json({workflow_runs:[{...run,status}]});}) as typeof fetch;
  assert.equal((await tickNewsClock({now,settings,token:"fixture",fetcher})).status,"guard_active");
  assert.equal(calls,1);
}
let requests: {url: string; init?: RequestInit}[]=[];
const fetcher=(async(input,init)=>{
  requests.push({url:String(input),init});
  return requests.length===1?Response.json({workflow_runs:[run]}):new Response(null,{status:204});
}) as typeof fetch;
assert.equal((await tickNewsClock({now,settings,token:"fixture",fetcher})).status,"guard_dispatched");
assert.equal(requests.length,2);
assert.equal(requests[1].url,"https://api.github.com/repos/Lucascristao/odinheiroexplica/actions/workflows/news-trigger-watchdog.yml/dispatches");
assert.deepEqual(JSON.parse(String(requests[1].init?.body)),{ref:"main",inputs:{dry_run:"false",trigger_source:"netlify"}});
const recentFetcher=(async()=>Response.json({workflow_runs:[{...run,created_at:"2026-11-10T11:39:00Z"}]})) as typeof fetch;
assert.equal((await tickNewsClock({now,settings,token:"fixture",fetcher:recentFetcher})).status,"guard_recent");
const denied=(async()=>new Response(null,{status:403})) as typeof fetch;
await assert.rejects(tickNewsClock({now,settings,token:"fixture",fetcher:denied}),/read_http_403/);
console.log("NEWS_EXTERNAL_CLOCK_OK: Fortaleza windows, cooldown, duplicate prevention and restricted dispatch");
