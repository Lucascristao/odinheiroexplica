import {z} from "zod";
import {annotationSchema, chartSchema, emphasisSchema, fullView, regionSchema, type Emphasis, type Region} from "./editorial-evidence";

// Coordinates are percentages of the safe editorial canvas, not the full video.
const stageCameraSchema = z.object({
  x: z.number().min(0).max(100),
  y: z.number().min(0).max(100),
  zoom: z.number().min(1).max(1.6),
  motion_seconds: z.number().min(0.2).max(2).optional(),
});
const stageEntranceSchema = z.object({
  style: z.enum(["fade", "slide", "scale", "wipe"]),
  direction: z.enum(["left", "right", "up", "down"]).optional(),
});
const stageSustainSchema = z.object({
  kind: z.enum(["breathe", "drift", "float", "tilt"]),
  amplitude: z.number().min(0).max(12),
  period_seconds: z.number().min(2).max(12),
  phase: z.number().min(0).max(1).optional(),
});
const stageActuationSchema = z.enum(["tap", "lock", "unlock", "confirm", "signal", "dispense", "count"]);

export const stageElementSchema = z.object({
  id: z.string().min(1),
  kind: z.enum(["step", "label", "metric", "note", "photo", "object", "source_excerpt", "chart"]),
  chart: chartSchema.optional(),
  annotations: z.array(annotationSchema).max(16).default([]),
  asset_width: z.number().positive().optional(),
  asset_height: z.number().positive().optional(),
  overlay_on: z.string().optional(),
  text_region: regionSchema.optional(),
  label_size: z.number().min(32).max(120).optional(),
  value_size: z.number().min(48).max(260).default(72),
  object_type: z.enum(["wallet", "bank", "receipt", "component", "factory", "truck", "package", "atm", "cash", "branch", "hub", "data", "store", "phone", "terminal"]).optional(),
  label: z.string().min(1).max(80),
  detail: z.string().max(160).optional(),
  value: z.string().max(32).optional(),
  icon: z.enum(["bank", "wallet", "person", "search", "bell", "lock", "check", "refund", "shield", "warning", "clock", "phone", "receipt", "cart", "key", "eye-off", "route", "coins", "chart", "house", "car", "document", "globe"]).optional(),
  svg_motion: z.enum(["assemble", "trace", "none"]).optional(),
  sustain: stageSustainSchema.optional(),
  surface: z.enum(["none", "glow", "paper", "spotlight"]).optional(),
  x: z.number().min(0).max(100),
  y: z.number().min(0).max(100),
  width: z.number().min(8).max(100),
  height: z.number().min(8).max(100),
  initially_visible: z.boolean().default(true),
  asset_id: z.string().optional(),
  asset_file: z.string().optional(),
  photo_style: z.enum(["clean", "paper"]).default("clean"),
  image_fit: z.enum(["contain", "cover"]).default("contain"),
  focal_x: z.number().min(0).max(100).default(50),
  focal_y: z.number().min(0).max(100).default(50),
  image_motion: z.enum(["none", "push", "pan"]).default("none"),
});

export const visualOperationSchema = z.discriminatedUnion("kind", [
  z.object({kind:z.literal("equation"),input_ids:z.array(z.string().min(1)).min(2),operator:z.enum(["+","-","×","÷"]),result_id:z.string().min(1)}),
  z.object({kind:z.literal("compare"),element_ids:z.array(z.string().min(1)).min(2)}),
  z.object({kind:z.literal("stack"),element_ids:z.array(z.string().min(1)).min(2)}),
  z.object({kind:z.literal("meter"),value:z.number().finite(),min:z.number().finite(),max:z.number().finite(),unit:z.string().max(24).optional()}),
  z.object({kind:z.literal("signal"),status:z.enum(["positive","neutral","warning"]),message:z.string().min(1).max(80)}),
]);
export type VisualOperation = z.infer<typeof visualOperationSchema>;

