import {readFileSync,writeFileSync} from "node:fs";
import {editorialStageSchema,resolveStage,resolveStageCamera} from "../src/lib/editorial-stage";
import {editorialCanvas,transformedRect} from "../src/lib/editorial-layout";
const [input,output]=process.argv.slice(2),p=JSON.parse(readFileSync(input,"utf8"));
const rows=[];
for(const scene of p.scenes){if(!scene.visual?.stage)continue;const stage=editorialStageSchema.parse(scene.visual.stage),canvas=editorialCanvas(1920,1080,stage.show_title);
  for(let frame=0;frame<scene.duration_frames;frame+=Math.max(1,Math.round(p.fps/2))){
    const solved=resolveStage(stage,scene.visual.beats,frame,p.fps),camera=resolveStageCamera(stage,scene.visual.beats,frame,p.fps);
    const dx=(50-camera.x)*canvas.width*camera.zoom/100,dy=(50-camera.y)*canvas.height*camera.zoom/100;
    const regions=solved.elements.filter(e=>e.visible).map(e=>{const b=transformedRect(e,frame,canvas);return {id:e.id,kind:e.kind,hyperframes:Boolean(e.hyperframes),x:canvas.x+(b.x-canvas.width/2)*camera.zoom+canvas.width/2+dx,y:canvas.y+(b.y-canvas.height/2)*camera.zoom+canvas.height/2+dy,w:b.w*camera.zoom,h:b.h*camera.zoom};});
    rows.push({frame:scene.start_frame+frame,scene_id:scene.id,regions});
  }
}
writeFileSync(output,JSON.stringify({fps:p.fps,width:1920,height:1080,samples:rows},null,2)+"\n");
