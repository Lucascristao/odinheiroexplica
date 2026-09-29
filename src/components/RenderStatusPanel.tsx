import {useCallback, useEffect, useRef, useState} from "react";
import {AlertTriangle, CheckCircle2, ExternalLink, Film, HardDrive, Image, RefreshCw} from "lucide-react";
import {supabase} from "../lib/supabase";

type Job = {runId:string; title:string; status:string; stage:string; detail:string; percent:number; etaSeconds:number|null; videoDurationSeconds:number|null; createdAt:string; updatedAt:string; finishedAt?:string|null; deliveryConfirmed?:boolean; driveFolderUrl?:string|null};
const stages = ["Preparação", "Narração", "Composição", "Render", "Drive"];
const positions: Record<string,number> = {fila:0,preparando:0,audio:1,timeline:2,dependencias:2,render:3,publicando:4,concluido:5};
const labels: Record<string,string> = {fila:"Na fila",preparando:"Preparando produção",audio:"Gerando narração",timeline:"Montando composição",dependencias:"Preparando render",render:"Renderizando vídeo",publicando:"Enviando ao Drive",concluido:"Processamento concluído",erro:"Produção interrompida"};
function duration(n:number|null|undefined) {if(n==null||!Number.isFinite(n))return "—"; n=Math.max(0,Math.floor(n));return `${Math.floor(n/60)}:${String(n%60).padStart(2,"0")}`;}
function time(s:string) {const d=new Date(s);return Number.isNaN(d.getTime())?"—":d.toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"});}

export function RenderStatusPanel() {
  const [job,setJob]=useState<Job|null>(null);
  const [checking,setChecking]=useState(false);
  const [error,setError]=useState("");
  const [now,setNow]=useState(Date.now());
  const inFlight=useRef(false);
  const refresh=useCallback(async()=>{
    if(inFlight.current)return;
    inFlight.current=true;setChecking(true);
    const controller=new AbortController();
    const timeout=window.setTimeout(()=>controller.abort(),15000);
    try {
      if(!supabase)throw new Error("A conexão do painel está indisponível.");
      const {data}=await supabase.auth.getSession();
      if(!data.session)throw new Error("Entre novamente para acompanhar a produção.");
      const response=await fetch("/.netlify/functions/render-status",{cache:"no-store",headers:{Authorization:`Bearer ${data.session.access_token}`},signal:controller.signal});
      const payload=await response.json();
      if(!response.ok)throw new Error(payload.error??"Não foi possível consultar o fluxo.");
      setJob(payload.job??null);setError("");setNow(Date.now());
    } catch(e) {setError(e instanceof Error && e.name!=="AbortError"?e.message:"A consulta demorou. Tente atualizar.");}
    finally {window.clearTimeout(timeout);inFlight.current=false;setChecking(false);}
  },[]);
  const running=job?.status==="running"||job?.status==="queued";
  useEffect(()=>{void refresh();const visible=()=>{if(document.visibilityState==="visible")void refresh();};document.addEventListener("visibilitychange",visible);return()=>document.removeEventListener("visibilitychange",visible);},[refresh]);
  useEffect(()=>{
    if(!running)return;
    const poll=window.setInterval(()=>{if(document.visibilityState==="visible")void refresh();},20000);
    const clock=window.setInterval(()=>setNow(Date.now()),1000);
    return()=>{window.clearInterval(poll);window.clearInterval(clock);};
  },[running,refresh]);

  const done=job?.status==="completed", failed=job?.status==="error", delivered=done&&job?.deliveryConfirmed;
  const stale=running&&now-new Date(job!.updatedAt).getTime()>180000;
  const github=job&&/^\d+$/.test(job.runId)?`https://github.com/Lucascristao/odinheiroexplica/actions/runs/${job.runId}`:"https://github.com/Lucascristao/odinheiroexplica/actions";
  const drive=job?.driveFolderUrl&&/^https:\/\/drive\.google\.com\/drive\/folders\/[a-zA-Z0-9_-]+$/.test(job.driveFolderUrl)?job.driveFolderUrl:null;
  const elapsed=job?((running?now:new Date(job.finishedAt??job.updatedAt).getTime())-new Date(job.createdAt).getTime())/1000:null;
  const position=job?positions[job.stage]??-1:-1;
  const next=failed?"Abra a execução no GitHub e leve a falha ao chat para corrigir e retomar.":delivered?"Volte ao ChatGPT para gerar a capa final com a embalagem deste vídeo.":done?"Confira a execução. A entrega no Drive ainda não tem confirmação registrada.":stale?"Confira o GitHub: ausência de atualização no painel não confirma falha do render.":job?"A produção segue no GitHub. Você pode fechar esta página e voltar depois.":"Peça o próximo vídeo no ChatGPT. Depois de iniciar, clique em Atualizar.";

  return <section className={`panel render-status-panel production-monitor ${failed?"failed":delivered?"ready":""}`} aria-labelledby="production-status">
    <div className="panel-heading"><div><p className="eyebrow">Acompanhamento do fluxo</p><h2 id="production-status">{delivered?"Vídeo entregue no Drive":job?labels[job.stage]??"Em produção":"Pronto para acompanhar"}</h2></div><button className="secondary-button" onClick={()=>void refresh()} disabled={checking}><RefreshCw size={16} className={checking?"spin":undefined}/>{checking?"Atualizando":"Atualizar"}</button></div>
    {error&&<div className="validation-box error" role="alert"><AlertTriangle size={18}/><span>{error} {job?"Exibindo a última informação recebida.":""}</span></div>}
    {job&&<>
      <div className="monitor-title"><Film size={22}/><h3>{job.title}</h3><span className="status-chip">{failed?"Atenção":delivered?"Entregue":done?"Finalizado":"Em produção"}</span></div>
      <ol className="monitor-stages">{stages.map((label,i)=><li key={label} className={delivered||(!failed&&position>i)?"complete":running&&position===i?"active":""} aria-current={running&&position===i?"step":undefined}><span>{delivered||(!failed&&position>i)?<CheckCircle2 size={18}/>:String(i+1).padStart(2,"0")}</span><strong>{label}</strong></li>)}</ol>
      <div className="render-progress-track" role="progressbar" aria-label="Progresso estimado da produção" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(job.percent)}><div style={{width:`${Math.max(0,Math.min(100,job.percent))}%`}}/></div>
      <div className="monitor-progress-caption"><span>{failed?"Interrompido":running?"Progresso estimado":"Processamento"} · {Math.round(job.percent)}%</span><span>Atualizado às {time(job.updatedAt)}</span></div>
      <div className="render-metrics"><div><span>Tempo decorrido</span><strong>{duration(elapsed)}</strong></div><div><span>Duração do vídeo</span><strong>{duration(job.videoDurationSeconds)}</strong></div><div><span>{running?"Estimativa restante":"Encerrado às"}</span><strong>{running?stale||error?"Sem atualização":duration(job.etaSeconds):time(job.finishedAt??job.updatedAt)}</strong></div></div>
      {job.detail&&<p className="muted render-detail">{job.detail}</p>}
      {stale&&<p className="monitor-warning" role="status">Sem atualização há mais de três minutos. Verifique a execução antes de tentar novamente.</p>}
      <div className="monitor-deliverables"><div><HardDrive size={20}/><span><strong>Vídeo + título + descrição</strong><small>{delivered?"Entrega confirmada":done?"Confirmação pendente":"Aguardando entrega"}</small></span>{delivered&&drive&&<a href={drive} target="_blank" rel="noreferrer">Abrir pasta <ExternalLink size={14}/></a>}</div><div><Image size={20}/><span><strong>Capa final</strong><small>Etapa conduzida no ChatGPT</small></span><span className="status-chip">No chat</span></div></div>
    </>}
    <div className="monitor-next"><span>Próximo passo</span><p>{next}</p></div>
    <div className="monitor-footer"><a href={github} target="_blank" rel="noreferrer">Ver no GitHub <ExternalLink size={14}/></a><span>{running?"Atualiza enquanto esta página estiver visível.":"Atualização manual; esta página não processa vídeos."}</span></div>
  </section>;
}
