// News-only structural preflight: before browser downloads, voice and expensive render.
// This validates EVERY scene with the exact production Zod contract, not a Python approximation.
import fs from "node:fs";
import {editorialStageSchema} from "../src/lib/editorial-stage";

const file = process.argv[2] || "video/generated/daily-project.json";
const project = JSON.parse(fs.readFileSync(file, "utf8"));
if (project?.editorial?.format !== "ode-news-single") {
  throw new Error("NEWS_PREFLIGHT: expected ode-news-single project");
}
const scenes = project.scenes ?? [];
if (scenes.length < 4 || scenes.length > 9) {
  throw new Error("NEWS_PREFLIGHT: expected 4-9 sequential scenes");
}
const assets = new Map((project.visual_assets ?? []).map((x: any) => [x.id, x]));
const distinctDocs = new Set<string>();
const distinctCards = new Set<string>();
let opinionCount = 0;
for (const [index, scene] of scenes.entries()) {
  if (scene.index !== index || scene.visual?.type !== "authored_stage") {
    throw new Error("NEWS_PREFLIGHT: scene identity/type mismatch at " + index);
  }
  const parsed = editorialStageSchema.safeParse(scene.visual.stage);
  if (!parsed.success) {
    const errors = parsed.error.issues.map(issue =>
      String(issue.path.join(".")) + ": " + issue.message
    );
    throw new Error("NEWS_STAGE_INVALID scene=" + scene.id + " " + errors.join("; "));
  }
  const stage = parsed.data;
  if (stage.elements.some(e => e.kind === "source_excerpt")) {
    for (const e of stage.elements.filter(e => e.kind === "source_excerpt")) {
      const asset = assets.get(e.asset_id || "") as any;
      if (asset?.type !== "source_excerpt") {
        throw new Error("NEWS_PREFLIGHT: missing documentary asset " + e.asset_id);
      }
      distinctDocs.add(e.asset_id!);
    }
  }
  // Opinion is signposted in spoken narration and semantic metadata,
  // not by an isolated visual card obscuring the article.
  if (scene.editorial_role === "opinion") {
    const spoken = String(scene.narration ?? "").toLocaleLowerCase("pt-BR");
    if (!/(minha leitura|minha opinião|na minha análise|meu ponto)/.test(spoken)) {
      throw new Error("NEWS_PREFLIGHT: Roberto commentary must be explicitly identified in speech");
    }
    opinionCount++;
  }
  const anchors = scene.visual.beats?.map((b: any) => b.anchor) ?? [];
  if (anchors.length < 3 || new Set(anchors).size !== anchors.length) {
    throw new Error("NEWS_PREFLIGHT: missing/duplicate speech anchors scene=" + scene.id);
  }
  for (const beat of scene.visual.beats ?? []) {
    if (typeof beat.headline === "string") distinctCards.add(beat.headline);
    if (!stage.elements.some(e => e.id === beat.target_id)) {
      throw new Error("NEWS_PREFLIGHT: invalid beat target scene=" + scene.id);
    }
  }
}
if (distinctDocs.size < 2) {
  throw new Error("NEWS_PREFLIGHT: at least 2 different documentary excerpts required");
}
if (opinionCount < 1) throw new Error("NEWS_PREFLIGHT: no clearly marked Roberto commentary");
if (distinctCards.size < scenes.length * 2) {
  throw new Error("NEWS_PREFLIGHT: not enough original visual changes");
}
console.log("NEWS_SINGLE_STAGE_OK", {
  episode: project.project_id, scenes: scenes.length,
  documentary_excerpts: distinctDocs.size,
  opinion_scenes: opinionCount,
  distinct_visual_headlines: distinctCards.size,
});
