import type {OperationLayout} from "../../src/lib/editorial-layout";
import {EDITORIAL_FONT} from "../../src/lib/editorial-typography";
import {kineticWordProgress} from "../../src/lib/editorial-stage";

const GOLD="#ffbd19";
export const EditorialOperation=({operation,frame,fps}:{operation:OperationLayout;frame:number;fps:number})=> {
  const progress=operation.motionProfile==="static"?1:Math.max(0,Math.min(1,(frame-operation.frame)/Math.max(1,operation.duration??fps*.5)));
  const eased=progress*progress*(3-2*progress);
  const color=operation.status==="warning"?"#ffbd19":operation.status==="positive"?"#91d7af":"#a6b6c3";
  return <div style={{position:"absolute",inset:0,zIndex:2,opacity:operation.opacity??1,pointerEvents:"none"}}>
    {(operation.kind==="compare"||operation.kind==="stack")&&<svg style={{position:"absolute",inset:0,width:"100%",height:"100%",overflow:"visible",pointerEvents:"none",zIndex:2}}>
      {operation.kind==="compare"&&operation.boxes.map((b,i)=>{
        // Equal treatment of the compared participants; no invented winner.
        const inset=4+(1-eased)*Math.min(b.w,b.h)*.055;
        return <rect key={i} data-operation-id={`compare-${i}`} x={b.x+inset} y={b.y+inset} width={Math.max(0,b.w-inset*2)} height={Math.max(0,b.h-inset*2)} rx={12} fill="none" stroke={GOLD} strokeWidth={3} pathLength={1} strokeDasharray={1} strokeDashoffset={1-eased} opacity={eased}/>;
      })}
      {operation.kind==="stack"&&operation.points&&<>
        <path d={`M${operation.points[0].x},${operation.points[0].y} L${operation.points[1].x},${operation.points[1].y}`} stroke={GOLD} strokeWidth={3} fill="none" pathLength={1} strokeDasharray={1} strokeDashoffset={1-progress}/>
        {operation.boxes.map((b,i)=><path key={i} d={`M${operation.points![0].x},${b.y+b.h/2} H${b.x}`} stroke={GOLD} strokeWidth={3} opacity={progress}/>)}
      </>}
    </svg>}
    {operation.kind==="meter"&&operation.meter&&operation.boxes[0]&&(()=>{
      const b=operation.boxes[0],m=operation.meter;
      const number=(v:number)=>v.toLocaleString("pt-BR");
      return <div data-operation-id="meter" style={{position:"absolute",left:b.x,top:b.y,width:b.w,height:b.h,boxSizing:"border-box",padding:12,fontFamily:EDITORIAL_FONT,fontWeight:700,color:"#f6f7f8",opacity:progress,zIndex:2}}>
        <div style={{fontSize:30,lineHeight:1.18}}>{number(m.value)} {m.unit}</div>
        <div style={{height:12,background:"#394751",borderRadius:6,margin:"10px 0",overflow:"hidden"}}><div style={{height:"100%",width:`${m.fraction*progress*100}%`,background:GOLD}}/></div>
        <div style={{display:"flex",justifyContent:"space-between",fontSize:28,lineHeight:1.18,color:"#a6b6c3"}}><span>{number(m.min)}</span><span>{number(m.max)}</span></div>
      </div>;
    })()}
    {operation.kind==="signal"&&operation.boxes[0]&&<div style={{position:"absolute",left:operation.boxes[0].x,top:operation.boxes[0].y,width:operation.boxes[0].w,height:operation.boxes[0].h,boxSizing:"border-box",borderLeft:`5px solid ${color}`,background:"rgba(13,19,24,.95)",borderRadius:8,opacity:progress}}/>}
    {operation.glyphs.map((g,index)=>{
      const p=operation.kind==="equation"?kineticWordProgress(progress,index,operation.glyphs.length):eased;
      return <div key={g.id} data-operation-id={g.id} data-text-minimum={operation.kind==="equation"?48:30} data-text-size={g.layout.size} style={{position:"absolute",left:g.box.x,top:g.box.y,width:g.box.w,height:g.box.h,fontFamily:EDITORIAL_FONT,fontSize:g.layout.size,lineHeight:1.18,fontWeight:700,whiteSpace:"pre",textAlign:operation.kind==="equation"?"center":"left",color:operation.kind==="signal"?color:GOLD,opacity:p,zIndex:2,display:"flex",flexDirection:"column",justifyContent:"center",transform:operation.kind==="equation"?`scale(${.72+.28*p})`:undefined,transformOrigin:"center"}}>{g.layout.lines.map((line,i)=><div key={i}>{line}</div>)}</div>;
    })}
  </div>;
};