export const editorialStageSchema = z.object({
  show_title: z.boolean().default(true),
  initial_camera: stageCameraSchema.optional(),
  // Automatic reframing is an author-selected tool, never a mandatory template.
  // Missing settings preserve the legacy identity/authored camera path.
  camera_mode: z.enum(["auto", "manual", "static"]).optional(),
  motion_profile: z.enum(["narrative", "static"]).default("narrative"),
  captions: z.object({
    enabled: z.boolean().default(true),
    max_words: z.union([z.literal(1), z.literal(2)]).default(2),
    font_size: z.number().min(72).max(140).default(104),
    preferred_side: z.enum(["auto", "left", "right", "center"]).default("auto"),
    region: regionSchema.optional(),
  }).optional(),
  elements: z.array(stageElementSchema).min(1).max(12),
  connections: z.array(z.object({
    id: z.string().min(1).optional(),
    from: z.string(),
    to: z.string(),
    label: z.string().max(40).optional(),
    from_port:z.enum(["auto","left","right","top","bottom"]).optional(),
    to_port:z.enum(["auto","left","right","top","bottom"]).optional(),
    label_region:regionSchema.optional(),
    token_label:z.string().min(1).max(8).optional(),
    label_position: z.enum(["auto", "above", "below", "left", "right", "between"]).default("auto"),
    label_size: z.number().min(30).max(42).default(32),
    semantic: z.enum(["relation", "transfer", "comparison", "cause", "sequence"]).default("relation"),
    motion: z.enum(["once", "flow", "pulse"]).default("once"),
    period_seconds: z.number().min(2).max(12).optional(),
  })).max(16).default([]),
}).superRefine((stage, ctx) => {
  const ids = new Set<string>();
  for (const [index, element] of stage.elements.entries()) {
    if (ids.has(element.id)) ctx.addIssue({code: "custom", path: ["elements", index, "id"], message: "ID visual duplicado."});
    ids.add(element.id);
    if(element.kind === "chart" && (!element.chart || element.width<60 || element.height<50))ctx.addIssue({code:"custom",path:["elements",index],message:"Gráfico exige dados e região de pelo menos 60% × 50%."});
    if(new Set(element.annotations.map(a=>a.id)).size !== element.annotations.length)ctx.addIssue({code:"custom",path:["elements",index],message:"Marcação com ID duplicado."});
    if(element.annotations.length && element.kind!=="source_excerpt")ctx.addIssue({code:"custom",path:["elements",index],message:"Marcações por região pertencem a recortes."});
    if(element.overlay_on){
      const parent=stage.elements.find(e=>e.id===element.overlay_on);
      const region=parent?.text_region;
      if(!parent || !region || !["photo","object"].includes(parent.kind) || !["label","metric"].includes(element.kind) || element.detail || element.icon || parent.overlay_on || element.x<parent.x+region.x*parent.width/100 || element.y<parent.y+region.y*parent.height/100 || element.x+element.width>parent.x+(region.x+region.width)*parent.width/100 || element.y+element.height>parent.y+(region.y+region.height)*parent.height/100)ctx.addIssue({code:"custom",path:["elements",index],message:"Camada de texto precisa caber na região reservada de uma foto/objeto, sem ícone ou detalhe."});
    }
    if (element.kind === "object" && !element.object_type) ctx.addIssue({code: "custom", path: ["elements", index, "object_type"], message: "Objeto precisa de object_type."});
    if(element.svg_motion==="assemble"&&element.kind!=="object")ctx.addIssue({code:"custom",path:["elements",index,"svg_motion"],message:"Montagem por partes exige um objeto SVG; ícones usam trace ou none."});
    if(element.surface==="paper" && !["photo","object"].includes(element.kind))ctx.addIssue({code:"custom",path:["elements",index,"surface"],message:"Papel claro é suporte da mídia/objeto, sem colocar texto branco sobre papel."});
    if(element.sustain && !["photo","object"].includes(element.kind) && !element.icon && !["glow","spotlight"].includes(element.surface??""))ctx.addIssue({code:"custom",path:["elements",index,"sustain"],message:"Sustentação move mídia/ícone ou iluminação autoral; rótulos, números e documentos permanecem estáveis para leitura."});
    if (element.x + element.width > 100 || element.y + element.height > 100) {
      ctx.addIssue({code: "custom", path: ["elements", index], message: "Elemento fora da área segura."});
    }
    if (["photo", "source_excerpt"].includes(element.kind) && !element.asset_id) {
      ctx.addIssue({code: "custom", path: ["elements", index, "asset_id"], message: "Foto precisa de asset_id."});
    }
    for (const previous of stage.elements.slice(0, index)) {
      if(element.overlay_on===previous.id || previous.overlay_on===element.id)continue;
      // Reserve space even for initially hidden elements: revealing a note must
      // never cover a previously visible fact. Layered photography is a separate treatment.
      if (element.x < previous.x + previous.width && element.x + element.width > previous.x &&
          element.y < previous.y + previous.height && element.y + element.height > previous.y) {
        ctx.addIssue({code: "custom", path: ["elements", index], message: `Região colide com ${previous.id}. Reserve espaço para cada elemento.`});
      }
    }
  }
  for (const [index, edge] of stage.connections.entries()) {
    if (edge.id && stage.connections.slice(0,index).some(previous=>previous.id===edge.id)) ctx.addIssue({code:"custom",path:["connections",index,"id"],message:"ID de conexão duplicado."});
    if (!ids.has(edge.from) || !ids.has(edge.to) || edge.from === edge.to) {
      ctx.addIssue({code: "custom", path: ["connections", index], message: "Conexão precisa de dois alvos existentes e distintos."});
    }
  }
});

