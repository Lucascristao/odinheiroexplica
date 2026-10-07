import {validateSpeechDirection} from "../src/lib/speech-direction";
import {summarizeEditorialDirection} from "../src/lib/editorial-direction";
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {normalizeEditorialProject,explanationReviewContent,stableJson} from "../src/lib/editorial-project";
import {validateExplanation} from "../src/lib/editorial-explanation";
import {validateLearningStrategy} from "../src/lib/editorial-learning";
import {editorialStageSchema, stageEventFields, validateStageEvents} from "../src/lib/editorial-stage";
import {z} from "zod";
import {visualAssetSchema} from "../src/lib/video-project-schema";
import {githubAnnotation} from "../src/lib/editorial-layout-audit";

const path = process.argv[2] ?? "video/data/daily.json";
const rawProject = JSON.parse(readFileSync(path, "utf8"));
const project = normalizeEditorialProject(rawProject);
const scenes = project.scenes ?? project.script?.scenes ?? [];
const direction = summarizeEditorialDirection(project);
console.log(`Direção autoral: ${JSON.stringify(direction.scenes)}`);
direction.warnings.forEach(message => console.warn(`::warning::${message}`));
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
for(const message of direction.errors??[]) {
  console.error(process.env.GITHUB_ACTIONS?`::error::${githubAnnotation(message)}`:`Direção: ${message}`);
  failures++;
}
for(const error of validateExplanation(project)){console.error(`Explicação: ${error}`);failures++;}
for(const error of validateLearningStrategy(project,process.argv.includes("--require-learning"))){console.error(`Aprendizado editorial: ${error}`);failures++;}
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

// Packaging is part of the editorial contract, not a post-render afterthought.
const packagingError = (message: string) => {console.error(`Embalagem: ${message}`); failures++;};
const normalizePackagingText = (value: string) => value
  .normalize("NFD")
  .replace(/\p{M}/gu, "")
  .toLowerCase()
  .replace(/[^a-z0-9\s]/g, " ")
  .replace(/\s+/g, " ")
  .trim();
