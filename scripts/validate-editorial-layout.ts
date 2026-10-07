import {readFileSync,writeFileSync,mkdirSync,appendFileSync} from "node:fs";
import {dirname,resolve} from "node:path";
import {createHash} from "node:crypto";
import {bundle} from "@remotion/bundler";
import {openBrowser,renderStill,selectComposition} from "@remotion/renderer";
import {normalizeEditorialProject} from "../src/lib/editorial-project";
import {LAYOUT_VERSION} from "../src/lib/editorial-layout";
import {TYPOGRAPHY_VERSION} from "../src/lib/editorial-typography";
import {layoutRepairGuidance,githubAnnotation,type LayoutAuditMode} from "../src/lib/editorial-layout-audit";

const args=process.argv.slice(2);
const arg=(name:string,fallback?:string)=>{const i=args.indexOf(name);return i>=0?args[i+1]:fallback;};
const projectPath=arg("--project","video/data/daily.json")!;
const inputPath=arg("--render-input");
const output=arg("--output","video/generated/daily-layout-report.json")!;
const framesDir=arg("--frames-dir","render-output/layout-review")!;
const assetsPath=arg("--visual-assets-manifest");
const input=readFileSync(inputPath??projectPath,"utf8"),project=normalizeEditorialProject(JSON.parse(input));
const scenes=project.scenes;
const mode=arg("--mode",inputPath?"final-timing":"pre-voice")! as LayoutAuditMode;
if(!["geometry-only","pre-voice","final-timing"].includes(mode))throw new Error("--mode deve ser geometry-only, pre-voice ou final-timing.");
const hash=(s:string|Buffer)=>createHash("sha256").update(s).digest("hex");
const report:any={version:LAYOUT_VERSION,typography_version:TYPOGRAPHY_VERSION,mode,input_sha256:hash(input),project_id:project.project_id,resolution:{width:1920,height:1080},fps:project.fps??30,font_sha256:hash(readFileSync("public/fonts/inter-latin-700-normal.woff2")),scenes:[],issues:[],deferred_assets:[]};
if(assetsPath) {
  const raw=readFileSync(assetsPath,"utf8"),manifest=JSON.parse(raw);
  report.visual_assets_manifest_sha256=hash(raw);
  const assets=new Map<string,any>((manifest.assets??[]).map((a:any)=>[String(a.id),a]));
  for(const scene of scenes)for(const element of scene.visual?.stage?.elements??[]) {
    const asset=assets.get(String(element.asset_id));
    if(!asset)continue;
    const file=String(asset.public_file??"");
    if(!file||file.includes("..")||/^[a-z]+:|^[/\\]/i.test(file))throw new Error(`Arquivo de asset inválido: ${element.asset_id}`);
    element.asset_file=file;
    if(asset.width)element.asset_width=asset.width;
    if(asset.height)element.asset_height=asset.height;
    if(asset.prepared?.width)element.asset_width=asset.prepared.width;
    if(asset.prepared?.height)element.asset_height=asset.prepared.height;
  }
}
mkdirSync(dirname(resolve(output)),{recursive:true});mkdirSync(resolve(framesDir),{recursive:true});
let browser:Awaited<ReturnType<typeof openBrowser>>|undefined;
try {
  const serveUrl=await bundle({entryPoint:resolve("video/src/LayoutAudit.tsx"),publicDir:resolve("public")});
  browser=await openBrowser("chrome");
  for(const [index,scene] of scenes.entries()) {
    if(!scene.visual?.stage)continue;
    const inputProps={scene,fps:project.fps??30,mode};
    const composition=await selectComposition({serveUrl,id:"LayoutAudit",inputProps,puppeteerInstance:browser});
    let result:any;
    await renderStill({serveUrl,composition,inputProps,puppeteerInstance:browser,output:resolve(framesDir,`scene-${String(index).padStart(2,"0")}.png`),onBrowserLog:log=> {
      const mark=log.text.indexOf("ODE_LAYOUT_REPORT:");
      if(mark>=0)result=JSON.parse(log.text.slice(mark+"ODE_LAYOUT_REPORT:".length));
    }});
    if(!result)throw new Error(`Cena ${index} não devolveu diagnóstico de layout.`);
    if(!result.font_loaded)throw new Error(`Cena ${scene.id??index}: fonte real não carregada; auditoria inconclusiva.`);
    report.scenes.push({...result,input_scene_index:index});
    for(const warning of result.warnings??[])console.warn(`${scene.id??index} [${warning.code}] ${warning.element}: ${warning.message}`);
    report.issues.push(...result.issues.map((i:any)=>({...i,scene_id:scene.id??index,repair_guidance:layoutRepairGuidance(i.code)})));
    report.deferred_assets.push(...(result.deferred_assets??[]).map((i:any)=>({...i,scene_id:scene.id??index})));
  }
} catch(error) {
  report.issues.push({code:"preflight-error",message:String(error)});
} finally {
  if(browser)await browser.close({silent:true});
  report.passed=report.issues.length===0;
  report.production_ready=mode==="final-timing"&&report.passed;
  report.scope=mode==="geometry-only"?"Composição inicial com fonte real; não aprova assets, DOM final, voz ou sincronização.":mode==="pre-voice"?"Composição com assets reais antes do TTS; sincronização aguarda narração real.":"Layout com assets e tempos da narração real; a entrega ainda exige QA do MP4.";
  writeFileSync(output,JSON.stringify(report,null,2)+"\n");
}
for(const issue of report.issues) {
  const message=`${issue.scene_id??"Projeto"} [${issue.code}] ${issue.element??issue.connection??""}${issue.frame!==undefined?` · frame ${issue.frame}`:""}: ${issue.message} ${issue.repair_guidance??layoutRepairGuidance(issue.code)}`;
  console.error(process.env.GITHUB_ACTIONS?`::error::${githubAnnotation(message)}`:message);
}
if(process.env.GITHUB_STEP_SUMMARY) {
  const safe=(value:unknown)=>String(value??"").replace(/[\\`*_[\]<>|]/g,"\\$&").replace(/[\r\n]+/g," ");
  const details=report.issues.map((issue:any)=>`- ${safe(issue.scene_id??"Projeto")} / ${safe(issue.element??issue.connection??issue.code)}${issue.frame!==undefined?` / frame ${issue.frame}`:""}: ${safe(issue.message)} ${safe(issue.repair_guidance??layoutRepairGuidance(issue.code))}`).join("\n");
  appendFileSync(process.env.GITHUB_STEP_SUMMARY,`\n### Layout ${mode}: ${report.passed?"aprovado":"precisa de ajuste"}\n\n${report.scope}\n\n${report.scenes.length} cenas, ${report.issues.length} falhas, ${report.deferred_assets.length} assets adiados. Relatório: ${safe(output)}.\n\n${details}\n`);
}
console.log(`Layout ${mode}: ${report.scenes.length} cenas; ${report.issues.length} falhas. ${output}`);
if(!report.passed)process.exitCode=1;