export const stageEventFields = {
  operation: visualOperationSchema.optional(),
  motion_seconds: z.number().min(0.1).max(2).optional(),
  camera: stageCameraSchema.optional(),
  camera_mode: z.enum(["auto", "hold"]).optional(),
  entrance: stageEntranceSchema.optional(),
  actuation: stageActuationSchema.optional(),
  mark_ids: z.array(z.string()).max(16).optional(),
  view: regionSchema.optional(),
  emphasis: emphasisSchema.nullable().optional(),
  chart_focus: z.object({from:z.number().int().min(0),to:z.number().int().min(0)}).nullable().optional(),
  target_id: z.string().optional(),
  action: z.enum(["focus", "reveal", "update", "retire"]).default("focus"),
  prominence: z.enum(["support", "contextual", "takeover"]).default("contextual"),
  takeover_reason: z.string().min(10).optional(),
  reveal_ids: z.array(z.string()).default([]),
  retire_ids: z.array(z.string()).default([]),
  moves: z.array(z.object({id: z.string(), x: z.number().min(0).max(100), y: z.number().min(0).max(100)})).default([]),
};

export type EditorialStage = z.infer<typeof editorialStageSchema>;
export type StageElement = z.infer<typeof stageElementSchema>;
export type StageEvent = {
  operation?: VisualOperation;
  treatment?: "kinetic_type" | "giant_number" | "flow_diagram" | "timeline" | "split_compare" | "meter" | "spotlight" | "equation" | "stack" | "signal" | "masked_emphasis" | "depth_photo";
  motion_seconds?: number;
  camera?: StageCamera;
  camera_mode?: "auto" | "hold";
  entrance?: z.infer<typeof stageEntranceSchema>;
  actuation?: z.infer<typeof stageActuationSchema>;
  mark_ids?: string[];
  view?: Region;
  emphasis?: Emphasis | null;
  chart_focus?: {from:number;to:number} | null;
  target_id?: string;
  action?: "focus" | "reveal" | "update" | "retire";
  prominence?: "support" | "contextual" | "takeover";
  takeover_reason?: string;
  reveal_ids?: string[];
  retire_ids?: string[];
  moves?: {id: string; x: number; y: number}[];
  headline: string;
  detail?: string;
  value?: string;
  resolved_frame?: number;
};

