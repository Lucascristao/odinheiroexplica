import {resolveStage, resolveStageCamera, type EditorialStage, type StageEvent} from "./editorial-stage";
import {composeText, textMinimums, type MeasureWidth, type TextLayout, type TextRole} from "./editorial-typography";
import {chartLayout} from "./editorial-chart-layout";

export const LAYOUT_VERSION = "2026-10-01.2";
export type Box = {x: number; y: number; w: number; h: number};
export type Point = {x: number; y: number};
export type LayoutIssue = {code: string; element?: string; connection?: string; role?: string; message: string};
export type ResolvedElement = ReturnType<typeof resolveStage>["elements"][number];
export const intersects = (a: Box, b: Box, gap=0) => a.x < b.x+b.w+gap && a.x+a.w+gap > b.x && a.y < b.y+b.h+gap && a.y+a.h+gap > b.y;
export const contains = (outer: Box, inner: Box, tolerance=.1) => inner.x >= outer.x-tolerance && inner.y >= outer.y-tolerance && inner.x+inner.w <= outer.x+outer.w+tolerance && inner.y+inner.h <= outer.y+outer.h+tolerance;
export const union = (boxes: Box[]): Box => {
  const x=Math.min(...boxes.map(b=>b.x)), y=Math.min(...boxes.map(b=>b.y));
  return {x,y,w:Math.max(...boxes.map(b=>b.x+b.w))-x,h:Math.max(...boxes.map(b=>b.y+b.h))-y};
};
export function editorialCanvas(width: number, height: number, showTitle: boolean) {
  return {x:130,y:showTitle?230:130,width:width-260,height:height-(showTitle?360:230)};
}
export function elementRect(e: {x:number;y:number;width:number;height:number}, canvas: {width:number;height:number}): Box {
  return {x:e.x*canvas.width/100,y:e.y*canvas.height/100,w:e.width*canvas.width/100,h:e.height*canvas.height/100};
}
export function entranceMotion(e: ResolvedElement, frame: number) {
  const reveal=Math.max(0,Math.min(1,(frame-e.changedAt)/Math.max(1,e.visibilityDuration)));
  const pose=entrancePose(e,e.visible?reveal:1-reveal);
  return {reveal:e.motionProfile==="static"?1:reveal,...pose};
}
export function entrancePose(e:Pick<ResolvedElement,"kind"|"width"|"overlay_on"|"x"|"entrance"|"motionProfile">, progress:number) {
  if(e.motionProfile==="static")return {scale:1,x:0,y:0,clip:undefined as string|undefined};
  if(e.entrance) {
    const p=progress*progress*(3-2*progress),remaining=1-p;
    const direction=e.entrance.direction??"up";
    if(e.entrance.style==="fade")return {scale:1,x:0,y:0,clip:undefined};
    if(e.entrance.style==="scale")return {scale:.82+.18*p,x:0,y:0,clip:undefined};
    if(e.entrance.style==="wipe") {
      const percent=remaining*100;
      const clip=direction==="left"?`inset(0 ${percent}% 0 0)`:direction==="right"?`inset(0 0 0 ${percent}%)`:direction==="down"?`inset(0 0 ${percent}% 0)`:`inset(${percent}% 0 0 0)`;
      return {scale:1,x:0,y:0,clip};
    }
    return {scale:.96+.04*p,x:direction==="left"?-48*remaining:direction==="right"?48*remaining:0,y:direction==="up"?-32*remaining:direction==="down"?32*remaining:0,clip:undefined};
  }
  const hero=e.kind==="metric"&&e.width>=40&&!e.overlay_on;
  return {scale:hero?.82+.18*progress:.96+.04*progress,x:e.kind==="step"&&!e.overlay_on?(1-progress)*(e.x>50?42:-42):0,y:(1-progress)*(hero?8:28),clip:undefined};
}
export function transformedRect(e: ResolvedElement, frame: number, canvas: {width:number;height:number}): Box {
  const b=elementRect(e,canvas), m=entranceMotion(e,frame);
  return {x:b.x+b.w*(1-m.scale)/2+m.x,y:b.y+b.h*(1-m.scale)/2+m.y,w:b.w*m.scale,h:b.h*m.scale};
}
export function nodeContent(e: ResolvedElement, box: Box, routeNode: boolean) {
  const wide=e.kind!=="source_excerpt"&&e.width>=50&&e.height<=26;
  const stacked=e.kind==="step"&&!wide;
  const hero=e.kind==="metric"&&e.width>=40&&!e.overlay_on;
  const card=e.kind==="note"||(e.kind==="metric"&&!hero);
  const padding=e.kind==="source_excerpt"?0:card&&!routeNode?24:16;
  const iconSize=e.icon?(wide?48:Math.min(130,Math.max(68,box.h*.38))):0;
  const iconSpace=e.icon?iconSize+12+20:0;
  const innerW=Math.max(1,box.w-padding*2-(stacked?0:iconSpace));
  const innerH=Math.max(1,box.h-padding*2-(stacked?iconSpace:0));
  const valueH=e.value?innerH*(wide?.45:e.value_size>100?.65:.42):0;
  const detailH=e.detail?innerH*(e.value?(e.value_size>100?.14:.28):.4):0;
  const labelH=Math.max(1,innerH-valueH-detailH-(e.value?4:0)-(e.detail?6:0));
  return {wide,stacked,hero,card,padding,iconSize,iconSpace,innerW,innerH,valueH,detailH,labelH};
}
export function nodeTexts(e: ResolvedElement, box: Box, routeNode: boolean, measure: MeasureWidth) {
  const c=nodeContent(e,box,routeNode);
  const out: {role:TextRole;text:string;layout:TextLayout}[]=[];
  const add=(role:TextRole,text:string,w:number,h:number,max:number)=>out.push({role,text,layout:composeText(text,w,h,max,textMinimums[role],measure)});
  if(e.kind==="object") {
    add("label",e.label,box.w-32,90,e.label_size??42);
    if(e.detail||e.value) out.push({role:"detail",text:e.detail??e.value!,layout:{lines:[],size:28,width:0,height:0,fits:false,requiredWidth:1,requiredHeight:1}});
  } else if(e.kind==="photo") add("caption",e.label,box.w-44,64,27);
  else if(!["source_excerpt","chart"].includes(e.kind)) {
    if(e.value) add("value",e.value,c.innerW,c.valueH,c.hero||e.treatment==="giant_number"?Math.max(108,e.value_size):e.value_size);
    add("label",e.label,c.innerW,c.labelH,e.label_size??(c.hero?58:e.kind==="step"?38:46));
    if(e.detail) add("detail",e.detail,c.innerW,c.detailH,30);
  }
  return out;
}
export type PhotoCaptionLayout={id:string;box:Box;text:string;layout:TextLayout};
export function photoCaptionLayout(e:ResolvedElement,frame:number,canvas:{x:number;y:number;width:number;height:number},camera:{x:number;y:number;zoom:number},measure:MeasureWidth):PhotoCaptionLayout {
  const local=transformedRect(e,frame,canvas);
  const x=canvas.x+canvas.width/2+(local.x-camera.x*canvas.width/100)*camera.zoom;
  const y=canvas.y+canvas.height/2+(local.y-camera.y*canvas.height/100)*camera.zoom;
  const left=Math.max(canvas.x,x),right=Math.min(canvas.x+canvas.width,x+local.w*camera.zoom);
  const top=Math.max(canvas.y,y),bottom=Math.min(canvas.y+canvas.height,y+local.h*camera.zoom);
  const box={x:left+10,y:bottom-94,w:Math.max(0,right-left-20),h:84};
  const layout=composeText(e.label,Math.max(0,box.w-24),64,27,textMinimums.caption,measure);
  if(right-left<180||bottom-top<95)layout.fits=false;
  return {id:e.id,box,text:e.label,layout};
}
export type ConnectionLayout = {id:string;from:string;to:string;points:Point[];path:string;label?:{box:Box;text:string;layout:TextLayout};bounds:Box;error?:string};
export function pointOnRoute(points: Point[], progress: number): Point {
  const lengths=points.slice(1).map((p,i)=>Math.hypot(p.x-points[i].x,p.y-points[i].y));
  let distance=lengths.reduce((a,b)=>a+b,0)*Math.max(0,Math.min(1,progress));
  for(let i=0;i<lengths.length;i++) {
    if(distance<=lengths[i]||i===lengths.length-1) {const p=lengths[i]?distance/lengths[i]:0;return {x:points[i].x+(points[i+1].x-points[i].x)*p,y:points[i].y+(points[i+1].y-points[i].y)*p};}
    distance-=lengths[i];
  }
  return points[0];
}
export function segmentHits(a:Point,b:Point,box:Box,gap=0) {
  // Open rectangle intersection (Liang–Barsky): touching a port is allowed,
  // entering the rectangle is not. This also supports diagonal authored paths.
  const inset=.001, bounds={x:box.x-gap+inset,y:box.y-gap+inset,w:box.w+2*gap-2*inset,h:box.h+2*gap-2*inset};
  let lower=0,upper=1;
  for(const [start,delta,min,max] of [[a.x,b.x-a.x,bounds.x,bounds.x+bounds.w],[a.y,b.y-a.y,bounds.y,bounds.y+bounds.h]]) {
    if(Math.abs(delta)<1e-9){if(start<min||start>max)return false;continue;}
    const u=(min-start)/delta,v=(max-start)/delta;
    lower=Math.max(lower,Math.min(u,v));upper=Math.min(upper,Math.max(u,v));
    if(lower>upper)return false;
  }
  return upper>0&&lower<1;
}

