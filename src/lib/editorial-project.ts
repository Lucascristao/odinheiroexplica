export function stableJson(value: any): string {
  if(Array.isArray(value))return `[${value.map(stableJson).join(",")}]`;
  if(value&&typeof value==="object")return `{${Object.keys(value).filter(k=>value[k]!==undefined).sort().map(k=>`${JSON.stringify(k)}:${stableJson(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
export function normalizeEditorialProject(raw:any) {
  if(!raw||typeof raw!=="object")throw new Error("Projeto editorial deve ser um objeto.");
  if(raw.scenes&&raw.script?.scenes&&stableJson(raw.scenes)!==stableJson(raw.script.scenes))throw new Error("scenes e script.scenes divergem; mantenha uma única versão da narração e do palco.");
  const input=raw.scenes??raw.script?.scenes;
  if(!Array.isArray(input)||!input.length)throw new Error("Projeto sem cenas.");
  const scenes=input.map((s:any,i:number)=>({...s,id:s.id??`scene-${String(s.scene_index??s.index??i).padStart(2,"0")}`,scene_index:s.scene_index??s.index??i,index:s.scene_index??s.index??i}));
  if(new Set(scenes.map((s:any)=>s.id)).size!==scenes.length)throw new Error("ID de cena duplicado.");
  return {...raw,scenes,script:{...raw.script,hook:raw.script?.hook??scenes[0].narration,scenes}};
}
export function explanationReviewContent(project:any) {
  project=normalizeEditorialProject(project);
  const e=project.editorial?.explanation;
  const assets=(project.visual_assets??[]).map(({captured_at,...asset}:any)=>asset);
  // The semantic record certifies which material was reviewed, never a score.
  return {story:project.story,sources:project.sources,claims:project.claims,visual_assets:assets,scenes:project.scenes??project.script?.scenes,explanation:e?{version:e.version,concepts:e.concepts,examples:e.examples,learning_units:e.learning_units}:null};
}