export type StageCamera = z.infer<typeof stageCameraSchema>;

export const stageMotionSeconds = (beat: StageEvent) => beat.motion_seconds ?? 0.45;

// A word sequence stays in the measured lines; only visibility/transforms change.
// It finishes inside the authored cue so the following interval is a reading hold.
export function kineticWordProgress(progress: number, index: number, count: number) {
  const start = count <= 1 ? 0 : 0.42 * index / Math.max(1, count - 1);
  const p = Math.max(0, Math.min(1, (progress - start) / 0.58));
  return p * p * (3 - 2 * p);
}

// Informational elements enter the camera as whole units. Cropping a future
// metric or label at the edge makes it look like damaged content.
export function fitsStageCamera(region: {x: number; y: number; width: number; height: number}, camera: StageCamera): boolean {
  const left = 50 + (region.x - camera.x) * camera.zoom;
  const top = 50 + (region.y - camera.y) * camera.zoom;
  const right = left + region.width * camera.zoom;
  const bottom = top + region.height * camera.zoom;
  return left >= -0.001 && top >= -0.001 && right <= 100.001 && bottom <= 100.001;
}

// Fade only inside a complete frame. Looking in both directions gives a smooth
// entrance/exit while keeping frame evaluation independent of render order.
export function stageCameraVisibility(fitsAtFrame: (frame: number) => boolean, frame: number, fadeFrames: number): number {
  if (!fitsAtFrame(frame)) return 0;
  const duration = Math.max(1, Math.round(fadeFrames));
  let progress = 1;
  for (let offset = 1; offset < duration; offset++) {
    if (!fitsAtFrame(frame - offset) || !fitsAtFrame(frame + offset)) {
      progress = offset / duration;
      break;
    }
  }
  return progress * progress * (3 - 2 * progress);
}

// Opt-in auto shots consider the complete already-presented group. The layout
// solver additionally protects routes, operators, raster captions and each
// intermediate frame. It never hides context just to manufacture a close-up.
function automaticCamera(stage: EditorialStage, beats: StageEvent[], beat: StageEvent, fps: number): StageCamera {
  const state = resolveStage(stage, beats, beat.resolved_frame!, fps);
  const visible = state.elements.filter(e => e.visible);
  if (!visible.length) return {x: 50, y: 50, zoom: 1};
  const regions = visible.flatMap(e => {
    const move = beat.moves?.find(m => m.id === e.id);
    return move ? [e,{...e, x: move.x, y: move.y}] : [e];
  });
  const left = Math.min(...regions.map(e => e.x));
  const top = Math.min(...regions.map(e => e.y));
  const right = Math.max(...regions.map(e => e.x + e.width));
  const bottom = Math.max(...regions.map(e => e.y + e.height));
  const zoom = Math.max(1, Math.min(beat.operation ? 1.1 : 1.2, 100 / (right - left + 6), 100 / (bottom - top + 6)));
  const target = regions.find(e => e.id === beat.target_id);
  const centerX = (left + right) / 2, centerY = (top + bottom) / 2;
  const desiredX = target && !beat.operation ? centerX * 0.7 + (target.x + target.width / 2) * 0.3 : centerX;
  const desiredY = target && !beat.operation ? centerY * 0.7 + (target.y + target.height / 2) * 0.3 : centerY;
  const safe = (desired: number, min: number, max: number) => Math.max(max - 50 / zoom, Math.min(min + 50 / zoom, desired));
  return {x: safe(desiredX, left, right), y: safe(desiredY, top, bottom), zoom};
}

