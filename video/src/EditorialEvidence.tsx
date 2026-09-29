import {Img, staticFile} from "remotion";
import {measureText} from "@remotion/layout-utils";
import type {StageElement} from "../../src/lib/editorial-stage";
import type {Chart, Region} from "../../src/lib/editorial-evidence";

const GOLD="#FFBD19", WHITE="#F6F7F8";
export const SourceExcerpt=({element, view, markIds, markProgress}:{element:StageElement;view:Region;markIds:string[];markProgress:Record<string,number>})=>{
  const w=element.asset_width, h=element.asset_height;
  if(!element.asset_file || !w || !h)throw new Error(`Recorte sem arquivo ou dimensões: ${element.id}`);
  return <svg width="100%" height="100%" viewBox={`${view.x*w/100} ${view.y*h/100} ${view.width*w/100} ${view.height*h/100}`} preserveAspectRatio="xMidYMid meet" style={{overflow:"hidden"}}>
    <foreignObject x={0} y={0} width={w} height={h}><Img src={staticFile(element.asset_file)} style={{width:w,height:h,display:"block"}} /></foreignObject>
    {element.annotations.filter(a=>markIds.includes(a.id)).map(a=>{
      const progress=markProgress[a.id]??1;
      const r=a.region,x=r.x*w/100,y=r.y*h/100,rw=r.width*w/100,rh=r.height*h/100;
      if(a.style==="highlight")return <rect key={a.id} x={x} y={y} width={rw*progress} height={rh} fill={GOLD} opacity={0.32} style={{mixBlendMode:"multiply"}} />;
      const path=a.style==="circle" ? `M${x+rw},${y+rh/2} a${rw/2},${rh/2} 0 1 0 ${-rw},0 a${rw/2},${rh/2} 0 1 0 ${rw},0` : `M${x},${y+rh*(a.style==="strike"?0.5:0.94)} L${x+rw},${y+rh*(a.style==="strike"?0.5:0.94)}`;
      return <path key={a.id} d={path} fill="none" stroke={GOLD} strokeWidth={5} vectorEffect="non-scaling-stroke" strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1-progress} />;
    })}
  </svg>;
};

const number=(v:number)=>new Intl.NumberFormat("pt-BR",{maximumFractionDigits:2}).format(v);
export const EditorialChart=({chart,width,height,title,focus,progress}:{chart:Chart;width:number;height:number;title:string;focus:{from:number;to:number}|null;progress:number})=>{
  const ticks=Array.from({length:4},(_,i)=>chart.y_min+(chart.y_max-chart.y_min)*i/3);
  const left=Math.max(100,...ticks.map(v=>number(v).length*19+24));
  const top=96,bottom=height-88,right=width-42,pw=right-left,ph=bottom-top;
  if(pw<250||ph<120)throw new Error("Gráfico sem área legível: amplie a região ou simplifique a escala.");
  const measure=(text:string,size=32)=>measureText({text,fontFamily:"ODE Inter",fontSize:size,fontWeight:700}).width;
  if(measure(title,36)>pw)throw new Error("Encurte o título do gráfico ou amplie sua região.");
  const xmin=chart.points[0].x,xmax=chart.points.at(-1)!.x;
  const gap=chart.type==="bar"?pw/(chart.points.length+1)/2:0;
  const px=(i:number)=>left+gap+(chart.points[i].x-xmin)/(xmax-xmin)*(pw-2*gap);
  const py=(v:number)=>bottom-(v-chart.y_min)/(chart.y_max-chart.y_min)*ph;
  const selected=(i:number)=>focus!==null && i>=focus.from && i<=focus.to;
  const tickIndexes:number[]=[];
  chart.points.forEach((p,i)=>{const previous=tickIndexes.at(-1); if(previous===undefined || px(i)-measure(p.label)/2>px(previous)+measure(chart.points[previous].label)/2+24)tickIndexes.push(i);});
  const minGap=Math.min(...chart.points.slice(1).map((_,i)=>px(i+1)-px(i)));
  const barWidth=Math.min(90,minGap*0.65);
  return <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{overflow:"visible",fontFamily:"ODE Inter"}}>
    <text x={left} y={34} fill={WHITE} fontSize={36}>{title}</text>
    <text x={left} y={72} fill="#aeb6bf" fontSize={32}>{chart.unit}</text>
    {focus && <rect x={px(focus.from)-14} y={top} width={Math.max(28,px(focus.to)-px(focus.from)+28)} height={ph} fill={GOLD} opacity={0.08*progress} />}
    {ticks.map((v,i)=><g key={i}><path d={`M${left},${py(v)} H${right}`} stroke="#39434c" strokeWidth={1}/><text x={left-16} y={py(v)+10} textAnchor="end" fontSize={32} fill="#aeb6bf">{number(v)}</text></g>)}
    {chart.type==="line" && <path d={chart.points.map((p,i)=>`${i?"L":"M"}${px(i)},${py(p.value)}`).join(" ")} stroke={GOLD} strokeWidth={5} fill="none" />}
    {chart.points.map((p,i)=><g key={i}>
      {chart.type==="bar" ? <rect x={px(i)-barWidth/2} y={py(p.value)} width={barWidth} height={bottom-py(p.value)} fill={GOLD} opacity={focus&&!selected(i)?0.4:1}/> : <circle cx={px(i)} cy={py(p.value)} r={selected(i)?8:4} fill={selected(i)?WHITE:GOLD}/>}
      {tickIndexes.includes(i)&&<text x={px(i)} y={bottom+38} textAnchor={i===0?"start":i===chart.points.length-1?"end":"middle"} fill={WHITE} fontSize={32}>{p.label}</text>}
      {focus?.to===i && (()=>{const text=number(p.value),bw=measure(text,32)+28,bx=Math.min(right-bw,Math.max(left,px(i)-bw/2)),by=Math.max(top,py(p.value)-51);return <g opacity={progress}><rect x={bx} y={by} width={bw} height={44} rx={6} fill={GOLD}/><text x={bx+bw/2} y={by+32} textAnchor="middle" fill="#101317" fontSize={32}>{text}</text></g>;})()}
    </g>)}
    <text x={(left+right)/2} y={height-8} textAnchor="middle" fill="#aeb6bf" fontSize={32}>{chart.x_label}</text>
  </svg>;
};