export function reservedElementBounds(stage:EditorialStage,beats:StageEvent[],canvas:{width:number;height:number}) {
  return stage.elements.map(e=> {
    const poses=[e,...beats.flatMap(b=>(b.moves??[]).filter(m=>m.id===e.id).map(m=>({...e,x:m.x,y:m.y})))];
    const boxes=poses.flatMap(p=> {
      const b=elementRect(p,canvas);
      const entrances=[undefined,...beats.filter(cue=>cue.target_id===e.id||cue.reveal_ids?.includes(e.id)||cue.retire_ids?.includes(e.id)).map(cue=>cue.entrance)];
      return [b,...entrances.map(entrance=>{
        const m=entrancePose({...p,entrance,motionProfile:stage.motion_profile},0);
        return {x:b.x+b.w*(1-m.scale)/2+m.x,y:b.y+b.h*(1-m.scale)/2+m.y,w:b.w*m.scale,h:b.h*m.scale};
      })];
    });
    return {id:e.id,box:union(boxes)};
  });
}
type Port = "left"|"right"|"top"|"bottom";
const portPoint=(b:Box,port:Port):Point=>port==="left"?{x:b.x,y:b.y+b.h/2}:port==="right"?{x:b.x+b.w,y:b.y+b.h/2}:port==="top"?{x:b.x+b.w/2,y:b.y}:{x:b.x+b.w/2,y:b.y+b.h};
const escapePoint=(p:Point,b:Box,port:Port):Point=>port==="left"?{x:b.x-22,y:p.y}:port==="right"?{x:b.x+b.w+22,y:p.y}:port==="top"?{x:p.x,y:b.y-22}:{x:p.x,y:b.y+b.h+22};
const compactPoints=(points:Point[])=>points.filter((p,i)=>i===0||Math.hypot(p.x-points[i-1].x,p.y-points[i-1].y)>.001);