// Finite cues, followed by a hold. Pure frame evaluation remains reproducible
// when Remotion renders frames in parallel or in a different order.
export function resolveStageCamera(stage: EditorialStage, beats: StageEvent[], frame: number, fps=30): StageCamera {
  const initial = stage.initial_camera ?? {x: 50, y: 50, zoom: 1};
  const mode = stage.camera_mode ?? (stage.motion_profile === "static" ? "static" : "manual");
  if (mode === "static") return {...initial};
  let camera: StageCamera = {...initial};
  const ordered = beats.filter(beat => Number.isFinite(beat.resolved_frame)).slice().sort((a,b) => a.resolved_frame! - b.resolved_frame!);
  let previousEnd = 0;
  const candidates = ordered.flatMap(beat => {
    if (beat.camera_mode === "hold") return [];
    const auto = !beat.camera && (mode === "auto" || beat.camera_mode === "auto");
    const destination = beat.camera ?? (auto && beat.action !== "retire" && beat.prominence !== "support" ? automaticCamera(stage, ordered, beat, fps) : undefined);
    if (!destination) return [];
    let start = beat.resolved_frame!, duration = (destination.motion_seconds ?? 0.9) * fps;
    // Open room before an opt-in reveal; its future content stays hidden until
    // the speech anchor. This avoids a camera snap when a distant item enters.
    if (auto && (beat.action === "reveal" || beat.reveal_ids?.length)) {
      start = Math.min(beat.resolved_frame!,Math.max(previousEnd, start-duration));
      duration = Math.max(1, beat.resolved_frame!-start);
    }
    previousEnd = start+duration;
    return [{start, duration, destination}];
  });
  const cues=candidates.map((cue,index)=>({...cue,duration:Math.max(1,Math.min(cue.duration,(candidates[index+1]?.start??Infinity)-cue.start))}));
  for (const cue of cues) {
    if (cue.start > frame) break;
    const p = Math.max(0, Math.min(1, (frame - cue.start) / cue.duration));
    const eased = p * p * (3 - 2 * p);
    camera = {x: camera.x + (cue.destination.x - camera.x) * eased, y: camera.y + (cue.destination.y - camera.y) * eased, zoom: camera.zoom + (cue.destination.zoom - camera.zoom) * eased};
  }
  return camera;
}

