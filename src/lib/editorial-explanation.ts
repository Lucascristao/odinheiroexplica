import {z} from "zod";
const reference=z.object({scene_id:z.string().min(1),quote:z.string().min(1)});
const binding=z.object({scene_id:z.string().min(1),element_id:z.string().min(1),beat_anchor:z.string().optional()});
const input=z.object({id:z.string().min(1),value:z.number().finite(),unit:z.string().min(1),source_ids:z.array(z.string()).default([])});
export const explanationSchema=z.object({
  version:z.literal("1.0"),
  concepts:z.array(z.object({id:z.string().min(1),terms:z.array(z.string().min(1)).min(1),explanation:reference,first_use:reference.optional(),claim_ids:z.array(z.string()).default([]),boundary:z.string().optional()})),
  examples:z.array(z.object({id:z.string().min(1),purpose:z.string().min(10),kind:z.enum(["observed","derived","illustrative","analogy"]),claim_ids:z.array(z.string()).default([]),actors:z.array(z.string()).min(1),assumptions:z.array(z.string()).default([]),inputs:z.array(input).default([]),calculation:z.object({operation:z.enum(["add","subtract","multiply","divide"]),input_ids:z.array(z.string()).min(2),result:z.number().finite(),unit:z.string().min(1),tolerance:z.number().min(0).max(.01).default(.000001)}).optional(),limitation:z.string().min(10),narration_refs:z.array(reference).min(1),visual_bindings:z.array(binding).min(1),identification:reference.optional(),visual_identification:binding.optional()})),
  learning_units:z.array(z.object({id:z.string().min(1),question:z.string().min(10),answer:reference,concept_ids:z.array(z.string()).default([]),claim_ids:z.array(z.string()).default([]),example_ids:z.array(z.string()).default([]),visual_purpose:z.string().min(10),bindings:z.array(binding).min(1)})).min(1),
  review:z.object({content_sha256:z.string().regex(/^[a-f0-9]{64}$/),findings:z.array(z.object({question:z.string().min(10),evidence:reference,conclusion:z.string().min(10)})).min(1)}),
});

export function validateExplanation(project:any):string[] {
  const raw=project.editorial?.explanation;
  if(!raw)return []; // Legacy projects remain importable; production may require the new contract.
  const parsed=explanationSchema.safeParse(raw);
  if(!parsed.success)return [parsed.error.message];
  const e=parsed.data,errors:string[]=[];
  const scenes=project.scenes??project.script?.scenes??[];
  const claims=new Set((project.claims??[]).map((c:any)=>c.id));
  const sources=new Set((project.sources??[]).map((s:any)=>s.id));
  const sceneById=new Map<string,any>(scenes.map((s:any,i:number)=>[s.id??`scene-${String(s.scene_index??s.index??i).padStart(2,"0")}`,s]));
  const ref=(r:z.infer<typeof reference>,label:string)=> {
    const scene=sceneById.get(r.scene_id),text=String(scene?.narration??"");
    if(!scene||text.split(r.quote).length!==2)errors.push(`${label}: trecho literal deve ser único na cena ${r.scene_id}.`);
    return scenes.indexOf(scene)*100000+text.indexOf(r.quote);
  };
  const bind=(b:z.infer<typeof binding>,label:string)=> {
    const scene=sceneById.get(b.scene_id);
    if(!scene?.visual?.stage?.elements?.some((v:any)=>v.id===b.element_id))errors.push(`${label}: elemento ${b.element_id} inexistente em ${b.scene_id}.`);
    if(b.beat_anchor&&!scene?.visual?.beats?.some((v:any)=>v.anchor===b.beat_anchor&&(v.target_id===b.element_id||(v.reveal_ids??[]).includes(b.element_id))))errors.push(`${label}: beat não atua no elemento declarado.`);
  };
  const ids=(items:{id:string}[],label:string)=> {if(new Set(items.map(i=>i.id)).size!==items.length)errors.push(`${label}: ID duplicado.`);};
  ids(e.concepts,"Conceitos");ids(e.examples,"Exemplos");ids(e.learning_units,"Unidades");
  const checkClaims=(list:string[],label:string)=>list.forEach(id=>{if(!claims.has(id))errors.push(`${label}: claim ${id} inexistente.`);});
  for(const c of e.concepts) {
    const start=ref(c.explanation,c.id);
    if(c.first_use&&ref(c.first_use,c.id)<start)errors.push(`${c.id}: conceito usado antes da explicação declarada.`);
    checkClaims(c.claim_ids,c.id);
  }
  for(const x of e.examples) {
    checkClaims(x.claim_ids,x.id);x.narration_refs.forEach(r=>ref(r,x.id));x.visual_bindings.forEach(b=>bind(b,x.id));ids(x.inputs,x.id);
    x.inputs.forEach(i=> {
      i.source_ids.forEach(id=>{if(!sources.has(id))errors.push(`${x.id}: fonte ${id} inexistente.`);});
      if(["observed","derived"].includes(x.kind)&&!i.source_ids.length)errors.push(`${x.id}: entrada factual sem origem.`);
    });
    if(x.kind==="illustrative") {
      if(!x.identification||!x.visual_identification)errors.push(`${x.id}: exemplo ilustrativo exige identificação na fala e na tela.`);
      else {
        ref(x.identification,x.id);bind(x.visual_identification,x.id);
        const v=sceneById.get(x.visual_identification.scene_id)?.visual.stage.elements.find((v:any)=>v.id===x.visual_identification!.element_id);
        if(!/hipot[eé]tic|ilustrativ|fict[ií]ci/i.test(x.identification.quote)||!/hipot[eé]tic|ilustrativ|fict[ií]ci/i.test(`${v?.label} ${v?.detail}`))errors.push(`${x.id}: declare explicitamente que os números são hipotéticos/ilustrativos.`);
      }
    }
    if(x.calculation) {
      const c=x.calculation,values=c.input_ids.map(id=>x.inputs.find(i=>i.id===id));
      if(values.some(v=>!v)){errors.push(`${x.id}: entrada de cálculo inexistente.`);continue;}
      const v=values as z.infer<typeof input>[];
      if(["add","subtract"].includes(c.operation)&&v.some(i=>i.unit!==c.unit))errors.push(`${x.id}: unidades incompatíveis no cálculo.`);
      const result=v.slice(1).reduce((a,i)=>c.operation==="add"?a+i.value:c.operation==="subtract"?a-i.value:c.operation==="multiply"?a*i.value:a/i.value,v[0].value);
      if(!Number.isFinite(result)||Math.abs(result-c.result)>c.tolerance)errors.push(`${x.id}: resultado aritmético incorreto.`);
    }
  }
  for(const u of e.learning_units) {
    ref(u.answer,u.id);checkClaims(u.claim_ids,u.id);u.bindings.forEach(b=>bind(b,u.id));
    u.concept_ids.forEach(id=>{if(!e.concepts.some(c=>c.id===id))errors.push(`${u.id}: conceito ${id} inexistente.`);});
    u.example_ids.forEach(id=>{if(!e.examples.some(c=>c.id===id))errors.push(`${u.id}: exemplo ${id} inexistente.`);});
  }
  e.review.findings.forEach(f=>ref(f.evidence,"Revisão"));
  return errors;
}