// Reserve all authored positions. Label choices remain deterministic across frames,
// including parallel render workers, instead of jumping sides during a movement.
export function solveConnections(stage:EditorialStage, beats:StageEvent[], elements:ResolvedElement[], frame:number, canvas:{width:number;height:number}, measure:MeasureWidth): ConnectionLayout[] {
  const bounds={x:8,y:8,w:canvas.width-16,h:canvas.height-16};
  const reserved=reservedElementBounds(stage,beats,canvas);
  const occupied:Box[]=[];
  return stage.connections.map((edge,index)=> {
    const id=edge.id??`connection-${index}`;
    const from=elements.find(e=>e.id===edge.from)!,to=elements.find(e=>e.id===edge.to)!;
    const a=transformedRect(from,frame,canvas), b=transformedRect(to,frame,canvas);
    const ra=reserved.find(r=>r.id===edge.from)!.box,rb=reserved.find(r=>r.id===edge.to)!.box;
    const horizontal=Math.abs((rb.x+rb.w/2)-(ra.x+ra.w/2))>=Math.abs((rb.y+rb.h/2)-(ra.y+ra.h/2));
    const forward=horizontal?rb.x>ra.x:rb.y>ra.y;
    const fromPort:Port=edge.from_port&&edge.from_port!=="auto"?edge.from_port:horizontal?(forward?"right":"left"):(forward?"bottom":"top");
    const toPort:Port=edge.to_port&&edge.to_port!=="auto"?edge.to_port:horizontal?(forward?"left":"right"):(forward?"top":"bottom");
    const start=portPoint(a,fromPort),end=portPoint(b,toPort);
    const startEscape=escapePoint(start,ra,fromPort),endEscape=escapePoint(end,rb,toPort);
    const cx=(ra.x+ra.w/2+rb.x+rb.w/2)/2,cy=(ra.y+ra.h/2+rb.y+rb.h/2)/2;
    const group=union([ra,rb]);
    const options:{points:Point[];label?:ConnectionLayout["label"];cost:number}[]=[];
    const gap=horizontal?Math.max(0,Math.max(ra.x,rb.x)-Math.min(ra.x+ra.w,rb.x+rb.w)):Math.max(0,Math.max(ra.y,rb.y)-Math.min(ra.y+ra.h,rb.y+rb.h));
    const widths=[Math.min(430,canvas.width-40),Math.min(300,canvas.width-40),Math.max(1,gap-28)];
    for(const w of edge.label?widths:[1]) {
      const text=edge.label?composeText(edge.label,w,120,edge.label_size??32,30,measure):undefined;
      if(text&&!text.fits)continue;
      const lw=text?Math.min(w,text.requiredWidth+20):0,lh=text?text.requiredHeight+16:0;
      const placements=horizontal?[{x:cx-lw/2,y:group.y-lh-40,side:"above"},{x:cx-lw/2,y:group.y+group.h+40,side:"below"},{x:cx-lw/2,y:cy-lh-14,side:"between"}]:[{x:group.x-lw-40,y:cy-lh/2,side:"left"},{x:group.x+group.w+40,y:cy-lh/2,side:"right"},{x:cx-lw-14,y:cy-lh/2,side:"between"}];
      const obstacles=union(reserved.map(r=>r.box));
      if(horizontal)placements.push({x:cx-lw/2,y:obstacles.y-lh-40,side:"above"},{x:cx-lw/2,y:obstacles.y+obstacles.h+40,side:"below"});
      else placements.push({x:obstacles.x-lw-40,y:cy-lh/2,side:"left"},{x:obstacles.x+obstacles.w+40,y:cy-lh/2,side:"right"});
      if(edge.label_region){const r=edge.label_region;placements.unshift({x:r.x*canvas.width/100,y:r.y*canvas.height/100,side:"authored"});}
      if(edge.label_position&&edge.label_position!=="auto") placements.sort((u,v)=>Number(v.side===edge.label_position)-Number(u.side===edge.label_position));
      for(const pos of placements) {
        const labelBox={x:Math.max(bounds.x,Math.min(bounds.x+bounds.w-lw,pos.x)),y:pos.y,w:lw,h:lh};
        if(edge.label_region&&pos.side==="authored"&&!contains(elementRect(edge.label_region,canvas),labelBox))continue;
        if(text&&(!contains(bounds,labelBox)||reserved.some(r=>intersects(labelBox,r.box,14))||occupied.some(r=>intersects(labelBox,r,12))))continue;
        let points:Point[];
        if(horizontal) {
          const lane=pos.side==="below"?pos.y-18:pos.side==="between"?cy:pos.y+lh+18;
          points=compactPoints([start,startEscape,{x:startEscape.x,y:lane},{x:endEscape.x,y:lane},endEscape,end]);
        } else {
          const lane=pos.side==="right"?pos.x-18:pos.side==="between"?cx:pos.x+lw+18;
          points=compactPoints([start,startEscape,{x:lane,y:startEscape.y},{x:lane,y:endEscape.y},endEscape,end]);
        }
        if(points.some(p=>!contains(bounds,{...p,w:0,h:0})))continue;
        if(points.slice(1).some((p,i)=>reserved.some(r=> {
          if(i===0&&r.id===edge.from||i===points.length-2&&r.id===edge.to)return false;
          return segmentHits(points[i],p,r.box,10);
        })||occupied.some(r=>segmentHits(points[i],p,r,10))||Boolean(text&&segmentHits(points[i],p,labelBox,8))))continue;
        // Cost uses authored envelopes; its ranking never depends on render order
        // or on small changes to the currently animated endpoint.
        const length=Math.abs(ra.x-rb.x)+Math.abs(ra.y-rb.y)+(pos.side==="between"?0:horizontal?Math.abs(pos.y-cy)*2:Math.abs(pos.x-cx)*2);
        const preference=edge.label_position&&edge.label_position!=="auto"&&pos.side!==edge.label_position?500:0;
        options.push({points,label:text?{box:labelBox,text:edge.label!,layout:{...text,width:lw-20,height:lh-16}}:undefined,cost:length+preference+(text?text.lines.length*5:0)});
      }
    }
    options.sort((u,v)=>u.cost-v.cost);
    const selected=options[0];
    if(!selected)return {id,from:edge.from,to:edge.to,points:[start,end],path:`M${start.x},${start.y} L${end.x},${end.y}`,bounds:union([a,b]),error:`Não existe região segura para a conexão${edge.label?` e legenda “${edge.label}”`:""}; amplie o espaço ou ajuste a composição.`};
    if(selected.label)occupied.push(selected.label.box);
    const raw=union(selected.points.map(p=>({...p,w:0,h:0})));
    const padding=edge.semantic==="transfer"?22:12;
    const routeBounds={x:raw.x-padding,y:raw.y-padding,w:raw.w+padding*2,h:raw.h+padding*2};
    return {id,from:edge.from,to:edge.to,points:selected.points,path:selected.points.map((p,i)=>`${i?"L":"M"}${p.x},${p.y}`).join(" "),label:selected.label,bounds:selected.label?union([routeBounds,selected.label.box]):routeBounds};
  });
}