export function validateStageEvents(stage: EditorialStage, beats: StageEvent[]): string[] {
  const ids = new Set(stage.elements.map((element) => element.id));
  const errors: string[] = [];
  const visible = new Set(stage.elements.filter((e) => e.initially_visible).map((e) => e.id));
  const layout = stage.elements.map(e => ({...e}));
  for (const [index, beat] of beats.entries()) {
    if(beat.camera&&beat.camera_mode==="hold")errors.push(`Beat ${index}: camera e camera_mode hold são instruções contraditórias; escolha mover ou manter o plano.`);
    const target=layout.find(e=>e.id===beat.target_id);
    if(target){
      if(beat.action==="update"){target.label=beat.headline;}
      if(beat.emphasis && (!target.label.includes(beat.emphasis.phrase) || target.label.split(beat.emphasis.phrase).length!==2 || !["label","note","step","metric"].includes(target.kind)))errors.push(`Beat ${index}: frase de marcação precisa ser única no rótulo de texto.`);
      if(beat.view && target.kind!=="source_excerpt")errors.push(`Beat ${index}: enquadramento regional exige recorte.`);
      if(beat.mark_ids && (target.kind!=="source_excerpt" || beat.mark_ids.some(id=>!target.annotations.some(a=>a.id===id))))errors.push(`Beat ${index}: marcação inexistente ou alvo incompatível.`);
      if(beat.chart_focus && (target.kind!=="chart" || !target.chart || beat.chart_focus.from>beat.chart_focus.to || beat.chart_focus.to>=target.chart.points.length))errors.push(`Beat ${index}: intervalo de gráfico inválido.`);
      if(beat.actuation && !target.icon && target.kind!=="object")errors.push(`Beat ${index}: atuação exige ícone ou objeto SVG; não modifica texto, números nem provas.`);
      if(beat.actuation==="dispense" && target.object_type!=="atm")errors.push(`Beat ${index}: saída de cédulas exige objeto ATM.`);
      if(beat.actuation==="count" && target.object_type!=="cash" && target.icon!=="coins")errors.push(`Beat ${index}: contagem visual exige dinheiro esquemático, sem inventar valores.`);
      if((beat.actuation==="lock"||beat.actuation==="unlock") && target.kind!=="object" && !["lock","key"].includes(target.icon??""))errors.push(`Beat ${index}: abrir/fechar exige objeto SVG, cadeado ou chave.`);
    }
    if (!beat.target_id || !ids.has(beat.target_id)) errors.push(`Beat ${index}: target_id inexistente.`);
    for (const id of [...(beat.reveal_ids ?? []), ...(beat.retire_ids ?? [])]) {
      if (!ids.has(id)) errors.push(`Beat ${index}: referência inexistente ${id}.`);
    }
    for (const id of beat.reveal_ids ?? []) visible.add(id);
    if (beat.action === "reveal" && beat.target_id) visible.add(beat.target_id);
    for (const id of beat.retire_ids ?? []) visible.delete(id);
    if (beat.action === "retire" && beat.target_id) visible.delete(beat.target_id);
    if (beat.target_id && beat.action !== "retire" && !visible.has(beat.target_id)) errors.push(`Beat ${index}: alvo oculto; revele antes de destacar.`);
    if (beat.prominence === "takeover" && !beat.takeover_reason) errors.push(`Beat ${index}: takeover exige justificativa.`);
    if (beat.prominence === "takeover" && beats[index - 1]?.prominence === "takeover") errors.push(`Beat ${index}: takeovers consecutivos.`);
    const before = layout.map(e => ({...e}));
    for (const move of beat.moves ?? []) {
      const element = layout.find(e => e.id === move.id);
      if (!element) errors.push(`Beat ${index}: movimento referencia ${move.id} inexistente.`);
      else {element.x = move.x; element.y = move.y;}
    }
    if (beat.camera && beat.action !== "retire") {
      const subject = layout.find(e => e.id === beat.target_id);
      if (subject) {
        const {x, y, zoom} = beat.camera;
        const left = 50 + zoom * (subject.x - x);
        const right = 50 + zoom * (subject.x + subject.width - x);
        const top = 50 + zoom * (subject.y - y);
        const bottom = 50 + zoom * (subject.y + subject.height - y);
        if (left < 0 || right > 100 || top < 0 || bottom > 100) {
          errors.push(`Beat ${index}: câmera corta o alvo ${subject.id} fora da área segura.`);
        }
      }
    }
    // Check the movement corridor, not just its endpoints. Linear motion is
    // deliberately bounded and does not overshoot its reserved area.
    for (let sample = 0; sample <= 20 && beat.moves?.length; sample++) {
      const t = sample/20;
      const positions = layout.map((e, i) => ({...e, x: before[i].x+(e.x-before[i].x)*t, y: before[i].y+(e.y-before[i].y)*t}));
      if (!editorialStageSchema.safeParse({...stage, elements: positions}).success) {
        errors.push(`Beat ${index}: movimento sai da área segura ou cruza outra região.`); break;
      }
    }
  }
  return errors;
}

