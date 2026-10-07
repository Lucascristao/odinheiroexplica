import {readFileSync,writeFileSync,mkdirSync,readdirSync,copyFileSync,existsSync,realpathSync} from "node:fs";
import {resolve,dirname,relative,join} from "node:path";
import {createHash} from "node:crypto";
import {spawnSync} from "node:child_process";
import {hyperframesArtSchema} from "../src/lib/editorial-stage";
import {validateArtSource,alignedArtStates} from "../src/lib/hyperframes-contract";
import {registerTemporaryPaths} from "./production-cleanup";

const root=resolve(import.meta.dirname,"..");process.chdir(root);
const args=process.argv.slice(2),preflight=args.includes("--preflight");
const option=(key:string,fallback:string)=>{const i=args.indexOf(key);return i<0?fallback:args[i+1];};
const inputPath=option("--input",preflight?"video/data/daily.json":"video/generated/daily-render-input.json");
const payload=JSON.parse(readFileSync(inputPath,"utf8")),scenes=payload.scenes??payload.script?.scenes??[];
const currentProject=JSON.parse(readFileSync("video/data/daily.json","utf8"));
const belongsToCurrent=payload.project_id===currentProject.project_id;
if(belongsToCurrent) {
  const outputs=[`video/generated/daily-hyperframes-${preflight?"preflight":"manifest"}.json`];
  const inputRelative=relative(root,resolve(inputPath)).replaceAll("\\","/");
  if(!preflight&&inputRelative.startsWith("video/generated/"))outputs.push(inputRelative);
  registerTemporaryPaths(root,outputs);
}
const digest=(s:string|Buffer)=>createHash("sha256").update(s).digest("hex");
const local=(file:string)=>{const p=realpathSync(resolve(root,file));if(relative(root,p).startsWith("..")||relative(root,p)==="")throw new Error(`Caminho fora do projeto: ${file}`);return p;};
const files=(dir:string):string[]=>readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(join(dir,e.name)):[join(dir,e.name)]).sort();
const run=(exe:string,values:string[])=>{const r=spawnSync(exe,values,{cwd:root,stdio:"inherit",env:{...process.env,CI:"true",HYPERFRAMES_NO_TELEMETRY:"1"}});if(r.error)throw r.error;if(r.status!==0)throw new Error(`${exe} terminou com ${r.status}`);};
const report:any={version:"1.0",scope:"Arte esquemática dentro de regiões Stage; texto/dados são auditados separadamente.",input_sha256:digest(readFileSync(inputPath)),clips:[]};
for(const scene of scenes)for(const element of scene.visual?.stage?.elements??[]) {
  if(!element.hyperframes)continue;
  const config=hyperframesArtSchema.parse(element.hyperframes);
  if(element.kind!=="object")throw new Error("HyperFrames exige objeto com envelope auditado.");
  const entry=local(config.entry),source=readFileSync(entry,"utf8");
  validateArtSource(source,config,scene.visual.beats??[]);
  if(preflight) {report.clips.push({scene_id:scene.id,element_id:element.id,entry:config.entry,states:config.states.length,prepared:false});continue;}
  const fps=payload.fps,frames=scene.duration_frames;
  const states=alignedArtStates(config,scene.visual.beats,frames,fps);
  const packagePath=local("node_modules/hyperframes/package.json"),pkg=JSON.parse(readFileSync(packagePath,"utf8"));
  const gsap=local("node_modules/gsap/dist/gsap.min.js");
  const sourceFiles=files(dirname(entry)).map(p=>({file:relative(dirname(entry),p).replaceAll("\\","/"),sha256:digest(readFileSync(p))}));
  const data={fps,frames,duration:frames/fps,width:config.width,height:config.height,initial_state:config.initial_state,states};
  const key=digest(JSON.stringify({data,sourceFiles,engine:pkg.version,gsap:digest(readFileSync(gsap))}));
  const id=`${String(scene.id).replace(/[^a-zA-Z0-9_-]/g,"_")}-${element.id.replace(/[^a-zA-Z0-9_-]/g,"_")}-${key.slice(0,16)}`;
  const publicFile=`generated-clips/${id}.mp4`,out=resolve("public",publicFile),meta=out+".json";
  let cached=false;
  if(existsSync(out)&&existsSync(meta)){const previous=JSON.parse(readFileSync(meta,"utf8"));cached=previous.key===key&&previous.output_sha256===digest(readFileSync(out));}
  const build=resolve("work/hyperframes",id);mkdirSync(build,{recursive:true});
  if(belongsToCurrent)registerTemporaryPaths(root,[`work/hyperframes/${id}`,`public/${publicFile}`,`public/${publicFile}.json`]);
  for(const p of files(dirname(entry))){const dest=resolve(build,relative(dirname(entry),p));mkdirSync(dirname(dest),{recursive:true});copyFileSync(p,dest);}
  copyFileSync(gsap,resolve(build,"gsap.min.js"));
  const json=JSON.stringify(data).replaceAll("<","\\u003c");
  writeFileSync(resolve(build,"index.html"),source.replace("<!--ODE_DATA-->",`<script>window.ODE=${json};</script>`).replaceAll("__ODE_DURATION__",String(data.duration)).replaceAll("__ODE_WIDTH__",String(config.width)).replaceAll("__ODE_HEIGHT__",String(config.height)));
  if(!cached){
    mkdirSync(dirname(out),{recursive:true});
    const bin=typeof pkg.bin==="string"?pkg.bin:pkg.bin.hyperframes;
    run(process.execPath,[resolve(dirname(packagePath),bin),"lint",build]);
    run(process.execPath,[resolve(dirname(packagePath),bin),"render",build,"--output",out,"--fps",String(fps),"--quality","delivery","--workers","2"]);
  }
  const probe=spawnSync("ffprobe",["-v","error","-select_streams","v:0","-count_frames","-show_entries","stream=width,height,avg_frame_rate,nb_read_frames:format=duration","-of","json",out],{encoding:"utf8"});
  if(probe.error||probe.status!==0)throw new Error(`FFprobe falhou: ${probe.error??probe.stderr}`);
  const info=JSON.parse(probe.stdout),stream=info.streams?.[0];
  if(!stream||Number(stream.nb_read_frames)!==frames||stream.avg_frame_rate!==`${fps}/1`||stream.width!==config.width||stream.height!==config.height)throw new Error(`Clipe diverge da timeline: ${id}`);
  if(Math.abs(Number(info.format.duration)-frames/fps)>1/fps+.001)throw new Error("Duração do clipe divergente.");
  const item={scene_id:scene.id,element_id:element.id,entry:config.entry,key,engine:`hyperframes@${pkg.version}`,sourceFiles,states,frames,fps,width:config.width,height:config.height,public_file:publicFile,output_sha256:digest(readFileSync(out)),cached};
  writeFileSync(meta,JSON.stringify(item,null,2)+"\n");report.clips.push(item);element.clip_file=publicFile;
}
mkdirSync("video/generated",{recursive:true});
writeFileSync(`video/generated/daily-hyperframes-${preflight?"preflight":"manifest"}.json`,JSON.stringify(report,null,2)+"\n");
if(!preflight)writeFileSync(inputPath,JSON.stringify(payload,null,2)+"\n");
console.log(`HyperFrames: ${report.clips.length} protagonistas; ${preflight?"contratos conferidos":"clipes preparados na timeline real"}.`);
