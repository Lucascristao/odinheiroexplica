import {readFileSync,writeFileSync,mkdirSync} from "node:fs";
import {dirname,resolve} from "node:path";
import {createHash} from "node:crypto";
import {bundle} from "@remotion/bundler";
import {openBrowser,renderStill,selectComposition} from "@remotion/renderer";
import {normalizeEditorialProject} from "../src/lib/editorial-project";
import {LAYOUT_VERSION} from "../src/lib/editorial-layout";
import {TYPOGRAPHY_VERSION} from "../src/lib/editorial-typography";

const args=process.argv.slice(2);
const arg=(name:string,fallback?:string)=>{const i=args.indexOf(name);return i>=0?args[i+1]:fallback;};
const projectPath=arg("--project","video/data/daily.json")!;
const inputPath=arg("--render-input");
const output=arg("--output","video/generated/daily-layout-report.json")!;
const framesDir=arg("--frames-dir","render-output/layout-review")!;
const assetsPath=arg("--visual-assets-manifest");
const input=readFileSync(inputPath??projectPath,"utf8"),project=normalizeEditorialProject(JSON.parse(input));
const scenes=project.scenes;
const mode=arg("--mode",inputPath?"final-timing":"pre-voice")!;
if(!["pre-voice","final-timing"].includes(mode))throw new Error("--mode deve ser pre-voice ou final-timing.");
const hash=(s:string|Buffer)=>createHash("sha256").update(s).digest("hex");
const report:any={version:LAYOUT_VERSION,typography_version:TYPOGRAPHY_VERSION,mode,input_sha256:hash(input),project_id:project.project_id,resolution:{width:1920,height:1080},fps:project.fps??30,font_sha256:hash(readFileSync("public/fonts/inter-latin-700-normal.woff2")),scenes:[],issues:[]};
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
    report.scenes.push({...result,input_scene_index:index});
    report.issues.push(...result.issues.map((i:any)=>({...i,scene_id:scene.id??index})));
  }
} catch(error) {
  report.issues.push({code:"preflight-error",message:String(error)});
} finally {
  if(browser)await browser.close({silent:true});
  report.passed=report.issues.length===0;
  writeFileSync(output,JSON.stringify(report,null,2)+"\n");
}
for(const issue of report.issues)console.error(`${issue.scene_id??"Projeto"}: ${issue.message}`);
console.log(`Layout ${mode}: ${report.scenes.length} cenas; ${report.issues.length} falhas. ${output}`);
if(!report.passed)process.exitCode=1;
