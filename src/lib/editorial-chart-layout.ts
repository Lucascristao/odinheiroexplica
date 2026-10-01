import type {Chart} from "./editorial-evidence";
import {composeText,type MeasureWidth,type TextLayout} from "./editorial-typography";

export const chartNumber=(v:number)=>v.toLocaleString("pt-BR",{maximumFractionDigits:4});
export function chartLayout(chart:Chart,width:number,height:number,title:string,measure:MeasureWidth) {
  const ticks=Array.from({length:4},(_,i)=>chart.y_min+(chart.y_max-chart.y_min)*i/3);
  const left=Math.max(80,...ticks.map(v=>measure(chartNumber(v),28)+20)),right=width-24;
  const titleLayout=composeText(title,right-left,85,36,32,measure);
  const unitLayout=composeText(chart.unit,right-left,36,30,28,measure);
  const top=titleLayout.requiredHeight+unitLayout.requiredHeight+30,bottom=height-90,pw=right-left,ph=bottom-top;
  const problems:string[]=[];
  if(!titleLayout.fits||!unitLayout.fits||pw<250||ph<120)problems.push("Gráfico exige mais área para título, unidade, escala e dados na fonte mínima.");
  const xmin=chart.points[0].x,xmax=chart.points.at(-1)!.x;
  const gap=chart.type==="bar"?pw/(chart.points.length+1)/2:0;
  const px=(i:number)=>left+gap+(chart.points[i].x-xmin)/(xmax-xmin)*(pw-2*gap);
  const py=(value:number)=>bottom-(value-chart.y_min)/(chart.y_max-chart.y_min)*ph;
  const xLabels:{index:number;x:number;y:number;w:number;layout:TextLayout}[]=[];
  const selected=[0];
  for(let i=1;i<chart.points.length-1;i++) {
    const w=measure(chart.points[i].label,28),previous=selected.at(-1)!;
    if(px(i)-w/2>px(previous)+measure(chart.points[previous].label,28)/2+20&&px(i)+w/2<px(chart.points.length-1)-measure(chart.points.at(-1)!.label,28)-20)selected.push(i);
  }
  selected.push(chart.points.length-1);
  for(const i of selected) {
    const w=measure(chart.points[i].label,28)+1,x=i===0?px(i):i===chart.points.length-1?px(i)-w:px(i)-w/2;
    const layout=composeText(chart.points[i].label,w,34,28,28,measure);
    if(x<0||x+w>width||!layout.fits)problems.push(`Rótulo de eixo não cabe: ${chart.points[i].label}`);
    xLabels.push({index:i,x,y:bottom+16,w,layout});
  }
  for(let i=1;i<xLabels.length;i++)if(xLabels[i].x<xLabels[i-1].x+xLabels[i-1].w+8)problems.push("Limites do eixo X colidem; amplie o gráfico.");
  const xTitle=composeText(chart.x_label,pw,34,28,28,measure);
  if(!xTitle.fits)problems.push("Nome do eixo X não cabe na fonte mínima.");
  const minGap=Math.min(...chart.points.slice(1).map((_,i)=>px(i+1)-px(i)));
  return {ticks,left,right,top,bottom,pw,ph,px,py,titleLayout,unitLayout,xLabels,xTitle,barWidth:Math.min(90,minGap*.65),problems};
}
