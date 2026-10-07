import {z} from "zod";

const count=z.number().finite().nonnegative().nullable();
const percent=count.refine(v=>v===null||v<=100,"Percentual deve estar entre 0 e 100.");
export const analyticsSnapshotSchema=z.object({
  version:z.literal("1.0"),record_type:z.literal("video_performance_snapshot"),
  captured_at:z.string().datetime({offset:true}),
  period:z.object({start:z.iso.date(),end:z.iso.date()}).refine(p=>p.start<=p.end,"Período invertido."),
  source:z.string().min(1),
  videos:z.array(z.object({
    video_id:z.string().regex(/^[A-Za-z0-9_-]{11}$/),title:z.string().min(1),
    format:z.enum(["long","short","live","unknown"]),traffic_source:z.string().min(1),
    published_at:z.string().datetime({offset:true}).nullable(),
    metrics:z.object({views:count,engaged_views:count,impressions:count,ctr_percent:percent,watch_hours:count,
      average_view_seconds:count,retention_30s_percent:percent,watch_hours_from_impressions:count}),
  })).min(1),
}).superRefine((snapshot,ctx)=>{
  const ids=snapshot.videos.map(v=>`${v.video_id}:${v.traffic_source}`);
  if(new Set(ids).size!==ids.length)ctx.addIssue({code:"custom",message:"Vídeo/origem duplicado no snapshot."});
});
export type AnalyticsSnapshot=z.infer<typeof analyticsSnapshotSchema>;

function csvRows(text:string):string[][] {
  text=text.replace(/^\uFEFF/,"");
  const first=text.split(/\r?\n/,1)[0];
  const delimiter=(first.match(/;/g)?.length??0)>(first.match(/,/g)?.length??0)?";":",";
  const rows:string[][]=[];let row:string[]=[],cell="",quoted=false;
  for(let i=0;i<text.length;i++) {
    const c=text[i];
    if(c==='"') {
      if(quoted&&text[i+1]==='"'){cell+='"';i++;}
      else if(quoted)quoted=false;
      else if(cell.length===0)quoted=true;
      else throw new Error("Aspas inesperadas no CSV.");
    } else if(c===delimiter&&!quoted){row.push(cell);cell="";}
    else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(v=>v.trim()))rows.push(row);row=[];cell="";}
    else cell+=c;
  }
  if(quoted)throw new Error("CSV contém campo com aspas não encerradas.");
  if(cell||row.length){row.push(cell);rows.push(row);}
  return rows;
}
const normalized=(s:string)=>s.normalize("NFD").replace(/\p{M}/gu,"").toLowerCase().replace(/[^a-z0-9]/g,"");
const empty=(s:string)=>!s.trim()||/^(—|-|n\/a)$/i.test(s.trim());
export function studioNumber(value:string,locale:"pt-BR"|"en-US"):number|null {
  if(empty(value))return null;
  let text=value.trim().replace(/[%\s\u00a0]/g,"");
  text=locale==="pt-BR"?text.replace(/\./g,"").replace(",","."):text.replace(/,/g,"");
  if(!/^\d+(\.\d+)?$/.test(text))throw new Error(`Número inválido para ${locale}: ${value}`);
  const result=Number(text);
  if(!Number.isFinite(result))throw new Error(`Número não finito: ${value}`);
  return result;
}
function duration(value:string):number|null {
  if(empty(value))return null;
  const parts=value.trim().split(":");
  if(parts.length<2||parts.length>3||parts.some(p=>!/^\d+$/.test(p))||parts.slice(1).some(p=>Number(p)>59))throw new Error(`Duração exige m:ss ou h:mm:ss: ${value}`);
  return parts.reduce((seconds,p)=>seconds*60+Number(p),0);
}
const aliases={
  video_id:["conteudo","content","videoid","iddovideo"],title:["titulodovideo","videotitle","title"],
  views:["visualizacoes","views"],engaged_views:["visualizacoesengajadas","engagedviews"],
  impressions:["impressoes","impressions"],ctr_percent:["taxadecliquesdeimpressoes","taxadecliquesnasimpressoes","taxadecliquesnaminiatura","impressionsclickthroughrate"],
  watch_hours:["tempodeexibicaohoras","watchtimehours"],average_view_seconds:["duracaomediadavisualizacao","averageviewduration"],
  retention_30s_percent:["retencaoem030","retentionat030"],watch_hours_from_impressions:["tempodeexibicaodeimpressoeshoras","watchtimefromimpressionshours"],
};
type CsvOptions={start:string;end:string;format:AnalyticsSnapshot["videos"][number]["format"];locale:"pt-BR"|"en-US";source:string;captured_at:string;traffic_source?:string};
export function importStudioCsv(text:string,options:CsvOptions):{snapshot:AnalyticsSnapshot;warnings:string[]} {
  const rows=csvRows(text);if(!rows.length)throw new Error("CSV vazio.");
  const headers=rows.shift()!.map(normalized),warnings:string[]=[];
  const columns=Object.fromEntries(Object.entries(aliases).map(([key,names])=>[key,headers.findIndex(h=>names.map(normalized).includes(h))]));
  if(columns.video_id<0||columns.title<0)throw new Error("Exportação exige ID (Conteúdo/Content) e Título do vídeo/Video title.");
  const get=(row:string[],key:string)=>columns[key]<0?"":row[columns[key]]??"";
  const videos:AnalyticsSnapshot["videos"]=[];
  for(const [index,row] of rows.entries()) {
    if(row.length!==headers.length)throw new Error(`Linha ${index+2}: número de colunas diverge do cabeçalho.`);
    const id=get(row,"video_id").trim();
    if(["total","totais"].includes(id.toLowerCase()))continue;
    if(!/^[A-Za-z0-9_-]{11}$/.test(id))throw new Error(`Linha ${index+2}: ID do vídeo inválido; não associe vídeos por título.`);
    const metrics=Object.fromEntries(Object.keys(aliases).filter(k=>!["video_id","title"].includes(k)).map(key=>[key,key==="average_view_seconds"?duration(get(row,key)):studioNumber(get(row,key),options.locale)]));
    videos.push({video_id:id,title:get(row,"title"),format:options.format,traffic_source:options.traffic_source??"all",published_at:null,metrics:metrics as AnalyticsSnapshot["videos"][number]["metrics"]});
  }
  warnings.push("Datas de publicação ausentes: compare idade dos vídeos apenas após preenchê-las com dados verificados.");
  if(options.format==="unknown")warnings.push("Formato não informado: não comparar Shorts, vídeos longos e lives como um grupo.");
  for(const key of Object.keys(aliases).filter(k=>!["video_id","title"].includes(k)&&columns[k]<0))warnings.push(`${key} não exportado; mantido como null.`);
  return {snapshot:analyticsSnapshotSchema.parse({version:"1.0",record_type:"video_performance_snapshot",captured_at:options.captured_at,period:{start:options.start,end:options.end},source:options.source,videos}),warnings};
}

export function summarizeSnapshot(snapshot:AnalyticsSnapshot) {
  return snapshot.videos.map(v=>({video_id:v.video_id,title:v.title,format:v.format,traffic_source:v.traffic_source,
    age_hours:v.published_at?Math.round((Date.parse(snapshot.captured_at)-Date.parse(v.published_at))/3600000*10)/10:null,
    ...v.metrics,
    // Only the impression funnel has a common numerator and denominator.
    watch_seconds_per_impression:v.metrics.impressions&&v.metrics.watch_hours_from_impressions!==null?
      Math.round(v.metrics.watch_hours_from_impressions*3600/v.metrics.impressions*1000)/1000:null,
  }));
}
