import {z} from "zod";

// Coordinates are percentages of the safe editorial canvas, not the full video.
export const stageElementSchema = z.object({
  id: z.string().min(1),
  kind: z.enum(["step", "label", "metric", "note", "photo", "object"]),
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
    if (element.kind === "object" && !element.object_type) ctx.addIssue({code: "custom", path: ["elements", index, "object_type"], message: "Objeto precisa de object_type."});
    if (element.x + element.width > 100 || element.y + element.height > 100) {
      ctx.addIssue({code: "custom", path: ["elements", index], message: "Elemento fora da área segura."});
    }
    if (element.kind === "photo" && !element.asset_id) {
      ctx.addIssue({code: "custom", path: ["elements", index, "asset_id"], message: "Foto precisa de asset_id."});
    }
    for (const previous of stage.elements.slice(0, index)) {
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

export function validateStageEvents(stage: EditorialStage, beats: StageEvent[]): string[] {
  const ids = new Set(stage.elements.map((element) => element.id));
  const errors: string[] = [];
  const visible = new Set(stage.elements.filter((e) => e.initially_visible).map((e) => e.id));
  const layout = stage.elements.map(e => ({...e}));
  for (const [index, beat] of beats.entries()) {
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
export function resolveStage(stage: EditorialStage, beats: StageEvent[], frame: number) {
  const elements = stage.elements.map((element) => ({...element, visible: element.initially_visible !== false, wasVisible: element.initially_visible !== false, changedAt: 0}));
  let active: StageEvent | undefined;
  const ordered = beats.filter((b) => Number.isFinite(b.resolved_frame)).slice().sort((a, b) => a.resolved_frame! - b.resolved_frame!);
  for (const [index, beat] of ordered.entries()) {
    if (beat.resolved_frame! > frame) break;
    active = beat;
    const motionFrames = Math.max(1, Math.min(18, (ordered[index+1]?.resolved_frame ?? Infinity) - beat.resolved_frame!));
    const p = Math.min(1, Math.max(0, (frame-beat.resolved_frame!)/motionFrames));
    const eased = p*p*(3-2*p);
    for (const element of elements) {
      const move = beat.moves?.find(m => m.id === element.id);
      if (move) {element.x += (move.x-element.x)*eased; element.y += (move.y-element.y)*eased;}
      let visible = element.visible;
      if (beat.reveal_ids?.includes(element.id)) visible = true;
      if (beat.retire_ids?.includes(element.id)) visible = false;
      if (element.id === beat.target_id) {
        if (beat.action === "reveal") visible = true;
        if (beat.action === "retire") visible = false;
        if (beat.action === "update") {
          element.label = beat.headline;
          if (beat.detail !== undefined) element.detail = beat.detail;
          if (beat.value !== undefined) element.value = beat.value;
        }
      }
      if (visible !== element.visible) {element.changedAt = beat.resolved_frame!; element.wasVisible = element.visible;}
      element.visible = visible;
    }
  }
  return {elements, active};
}
