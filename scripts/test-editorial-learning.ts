import assert from "node:assert/strict";
import {validateLearningStrategy} from "../src/lib/editorial-learning";
import {explanationReviewContent,stableJson} from "../src/lib/editorial-project";

const project:any={sources:[{id:"bc"}],scenes:[{id:"opening",narration:"Você pode pagar por serviços opcionais. O limite depende do uso. Eu sou Roberto. Inscreva-se no canal."}],
  claims:[{id:"free",verification_status:"verified",source_ids:["bc"]}],packaging:{titles:[{text:"Sua conta precisa dessa tarifa?"}],thumbnails:[{headline:"PRECISA PAGAR?"}]},
  editorial:{narrative_contract:{subscription_request:"Inscreva-se no canal."},explanation:{learning_units:[{id:"choice",claim_ids:["free"]}],examples:[{id:"fiction",kind:"illustrative"}]},learning_strategy:{version:"1.0",audience:{situation:"Pessoa que vê uma tarifa mensal no extrato.",prior_belief:"Acredita que toda conta exige mensalidade.",desired_understanding:"Distinguir uso essencial e pacote opcional."},hypothesis:{change:"Mostrar a escolha antes de definir todos os serviços.",expected_effect:"Reduzir abandono antes da primeira descoberta.",evaluation:"Comparar retenção inicial com vídeos da mesma idade."},first_value:{scene_id:"opening",quote:"Você pode pagar por serviços opcionais."},promises:["title","thumbnail"].map(surface=>({surface,text:surface==="title"?"Sua conta precisa dessa tarifa?":"PRECISA PAGAR?",kind:"explanation",claim_ids:["free"],learning_unit_ids:["choice"],example_ids:[],delivery:{scene_id:"opening",quote:"Você pode pagar por serviços opcionais."},boundary:{scene_id:"opening",quote:"O limite depende do uso."}})),progression:[{learning_unit_id:"choice",new_information:"A cobrança recorrente pode ser opcional.",next_question:"Quando o uso passa do limite gratuito?"}]}}};
assert.deepEqual(validateLearningStrategy(project,true),[]);
const bad=(mutate:(p:any)=>void,pattern:RegExp)=>{const p=structuredClone(project);mutate(p);assert(validateLearningStrategy(p,true).some(e=>pattern.test(e)));};
bad(p=>p.packaging.titles[0].text="Economize R$ 500 garantidos",/outra embalagem/);
bad(p=>p.editorial.learning_strategy.promises[0].delivery.quote="não existe",/literal/);
bad(p=>p.claims[0].verification_status="unverified",/verificado/);
bad(p=>p.editorial.learning_strategy.promises[0].learning_unit_ids=["missing"],/inexistente/);
bad(p=>{p.editorial.learning_strategy.promises[0].kind="quantitative_generalization";p.editorial.learning_strategy.promises[0].example_ids=["fiction"];},/hipótese isolada/);
bad(p=>p.editorial.learning_strategy.first_value.quote="Inscreva-se no canal.",/depois/);
const legacy=structuredClone(project);delete legacy.editorial.learning_strategy;
assert.deepEqual(validateLearningStrategy(legacy),[]);
assert.match(validateLearningStrategy(legacy,true)[0],/Nova produção/);
assert(!("learning_strategy" in explanationReviewContent(legacy)));
const before=stableJson(explanationReviewContent(project));
project.packaging.titles[0].text="Título alterado";
assert.notEqual(stableJson(explanationReviewContent(project)),before);
console.log("Aprendizado: promessa, proveniência, primeira entrega, contratos legados e hash da embalagem verificados.");
