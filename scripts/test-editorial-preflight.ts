import assert from "node:assert/strict";
import {layoutStage} from "../src/lib/editorial-layout";
import {editorialStageSchema} from "../src/lib/editorial-stage";
import {partitionLayoutIssues,layoutRepairGuidance,githubAnnotation} from "../src/lib/editorial-layout-audit";
import {validateSpeechDirection} from "../src/lib/speech-direction";

const stage=editorialStageSchema.parse({camera_mode:"static",elements:[
  {id:"document",kind:"source_excerpt",asset_id:"official",label:"Documento",x:5,y:5,width:40,height:60},
  {id:"explanation",kind:"label",label:"Uma explicação que exige espaço legível",x:55,y:5,width:8,height:8},
],connections:[]});
const result=layoutStage(stage,[],0,30,1920,1080,(text,size)=>text.length*size*.6);
assert(result.issues.some(issue=>issue.code==="missing-visual-asset"));
assert(result.issues.some(issue=>issue.code==="text-capacity"));
const early=partitionLayoutIssues(result.issues,"geometry-only");
assert.equal(early.deferred.length,1);
assert(early.issues.some(issue=>issue.code==="text-capacity"),"Early composition must still block unreadable text");
for(const mode of ["pre-voice","final-timing"] as const) {
  const full=partitionLayoutIssues(result.issues,mode);
  assert.equal(full.deferred.length,0);
  assert(full.issues.some(issue=>issue.code==="missing-visual-asset"),"Paid and final gates must require real evidence");
}
assert.match(layoutRepairGuidance("stack-space"),/ordem vertical.*moves/);
assert.match(layoutRepairGuidance("connection-space"),/preserve a demonstração/);
assert.match(layoutRepairGuidance("camera-capacity"),/quadros intermediários/);
const longCue="Palavra ".repeat(22).trim();
const errors=validateSpeechDirection(longCue,{cues:[{text:longCue,kind:"emphasis"}]});
assert.equal(errors.length,1);
assert.match(errors[0],/cues\.0\.text: trecho tem \d+ caracteres; máximo 160/);
assert.match(errors[0],/não altere a narração/);
assert.equal(githubAnnotation("a%\n::error::b\rc"),"a%25%0A::error::b%0Dc");
console.log("Preflight: composição inicial bloqueia texto inválido, produção exige evidência real e reparos preservam a explicação.");
