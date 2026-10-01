import assert from "node:assert/strict";
import {composeText} from "../src/lib/editorial-typography";
import {editorialStageSchema,type StageEvent} from "../src/lib/editorial-stage";
import {layoutStage,intersects,segmentHits,transformedRect,pointOnRoute,reservedElementBounds} from "../src/lib/editorial-layout";
import {chartLayout} from "../src/lib/editorial-chart-layout";

const measure=(text:string,size:number)=>text.length*size*.55;
let passed=0;
function check(name:string,fn:()=>void){fn();passed++;console.log(`OK ${name}`);}
const stage=(elements:any[],connections:any[]=[])=>editorialStageSchema.parse({show_title:false,elements,connections});
const node=(id:string,x:number,y:number,w=24,h=36)=>({id,kind:"step",label:id,icon:"document",x,y,width:w,height:h});
const resolved=(s:ReturnType<typeof stage>,beats:StageEvent[]=[],f=100)=>layoutStage(s,beats,f,30,1920,1080,measure);

check("Typography preserves words and enforces its minimum",()=>{
  const text="Condição que precisa continuar inteira";
  const t=composeText(text,240,160,38,32,measure);
  assert.equal(t.lines.join(" "),text);assert(t.size>=32);assert(t.fits);
  const bad=composeText(text,60,30,38,32,measure);assert.equal(bad.fits,false);assert.equal(bad.size,32);
});
check("Long unbreakable token is rejected, never clipped",()=>assert.equal(composeText("abcdefghijklmnopqrstuvwxyz",100,200,38,32,measure).fits,false));
check("Measured long edge captions avoid nodes and other captions",()=>{
  const s=stage([{...node("purchase",4,30),kind:"object",object_type:"package",label:"Compras e insumos"},{...node("company",38,26,24,44),label:"Sua empresa",detail:"Débito nas vendas"},{...node("client",72,26,24,44),label:"Cliente no regime regular",detail:"Crédito conforme a regra aplicável",icon:"bank"}], [{from:"purchase",to:"company",label:"créditos permitidos"},{from:"company",to:"client",label:"crédito do adquirente"}]);
  const r=resolved(s);assert.deepEqual(r.issues,[]);
  const boxes=reservedElementBounds(s,[],r.canvas).map(e=>e.box);
  r.connections.forEach(c=>{assert(c.label);assert.equal(c.label.text,s.connections.find(e=>e.from===c.from)!.label);boxes.forEach(b=>assert(!intersects(c.label!.box,b,12)));assert(c.label.layout.size>=30);});
  assert(!intersects(r.connections[0].label!.box,r.connections[1].label!.box,10));
});
for(const [name,elements] of [
  ["vertical",[node("first",30,5,30,25),node("second",30,65,30,25)]],
  ["reverse",[node("first",70,30,25,35),node("second",5,30,25,35)]],
  ["diagonal",[node("first",5,10,25,25),node("second",70,60,25,25)]],
] as const)check(`${name} flow routes are safe`,()=>{
  const s=stage([...elements],[{from:"first",to:"second",label:"Relação declarada"}]);const r=resolved(s);
  assert.deepEqual(r.issues,[]);
  const edge=r.connections[0],rects=r.elements.map(e=>transformedRect(e,100,r.canvas));
  edge.points.slice(1).forEach((p,i)=>rects.forEach((b,j)=>{if(i===0&&j===0||i===edge.points.length-2&&j===1)return;assert(!segmentHits(edge.points[i],p,b));}));
});
check("Route avoids a third obstacle",()=>{
  const s=stage([node("first",5,35,22,30),node("obstacle",39,20,22,60),node("second",73,35,22,30)],[{from:"first",to:"second",label:"Relação"}]);const r=resolved(s);assert.deepEqual(r.issues,[]);
  const box=transformedRect(r.elements[1],100,r.canvas),edge=r.connections[0];edge.points.slice(1).forEach((p,i)=>assert(!segmentHits(edge.points[i],p,box,8)));
});
check("Ports follow entrance and remain outside their own node",()=>{
  const s=stage([node("first",5,30),node("second",70,30)],[{from:"first",to:"second",label:"Relação"}]);
  for(const frame of [1,4,8,14,100]){
    const r=resolved(s,[],frame),a=transformedRect(r.elements[0],frame,r.canvas),edge=r.connections[0];assert.deepEqual(r.issues,[]);
    assert(Math.abs(edge.points[0].x-a.x-a.w)<.01);
    edge.points.slice(1).forEach((p,i)=>{if(i!==0)assert(!segmentHits(edge.points[i],p,a));});
  }
});
check("Frames evaluated out of order produce identical routes",()=>{
  const s=stage([node("first",5,30),node("second",70,30)],[{from:"first",to:"second",label:"Relação"}]);
  const before=JSON.stringify(s),a=resolved(s,[],4);resolved(s,[],100);resolved(s,[],1);assert.deepEqual(resolved(s,[],4),a);assert.equal(JSON.stringify(s),before);
});
check("Caption slot remains stable through entrance",()=>{
  const s=stage([node("first",5,30),node("second",70,30)],[{from:"first",to:"second",label:"Relação"}]);assert.deepEqual(resolved(s,[],1).connections[0].label!.box,resolved(s,[],100).connections[0].label!.box);
});
check("Updated text is checked instead of only initial label",()=>{
  const s=stage([{id:"label",kind:"label",label:"Curto",x:10,y:10,width:10,height:8}]);
  const beats:StageEvent[]=[{target_id:"label",headline:"UmaPalavraSemEspaçoMuitoLongaParaSuaRegião",action:"update",resolved_frame:20}];
  assert(resolved(s,beats,100).issues.some(i=>i.code==="text-capacity"));
});
check("Photo caption follows its visible region and never silently disappears",()=>{
  const s=stage([{id:"photo",kind:"photo",label:"Contexto da imagem",asset_id:"fixture",asset_file:"fixture.png",x:5,y:10,width:30,height:35},{id:"topic",kind:"label",label:"Assunto",x:65,y:25,width:25,height:25}]);
  const normal=resolved(s);assert.deepEqual(normal.issues,[]);assert.equal(normal.photo_captions.length,1);assert(normal.photo_captions[0].layout.fits);
  const crop=resolved(s,[{target_id:"topic",headline:"Assunto",camera:{x:80,y:45,zoom:1.8},resolved_frame:20}]);
  assert(crop.issues.some(i=>i.code==="photo-caption-capacity"));assert.equal(crop.photo_captions.length,1);
});
check("Camera includes full route and caption without hiding nodes",()=>{
  const s=stage([node("first",5,30),node("second",70,30)],[{from:"first",to:"second",label:"Relação"}]);
  const beats:StageEvent[]=[{target_id:"first",headline:"Primeiro",camera:{x:15,y:45,zoom:1.6},resolved_frame:20}];
  const r=resolved(s,beats);assert.deepEqual(r.issues,[]);assert(r.camera.zoom<1.6);assert.equal(r.elements.filter(e=>e.visible).length,2);
});
check("Equation binds existing values and reserves operators",()=>{
  const s=stage([{id:"a",kind:"metric",label:"Entrada",value:"R$ 1.000",x:4,y:30,width:25,height:35},{id:"b",kind:"metric",label:"Crédito",value:"R$ 300",x:38,y:30,width:25,height:35},{id:"r",kind:"metric",label:"Resultado",value:"R$ 700",x:72,y:30,width:24,height:35,initially_visible:false}]);
  const beats:StageEvent[]=[{target_id:"a",headline:"Conta",operation:{kind:"equation",input_ids:["a","b"],operator:"-",result_id:"r"},resolved_frame:10},{target_id:"r",headline:"Resultado",action:"reveal",resolved_frame:60}];
  const r=resolved(s,beats,40);assert.deepEqual(r.issues,[]);assert.deepEqual(r.operation!.glyphs.map(g=>g.text),["-","="]);assert.equal(r.elements[2].visible,false);assert.equal(resolved(s,beats,100).elements[2].visible,true);
});
check("Compare targets all declared participants",()=>{
  const s=stage([node("left",5,25,40,50),node("right",55,25,40,50)]);const r=resolved(s,[{target_id:"left",headline:"Cenários",operation:{kind:"compare",element_ids:["left","right"]},resolved_frame:20}]);assert.deepEqual(r.issues,[]);assert.equal(r.operation!.boxes.length,2);
});
check("Meter rejects out-of-range values instead of clamping",()=>{
  const s=stage([node("meter",10,20,30,30)]);const r=resolved(s,[{target_id:"meter",headline:"Escala",operation:{kind:"meter",value:120,min:0,max:100,unit:"%"},resolved_frame:20}]);assert(r.issues.some(i=>i.code==="meter-scale"));
});
check("Chart labels and unit have measured capacity",()=>{
  const g=chartLayout({type:"line",source_id:"source",unit:"R$",x_label:"Data",y_min:0,y_max:100,points:[{x:1,label:"1 JAN",value:20},{x:2,label:"2 JAN",value:30},{x:3,label:"3 JAN",value:80}]},1000,600,"Dados observados",measure);assert.deepEqual(g.problems,[]);assert.equal(g.px(0),g.left);assert.equal(g.py(100),g.top);assert.equal(g.py(0),g.bottom);
});
check("Route interpolation reaches both endpoints",()=>{
  const points=[{x:0,y:0},{x:10,y:0},{x:10,y:30}];assert.deepEqual(pointOnRoute(points,0),points[0]);assert.deepEqual(pointOnRoute(points,1),points[2]);assert.deepEqual(pointOnRoute(points,.5),{x:10,y:10});
});
console.log(`${passed} regressões de layout passaram.`);
