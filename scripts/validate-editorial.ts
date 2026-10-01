import {validateSpeechDirection} from "../src/lib/speech-direction";
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {normalizeEditorialProject,explanationReviewContent,stableJson} from "../src/lib/editorial-project";
import {validateExplanation} from "../src/lib/editorial-explanation";
import {editorialStageSchema, stageEventFields, validateStageEvents} from "../src/lib/editorial-stage";
import {z} from "zod";
import {visualAssetSchema} from "../src/lib/video-project-schema";

const path = process.argv[2] ?? "video/data/daily.json";
const rawProject = JSON.parse(readFileSync(path, "utf8"));
const project = normalizeEditorialProject(rawProject);
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
for(const error of validateExplanation(project)){console.error(`Explicação: ${error}`);failures++;}
if(process.argv.includes("--require-explanation")&&!project.editorial?.explanation){console.error("Produção exige contrato editorial.explanation; migre conceitos, exemplos e unidades.");failures++;}
if(project.editorial?.explanation) {
  const digest=createHash("sha256").update(stableJson(explanationReviewContent(rawProject))).digest("hex");
  if(project.editorial.explanation.review?.content_sha256!==digest){console.error("Revisão editorial corresponde a outro conteúdo; revise o roteiro e atualize a evidência.");failures++;}
}
// Check the spoken script, rather than assuming the agent followed prose docs.
const contract = project.editorial?.narrative_contract ?? {};
const narrations = scenes.map((scene: any) => String(scene.narration ?? ""));
const spokenScript = narrations.join("\n\n");
const publicationRelativePattern = /\bhoje\b|\bontem\b|\bamanhã\b|\bno dia de hoje\b|\bna manhã de hoje\b|\bnesta manhã\b|\bnesta tarde\b|\bnesta noite\b/giu;
const publicationRelativeMatches = spokenScript.match(publicationRelativePattern) ?? [];
if (publicationRelativeMatches.length) {
  console.error(
    `Narração data o vídeo pela publicação: ${[...new Set(publicationRelativeMatches)].join(", ")}. Use a data objetiva do fato.`
  );
  failures++;
}
const contractError = (message: string) => {console.error(`Contrato narrativo: ${message}`); failures++;};
const excerpt = (key: string): string => {
  const value = String(contract[key] ?? "").trim();
  if (!value || spokenScript.split(value).length !== 2) {
    contractError(`${key} deve conter um trecho literal e único da narração.`);
    return "";
  }
  return value;
};
const explanation = excerpt("topic_explanation");
const introduction = excerpt("presenter_introduction");
const subscription = excerpt("subscription_request");
const presenterName = project.presenter?.name ?? (project.presenter?.gender === "female" ? "Luana" : "Roberto");
if (explanation && !narrations.slice(0, 2).join("\n\n").includes(explanation)) {
  contractError("explique o assunto na abertura, nas primeiras cenas.");
}
if (introduction && (!narrations[0]?.includes(introduction) || !introduction.includes(presenterName))) {
  contractError(`a primeira cena deve apresentar ${presenterName} naturalmente após o gancho.`);
}
if (introduction && spokenScript.indexOf(introduction) === 0) {
  contractError("entregue o gancho antes da apresentação.");
}
if (subscription && !/inscrev|inscri[cç][aã]o/i.test(subscription)) {
  contractError("subscription_request deve pedir inscrição no canal.");
}
if (subscription && introduction && spokenScript.indexOf(subscription) <= spokenScript.indexOf(introduction)) {
  contractError("o pedido de inscrição deve vir após a apresentação e a entrega de valor.");
}
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
