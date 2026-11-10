import assert from "node:assert/strict";
import {newsDocumentContext} from "../src/lib/news-document-context";
import {editorialStageSchema,resolveStage,validateStageEvents,type StageEvent} from "../src/lib/editorial-stage";
const proof={x:20,y:30,width:60,height:20};
assert.deepEqual(newsDocumentContext(proof,1.6,0,30).view,{x:0,y:0,width:100,height:100});
assert.deepEqual(newsDocumentContext(proof,1.6,48,30).view,{x:0,y:0,width:100,height:100});
assert.equal(newsDocumentContext(proof,1.6,47,30).showContext,true);
assert.equal(newsDocumentContext(proof,1.6,48,30).showContext,false);
const moving=newsDocumentContext(proof,1.6,57,30);
assert.equal(moving.progress,.5);
assert(moving.view.y<proof.y && moving.view.y+moving.view.height>proof.y+proof.height);
assert.deepEqual(newsDocumentContext(proof,1.6,66,30).view,proof);
assert.deepEqual(newsDocumentContext(proof,undefined,0,30).view,proof);
console.log("News document context: real page establishes before crop; intermediate frame preserves the complete proof; historical framing unchanged.");
const stage=editorialStageSchema.parse({show_title:false,full_bleed_news:true,camera_mode:"manual",
  motion_profile:"narrative",elements:[{id:"evidence",kind:"source_excerpt",asset_id:"a",asset_file:"generated-assets/a.png",
    label:"Documento",x:0,y:0,width:100,height:100,asset_width:1360,asset_height:900}],connections:[]});
const shots:StageEvent[]=[{target_id:"evidence",action:"focus",resolved_frame:0,document_shot:{asset_id:"a",asset_file:"generated-assets/a.png",asset_width:1360,asset_height:900,annotations:[]}},
  {target_id:"evidence",action:"focus",resolved_frame:30,document_shot:{asset_id:"b",asset_file:"generated-assets/b.png",asset_width:1360,asset_height:900,
    annotations:[{id:"proof",style:"highlight",region:proof}]},mark_ids:["proof"],view:{x:10,y:20,width:80,height:60}}];
assert.deepEqual(validateStageEvents(stage,shots),[]);
assert.equal(resolveStage(stage,shots,15).elements[0].asset_file,"generated-assets/a.png");
const after=resolveStage(stage,shots,60).elements[0];
assert.equal(after.asset_file,"generated-assets/b.png");
assert.deepEqual(after.markIds,["proof"]);
assert.equal(after.annotations[0].style,"highlight");
assert.deepEqual(after.view,{x:10,y:20,width:80,height:60});
console.log("News documentary sequence: authentic source changes at speech cue and its measured annotation survives production state.");
