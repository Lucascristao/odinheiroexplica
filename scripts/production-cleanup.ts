import {createHash} from "node:crypto";
import {execFileSync} from "node:child_process";
import {existsSync,lstatSync,mkdirSync,readFileSync,readdirSync,realpathSync,rmSync,rmdirSync,writeFileSync} from "node:fs";
import {dirname,isAbsolute,relative,resolve,sep} from "node:path";

export const projectSourceHash=(text:string)=>createHash("sha256").update(text.replaceAll("\r\n","\n")).digest("hex");
const hash=(file:string,algorithm="sha256")=>createHash(algorithm).update(readFileSync(file)).digest("hex");
const read=(file:string)=>{
  if(lstatSync(file).isSymbolicLink()||lstatSync(file).size>32*1024*1024)throw new Error("Recibo inválido ou simbólico.");
  return JSON.parse(readFileSync(file,"utf8"));
};
const inside=(root:string,path:string)=>{const r=relative(root,path);return r!==""&&!isAbsolute(r)&&r!==".."&&!r.startsWith(`..${sep}`);};
const normalized=(path:string)=>path.replaceAll("\\","/");

export function completePackage(files:any[]):boolean {
  const usable=files.filter(f=>typeof f.id==="string"&&f.id.length>0&&Number(f.size)>0);
  return [
    (n:string)=>n==="daily-video.mp4",
    (n:string)=>n==="daily-youtube.json",
    (n:string)=>n==="daily-youtube.txt",
    (n:string)=>/^thumbnail-[a-f0-9]{12}\.(?:jpe?g|png)$/.test(n),
    (n:string)=>/^editorial-review-[a-f0-9]{12}\.(?:md|json)$/.test(n),
  ].every(test=>usable.some(f=>test(f.name)));
}

function safePath(root:string,path:string) {
  if(!inside(root,path))throw new Error("Destino de limpeza fora do workspace.");
  for(let p=path;p!==root;p=dirname(p)) {
    if(existsSync(p)&&lstatSync(p).isSymbolicLink())throw new Error("Limpeza recusada: link ou junction.");
  }
  if(existsSync(path)&&!inside(root,realpathSync(path)))throw new Error("Destino real fora do workspace.");
}

const allowedTemporary=(p:string)=>!p.includes("\\")&&/^(?:work\/runs\/\d+|work\/hyperframes\/[A-Za-z0-9_-]+|work\/[A-Za-z0-9_-]+\.[A-Za-z0-9]+|render-output\/.+|video\/generated\/.+|public\/(?:generated-audio|processed-audio|generated-assets|generated-sfx|generated-music|generated-clips)\/.+)$/.test(p)&&p!=="work/production-state.json"&&p!=="work/temporary-ownership.json"&&!p.split("/").some(s=>s===".."||s===".");

export function registerTemporaryPaths(rootPath:string,paths:string[]) {
  const root=realpathSync(rootPath),text=readFileSync(resolve(root,"video/data/daily.json"),"utf8"),project=JSON.parse(text);
  const registry=resolve(root,"work/temporary-ownership.json");safePath(root,registry);
  const entries:any[]=existsSync(registry)?read(registry).entries:[];
  for(const path of paths) {
    if(!allowedTemporary(path))throw new Error(`Destino temporário não permitido: ${path}`);
    safePath(root,resolve(root,path));
    const previous=entries.findIndex(e=>e.path===path);if(previous>=0)entries.splice(previous,1);
    entries.push({path,project_id:project.project_id,source_project_sha256:projectSourceHash(text)});
  }
  mkdirSync(dirname(registry),{recursive:true});writeFileSync(registry,JSON.stringify({entries},null,2)+"\n");
}

