import {hyperframesArtSchema} from "./editorial-stage";

type Beat={anchor?:string;resolved_frame?:number;timing_source?:string};
/** Both authoring formats must bind states to unique beats before paid voice work. */
export function validateArtSource(source:string, config:unknown, beats:Beat[]) {
  const art=hyperframesArtSchema.parse(config);
  if(art.width%2||art.height%2)throw new Error("Dimensões do clipe devem ser pares.");
  if(!source.includes("<!--ODE_DATA-->")||!source.includes('data-composition-id="ode"'))throw new Error("Faltam contrato de dados e composição ode.");
  if(/https?:\/\/|Math\.random\s*\(|Date\.now\s*\(|setInterval\s*\(/.test(source))throw new Error("Runtime deve ser local e determinístico.");
  const supported=source.match(/data-ode-states="([a-z,]+)"/)?.[1].split(",");
  if(!supported?.includes(art.initial_state))throw new Error("Estado inicial não suportado pelo HTML.");
  for(const state of art.states){
    if(!supported.includes(state.state))throw new Error(`Estado não suportado: ${state.state}`);
    if(beats.filter(b=>b.anchor===state.anchor).length!==1)throw new Error(`Estado exige um único beat: ${state.anchor}`);
  }
  return art;
}
export function alignedArtStates(config:unknown, beats:Beat[], frames:number, fps:number) {
  const art=hyperframesArtSchema.parse(config);
  if(!Number.isInteger(frames)||frames<=0||fps!==30)throw new Error("Clipe exige timeline real em 30 fps.");
  let previous=-1;
  return art.states.map(state=>{
    const beat=beats.find(b=>b.anchor===state.anchor);
    const frame=beat?.resolved_frame;
    if(frame===undefined||!Number.isInteger(frame)||frame<0||frame>=frames||frame<=previous||!beat?.timing_source)throw new Error("Estado exige frame ordenado, dentro da cena e com proveniência.");
    previous=frame;
    return {...state,frame,timing_source:beat.timing_source};
  });
}
