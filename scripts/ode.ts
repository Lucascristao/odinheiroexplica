import {readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync} from "node:fs";
import {resolve, dirname} from "node:path";
import {spawnSync} from "node:child_process";
import {createHash} from "node:crypto";
import {productionChatRequest} from "../src/lib/production-chat-request";
import {cleanupCompletedProduction,prepareReceiptDirectory,recordSupplementCompletion,registerTemporaryPaths} from "./production-cleanup";

const root=resolve(import.meta.dirname,"..");
process.chdir(root);
const args=process.argv.slice(2), command=args[0]??"context";
const option=(key:string,fallback?:string)=>{const i=args.indexOf(key);return i<0?fallback:args[i+1];};
const load=(file:string)=>JSON.parse(readFileSync(resolve(root,file),"utf8"));
const run=(exe:string,values:string[])=>{
  const result=spawnSync(exe,values,{cwd:root,stdio:"inherit",env:process.env});
  if(result.error)throw result.error;
  if(result.status!==0)process.exit(result.status??1);
};
const gh=(values:string[])=>run("gh",[...values,"--repo","Lucascristao/odinheiroexplica"]);
const capture=(exe:string,values:string[])=>{
  const result=spawnSync(exe,values,{cwd:root,encoding:"utf8",env:process.env});
  if(result.error||result.status!==0)throw new Error(`${exe}: ${result.error??result.stderr}`);
  return result.stdout.trim();
};
const python=process.env.ODE_PYTHON??"python";
const statePath=resolve(root,"work/production-state.json");
const project=load("video/data/daily.json");
const fingerprint=createHash("sha256").update(readFileSync("video/data/daily.json")).digest("hex");
const state=()=>existsSync(statePath)?load("work/production-state.json"):null;
const save=(value:object)=>{mkdirSync(dirname(statePath),{recursive:true});writeFileSync(statePath,JSON.stringify(value,null,2)+"\n");};
if(command==="thumbnail-spec") {
  run(process.execPath,["node_modules/tsx/dist/cli.mjs","scripts/thumbnail-spec.ts",...args.slice(1)]);
} else if(command==="analytics") {
  run(process.execPath,["node_modules/tsx/dist/cli.mjs","scripts/youtube-analytics.ts",...args.slice(1)]);
} else if(command==="prompt") {
  console.log(productionChatRequest(option("--request","Gere um vídeo inédito para o O Dinheiro Explica e entregue o pacote completo no Drive.")!,{mode:args.includes("--direct")?"direct":"normal",chooseTopic:!args.includes("--ask-topic")}));
} else if(command==="context"||command==="capabilities") {
  console.log(JSON.stringify({version:"1.0",project:project.project_id,title:project.title,project_sha256:fingerprint,voice:load("worker/voice-policy.json"),skills:readdirSync("skills").filter(s=>existsSync(`skills/${s}/SKILL.md`)).map(s=>`skills/${s}/SKILL.md`),contracts:["AGENTS.md","frame.md","docs/architecture.md","docs/production-portable.md","src/lib/video-project-schema.ts","src/lib/editorial-stage.ts"],capabilities:{stage:["objects","camera","equation","compare","chart","source_excerpt","captions","sfx"],hyperframes:"HTML por protagonista, eventos alinhados, texto e relações no Stage",review:"frames do MP4 e diagnóstico regional; revisão semântica pelo agente",delivery:"Actions → Drive; publicação manual"},state:state()},null,2));
} else if(command==="preflight") {
  registerTemporaryPaths(root,["video/generated/daily-source-audit.json","video/generated/daily-pronunciation-audit.json","video/generated/daily-hyperframes-preflight.json"]);
  run(process.execPath,["node_modules/tsx/dist/cli.mjs","scripts/thumbnail-spec.ts","--check",...(args.includes("--new-episode")?["--new-episode"]:[])]);
  run(process.execPath,["node_modules/tsx/dist/cli.mjs","scripts/validate-editorial.ts","video/data/daily.json","--require-explanation",...(args.includes("--new-episode")?["--require-learning"]:[])]);
  run(python,["worker/editorial_source_audit.py","--input","video/data/daily.json","--output","video/generated/daily-source-audit.json","--strict"]);
  run(python,["worker/pronunciation_audit.py","--input","video/data/daily.json","--output","video/generated/daily-pronunciation-audit.json","--strict"]);
  run(process.execPath,["node_modules/tsx/dist/cli.mjs","scripts/prepare-hyperframes.ts","--preflight"]);
  save({version:"1.0",project_id:project.project_id,project_sha256:fingerprint,stage:"preflight-complete",updated_at:new Date().toISOString()});
} else if(command==="dispatch"||command==="render") {
  const previous=state();
  if(previous?.project_sha256!==fingerprint||previous?.stage!=="preflight-complete")throw new Error("Execute preflight para o conteúdo atual antes do dispatch.");
  const head=capture("git",["rev-parse","HEAD"]);
  const committed=capture("git",["show","HEAD:video/data/daily.json"]);
  if(JSON.stringify(JSON.parse(committed))!==JSON.stringify(project))throw new Error("daily.json atual ainda não está no commit.");
  const remote=capture("gh",["api","repos/Lucascristao/odinheiroexplica/commits/main","--jq",".sha"]);
  if(remote!==head)throw new Error("A main remota diverge do checkout. Envie e confira o commit antes de produzir.");
  const direct=project.editorial?.production_mode==="direct";
  if(!direct){
    const checks=JSON.parse(capture("gh",["run","list","--workflow","ci.yml","--branch","main","--limit","20","--json","headSha,status,conclusion","--repo","Lucascristao/odinheiroexplica"]));
    if(!checks.some((c:any)=>c.headSha===head&&c.status==="completed"&&c.conclusion==="success"))throw new Error("Aguarde o CI aprovado do mesmo commit antes do dispatch normal.");
  }
  gh(["workflow","run","render-daily.yml","--ref","main"]);
  save({...previous,head_sha:head,stage:"dispatch-requested",updated_at:new Date().toISOString()});
  console.log("Disparo solicitado. Use status e confira headSha; iniciar não conclui a entrega.");
} else if(command==="status") {
  const id=option("--run-id");
  if(id)gh(["run","view",id,"--json","databaseId,headSha,status,conclusion,jobs,url"]);
  else gh(["run","list","--workflow","render-daily.yml","--limit","5","--json","databaseId,headSha,status,conclusion,url"]);
} else if(command==="resume") {
  const id=option("--run-id");if(!id||!/^\d+$/.test(id))throw new Error("resume exige --run-id numérico. Confira que o run corresponde ao commit desejado.");
  if(args.includes("--delivery-only")) {
    gh(["workflow","run","resume-delivery.yml","--ref","main","-f",`source_run_id=${id}`]);
  } else gh(["run","rerun",id,"--failed"]);
} else if(command==="review") {
  if(load("video/generated/daily-render-input.json").project_id!==project.project_id)throw new Error("O vídeo preparado não pertence ao projeto atual; não registre nem remova a revisão de outro episódio.");
  registerTemporaryPaths(root,["render-output/visual-review","render-output/daily-visual-review.zip"]);
  run(python,["worker/review_rendered_video.py","--input","video/generated/daily-render-input.json","--video","render-output/daily-video.mp4","--output-dir","render-output/visual-review"]);
} else if(command==="deliver") {
  const folder=option("--folder-id"),file=option("--file"),role=option("--role","thumbnail");
  const validFile=role==="thumbnail"&&/^production\/[A-Za-z0-9][A-Za-z0-9._-]*\/thumbnail\.(jpg|png)$/.test(file??"")||role==="editorial-review"&&/^production\/[A-Za-z0-9][A-Za-z0-9._-]*\/review\.(md|json)$/.test(file??"");
  if(!folder||!validFile)throw new Error("deliver exige pasta verificada e arquivo canônico production/EPISODIO/thumbnail.jpg|png ou review.md|json.");
  const dispatched=capture("gh",["workflow","run","deliver-supplement.yml","--ref","main","-f",`folder_id=${folder}`,"-f",`asset_path=${file}`,"-f",`role=${role}`,"--repo","Lucascristao/odinheiroexplica"]);
  console.log(dispatched);
  const id=dispatched.match(/github\.com\/Lucascristao\/odinheiroexplica\/actions\/runs\/(\d+)/i)?.[1];
  if(!id)throw new Error("Envio solicitado, mas a versão do gh não retornou o ID. Nenhum temporário será apagado sem o recibo da execução.");
  gh(["run","watch",id,"--exit-status","--interval","15"]);
  const directory=prepareReceiptDirectory(root,id);
  gh(["run","download",id,"--name","daily-supplement-delivery","--dir",directory]);
  const receiptPath=[resolve(directory,"daily-supplement-drive.json"),resolve(directory,"render-output/daily-supplement-drive.json")].find(existsSync);
  if(!receiptPath)throw new Error("Recibo do suplemento ausente; temporários preservados.");
  const result=recordSupplementCompletion(root,dirname(file!).replaceAll("\\","/"),JSON.parse(readFileSync(receiptPath,"utf8")),id);
  if(result){console.log(JSON.stringify(result,null,2));if(result.status!=="complete")process.exitCode=1;}
  else console.log("Suplemento entregue. Limpeza automática aguarda capa e revisão das versões atuais para confirmar o pacote completo.");
} else if(command==="complete"||command==="cleanup") {
  const production=option("--production");if(!production)throw new Error("complete exige --production production/EPISODIO com recibo completo.");
  const result=cleanupCompletedProduction(root,production);console.log(JSON.stringify(result,null,2));if(result.status!=="complete")process.exitCode=1;
} else throw new Error("Comando desconhecido: context, capabilities, thumbnail-spec, prompt, analytics, preflight, dispatch, render, status, resume, review, deliver, complete.");
