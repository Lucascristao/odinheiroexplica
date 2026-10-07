import {z} from "zod";

const spoken = z.object({scene_id:z.string().min(1),quote:z.string().min(1)});
export const learningStrategySchema = z.object({
  version:z.literal("1.0"),
  audience:z.object({situation:z.string().min(10),prior_belief:z.string().min(10),desired_understanding:z.string().min(10)}),
  hypothesis:z.object({change:z.string().min(10),expected_effect:z.string().min(10),evaluation:z.string().min(10)}),
  first_value:spoken,
  promises:z.array(z.object({
    surface:z.enum(["title","thumbnail"]),text:z.string().min(1),
    kind:z.enum(["explanation","conditional_result","quantitative_generalization"]),
    claim_ids:z.array(z.string()).min(1),learning_unit_ids:z.array(z.string()).min(1),
    example_ids:z.array(z.string()).default([]),delivery:spoken,boundary:spoken,
  })).length(2),
  progression:z.array(z.object({learning_unit_id:z.string().min(1),new_information:z.string().min(10),next_question:z.string().min(10)})).min(1),
});

// Integrity and provenance checks only. An agent still reviews what the evidence proves.
export function validateLearningStrategy(project:any,required=false):string[] {
  const raw=project.editorial?.learning_strategy;
  if(!raw)return required?["Nova produção exige editorial.learning_strategy. Consulte docs/editorial-learning.md."]:[];
  const parsed=learningStrategySchema.safeParse(raw);
  if(!parsed.success)return [parsed.error.message];
  const strategy=parsed.data,errors:string[]=[];
  const scenes=project.scenes??project.script?.scenes??[];
  const units=project.editorial?.explanation?.learning_units??[];
  const examples=project.editorial?.explanation?.examples??[];
  const claims=project.claims??[];
  const sources=new Set((project.sources??[]).map((s:any)=>s.id));
  const ref=(r:z.infer<typeof spoken>,label:string)=>{
    const index=scenes.findIndex((s:any)=>s.id===r.scene_id);
    const text=String(scenes[index]?.narration??"");
    if(index<0||text.split(r.quote).length!==2)errors.push(`${label}: trecho literal deve ser único em ${r.scene_id}.`);
    return {index,offset:text.indexOf(r.quote)};
  };
  const first=ref(strategy.first_value,"Primeira entrega");
  if(first.index!==0)errors.push("Primeira entrega deve ocorrer na cena de abertura.");
  const subscription=project.editorial?.narrative_contract?.subscription_request;
  const opening=String(scenes[0]?.narration??"");
  if(subscription&&opening.includes(subscription)&&first.offset>=opening.indexOf(subscription))errors.push("Pedido de inscrição deve vir depois da primeira entrega.");
  for(const surface of ["title","thumbnail"] as const) {
    const promises=strategy.promises.filter(p=>p.surface===surface);
    if(promises.length!==1){errors.push(`Declare exatamente uma prova para ${surface}.`);continue;}
    const p=promises[0];
    const text=surface==="title"?project.packaging?.titles?.[0]?.text:project.packaging?.thumbnails?.[0]?.headline;
    if(p.text!==text)errors.push(`Prova de ${surface} corresponde a outra embalagem.`);
    ref(p.delivery,`Entrega de ${surface}`);ref(p.boundary,`Limite de ${surface}`);
    for(const id of p.claim_ids) {
      const c=claims.find((c:any)=>c.id===id);
      if(!c||c.verification_status!=="verified"||!c.source_ids?.length||c.source_ids.some((s:string)=>!sources.has(s)))errors.push(`Prova de ${surface}: claim ${id} precisa estar verificado e ter fonte existente.`);
    }
    for(const id of p.learning_unit_ids) {
      const unit=units.find((u:any)=>u.id===id);
      if(!unit)errors.push(`Prova de ${surface}: unidade ${id} inexistente.`);
      else if(!unit.claim_ids?.some((c:string)=>p.claim_ids.includes(c)))errors.push(`Prova de ${surface}: unidade ${id} não explica seus claims.`);
    }
    const evidence=p.example_ids.map(id=>examples.find((x:any)=>x.id===id));
    if(evidence.some(x=>!x))errors.push(`Prova de ${surface}: exemplo inexistente.`);
    if(p.kind==="quantitative_generalization"&&(!evidence.length||evidence.every(x=>!x||["illustrative","analogy"].includes(x.kind))))errors.push(`Prova de ${surface}: resultado quantitativo geral exige demonstração factual; hipótese isolada não sustenta promessa universal.`);
  }
  const progression=strategy.progression.map(p=>p.learning_unit_id);
  if(new Set(progression).size!==progression.length)errors.push("Progressão repete uma unidade explicativa.");
  if(progression.some(id=>!units.some((u:any)=>u.id===id))||units.some((u:any)=>!progression.includes(u.id)))errors.push("Progressão deve cobrir as unidades explicativas existentes, sem inventar blocos.");
  return errors;
}