export function cleanupCompletedProduction(rootPath:string,productionRelative:string,options:{trackedFiles?:string[]}={}) {
  const root=realpathSync(rootPath);
  if(!/^production\/[A-Za-z0-9][A-Za-z0-9._-]*$/.test(productionRelative))throw new Error("Limpeza exige production/EPISODIO, sem traversal.");
  const production=resolve(root,productionRelative);safePath(root,production);
  const currentPath=resolve(root,"video/data/daily.json"),currentText=readFileSync(currentPath,"utf8"),project=JSON.parse(currentText);
  const fingerprint=projectSourceHash(currentText);
  const receipt=read(resolve(production,"final-delivery.json"));
  if(receipt.complete_package!==true||!Array.isArray(receipt.files)||!completePackage(receipt.files))throw new Error("Entrega incompleta: temporários preservados.");
  if(receipt.project_id!==project.project_id||receipt.source_project_sha256!==fingerprint)throw new Error("Projeto do recibo diverge do projeto atual; nada será apagado.");
  for(const [role,names] of [["thumbnail",["thumbnail.jpg","thumbnail.png"]],["editorial-review",["review.md","review.json"]]] as const) {
    const file=names.map(name=>resolve(production,name)).find(existsSync);
    if(file) {
      const digest=role==="thumbnail"?hash(file):projectSourceHash(readFileSync(file,"utf8"));
      if(!receipt.files.some((f:any)=>f.name.startsWith(`${role}-${digest.slice(0,12)}.`)))throw new Error("A versão atual da capa/revisão ainda não está no Drive; temporários preservados.");
    }
  }
  if(!/^[A-Za-z0-9_-]{10,}$/.test(receipt.folder_id??""))throw new Error("Pasta de entrega inválida.");
  const statePath=resolve(root,"work/production-state.json");
  if(existsSync(statePath)) {
    const state=read(statePath);
    if(state.project_id&&state.project_id!==project.project_id)throw new Error("Outra produção possui estado ativo; temporários preservados.");
  }
  const deliveryPath=resolve(production,"delivery.json"),delivery=existsSync(deliveryPath)?read(deliveryPath):null;
  if(delivery&&delivery.folder_id!==receipt.folder_id)throw new Error("Recibos de entrega apontam pastas diferentes.");
  const expectedSha=delivery?.files?.video?.sha256;
  const remoteVideo=receipt.files.find((f:any)=>f.name==="daily-video.mp4");
  if(delivery&&(delivery.files?.video?.file_id!==remoteVideo.id||Number(delivery.files.video.size_bytes)!==Number(remoteVideo.size)))throw new Error("O vídeo confirmado difere do upload original; temporários preservados.");
  const expectedMd5=remoteVideo?.md5Checksum;
  if(!/^[a-f0-9]{64}$/.test(expectedSha??"")&&!/^[a-f0-9]{32}$/.test(expectedMd5??""))throw new Error("Falta checksum do vídeo entregue; temporários preservados.");
  const resumePath=resolve(production,"resume-receipt.json"),resume=existsSync(resumePath)?read(resumePath):null;
  const targets:string[]=[];
  const runs=resolve(root,"work/runs");safePath(root,runs);
  for(const name of existsSync(runs)?readdirSync(runs):[]) {
    if(!/^\d+$/.test(name))continue;
    const dir=resolve(runs,name);safePath(root,dir);
    if(!lstatSync(dir).isDirectory())continue;
    const source=resolve(dir,"video/data/daily.json"),video=resolve(dir,"render-output/daily-video.mp4");
    const recovered=resolve(dir,"video/generated/daily-resume-receipt.json");
    const supplement=[resolve(dir,"daily-supplement-drive.json"),resolve(dir,"render-output/daily-supplement-drive.json")].find(existsSync);
    let owned=false;
    for(const path of [source,video,recovered,...(supplement?[supplement]:[])])safePath(root,path);
    if(existsSync(source)&&projectSourceHash(readFileSync(source,"utf8"))===fingerprint) {
      if(!existsSync(video)||(expectedSha?hash(video)!==expectedSha:hash(video,"md5")!==expectedMd5)||(expectedMd5&&hash(video,"md5")!==expectedMd5))throw new Error("MP4 local ainda não corresponde à entrega; arquivos preservados.");
      owned=true;
    } else if(existsSync(recovered)&&resume) {
      const data=read(recovered);
      owned=data.source_run_id===resume.source_run_id&&data.video_sha256===expectedSha;
      if(owned&&existsSync(video)&&(hash(video)!==expectedSha||(expectedMd5&&hash(video,"md5")!==expectedMd5)))throw new Error("MP4 retomado diverge da entrega; temporários preservados.");
    } else if(supplement) {
      const data=read(supplement);
      owned=data.verified_readback===true&&data.project_id===project.project_id&&data.source_project_sha256===fingerprint&&data.folder?.id===receipt.folder_id;
    }
    if(owned)targets.push(dir);
  }
  // HTML staging is disposable only when the renderer marked its project owner.
  const staging=resolve(root,"work/hyperframes");safePath(root,staging);
  for(const name of existsSync(staging)?readdirSync(staging):[]) {
    const dir=resolve(staging,name);safePath(root,dir);
    if(!lstatSync(dir).isDirectory())continue;
    const marker=resolve(dir,".ode-temporary-owner.json");
    if(existsSync(marker)) {
      const owner=read(marker);
      if(owner.project_id===project.project_id&&owner.source_project_sha256===fingerprint)targets.push(dir);
    }
  }
  const registry=resolve(root,"work/temporary-ownership.json");safePath(root,registry);
  const registered=existsSync(registry)?read(registry).entries:[];
  for(const entry of registered)if(entry.project_id===project.project_id&&entry.source_project_sha256===fingerprint) {
    if(!allowedTemporary(entry.path))throw new Error("Registro de temporário fora das pastas permitidas.");
    const path=resolve(root,entry.path);safePath(root,path);
    if(existsSync(path)&&!targets.includes(path))targets.push(path);
  }
  const tracked=options.trackedFiles??execFileSync("git",["ls-files","-z"],{cwd:root,encoding:"utf8"}).split("\0").filter(Boolean);
  const walk=(path:string):number=>{
    safePath(root,path);
    const info=lstatSync(path);
    if(info.isSymbolicLink())throw new Error("Limpeza recusada: link ou junction.");
    if(info.isDirectory())return readdirSync(path).reduce((n,e)=>n+walk(resolve(path,e)),0);
    if(!info.isFile())throw new Error("Temporário contém entrada não regular.");
    return info.size;
  };
  // Validate the whole plan before the first recursive deletion.
  const plan=targets.filter(path=>!targets.some(parent=>parent!==path&&inside(parent,path))).map(path=>{
    const local=normalized(relative(root,path));
    if(tracked.some(file=>file===local||file.startsWith(local+"/")))throw new Error("Limpeza recusada: destino contém arquivo versionado.");
    return {path,local,bytes:walk(path)};
  });
  const result:{status:"complete"|"pending";removed_paths:string[];reclaimed_bytes:number;errors:string[];project_id:string;folder_id:string;completed_at:string}={status:"complete",removed_paths:[],reclaimed_bytes:0,errors:[],project_id:project.project_id,folder_id:receipt.folder_id,completed_at:new Date().toISOString()};
  for(const item of plan) {
    try {
      safePath(root,item.path);walk(item.path);
      rmSync(item.path,{recursive:true,force:false,maxRetries:2,retryDelay:100});
      result.removed_paths.push(item.local);result.reclaimed_bytes+=item.bytes;
    } catch(error) {result.status="pending";result.errors.push(`${item.local}: ${error instanceof Error?error.message:String(error)}`);}
  }
  for(const dir of [runs,staging])if(existsSync(dir)&&readdirSync(dir).length===0)rmdirSync(dir);
  if(existsSync(registry)) {
    const remaining=registered.filter((e:any)=>!result.removed_paths.some(path=>e.path===path||e.path.startsWith(path+"/")));
    if(remaining.length)writeFileSync(registry,JSON.stringify({entries:remaining},null,2)+"\n");else rmSync(registry);
  }
  mkdirSync(production,{recursive:true});writeFileSync(resolve(production,"cleanup.json"),JSON.stringify(result,null,2)+"\n");
  if(existsSync(statePath)&&result.status==="complete")writeFileSync(statePath,JSON.stringify({...read(statePath),stage:"delivered-and-cleaned",folder_id:receipt.folder_id,updated_at:result.completed_at},null,2)+"\n");
  return result;
}

