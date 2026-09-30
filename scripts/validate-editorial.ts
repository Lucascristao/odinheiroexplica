import {validateSpeechDirection} from "../src/lib/speech-direction";
import {readFileSync} from "node:fs";
import {editorialStageSchema, stageEventFields, validateStageEvents} from "../src/lib/editorial-stage";
import {z} from "zod";
import {visualAssetSchema} from "../src/lib/video-project-schema";

const path = process.argv[2] ?? "video/data/daily.json";
const project = JSON.parse(readFileSync(path, "utf8"));
const scenes = project.scenes ?? project.script?.scenes ?? [];
const assets = new Set((project.visual_assets ?? []).map((a: {id: string}) => a.id));
const stagedAssets = new Set<string>(scenes.flatMap((scene: any) =>
  (scene.visual?.stage?.elements ?? []).map((element: any) => element.asset_id).filter(Boolean)));
const beatSchema = z.object({...stageEventFields, headline: z.string().min(1), anchor: z.string().min(1), detail: z.string().optional(), value: z.string().optional()}).passthrough();
// Report what will actually be on stage, not merely assets registered in JSON.
const imageScenes = scenes.filter((scene: any) => {
  const visual = scene.visual ?? {};
  return (visual.stage?.elements ?? []).some((e: any) =>
    ["photo", "source_excerpt"].includes(e.kind) && assets.has(e.asset_id) &&
    (e.initially_visible !== false || (visual.beats ?? []).some((b: any) =>
      (b.action === "reveal" && b.target_id === e.id) || (b.reveal_ids ?? []).includes(e.id))));
}).length;
console.log(`Cobertura visual: ${imageScenes}/${scenes.length} cenas com foto ou recorte utilizável.`);
let failures = 0;
if (scenes.length >= 4 && imageScenes === 0) {
  console.warn("::warning::Nenhuma foto/recorte aparece no palco. Confirme que o episódio usa motion graphics por decisão editorial, e não por omissão de assets.");
}
const sourceIds=new Set((project.sources??[]).map((s:{id:string})=>s.id));
for(const raw of project.visual_assets??[]){
  const result=visualAssetSchema.safeParse(raw);
  if(!result.success){console.error(result.error.message);failures++;}
  if(raw.type==="source_excerpt"&&!sourceIds.has(raw.source_id)){console.error(`Fonte inexistente para recorte ${raw.id}`);failures++;}
  if(raw.type==="source_excerpt"&&!stagedAssets.has(raw.id)){console.error(`Recorte cadastrado mas ausente do palco: ${raw.id}`);failures++;}
  if(raw.type==="source_excerpt"&&!String(raw.expected_text??"").trim()){console.error(`Recorte sem expected_text verificável: ${raw.id}`);failures++;}
}
for (const [index, scene] of scenes.entries()) {
  const error = (message: string) => {console.error(`Cena ${index}: ${message}`); failures++;};
  validateSpeechDirection(String(scene.narration ?? ""), scene.tts).forEach(error);
  const raw = scene.visual?.beats ?? [];
  if (!raw.length && !scene.visual?.stage) continue; // Legacy scenes without events.
  const stage = editorialStageSchema.safeParse(scene.visual?.stage);
  const beats = z.array(beatSchema).safeParse(raw);
  if (!stage.success) {error(stage.error.message); continue;}
  if (!beats.success) {error(beats.error.message); continue;}
  validateStageEvents(stage.data, beats.data).forEach(error);
  let previous = -1;
  for (const beat of beats.data) {
    const narration = String(scene.narration ?? "");
    const at = narration.indexOf(beat.anchor);
    if (at < 0 || narration.split(beat.anchor).length !== 2) error(`Âncora não é literal e única: ${beat.anchor}`);
    if (at <= previous) error("Eventos precisam estar em ordem da fala, sem âncoras simultâneas.");
    previous = at;
  }
  for (const element of stage.data.elements) {
    if(element.chart&&!sourceIds.has(element.chart.source_id))error(`Fonte inexistente para gráfico ${element.id}`);
    if(element.kind==="source_excerpt" && !(project.visual_assets??[]).some((a:{id:string;type:string})=>a.id===element.asset_id&&a.type==="source_excerpt"))error(`Recorte precisa de asset documental: ${element.id}`);
    if (element.asset_id && !assets.has(element.asset_id)) error(`Asset inexistente: ${element.asset_id}`);
  }
}
if (!scenes.length) {console.error("Projeto sem cenas."); failures++;}
if (failures) process.exitCode = 1;
else console.log(`Plano editorial válido: ${scenes.length} cenas em ${path}`);