export type OperationLayout = {
  kind:"equation"|"compare"|"stack"|"meter"|"signal";
  ids:string[]; frame:number;
  duration:number; motionProfile?:"narrative"|"static";
  opacity?:number;
  glyphs:{id:string;box:Box;text:string;layout:TextLayout}[];
  boxes:Box[]; points?:Point[];
  meter?:{value:number;min:number;max:number;unit:string;fraction:number};
  status?:"positive"|"neutral"|"warning";
};
export const visualCapabilities = {
  equation:{requires:"operation.kind=equation + input_ids/operator/result_id",effect:"Operadores entram em sequência no intervalo autoral; valores exatos e resultado só no reveal declarado."},
  split_compare:{requires:"operation.kind=compare + element_ids",effect:"Contornos traçados e expandidos dentro das regiões declaradas, com destaque igual e sem inferir vencedor."},
  stack:{requires:"operation.kind=stack + element_ids em ordem vertical",effect:"Espinha e ligações de uma lista declarada."},
  meter:{requires:"operation.kind=meter + value/min/max",effect:"Barra proporcional à escala explícita, com valor e limites."},
  signal:{requires:"operation.kind=signal + status/message",effect:"Condição textual e sinal cromático explícitos."},
  flow_diagram:{requires:"stage.connections",effect:"Traçado e percurso nas relações declaradas."},
  giant_number:{requires:"target.value",effect:"Valor ampliado dentro de sua área reservada."},
  kinetic_type:{requires:"reveal/update + target.label",effect:"Palavras entram em sequência nas linhas medidas, com deslocamento e pausa após a cue; nunca altera números."},
  masked_emphasis:{requires:"target.label / emphasis",effect:"Varredura do grifo pela frase existente, no intervalo declarado e sem trocar a composição."},
  depth_photo:{requires:"photo.image_motion",effect:"Movimento limitado da imagem dentro de sua região."},
  spotlight:{requires:"target_id",effect:"Destaque do participante ou prova alvo."},
  timeline:{requires:"datas declaradas + stage/moves/connections",effect:"Revelação e foco dos marcos autorais; não inventa cronologia."},
} as const;

