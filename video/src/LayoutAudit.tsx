import {useEffect, useState} from "react";
import {AbsoluteFill, Composition, continueRender, delayRender, registerRoot} from "remotion";
import {editorialStageSchema, type StageEvent} from "../../src/lib/editorial-stage";
import {layoutStage, LAYOUT_VERSION, transformedRect, contains, type Box} from "../../src/lib/editorial-layout";
import {EDITORIAL_FONT, TYPOGRAPHY_VERSION} from "../../src/lib/editorial-typography";
import {EditorialStage} from "./EditorialStage";
import {useEditorialFont, measureEditorialText} from "./editorial-font";

type AuditProps={scene:any;fps:number;mode:string};
const Audit=({scene,fps=30,mode="pre-voice"}:AuditProps)=> {
  const ready=useEditorialFont();
  const [handle]=useState(()=>delayRender("Auditing editorial layout"));
  const stage=editorialStageSchema.parse(scene.visual.stage);
  const duration=scene.duration_frames??Math.max(180,(scene.visual.beats?.length??1)*120+90);
  const beats:StageEvent[]=(scene.visual.beats??[]).map((b:any,i:number)=>({...b,resolved_frame:b.resolved_frame??i*120+30}));
  const frames=new Set([0,1,30,duration-1]);
  for(let f=0;f<=Math.min(duration-1,Math.ceil(fps*.45)+2);f++)frames.add(f);
  for(const b of beats) {
    const start=b.resolved_frame!;
    const length=Math.ceil(Math.max(b.motion_seconds??.45,b.camera?.motion_seconds??.9)*fps)+2;
    for(let f=Math.max(0,start-1);f<=Math.min(duration-1,start+length);f++)frames.add(f);
  }
  const issues:any[]=[];
  const seen=new Set<string>();
  if(ready)for(const frame of [...frames].sort((a,b)=>a-b)) {
    const result=layoutStage(stage,beats,frame,fps,1920,1080,measureEditorialText,scene.title);
    for(const issue of result.issues) {
      const key=JSON.stringify(issue);
      if(!seen.has(key)){seen.add(key);issues.push({...issue,frame});}
    }
  }
  if(mode==="final-timing"&&(scene.visual.beats??[]).some((b:any)=>!Number.isFinite(b.resolved_frame)))issues.push({code:"missing-final-timing",message:"O passe final exige resolved_frame real em todos os beats; não usa tempos sintéticos."});
  const representative=ready?layoutStage(stage,beats,duration-1,fps,1920,1080,measureEditorialText,scene.title):null;
  useEffect(()=> {
    if(!ready||!representative)return;
    const frameHandle=requestAnimationFrame(()=>requestAnimationFrame(()=>{
    const dom=[...document.querySelectorAll<HTMLElement>("[data-element-id]")].map(el=> {
      const actual=el.getBoundingClientRect();
      const element=representative.elements.find(e=>e.id===el.dataset.elementId)!;
      const local=transformedRect(element,duration-1,representative.canvas);
      const c=representative.camera,canvas=representative.canvas;
      const predicted={x:canvas.x+canvas.width/2+(local.x-c.x*canvas.width/100)*c.zoom,y:canvas.y+canvas.height/2+(local.y-c.y*canvas.height/100)*c.zoom,w:local.w*c.zoom,h:local.h*c.zoom};
      const delta=Math.max(Math.abs(actual.x-predicted.x),Math.abs(actual.y-predicted.y),Math.abs(actual.width-predicted.w),Math.abs(actual.height-predicted.h));
      if(delta>1.1)issues.push({code:"dom-layout-mismatch",element:element.id,frame:duration-1,message:`DOM difere ${delta.toFixed(2)} px da geometria compartilhada.`});
      return {id:element.id,maximum_delta_px:+delta.toFixed(3)};
    });
    const projected=(local:Box)=>{const c=representative.camera,canvas=representative.canvas;return {x:canvas.x+canvas.width/2+(local.x-c.x*canvas.width/100)*c.zoom,y:canvas.y+canvas.height/2+(local.y-c.y*canvas.height/100)*c.zoom,w:local.w*c.zoom,h:local.h*c.zoom};};
    const domConnections=[...document.querySelectorAll<SVGForeignObjectElement>("[data-connection-id]")].map(el=> {
      const edge=representative.connections.find(c=>c.id===el.dataset.connectionId)!;
      const predicted=projected(edge.label!.box),actual=el.getBoundingClientRect();
      const delta=Math.max(Math.abs(actual.x-predicted.x),Math.abs(actual.y-predicted.y),Math.abs(actual.width-predicted.w),Math.abs(actual.height-predicted.h));
      if(delta>1.1)issues.push({code:"dom-legend-mismatch",connection:edge.id,message:`Legenda no DOM difere ${delta.toFixed(2)} px da geometria compartilhada.`});
      return {id:edge.id,maximum_delta_px:+delta.toFixed(3)};
    });
    const domPhotoCaptions=[...document.querySelectorAll<HTMLElement>("[data-photo-caption-id]")].map(el=> {
      const caption=representative.photo_captions.find(c=>c.id===el.dataset.photoCaptionId)!;
      const predicted=caption.box,actual=el.getBoundingClientRect();
      const delta=Math.max(Math.abs(actual.x-predicted.x),Math.abs(actual.y-predicted.y),Math.abs(actual.width-predicted.w),Math.abs(actual.height-predicted.h));
      if(delta>1.1)issues.push({code:"dom-photo-caption-mismatch",element:caption.id,message:`Legenda de foto no DOM difere ${delta.toFixed(2)} px da geometria compartilhada.`});
      return {id:caption.id,maximum_delta_px:+delta.toFixed(3)};
    });
    const typography=[...document.querySelectorAll<HTMLElement>("[data-text-minimum]")].map(el=> {
      const size=parseFloat(getComputedStyle(el).fontSize),minimum=Number(el.dataset.textMinimum),actual=el.getBoundingClientRect();
      const owner=el.closest<HTMLElement>("[data-element-id]"),ownerBox=owner?.getBoundingClientRect();
      if(size<minimum-.1||el.scrollWidth>el.clientWidth+1||Boolean(ownerBox&&!contains({x:ownerBox!.x,y:ownerBox!.y,w:ownerBox!.width,h:ownerBox!.height},{x:actual.x,y:actual.y,w:actual.width,h:actual.height},1.1)))issues.push({code:"dom-text-capacity",element:owner?.dataset.elementId,message:`Texto real “${el.textContent}” ultrapassa sua região ou viola a fonte mínima.`});
      return {element:owner?.dataset.elementId??null,text:el.textContent,size,minimum};
    });
    if(!issues.length&&dom.length!==representative.elements.filter(e=>e.visible).length)issues.push({code:"missing-dom-elements",frame:duration-1,message:"A verificação não encontrou todos os elementos visíveis do renderer."});
    const expectedEdges=representative.connections.filter(c=>c.label&&representative.elements.find(e=>e.id===c.from)?.visible&&representative.elements.find(e=>e.id===c.to)?.visible).length;
    if(!issues.length&&domConnections.length!==expectedEdges)issues.push({code:"missing-dom-legends",message:"A verificação não encontrou todas as legendas visíveis do renderer."});
    if(!issues.length&&domPhotoCaptions.length!==representative.photo_captions.length)issues.push({code:"missing-dom-photo-captions",message:"A verificação não encontrou todas as legendas de fotos."});
    console.info("ODE_LAYOUT_REPORT:"+JSON.stringify({version:LAYOUT_VERSION,typography_version:TYPOGRAPHY_VERSION,font:EDITORIAL_FONT,font_loaded:document.fonts.check(`700 32px "${EDITORIAL_FONT}"`),resolution:{width:1920,height:1080},mode,scene_id:scene.id??scene.scene_index,checked_frames:frames.size,issues,dom,dom_connections:domConnections,dom_photo_captions:domPhotoCaptions,typography}));
    continueRender(handle);
    }));
    return ()=>cancelAnimationFrame(frameHandle);
  },[ready]);
  if(!ready)return null;
  if(issues.length)return <AbsoluteFill style={{background:"#101317",color:"#ffbd19",padding:80,fontFamily:EDITORIAL_FONT,fontSize:32}}><h1>Composição precisa de ajuste</h1>{issues.slice(0,8).map((i,index)=><p key={index}>{i.element??i.connection}: {i.message}</p>)}</AbsoluteFill>;
  // The renderer uses the same geometry; this frame also checks real DOM boxes.
  return <EditorialStage stage={stage} beats={beats} title={scene.title} frameOverride={duration-1}/>;
};
registerRoot(()=> <Composition id="LayoutAudit" component={Audit} durationInFrames={1} fps={30} width={1920} height={1080} defaultProps={{scene:{visual:{stage:{show_title:false,elements:[{id:"placeholder",kind:"label",label:"Layout",x:20,y:20,width:60,height:30}],connections:[]}}},fps:30,mode:"pre-voice"}}/>);