// Pure frame evaluation works with parallel/out-of-order Remotion rendering.
// Events preserve element identity and previous values until explicitly changed.
export function resolveStage(stage: EditorialStage, beats: StageEvent[], frame: number, fps=30) {
  const elements = stage.elements.map((element) => ({...element, motionProfile:stage.motion_profile, entrance:undefined as StageEvent["entrance"], actuation:undefined as StageEvent["actuation"], actuationFrame:0, actuationDuration:fps*0.9, locked:undefined as boolean|undefined, lockFrom:true, lockFrame:0, lockDuration:fps*0.75, visible: element.initially_visible !== false, wasVisible: element.initially_visible !== false, changedAt: 0, cueFrame:0, cueDuration:fps*0.45, cueAction:undefined as StageEvent["action"], treatment:undefined as StageEvent["treatment"], visibilityDuration:fps*0.35, markIds:[] as string[], markTiming:{} as Record<string,{frame:number;duration:number}>, emphasisTiming:{frame:0,duration:1}, view:{...fullView}, emphasis:null as Emphasis|null, chartFocus:null as {from:number;to:number}|null}));
  let active: StageEvent | undefined;
  const ordered = beats.filter((b) => Number.isFinite(b.resolved_frame)).slice().sort((a, b) => a.resolved_frame! - b.resolved_frame!);
  for (const [index, beat] of ordered.entries()) {
    if (beat.resolved_frame! > frame) break;
    active = beat;
    const motionFrames = Math.max(1, Math.min(stageMotionSeconds(beat)*fps, (ordered[index+1]?.resolved_frame ?? Infinity) - beat.resolved_frame!));
    const p = Math.min(1, Math.max(0, (frame-beat.resolved_frame!)/motionFrames));
    const eased = stage.motion_profile === "static" ? 1 : p*p*(3-2*p);
    for (const element of elements) {
      const move = beat.moves?.find(m => m.id === element.id);
      if (move) {element.x += (move.x-element.x)*eased; element.y += (move.y-element.y)*eased;}
      let visible = element.visible;
      if (beat.reveal_ids?.includes(element.id)) visible = true;
      if (beat.retire_ids?.includes(element.id)) visible = false;
      if (element.id === beat.target_id) {
        element.cueFrame=beat.resolved_frame!; element.cueDuration=motionFrames;
        element.cueAction=beat.action; element.treatment=beat.treatment;
        element.entrance=beat.entrance;
        if(beat.actuation){element.actuation=beat.actuation;element.actuationFrame=beat.resolved_frame!;element.actuationDuration=Math.max(motionFrames,fps*0.75);}
        if(beat.actuation==="lock"||beat.actuation==="unlock"){element.lockFrom=element.locked??true;element.locked=beat.actuation==="lock";element.lockFrame=beat.resolved_frame!;element.lockDuration=Math.max(motionFrames,fps*0.75);}
        if(beat.mark_ids!==undefined){element.markTiming=Object.fromEntries(beat.mark_ids.map(id=>[id,element.markTiming[id]??{frame:beat.resolved_frame!,duration:motionFrames}]));element.markIds=beat.mark_ids;}
        if(beat.emphasis!==undefined){element.emphasis=beat.emphasis;element.emphasisTiming={frame:beat.resolved_frame!,duration:motionFrames};}
        if(beat.chart_focus!==undefined)element.chartFocus=beat.chart_focus;
        if(beat.view)element.view={x:element.view.x+(beat.view.x-element.view.x)*eased,y:element.view.y+(beat.view.y-element.view.y)*eased,width:element.view.width+(beat.view.width-element.view.width)*eased,height:element.view.height+(beat.view.height-element.view.height)*eased};
        if (beat.action === "reveal") visible = true;
        if (beat.action === "retire") visible = false;
        if (beat.action === "update") {
          if(beat.emphasis===undefined)element.emphasis=null;
          element.label = beat.headline;
          if (beat.detail !== undefined) element.detail = beat.detail;
          if (beat.value !== undefined) element.value = beat.value;
        }
      }
      if (visible !== element.visible) {element.changedAt = beat.resolved_frame!; element.wasVisible = element.visible; element.visibilityDuration=motionFrames; element.entrance=beat.entrance;}
      element.visible = visible;
    }
  }
  return {elements, active};
}