export function prepareReceiptDirectory(rootPath:string,runId:string) {
  if(!/^\d+$/.test(runId))throw new Error("ID de execução inválido.");
  const root=realpathSync(rootPath),dir=resolve(root,"work/runs",runId);safePath(root,dir);
  if(existsSync(dir)&&readdirSync(dir).length)throw new Error("Destino do recibo já contém arquivos.");
  mkdirSync(dir,{recursive:true});safePath(root,dir);return dir;
}

export function recordSupplementCompletion(rootPath:string,productionRelative:string,supplement:any,runId:string) {
  const root=realpathSync(rootPath),projectText=readFileSync(resolve(root,"video/data/daily.json"),"utf8"),project=JSON.parse(projectText);
  const fingerprint=projectSourceHash(projectText);
  if(supplement.verified_readback!==true||supplement.project_id!==project.project_id||supplement.source_project_sha256!==fingerprint)throw new Error("Readback do suplemento não corresponde ao projeto atual.");
  const files=supplement.folder_files??[];
  if(!completePackage(files))return null; // The other supplement has not arrived yet.
  if(!/^production\/[A-Za-z0-9][A-Za-z0-9._-]*$/.test(productionRelative))throw new Error("Pasta de produção inválida.");
  const production=resolve(root,productionRelative);safePath(root,production);
  for(const [role,names] of [["thumbnail",["thumbnail.jpg","thumbnail.png"]],["editorial-review",["review.md","review.json"]]] as const) {
    const file=names.map(name=>resolve(production,name)).find(existsSync);
    if(!file)return null;
    const digest=role==="thumbnail"?hash(file):projectSourceHash(readFileSync(file,"utf8"));
    if(!files.some((f:any)=>f.name.startsWith(`${role}-${digest.slice(0,12)}.`)))return null;
  }
  const receipt={project_id:project.project_id,source_project_sha256:fingerprint,verified_at:new Date().toISOString(),method:"Actions supplement readback",folder_id:supplement.folder.id,folder_url:supplement.folder.webViewLink,files,complete_package:true,supplement_run_id:runId};
  writeFileSync(resolve(production,"final-delivery.json"),JSON.stringify(receipt,null,2)+"\n");
  return cleanupCompletedProduction(root,productionRelative);
}
