import {readFileSync,writeFileSync,mkdirSync} from "node:fs";
import {resolve,dirname,basename} from "node:path";
import {analyticsSnapshotSchema,importStudioCsv,summarizeSnapshot} from "../src/lib/youtube-analytics";

const args=process.argv.slice(2);
const option=(key:string)=>{const i=args.indexOf(key);return i<0?undefined:args[i+1];};
const input=option("--input");
if(!input)throw new Error("Informe --input export.csv|snapshot.json. CSV exige --start YYYY-MM-DD --end YYYY-MM-DD e --locale pt-BR|en-US.");
const text=readFileSync(resolve(input),"utf8");
let snapshot,warnings:string[]=[];
if(input.toLowerCase().endsWith(".csv")) {
  const start=option("--start"),end=option("--end"),locale=option("--locale");
  const format=option("--format")??"unknown";
  if(!start||!end||!["pt-BR","en-US"].includes(locale??""))throw new Error("CSV exige período e locale explícitos; não inferir janela nem separador decimal.");
  if(!["long","short","live","unknown"].includes(format))throw new Error("--format deve ser long, short, live ou unknown.");
  ({snapshot,warnings}=importStudioCsv(text,{start,end,locale:locale as "pt-BR"|"en-US",format:format as "long"|"short"|"live"|"unknown",source:basename(input),captured_at:new Date().toISOString(),traffic_source:option("--traffic-source")}));
} else snapshot=analyticsSnapshotSchema.parse(JSON.parse(text));
const output=option("--output");
if(output){const path=resolve(output);mkdirSync(dirname(path),{recursive:true});writeFileSync(path,JSON.stringify(snapshot,null,2)+"\n");}
console.log(JSON.stringify({period:snapshot.period,warnings,comparison_notes:["Compare formato, idade, janela e origem de tráfego semelhantes.","Não há vencedor automático nem meta universal de CTR/retenção.","Views gerais não são denominador da duração média engajada."],videos:summarizeSnapshot(snapshot)},null,2));
