import {Img,staticFile} from "remotion";
import type {StageElement} from "../../src/lib/editorial-stage";
import type {Chart,Region} from "../../src/lib/editorial-evidence";
import {chartLayout,chartNumber} from "../../src/lib/editorial-chart-layout";
import {EDITORIAL_FONT,type TextLayout} from "../../src/lib/editorial-typography";
import {measureEditorialText} from "./editorial-font";

const GOLD="#ffbd19",WHITE="#f6f7f8";
export const SourceExcerpt=({element,view,markIds,markProgress}:{element:StageElement;view:Region;markIds:string[];markProgress:Record<string,number>})=> {
  if(!element.asset_file)throw new Error(`Recorte ${element.id} não tem asset real preparado.`);
  const w=element.asset_width??1351,h=element.asset_height??917;
  return <div style={{width:"100%",height:"100%",overflow:"hidden",background:"transparent",borderRadius:8}}>
    <svg width="100%" height="100%" viewBox={`${view.x*w/100} ${view.y*h/100} ${view.width*w/100} ${view.height*h/100}`} preserveAspectRatio="xMidYMid meet" style={{display:"block"}}>
      <foreignObject x={0} y={0} width={w} height={h}><Img src={staticFile(element.asset_file)} style={{width:w,height:h,display:"block"}}/></foreignObject>
      {element.annotations.filter(a=>markIds.includes(a.id)).map(a=> {
        const p=markProgress[a.id]??1,r=a.region,x=r.x*w/100,y=r.y*h/100,rw=r.width*w/100,rh=r.height*h/100;
        if(a.style==="highlight")return <rect key={a.id} x={x} y={y} width={rw*p} height={rh} fill={GOLD} opacity={.55} style={{mixBlendMode:"multiply"}}/>;
        if(a.style==="circle")return <ellipse key={a.id} cx={x+rw/2} cy={y+rh/2} rx={rw/2} ry={rh/2} fill="none" stroke={GOLD} strokeWidth={6} pathLength={1} strokeDasharray={1} strokeDashoffset={1-p}/>;
        return <path key={a.id} d={`M${x},${y+rh*(a.style==="strike"?.5:1)} H${x+rw*p}`} stroke={GOLD} strokeWidth={6} fill="none"/>;
      })}
    </svg>
  </div>;
};

const ChartText=({layout,x,y,w,color=WHITE}:{layout:TextLayout;x:number;y:number;w:number;color?:string})=><foreignObject x={x} y={y} width={w} height={layout.requiredHeight+.2}><div data-text-minimum={layout.size} data-text-size={layout.size} style={{fontFamily:EDITORIAL_FONT,fontWeight:700,fontSize:layout.size,lineHeight:1.18,color,whiteSpace:"pre"}}>{layout.lines.map((line,i)=><div key={i}>{line}</div>)}</div></foreignObject>;
export const EditorialChart=({chart,width,height,title,focus,progress}:{chart:Chart;width:number;height:number;title:string;focus:{from:number;to:number}|null;progress:number})=> {
  const g=chartLayout(chart,width,height,title,measureEditorialText);
  if(g.problems.length)throw new Error(g.problems.join("\n"));
  const selected=(i:number)=>focus!==null&&i>=focus.from&&i<=focus.to;
  return <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{fontFamily:EDITORIAL_FONT,background:"rgba(18,22,28,.75)",borderRadius:8,overflow:"hidden"}}>
    <ChartText layout={g.titleLayout} x={g.left} y={10} w={g.pw}/>
    <ChartText layout={g.unitLayout} x={g.left} y={14+g.titleLayout.requiredHeight} w={g.pw} color="#a6b6c3"/>
    {g.ticks.map((v,i)=><g key={i}><path d={`M${g.left},${g.py(v)} H${g.right}`} stroke="#394751" strokeWidth={1} strokeDasharray="4 6"/><text x={g.left-16} y={g.py(v)+9} textAnchor="end" fill="#a6b6c3" fontWeight={700} fontSize={28}>{chartNumber(v)}</text></g>)}
    {focus&&<rect x={g.px(focus.from)-12} y={g.top} width={Math.max(24,g.px(focus.to)-g.px(focus.from)+24)} height={g.ph} fill={GOLD} opacity={.1*progress}/>}
    {chart.type==="line"&&<path d={chart.points.map((p,i)=>`${i?"L":"M"}${g.px(i)},${g.py(p.value)}`).join(" ")} fill="none" stroke={GOLD} strokeWidth={5} strokeLinejoin="round" strokeLinecap="round"/>}
    {chart.points.map((p,i)=><g key={i}>{chart.type==="bar"?<rect x={g.px(i)-g.barWidth/2} y={g.py(p.value)} width={g.barWidth} height={g.bottom-g.py(p.value)} rx={4} fill={GOLD} opacity={focus&&!selected(i)?.4:1}/>:<circle cx={g.px(i)} cy={g.py(p.value)} r={selected(i)?8:4.5} fill={selected(i)?WHITE:GOLD}/>}</g>)}
    {g.xLabels.map(l=><ChartText key={l.index} layout={l.layout} x={l.x} y={l.y} w={l.w}/>)}
    <ChartText layout={g.xTitle} x={g.left+(g.pw-g.xTitle.requiredWidth)/2} y={height-35} w={g.xTitle.requiredWidth+1} color="#a6b6c3"/>
    {focus&&(()=>{const i=focus.to,text=chartNumber(chart.points[i].value),w=measureEditorialText(text,30)+28,x=Math.min(g.right-w,Math.max(g.left,g.px(i)-w/2)),y=Math.max(g.top,g.py(chart.points[i].value)-48);return <g opacity={progress}><rect x={x} y={y} width={w} height={44} rx={6} fill={GOLD}/><text x={x+w/2} y={y+31} textAnchor="middle" fill="#101317" fontWeight={700} fontSize={30}>{text}</text></g>;})()}
  </svg>;
};