function operationLayout(stage:EditorialStage,beats:StageEvent[],elements:ResolvedElement[],frame:number,fps:number,canvas:{width:number;height:number},connections:ConnectionLayout[],measure:MeasureWidth,issues:LayoutIssue[]):OperationLayout|undefined {
  const cue=beats.filter(b=>b.operation&&Number.isFinite(b.resolved_frame)&&b.resolved_frame!<=frame).sort((a,b)=>a.resolved_frame!-b.resolved_frame!).at(-1);
  if(!cue?.operation)return;
  const op=cue.operation;
  const ids=op.kind==="equation"?[...op.input_ids,op.result_id]:op.kind==="compare"||op.kind==="stack"?op.element_ids:[cue.target_id??""];
  const targets=ids.map(id=>elements.find(e=>e.id===id));
  const nextCue=beats.filter(b=>Number.isFinite(b.resolved_frame)&&b.resolved_frame!>cue.resolved_frame!).sort((a,b)=>a.resolved_frame!-b.resolved_frame!)[0];
  const result:OperationLayout={kind:op.kind,ids,frame:cue.resolved_frame!,duration:Math.max(1,Math.min((cue.motion_seconds??.5)*fps, nextCue?nextCue.resolved_frame!-cue.resolved_frame!:Infinity)),motionProfile:stage.motion_profile,glyphs:[],boxes:[]};
  if(new Set(ids).size!==ids.length||targets.some(e=>!e)){issues.push({code:"operation-reference",message:`Operação ${op.kind} precisa de IDs existentes e distintos.`});return result;}
  // Previously revealed participants may retire gradually. Keep their operation
  // attached during the fade, then release its camera space when it is gone.
  const presented=targets.filter(e=>e!.visible||e!.wasVisible);
  result.opacity=Math.min(1,...presented.map(e=>{const p=entranceMotion(e!,frame).reveal;return e!.visible?p:1-p;}));
  if(result.opacity<=0)return;
  const reserved=reservedElementBounds(stage,beats,canvas);
  const outer={x:8,y:8,w:canvas.width-16,h:canvas.height-16};
  const rects=targets.map(e=>transformedRect(e!,frame,canvas));
  if(op.kind==="equation") {
    targets.forEach(e=>{if(!e!.value)issues.push({code:"equation-value",element:e!.id,message:"Operando/resultado precisa de value declarado; o motor não calcula nem inventa valores."});});
    for(let i=0;i<rects.length-1;i++) {
      const a=rects[i],b=rects[i+1],horizontal=Math.abs(b.x-a.x)>=Math.abs(b.y-a.y);
      const text=i===rects.length-2?"=":op.operator;
      const box=horizontal?{x:(Math.min(a.x+a.w,b.x+b.w)+Math.max(a.x,b.x))/2-32,y:(a.y+a.h/2+b.y+b.h/2)/2-34,w:64,h:68}:{x:(a.x+a.w/2+b.x+b.w/2)/2-32,y:(Math.min(a.y+a.h,b.y+b.h)+Math.max(a.y,b.y))/2-34,w:64,h:68};
      const layout=composeText(text,64,68,48,48,measure);
      if(!contains(outer,box)||reserved.some(r=>intersects(box,r.box,10))||connections.some(c=>c.label&&intersects(box,c.label.box,10)))issues.push({code:"equation-space",message:`Reserve um corredor para “${text}” entre ${ids[i]} e ${ids[i+1]}.`});
      result.glyphs.push({id:`equation-${i}`,box,text,layout});result.boxes.push(box);
    }
  } else if(op.kind==="compare") result.boxes=rects;
  else if(op.kind==="stack") {
    const x=Math.min(...rects.map(r=>r.x))-18;
    const centers=rects.map(r=>({x:r.x,y:r.y+r.h/2}));
    if(centers.some((p,i)=>i>0&&p.y<=centers[i-1].y))issues.push({code:"stack-order",message:"A pilha precisa preservar a ordem vertical dos IDs declarados; forneça moves/posições apropriados."});
    result.points=[{x,y:centers[0].y},{x,y:centers.at(-1)!.y}];
    const spine=union(result.points.map(p=>({...p,w:0,h:0})));
    if(!contains(outer,spine)||reserved.some(r=>segmentHits(result.points![0],result.points![1],r.box,5)))issues.push({code:"stack-space",message:"Reserve um corredor lateral para a espinha da pilha."});
    result.boxes=rects;
  } else {
    const target=reserved.find(r=>r.id===ids[0])!.box;
    const w=op.kind==="meter"?410:Math.min(520,canvas.width-32),h=op.kind==="meter"?112:96;
    const candidates=[{x:target.x+(target.w-w)/2,y:target.y+target.h+24,w,h},{x:target.x+(target.w-w)/2,y:target.y-h-24,w,h},{x:target.x+target.w+24,y:target.y,w,h},{x:target.x-w-24,y:target.y,w,h}];
    const box=candidates.find(b=>contains(outer,b)&&!reserved.some(r=>intersects(b,r.box,12))&&!connections.some(c=>c.label&&intersects(b,c.label.box,12)));
    if(!box){issues.push({code:"operation-space",element:ids[0],message:`Reserve uma região livre de ${w} × ${h} px para a operação ${op.kind}.`});return result;}
    result.boxes=[box];
    if(op.kind==="meter") {
      if(op.max<=op.min||op.value<op.min||op.value>op.max){issues.push({code:"meter-scale",element:ids[0],message:"Medidor exige min < max e value dentro da escala; não limita valores silenciosamente."});return result;}
      result.meter={value:op.value,min:op.min,max:op.max,unit:op.unit??"",fraction:(op.value-op.min)/(op.max-op.min)};
    } else {
      const layout=composeText(op.message,box.w-32,box.h-24,32,30,measure);
      if(!layout.fits)issues.push({code:"signal-capacity",element:ids[0],message:"A condição do sinal não cabe na fonte mínima."});
      result.status=op.status;result.glyphs=[{id:"signal-message",box:{x:box.x+16,y:box.y+12,w:box.w-32,h:box.h-24},text:op.message,layout}];
    }
  }
  return result;
}

