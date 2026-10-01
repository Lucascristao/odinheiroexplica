import assert from "node:assert/strict";
import {normalizeEditorialProject} from "../src/lib/editorial-project";
import {validateExplanation} from "../src/lib/editorial-explanation";

const raw:any={sources:[{id:"source"}],claims:[{id:"fact"}],scenes:[{id:"s",narration:"Débito é a conta inicial. Crédito é um valor permitido para abater. Exemplo hipotético: cem menos trinta resulta em setenta.",visual:{stage:{elements:[{id:"label",label:"Exemplo hipotético"},{id:"result",label:"Resultado"}]},beats:[{anchor:"cem menos trinta",target_id:"result"}]}}],editorial:{explanation:{version:"1.0",concepts:[{id:"credit",terms:["crédito"],explanation:{scene_id:"s",quote:"Crédito é um valor permitido para abater."},claim_ids:["fact"]}],examples:[{id:"calc",purpose:"Demonstrar uma subtração sem apresentar alíquota real.",kind:"illustrative",actors:["empresa"],assumptions:["Valores fictícios de um único tributo"],claim_ids:["fact"],inputs:[{id:"a",value:100,unit:"BRL"},{id:"b",value:30,unit:"BRL"}],calculation:{operation:"subtract",input_ids:["a","b"],result:70,unit:"BRL"},limitation:"Não representa alíquota nem cálculo tributário real.",narration_refs:[{scene_id:"s",quote:"cem menos trinta resulta em setenta"}],visual_bindings:[{scene_id:"s",element_id:"result",beat_anchor:"cem menos trinta"}],identification:{scene_id:"s",quote:"Exemplo hipotético"},visual_identification:{scene_id:"s",element_id:"label"}}],learning_units:[{id:"unit",question:"O que esta conta simples demonstra?",answer:{scene_id:"s",quote:"cem menos trinta resulta em setenta"},concept_ids:["credit"],claim_ids:["fact"],example_ids:["calc"],visual_purpose:"Construir a operação com valores visíveis.",bindings:[{scene_id:"s",element_id:"result"}]}],review:{content_sha256:"a".repeat(64),findings:[{question:"A hipótese está identificada para o espectador?",evidence:{scene_id:"s",quote:"Exemplo hipotético"},conclusion:"Sim, a natureza fictícia aparece antes dos números."}]}}}};
assert.deepEqual(validateExplanation(normalizeEditorialProject(raw)),[]);
const broken=(mutate:(p:any)=>void,pattern:RegExp)=>{const p=structuredClone(raw);mutate(p);assert(validateExplanation(normalizeEditorialProject(p)).some(e=>pattern.test(e)));};
broken(p=>p.editorial.explanation.examples[0].calculation.result=75,/aritmético/);
broken(p=>p.editorial.explanation.examples[0].inputs[1].unit="USD",/unidades/);
broken(p=>delete p.editorial.explanation.examples[0].identification,/identificação/);
broken(p=>p.editorial.explanation.examples[0].kind="observed",/origem/);
broken(p=>p.editorial.explanation.learning_units[0].bindings[0].element_id="missing",/inexistente/);
broken(p=>p.editorial.explanation.concepts[0].first_use={scene_id:"s",quote:"Débito é a conta inicial."},/antes/);
assert.throws(()=>normalizeEditorialProject({scenes:raw.scenes,script:{scenes:[{narration:"diverge"}]}}),/divergem/);
assert.equal(normalizeEditorialProject({script:{scenes:raw.scenes}}).scenes[0].id,"s");
console.log("Editorial: arithmetic, units, provenance, identification, references, concept order and portable formats verified.");
