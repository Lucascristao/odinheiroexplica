import assert from "node:assert/strict";
import {editorialStageSchema, kineticWordProgress, resolveStage, resolveStageCamera, validateStageEvents, type StageEvent} from "../src/lib/editorial-stage";
import {entranceMotion, layoutStage, transformedRect} from "../src/lib/editorial-layout";

const measure=(text:string,size:number)=>text.length*size*.55;
const label=(id:string,x:number,y:number,width=30,height=35)=>({id,kind:"label",label:id,x,y,width,height});
const stage=(settings:Record<string,unknown>={})=>editorialStageSchema.parse({show_title:false,elements:[label("A",10,20),{...label("B",65,20),initially_visible:false}],connections:[],...settings});
let passed=0;
const check=(name:string,fn:()=>void)=>{fn();passed++;console.log(`OK ${name}`);};

check("Legacy input never acquires a camera path or a word treatment",()=>{
  const s=stage(),beats:StageEvent[]=[{target_id:"A",headline:"A",action:"focus",resolved_frame:30},{target_id:"B",headline:"B",action:"reveal",resolved_frame:120}];
  for(const frame of [0,30,45,90,120,200])assert.deepEqual(resolveStageCamera(s,beats,frame),{x:50,y:50,zoom:1});
  assert.equal(resolveStage(s,beats,140).elements[1].treatment,undefined);
});
check("Authored camera wins; static and hold opt out of auto shots",()=>{
  const s=stage({camera_mode:"auto"});
  const beats:StageEvent[]=[{target_id:"A",headline:"A",resolved_frame:30,camera:{x:40,y:40,zoom:1.1,motion_seconds:.6}},{target_id:"A",headline:"Pausa",resolved_frame:90,camera_mode:"hold"}];
  assert.deepEqual(resolveStageCamera(s,beats,70),{x:40,y:40,zoom:1.1});
  assert.deepEqual(resolveStageCamera(s,beats,140),resolveStageCamera(s,beats,70));
  assert.deepEqual(resolveStageCamera(stage({camera_mode:"static"}),beats,140),{x:50,y:50,zoom:1});
});
check("Opt-in camera anticipates a reveal without exposing future information",()=>{
  const s=stage({camera_mode:"auto"}),beats:StageEvent[]=[{target_id:"A",headline:"A",action:"focus",resolved_frame:30},{target_id:"B",headline:"B",action:"reveal",resolved_frame:150,entrance:{style:"fade"}}];
  assert.notDeepEqual(resolveStageCamera(s,beats,70),{x:50,y:50,zoom:1});
  assert.equal(resolveStage(s,beats,149).elements[1].visible,false);
  assert.notDeepEqual(resolveStageCamera(s,beats,145),resolveStageCamera(s,beats,110));
  for(let frame=0;frame<=210;frame++) {
    const r=layoutStage(s,beats,frame,30,1920,1080,measure);
    assert.deepEqual(r.issues,[],`frame ${frame}`);
    for(const element of r.elements.filter(e=>e.visible&&entranceMotion(e,frame).reveal>.01)) {
      const b=transformedRect(element,frame,r.canvas),c=r.camera;
      const x=50+(b.x/r.canvas.width*100-c.x)*c.zoom,y=50+(b.y/r.canvas.height*100-c.y)*c.zoom;
      assert(x>=-.001&&y>=-.001&&x+b.w/r.canvas.width*100*c.zoom<=100.001&&y+b.h/r.canvas.height*100*c.zoom<=100.001,`complete frame ${frame}`);
    }
  }
});
check("Authored moves and reframing are deterministic, settle, and preserve values",()=>{
  const s=stage({elements:[{...label("A",10,20),kind:"metric",value:"R$ 1.000"}]}),beats:StageEvent[]=[{target_id:"A",headline:"Conta",action:"focus",resolved_frame:30,motion_seconds:1,moves:[{id:"A",x:55,y:45}],camera_mode:"auto"}];
  assert.deepEqual(validateStageEvents(s,beats),[]);
  const at45=resolveStage(s,beats,45);resolveStage(s,beats,90);resolveStage(s,beats,1);
  assert.deepEqual(resolveStage(s,beats,45),at45);
  assert.equal(at45.elements[0].value,"R$ 1.000");
  assert.equal(resolveStage(s,beats,100).elements[0].x,55);
  assert.deepEqual(resolveStageCamera(s,beats,100),resolveStageCamera(s,beats,200));
});
check("Word animation staggers within its cue, then holds all words for reading",()=>{
  const p=Array.from({length:5},(_,i)=>kineticWordProgress(.4,i,5));
  assert(p[0]>p[1]&&p[1]>p[2]);
  for(let i=0;i<5;i++){assert.equal(kineticWordProgress(0,i,5),0);assert.equal(kineticWordProgress(1,i,5),1);assert.equal(kineticWordProgress(2,i,5),1);}
});
check("A retiring fact and its route stay framed until the fade has ended",()=>{
  const s=stage({elements:[label("A",8,25,25,35),label("B",68,25,24,35)],connections:[{from:"A",to:"B"}]}),beats:StageEvent[]=[{target_id:"A",headline:"Retirar",action:"retire",resolved_frame:60,motion_seconds:1,camera:{x:80,y:42,zoom:1.4,motion_seconds:.4}}];
  for(let frame=60;frame<90;frame++) {
    const r=layoutStage(s,beats,frame,30,1920,1080,measure);
    assert.deepEqual(r.issues,[],`retire frame ${frame}`);
    for(const e of r.elements.filter(e=>e.visible||e.wasVisible&&entranceMotion(e,frame).reveal<.99)) {
      const b=transformedRect(e,frame,r.canvas),c=r.camera;
      assert(50+(b.x/r.canvas.width*100-c.x)*c.zoom>=-.001);
      assert(50+((b.x+b.w)/r.canvas.width*100-c.x)*c.zoom<=100.001);
    }
  }
  assert(layoutStage(s,beats,110,30,1920,1080,measure).camera.zoom>1.1);
});
check("Contradictory camera move and hold is rejected before rendering",()=>{
  const errors=validateStageEvents(stage(),[{target_id:"A",headline:"A",camera_mode:"hold",camera:{x:40,y:40,zoom:1},resolved_frame:30}]);
  assert(errors.some(error=>error.includes("contraditórias")));
});
check("Wipe and directional slide are explicit capabilities, never implicit presets",()=>{
  const s=stage(),wipe:StageEvent[]=[{target_id:"B",headline:"B",action:"reveal",resolved_frame:30,motion_seconds:1,entrance:{style:"wipe",direction:"left"}}];
  const e=resolveStage(s,wipe,45).elements[1],m=entranceMotion(e,45);
  assert.equal(m.scale,1);assert.equal(m.x,0);assert(m.clip?.includes("50%"));
  assert.equal(entranceMotion(resolveStage(s,wipe,100).elements[1],100).clip,"inset(0 0% 0 0)");
  const slide:StageEvent[]=[{...wipe[0],entrance:{style:"slide",direction:"right"}}];
  assert(entranceMotion(resolveStage(s,slide,40).elements[1],40).x>0);
  assert.equal(entranceMotion(resolveStage(s,slide,100).elements[1],100).x,0);
});
check("Operation durations follow the authored cue and stop before the next event",()=>{
  const s=stage({elements:[label("A",5,25,40,50),label("B",55,25,40,50)]});
  const beats:StageEvent[]=[{target_id:"A",headline:"Comparar",resolved_frame:30,motion_seconds:2,operation:{kind:"compare",element_ids:["A","B"]}},{target_id:"B",headline:"Ler",resolved_frame:60}];
  const r=layoutStage(s,beats,40,30,1920,1080,measure);
  assert.deepEqual(r.issues,[]);assert.equal(r.operation?.duration,30);
});
console.log(`${passed} regressões de direção e movimento passaram.`);
