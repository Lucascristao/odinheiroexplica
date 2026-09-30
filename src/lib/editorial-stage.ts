import {z} from "zod";
import {annotationSchema, chartSchema, emphasisSchema, fullView, regionSchema, type Emphasis, type Region} from "./editorial-evidence";

// Coordinates are percentages of the safe editorial canvas, not the full video.
const stageCameraSchema = z.object({
  x: z.number().min(0).max(100),
  y: z.number().min(0).max(100),
  zoom: z.number().min(1).max(1.6),
  motion_seconds: z.number().min(0.2).max(2).optional(),
});

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
  object_type: z.enum(["wallet", "bank", "receipt"]).optional(),
  label: z.string().min(1).max(80),
  detail: z.string().max(160).optional(),
  value: z.string().max(32).optional(),
  icon: z.enum(["bank", "wallet", "person", "search", "bell", "lock", "check", "refund", "shield", "warning", "clock", "phone", "receipt", "cart", "key", "eye-off", "route", "coins", "chart", "house", "car", "document", "globe"]).optional(),
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

export const editorialStageSchema = z.object({
  show_title: z.boolean().default(true),
  initial_camera: stageCameraSchema.optional(),
  elements: z.array(stageElementSchema).min(1).max(12),
  connections: z.array(z.object({
    from: z.string(),
    to: z.string(),
    label: z.string().max(40).optional(),
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
    if (!ids.has(edge.from) || !ids.has(edge.to) || edge.from === edge.to) {
      ctx.addIssue({code: "custom", path: ["connections", index], message: "Conexão precisa de dois alvos existentes e distintos."});
    }
  }
});

export const stageEventFields = {
  motion_seconds: z.number().min(0.1).max(2).default(0.45),
  camera: stageCameraSchema.optional(),
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
  motion_seconds?: number;
  camera?: StageCamera;
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

// Camera cues share the same frame clock as the stage. A cue reaches its
// destination before the next camera cue, so parallel Remotion workers resolve
// identical positions regardless of frame order. Without cues, this is identity.
export function resolveStageCamera(stage: EditorialStage, beats: StageEvent[], frame: number, fps=30): StageCamera {
  let camera: StageCamera = stage.initial_camera ?? {x: 50, y: 50, zoom: 1};
  const cues = beats.filter((beat) => beat.camera && Number.isFinite(beat.resolved_frame))
    .slice().sort((a, b) => a.resolved_frame! - b.resolved_frame!);
  for (const [index, beat] of cues.entries()) {
    if (beat.resolved_frame! > frame) break;
    const nextFrame = cues[index + 1]?.resolved_frame ?? Infinity;
    const duration = Math.max(1, Math.min((beat.camera!.motion_seconds ?? 0.9) * fps, nextFrame - beat.resolved_frame!));
    const p = Math.min(1, Math.max(0, (frame - beat.resolved_frame!) / duration));
    const eased = p * p * (3 - 2 * p);
    camera = {
      x: camera.x + (beat.camera!.x - camera.x) * eased,
      y: camera.y + (beat.camera!.y - camera.y) * eased,
      zoom: camera.zoom + (beat.camera!.zoom - camera.zoom) * eased,
    };
  }
  return camera;
}

export function validateStageEvents(stage: EditorialStage, beats: StageEvent[]): string[] {
  const ids = new Set(stage.elements.map((element) => element.id));
  const errors: string[] = [];
  const visible = new Set(stage.elements.filter((e) => e.initially_visible).map((e) => e.id));
  const layout = stage.elements.map(e => ({...e}));
  for (const [index, beat] of beats.entries()) {
    const target=layout.find(e=>e.id===beat.target_id);
    if(target){
      if(beat.action==="update"){target.label=beat.headline;}
      if(beat.emphasis && (!target.label.includes(beat.emphasis.phrase) || target.label.split(beat.emphasis.phrase).length!==2 || !["label","note","step","metric"].includes(target.kind)))errors.push(`Beat ${index}: frase de marcação precisa ser única no rótulo de texto.`);
      if(beat.view && target.kind!=="source_excerpt")errors.push(`Beat ${index}: enquadramento regional exige recorte.`);
      if(beat.mark_ids && (target.kind!=="source_excerpt" || beat.mark_ids.some(id=>!target.annotations.some(a=>a.id===id))))errors.push(`Beat ${index}: marcação inexistente ou alvo incompatível.`);
      if(beat.chart_focus && (target.kind!=="chart" || !target.chart || beat.chart_focus.from>beat.chart_focus.to || beat.chart_focus.to>=target.chart.points.length))errors.push(`Beat ${index}: intervalo de gráfico inválido.`);
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
  const elements = stage.elements.map((element) => ({...element, visible: element.initially_visible !== false, wasVisible: element.initially_visible !== false, changedAt: 0, cueFrame:0, cueDuration:fps*0.45, visibilityDuration:fps*0.35, markIds:[] as string[], markTiming:{} as Record<string,{frame:number;duration:number}>, emphasisTiming:{frame:0,duration:1}, view:{...fullView}, emphasis:null as Emphasis|null, chartFocus:null as {from:number;to:number}|null}));
  let active: StageEvent | undefined;
  const ordered = beats.filter((b) => Number.isFinite(b.resolved_frame)).slice().sort((a, b) => a.resolved_frame! - b.resolved_frame!);
  for (const [index, beat] of ordered.entries()) {
    if (beat.resolved_frame! > frame) break;
    active = beat;
    const motionFrames = Math.max(1, Math.min((beat.motion_seconds??0.45)*fps, (ordered[index+1]?.resolved_frame ?? Infinity) - beat.resolved_frame!));
    const p = Math.min(1, Math.max(0, (frame-beat.resolved_frame!)/motionFrames));
    const eased = p*p*(3-2*p);
    for (const element of elements) {
      const move = beat.moves?.find(m => m.id === element.id);
      if (move) {element.x += (move.x-element.x)*eased; element.y += (move.y-element.y)*eased;}
      let visible = element.visible;
      if (beat.reveal_ids?.includes(element.id)) visible = true;
      if (beat.retire_ids?.includes(element.id)) visible = false;
      if (element.id === beat.target_id) {
        element.cueFrame=beat.resolved_frame!; element.cueDuration=motionFrames;
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
      if (visible !== element.visible) {element.changedAt = beat.resolved_frame!; element.wasVisible = element.visible; element.visibilityDuration=motionFrames;}
      element.visible = visible;
    }
  }
  return {elements, active};
}
