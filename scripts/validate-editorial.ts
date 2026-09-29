import {readFileSync} from "node:fs";
import {editorialStageSchema, stageEventFields, validateStageEvents} from "../src/lib/editorial-stage";
import {z} from "zod";

const path = process.argv[2] ?? "video/data/daily.json";
const project = JSON.parse(readFileSync(path, "utf8"));
const scenes = project.scenes ?? project.script?.scenes ?? [];
const assets = new Set((project.visual_assets ?? []).map((a: {id: string}) => a.id));
const beatSchema = z.object({...stageEventFields, headline: z.string().min(1), anchor: z.string().min(1), detail: z.string().optional(), value: z.string().optional()}).passthrough();
let failures = 0;
for (const [index, scene] of scenes.entries()) {
  const error = (message: string) => {console.error(`Cena ${index}: ${message}`); failures++;};
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
    if (element.asset_id && !assets.has(element.asset_id)) error(`Asset inexistente: ${element.asset_id}`);
  }
}
if (!scenes.length) {console.error("Projeto sem cenas."); failures++;}
if (failures) process.exitCode = 1;
else console.log(`Plano editorial válido: ${scenes.length} cenas em ${path}`);