export function layoutStage(stage:EditorialStage,beats:StageEvent[],frame:number,fps:number,width:number,height:number,measure:MeasureWidth,title?:string) {
  const canvas=editorialCanvas(width,height,stage.show_title);
  const state=resolveStage(stage,beats,frame,fps);
  const connections=solveConnections(stage,beats,state.elements,frame,canvas,measure);
  const routeIds=new Set(stage.connections.flatMap(e=>[e.from,e.to]));
  const issues:LayoutIssue[]=[];
  if(stage.show_title&&title&&!composeText(title,canvas.width,90,46,textMinimums.title,measure).fits)issues.push({code:"title-capacity",role:"title",message:"Título do palco não cabe na fonte mínima; amplie a área ou revise a composição."});
  for(const e of state.elements) {
    for(const t of nodeTexts(e,elementRect(e,canvas),routeIds.has(e.id),measure)) if(!t.layout.fits)issues.push({code:"text-capacity",element:e.id,role:t.role,message:`“${t.text}” exige ${Math.ceil(t.layout.requiredWidth)} × ${Math.ceil(t.layout.requiredHeight)} px na fonte mínima ${t.layout.size}; disponíveis ${Math.floor(t.layout.width)} × ${Math.floor(t.layout.height)} px.`});
    if(e.kind==="chart"&&e.chart){const b=elementRect(e,canvas);chartLayout(e.chart,b.w-32,b.h-32,e.label,measure).problems.forEach(message=>issues.push({code:"chart-capacity",element:e.id,message}));}
    if(["photo","source_excerpt"].includes(e.kind)&&!e.asset_file)issues.push({code:"missing-visual-asset",element:e.id,message:"Imagem/recorte precisa do arquivo real preparado; o motor não substitui evidência por texto inventado."});
  }
  connections.filter(c=>c.error).forEach(c=>issues.push({code:"connection-space",connection:c.id,message:c.error!}));
  const operation=operationLayout(stage,beats,state.elements,frame,fps,canvas,connections,measure,issues);
  const requested=resolveStageCamera(stage,beats,frame,fps);
  const visible=state.elements.filter(e=>{
    const p=entranceMotion(e,frame).reveal;
    return e.visible?p>.01:e.wasVisible&&p<.99;
  });
  for(const [i,e] of visible.entries()) for(const other of visible.slice(0,i)) {
    if(e.overlay_on===other.id||other.overlay_on===e.id)continue;
    if(intersects(transformedRect(e,frame,canvas),transformedRect(other,frame,canvas)))issues.push({code:"animated-node-collision",element:e.id,message:`Entrada/movimento colide com ${other.id}; reserve também o percurso.`});
  }
  const important=visible.filter(e=>e.kind!=="photo").map(e=>transformedRect(e,frame,canvas));
  connections.filter(c=>visible.some(e=>e.id===c.from)&&visible.some(e=>e.id===c.to)&&!c.error).forEach(c=>important.push(c.bounds));
  if(operation)important.push(...operation.boxes);
  let camera=requested;
  if(important.length) {
    const box=union(important);
    const left=box.x/canvas.width*100,right=(box.x+box.w)/canvas.width*100,top=box.y/canvas.height*100,bottom=(box.y+box.h)/canvas.height*100;
    const fits=(c:typeof requested)=>50+(left-c.x)*c.zoom>=-.001&&50+(right-c.x)*c.zoom<=100.001&&50+(top-c.y)*c.zoom>=-.001&&50+(bottom-c.y)*c.zoom<=100.001;
    if(!fits(requested)) {
      const zoom=Math.max(1,Math.min(requested.zoom,100/(right-left+2),100/(bottom-top+2)));
      camera={x:Math.max(right-50/zoom,Math.min(left+50/zoom,requested.x)),y:Math.max(bottom-50/zoom,Math.min(top+50/zoom,requested.y)),zoom};
    }
    if(!fits(camera))issues.push({code:"camera-capacity",message:"O grupo visível completo não cabe no enquadramento; ajuste os movimentos ou a área reservada."});
  }
  const photo_captions=visible.filter(e=>e.kind==="photo"&&e.asset_file&&!stage.elements.some(child=>child.overlay_on===e.id)).map(e=>photoCaptionLayout(e,frame,canvas,camera,measure));
  for(const caption of photo_captions)if(!caption.layout.fits)issues.push({code:"photo-caption-capacity",element:caption.id,role:"caption",message:"A legenda da foto não cabe na área visível na fonte mínima; ajuste a câmera/composição. O motor não oculta a legenda."});
  return {...state,canvas,connections,camera,operation,photo_captions,issues};
}
