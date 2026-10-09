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

// ODE Notícias: o recorte permanece uma imagem autêntica e sem alterações.
// O cenário ao redor é um tratamento de apresentação, nunca um portal recriado.
export const NewsDocumentFrame=({
  element,view,markIds,markProgress,width,height
}:{
  element:StageElement;view:Region;markIds:string[];markProgress:Record<string,number>;
  width:number;height:number;
})=>{
  if(!element.asset_file)throw new Error(`Recorte jornalístico ${element.id} sem arquivo original.`);
  const sourceWidth=Math.max(1,element.asset_width??1351);
  const sourceHeight=Math.max(1,element.asset_height??917);
  const cropWidth=sourceWidth*Math.max(.01,view.width)/100;
  const cropHeight=sourceHeight*Math.max(.01,view.height)/100;
  const ratio=cropWidth/cropHeight;
  // A imagem inteira selecionada cabe no quadro sem distorção ou corte.
  // Para recortes muito largos, não criar barras vazias sobre fundo preto.
  const frameWidth=Math.min(Math.max(1,width-128),Math.max(1,height-92)*ratio);
  const frameHeight=frameWidth/ratio;
  return <div data-news-document-backdrop="true" style={{
    position:"relative",width:"100%",height:"100%",overflow:"hidden",
    background:"radial-gradient(ellipse at 50% 45%, #253039 0%, #141a20 58%, #0b1015 100%)",
    display:"flex",alignItems:"center",justifyContent:"center"
  }}>
    <Img src={staticFile(element.asset_file)} aria-hidden style={{
      position:"absolute",inset:"-10%",width:"120%",height:"120%",
      objectFit:"cover",filter:"blur(40px) brightness(.28) saturate(.68)",
      opacity:.88
    }}/>
    <div aria-hidden style={{
      position:"absolute",inset:0,
      background:"linear-gradient(180deg,rgba(8,12,18,.26),rgba(8,12,18,.52))",
    }}/>
    <div data-news-document-frame="true" style={{
      position:"relative",width:frameWidth,height:frameHeight,
      background:"#f9f8f5",padding:6,boxSizing:"border-box",
      border:"1px solid rgba(245,247,249,.46)",borderRadius:12,
      boxShadow:"0 20px 74px rgba(0,0,0,.8), 0 3px 20px rgba(0,0,0,.48)",
      overflow:"hidden",
    }}>
      <SourceExcerpt element={element} view={view} markIds={markIds} markProgress={markProgress}/>
    </div>
  </div>;
};

const ChartText=({layout,x,y,w,color=WHITE}:{layout:TextLayout;x:number;y:number;w:number;color?:string})=><foreignObject x={x} y={y} width={w} height={layout.requiredHeight+.2}><div data-text-minimum={layout.size} data-text-size={layout.size} style={{fontFamily:EDITORIAL_FONT,fontWeight:700,fontSize:layout.size,lineHeight:1.18,color,whiteSpace:"pre"}}>{layout.lines.map((line,i)=><div key={i}>{line}</div>)}</div></foreignObject>;
export const EditorialChart=({chart,width,height,title,focus,progress,revealTo=chart.points.length-1,revealFrom=revealTo,revealProgress=1}:{chart:Chart;width:number;height:number;title:string;focus:{from:number;to:number}|null;progress:number;revealTo?:number;revealFrom?:number;revealProgress?:number})=> {
  const g=chartLayout(chart,width,height,title,measureEditorialText);
  if(g.problems.length)throw new Error(g.problems.join("\n"));
  const selected=(i:number)=>focus!==null&&i>=focus.from&&i<=focus.to;
  const entrance=(i:number)=>i>revealTo?0:i>revealFrom?Math.max(0,Math.min(1,revealProgress)):1;
  return <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{fontFamily:EDITORIAL_FONT,background:"rgba(18,22,28,.75)",borderRadius:8,overflow:"hidden"}}>
    <ChartText layout={g.titleLayout} x={g.left} y={10} w={g.pw}/>
    <ChartText layout={g.unitLayout} x={g.left} y={14+g.titleLayout.requiredHeight} w={g.pw} color="#a6b6c3"/>
    {g.ticks.map((v,i)=><g key={i}><path d={`M${g.left},${g.py(v)} H${g.right}`} stroke="#394751" strokeWidth={1} strokeDasharray="4 6"/><text x={g.left-16} y={g.py(v)+9} textAnchor="end" fill="#a6b6c3" fontWeight={700} fontSize={28}>{chartNumber(v)}</text></g>)}
    {focus&&<rect x={g.px(focus.from)-12} y={g.top} width={Math.max(24,g.px(focus.to)-g.px(focus.from)+24)} height={g.ph} fill={GOLD} opacity={.1*progress}/>}
    {chart.type==="line"&&chart.points.slice(1).map((p,j)=>{const i=j+1;return i<=revealTo?<path key={i} d={`M${g.px(i-1)},${g.py(chart.points[i-1].value)} L${g.px(i)},${g.py(p.value)}`} pathLength={1} strokeDasharray={1} strokeDashoffset={1-entrance(i)} fill="none" stroke={GOLD} strokeWidth={5} strokeLinecap="round"/>:null;})}
    {chart.points.map((p,i)=>i<=revealTo?<g key={i}>{chart.type==="bar"?<rect x={g.px(i)-g.barWidth/2} y={g.bottom-(g.bottom-g.py(p.value))*entrance(i)} width={g.barWidth} height={(g.bottom-g.py(p.value))*entrance(i)} rx={4} fill={GOLD} opacity={focus&&!selected(i)?.4:1}/>:<circle cx={g.px(i)} cy={g.py(p.value)} r={selected(i)?8:4.5} opacity={entrance(i)} fill={selected(i)?WHITE:GOLD}/>}</g>:null)}
    {g.xLabels.map(l=>l.index<=revealTo?<g key={l.index} opacity={entrance(l.index)}><ChartText layout={l.layout} x={l.x} y={l.y} w={l.w}/></g>:null)}
    <ChartText layout={g.xTitle} x={g.left+(g.pw-g.xTitle.requiredWidth)/2} y={height-35} w={g.xTitle.requiredWidth+1} color="#a6b6c3"/>
    {focus&&focus.to<=revealTo&&(()=>{const i=focus.to,text=chartNumber(chart.points[i].value),w=measureEditorialText(text,30)+28,x=Math.min(g.right-w,Math.max(g.left,g.px(i)-w/2)),y=Math.max(g.top,g.py(chart.points[i].value)-48);return <g opacity={progress*entrance(i)}><rect x={x} y={y} width={w} height={44} rx={6} fill={GOLD}/><text x={x+w/2} y={y+31} textAnchor="middle" fill="#101317" fontWeight={700} fontSize={30}>{text}</text></g>;})()}
  </svg>;
};