const findPhraseStart = (haystack: string[], needle: string[]) => {
  if (!needle.length) return -1;
  for (let i = 0; i <= haystack.length - needle.length; i++) {
    if (needle.every((word, offset) => haystack[i + offset] === word)) return i;
  }
  return -1;
};
const packaging = project.packaging ?? {};
const title = String(packaging.titles?.[0]?.text ?? "").trim();
const thumbnailHeadline = String(packaging.thumbnails?.[0]?.headline ?? "").trim();
const publication = project.publication ?? {};
const description = String(publication.description ?? "").trim();
const primaryKeyword = String(publication.seo?.primary_keyword ?? "").trim();
if (!title || title.length > 100) packagingError("título deve ter entre 1 e 100 caracteres.");
if (title.length > 65) console.warn("::warning::Título passou de 65 caracteres; confirme se o assunto e a consequência sobrevivem ao corte no celular.");
if (/^(entenda|saiba|veja|instru[cç][aã]o normativa|regulamenta[cç][aã]o|resolu[cç][aã]o|norma)\b/i.test(title)) {
  console.warn("::warning::Título começa de forma genérica ou burocrática; prefira abrir pelo assunto/impacto quando isso for natural.");
}
if (primaryKeyword) {
  const titleWords = normalizePackagingText(title).split(" ").filter(Boolean);
  const keywordWords = normalizePackagingText(primaryKeyword).split(" ").filter(Boolean);
  const keywordStart = findPhraseStart(titleWords, keywordWords);
  if (keywordStart < 0 || keywordStart > 4) {
    console.warn(`::warning::A palavra-chave principal "${primaryKeyword}" não aparece nas primeiras 5 palavras do título; confirme se o front-loading pode melhorar.`);
  }
}
if (title && thumbnailHeadline) {
  const titleTokens = new Set(normalizePackagingText(title).split(" ").filter(Boolean));
  const thumbTokens = [...new Set(normalizePackagingText(thumbnailHeadline).split(" ").filter(Boolean))];
  const overlap = thumbTokens.length ? thumbTokens.filter(token => titleTokens.has(token)).length / thumbTokens.length : 0;
  if (normalizePackagingText(title) === normalizePackagingText(thumbnailHeadline) || overlap >= 0.8) {
    console.warn("::warning::Título e thumbnail repetem quase a mesma mensagem; faça a capa complementar o título.");
  }
}
if (!description) packagingError("publication.description está vazia.");
if (/^\s*(fontes|bases do v[ií]deo|cap[ií]tulos|cr[eé]ditos visuais)\s*:?.*$/gim.test(description)) {
  packagingError("publication.description não deve conter fontes, capítulos ou créditos; o pipeline acrescenta essas seções uma única vez.");
}
if (/https?:\/\/|www\./i.test(description)) packagingError("publication.description não pode conter links.");
const bulletLines = description.split(/\r?\n/).filter((line: string) => /^\s*[-•*]\s+\S/.test(line));
if (bulletLines.length < 3 || bulletLines.length > 4) packagingError("publication.description deve ter 3 ou 4 bullets didáticos.");
if (primaryKeyword && !normalizePackagingText(description.slice(0, 360)).includes(normalizePackagingText(primaryKeyword))) {
  packagingError("a palavra-chave principal deve aparecer naturalmente no gancho inicial da descrição.");
}
if (description.length > 3200) console.warn("::warning::Corpo da descrição está longo; reserve espaço para capítulos, fontes, créditos, pergunta e hashtags.");
const engagementQuestion = String(publication.engagement_question ?? "").trim();
if (!engagementQuestion || !engagementQuestion.endsWith("?")) packagingError("publication.engagement_question deve conter uma pergunta simples terminada em ?.");
const hashtags = Array.isArray(publication.hashtags) ? publication.hashtags.map((value: unknown) => String(value).trim()) : [];
if (hashtags.length !== 3) packagingError("publication.hashtags deve conter exatamente 3 hashtags.");
for (const hashtag of hashtags) {
  if (!/^#[\p{L}\p{N}_]+$/u.test(hashtag)) packagingError(`hashtag inválida: ${hashtag}`);
}
if (scenes.length >= 4 && imageScenes === 0) {
  console.warn("::warning::Nenhuma foto/recorte aparece no palco. Confirme que o episódio usa motion graphics por decisão editorial, e não por omissão de assets.");
}
const sourceIds=new Set((project.sources??[]).map((s:{id:string})=>s.id));
for(const raw of project.visual_assets??[]){
  if(raw.attribution && /https?:\/\/|www\.|\[[^\]]+\]\([^)]+\)/i.test(`${raw.attribution} ${raw.license??""}`))packagingError(`Crédito público do asset ${raw.id} contém link. Use crédito/licença textual compatível e preserve o endereço em license_url ou nos metadados técnicos.`);
  const result=visualAssetSchema.safeParse(raw);
  if(!result.success){console.error(result.error.message);failures++;}
  if(raw.type==="source_excerpt"&&!sourceIds.has(raw.source_id)){console.error(`Fonte inexistente para recorte ${raw.id}`);failures++;}
  if(raw.type==="source_excerpt"&&!stagedAssets.has(raw.id)){console.error(`Recorte cadastrado mas ausente do palco: ${raw.id}`);failures++;}
  if(raw.type==="source_excerpt"&&!String(raw.expected_text??"").trim()){console.error(`Recorte sem expected_text verificável: ${raw.id}`);failures++;}
}
for (const [index, scene] of scenes.entries()) {
  const error = (message: string) => {const detail=`Cena ${scene.id??index}: ${message}`;console.error(process.env.GITHUB_ACTIONS?`::error::${githubAnnotation(detail)}`:detail); failures++;};
  validateSpeechDirection(String(scene.narration ?? ""), scene.tts).forEach(error);
  const raw = scene.visual?.beats ?? [];
  if (!raw.length && !scene.visual?.stage) continue; // Legacy scenes without events.
  const stage = editorialStageSchema.safeParse(scene.visual?.stage);
  const beats = z.array(beatSchema).safeParse(raw);
  if (!stage.success) {error(stage.error.message); continue;}
  if (!beats.success) {error(beats.error.message); continue;}
  validateStageEvents(stage.data, beats.data).forEach(error);
  let previous = -1;
  const narration = String(scene.narration ?? "");
  if (beats.data.length > 0) {
    const firstAt = narration.indexOf(beats.data[0].anchor);
    if (firstAt > 75) {
      console.warn(`::warning::Cena ${scene.id ?? index}: Beat 0 começa tarde na fala (caractere ${firstAt} de ${narration.length}). Ancore o primeiro evento visual nos primeiros 2 a 3 segundos (primeiras 5 a 10 palavras) para evitar tela estática na abertura da cena.`);
    }
  }
  for (let bIdx = 0; bIdx < beats.data.length; bIdx++) {
    const beat = beats.data[bIdx];
    const at = narration.indexOf(beat.anchor);
    if (at < 0 || narration.split(beat.anchor).length !== 2) error(`Âncora não é literal e única: ${beat.anchor}`);
    if (at <= previous) error("Eventos precisam estar em ordem da fala, sem âncoras simultâneas.");
    if (bIdx > 0 && at - previous > 115) {
      console.warn(`::warning::Cena ${scene.id ?? index}, entre beat ${bIdx - 1} e beat ${bIdx}: intervalo de ${at - previous} caracteres de fala sem eventos visuais intermediários (~${Math.round((at - previous) / 16)}s). Adicione micro-beats intermediários (foco, destaque, atualização ou reframe) para respeitar o limite de 4 a 5 segundos.`);
    }
    previous = at;
  }
  if (beats.data.length > 0) {
    const lastBeat = beats.data[beats.data.length - 1];
    const lastAt = narration.indexOf(lastBeat.anchor);
    if (lastAt >= 0) {
      const trailingChars = narration.length - (lastAt + lastBeat.anchor.length);
      if (trailingChars > 120) {
        console.warn(`::warning::Cena ${scene.id ?? index}: cauda final de ${trailingChars} caracteres sem eventos visuais (~${Math.round(trailingChars / 16)}s) até o encerramento da cena.`);
      }
    }
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
