import {editorialStageSchema, resolveStageCamera, type StageCamera} from "./editorial-stage";

export type EditorialDirectionIssue = {
  severity: "error" | "warning";
  code: string;
  scene_id?: string;
  beat_index?: number;
  element_id?: string;
  message: string;
};

const textKinds = new Set(["label", "note", "step", "metric"]);
const operationTreatments: Record<string, string> = {equation: "equation", split_compare: "compare", stack: "stack", meter: "meter", signal: "signal"};
const differentCamera = (a: StageCamera, b: StageCamera) => Math.abs(a.x - b.x) > .001 || Math.abs(a.y - b.y) > .001 || Math.abs(a.zoom - b.zoom) > .001;

// The renderer's camera resolver answers whether the authored shot changes.
// Ordered planning frames do not pretend to measure speech synchronization.
function plannedCameraChanges(rawStage: any, beats: any[]) {
  const parsed = editorialStageSchema.safeParse(rawStage);
  if (!parsed.success) return [] as number[]; // Structural validation reports this.
  const planned = beats.map((beat, index) => ({...beat, resolved_frame: index * 90}));
  let previous = parsed.data.initial_camera ?? {x: 50, y: 50, zoom: 1};
  return planned.flatMap((beat, index) => {
    const camera = resolveStageCamera(parsed.data, planned.slice(0, index + 1), beat.resolved_frame + 61);
    const changed = differentCamera(previous, camera);
    previous = camera;
    return changed ? [index] : [];
  });
}

type FrameWindow = {start: number; end: number};
const roundedSeconds = (frames: number, fps: number) => Math.round(frames / fps * 100) / 100;

function quietWindows(windows: FrameWindow[], duration: number): FrameWindow[] {
  const ordered = windows.map(w => ({start: Math.max(0, w.start), end: Math.min(duration, w.end)}))
    .filter(w => w.end > w.start).sort((a, b) => a.start - b.start);
  const gaps: FrameWindow[] = [];
  let cursor = 0;
  for (const window of ordered) {
    if (window.start > cursor) gaps.push({start: cursor, end: window.start});
    cursor = Math.max(cursor, window.end);
  }
  if (cursor < duration) gaps.push({start: cursor, end: duration});
  return gaps;
}

function visibilityWindows(stage: any, beats: any[], id: string, duration: number): FrameWindow[] {
  const element = stage.elements?.find((e: any) => e.id === id);
  if (!element) return [];
  let visible = element.initially_visible !== false;
  let start = 0;
  const windows: FrameWindow[] = [];
  for (const beat of beats) {
    const reveal = beat.reveal_ids?.includes(id) || (beat.target_id === id && beat.action === "reveal");
    const retire = beat.retire_ids?.includes(id) || (beat.target_id === id && beat.action === "retire");
    if (reveal && !visible) {start = beat.resolved_frame; visible = true;}
    if (retire && visible) {windows.push({start, end: beat.resolved_frame}); visible = false;}
  }
  if (visible) windows.push({start, end: duration});
  return windows;
}

// Contract timing describes possible holds, never perceived motion in the MP4.
// No invented seconds are emitted before the scene has a resolved timeline.
function rhythmDiagnostics(stage: any, scene: any, beats: any[], motionIndices: Set<number>, transformationIndices: Set<number>, fps: number) {
  const duration = scene.duration_frames;
  const ordered = beats.map((beat, index) => ({...beat, index})).sort((a, b) => a.resolved_frame - b.resolved_frame);
  const timingReady = Number.isFinite(duration) && duration > 0 && beats.every(beat => Number.isFinite(beat.resolved_frame)) && fps > 0;
  const base = {timing: timingReady ? "resolved-contract" : "pending-audio", transformations: transformationIndices.size};
  if (!timingReady) return {...base, quiet_visual_intervals: null, longest_without_visual_events_seconds: null, longest_without_transformation_seconds: null};
  const motion: FrameWindow[] = [];
  const transformations: FrameWindow[] = [];
  if (stage.motion_profile !== "static" && stage.elements?.some((e: any) => e.initially_visible !== false)) motion.push({start: 0, end: fps * .35});
  for (const beat of ordered) {
    const nextFrame = ordered.find((next: any) => next.resolved_frame > beat.resolved_frame)?.resolved_frame ?? duration;
    const end = Math.min(nextFrame, beat.resolved_frame + (beat.motion_seconds ?? .45) * fps);
    if (transformationIndices.has(beat.index)) transformations.push({start: beat.resolved_frame, end});
    if (stage.motion_profile !== "static" && motionIndices.has(beat.index)) {
      const connected = stage.connections?.some((edge: any) => edge.from === beat.target_id || edge.to === beat.target_id);
      const motionEnd = Math.max(end, beat.camera ? beat.resolved_frame + (beat.camera.motion_seconds ?? .9) * fps : end,
        connected && beat.action !== "retire" ? beat.resolved_frame + Math.max(beat.motion_seconds ?? .45, 1.15) * fps : end);
      motion.push({start: beat.resolved_frame, end: Math.min(duration, motionEnd)});
    }
  }
  if (stage.motion_profile !== "static") {
    for (const element of stage.elements ?? []) {
      const windows = visibilityWindows(stage, ordered, element.id, duration);
      if (element.sustain?.amplitude > 0) motion.push(...windows);
      if (["push", "pan"].includes(element.image_motion)) motion.push(...windows.map(window => ({start: window.start, end: Math.min(window.end, window.start + fps * (element.image_motion === "push" ? 8 : 12))})));
    }
    for (const edge of stage.connections ?? []) if (["flow", "pulse"].includes(edge.motion)) {
      const from = visibilityWindows(stage, ordered, edge.from, duration), to = visibilityWindows(stage, ordered, edge.to, duration);
      for (const a of from) for (const b of to) motion.push({start: Math.max(a.start, b.start), end: Math.min(a.end, b.end)});
    }
  }
  if (stage.captions?.enabled) for (const token of scene.audio_captions ?? []) {
    if (Number.isFinite(token.start_frame) && Number.isFinite(token.end_frame)) motion.push({start: token.start_frame, end: token.end_frame});
  }
  const gaps = quietWindows(motion, duration);
  const semanticGaps = quietWindows(transformations, duration);
  return {...base,
    quiet_visual_intervals: gaps.map(w => ({from_seconds: roundedSeconds(w.start, fps), to_seconds: roundedSeconds(w.end, fps), duration_seconds: roundedSeconds(w.end - w.start, fps)})),
    longest_without_visual_events_seconds: roundedSeconds(Math.max(0, ...gaps.map(w => w.end - w.start)), fps),
    longest_without_transformation_seconds: roundedSeconds(Math.max(0, ...semanticGaps.map(w => w.end - w.start)), fps),
  };
}

// Errors mean an explicitly selected capability has no executable data.
// Diagnostics never choose a topic, composition, camera path or effect quota.
export function summarizeEditorialDirection(project: any) {
  const issues: EditorialDirectionIssue[] = [];
  const rawScenes = project.scenes ?? project.script?.scenes ?? [];
  const scenes = rawScenes.map((scene: any, sceneIndex: number) => {
    const stage = scene.visual?.stage;
    const beats = scene.visual?.beats ?? [];
    const cues = scene.tts?.cues ?? [];
    const sceneId = String(scene.id ?? scene.index ?? sceneIndex);
    const cameraChanges = stage ? plannedCameraChanges(stage, beats) : [];
    const add = (severity: EditorialDirectionIssue["severity"], code: string, message: string, beat_index?: number, element_id?: string) => issues.push({severity, code, scene_id: sceneId, beat_index, element_id, message: `Cena ${sceneId}${beat_index === undefined ? "" : `, beat ${beat_index}`}${element_id ? `, elemento ${element_id}` : ""}: ${message}`});
    let effectiveMoves = 0;
    const transformationIndices = new Set<number>();
    const motionIndices = new Set<number>(cameraChanges);
    let activeOperation: any;
    const elements = new Map<string, any>((stage?.elements ?? []).map((e: any) => [e.id, {...e}]));
    const positions = new Map<string, {x: number; y: number}>((stage?.elements ?? []).map((e: any) => [e.id, {x: e.x, y: e.y}]));
    const visible = new Set<string>((stage?.elements ?? []).filter((e: any) => e.initially_visible !== false).map((e: any) => e.id));
    for (const [index, beat] of beats.entries()) {
      for (const move of beat.moves ?? []) {
        const before = positions.get(move.id);
        if (before && (before.x !== move.x || before.y !== move.y)) {effectiveMoves++; transformationIndices.add(index); motionIndices.add(index);}
        else if (before) add("warning", "unchanged-move", "moves repete a posição atual; reposicione o objeto se a intenção é deslocá-lo, ou retire a instrução sem efeito.", index, move.id);
        positions.set(move.id, {x: move.x, y: move.y});
      }
      if (!stage) continue; // Legacy treatments have another renderer.
      const target = elements.get(beat.target_id);
      if (target) motionIndices.add(index); // Finite focus/entrance, not a semantic transformation.
      const changesVisibility = (beat.action === "reveal" && target && !visible.has(target.id)) || (beat.action === "retire" && target && visible.has(target.id)) || (beat.reveal_ids ?? []).some((id: string) => elements.has(id) && !visible.has(id)) || (beat.retire_ids ?? []).some((id: string) => visible.has(id));
      if (changesVisibility) {transformationIndices.add(index); motionIndices.add(index);}
      if (target && beat.action === "update") {
        if (target.label !== beat.headline || (beat.value !== undefined && target.value !== beat.value) || (beat.detail !== undefined && target.detail !== beat.detail)) transformationIndices.add(index);
        target.label = beat.headline;
        if (beat.value !== undefined) target.value = beat.value;
        if (beat.detail !== undefined) target.detail = beat.detail;
      }
      if (beat.operation && JSON.stringify(beat.operation) !== JSON.stringify(activeOperation)) {transformationIndices.add(index); motionIndices.add(index);}
      if (target && (beat.actuation || beat.view || beat.mark_ids?.length || beat.chart_focus || beat.emphasis)) transformationIndices.add(index);
      activeOperation = beat.operation ?? activeOperation;
      const requiredOperation = operationTreatments[beat.treatment];
      if (requiredOperation && activeOperation?.kind !== requiredOperation) add("error", "missing-operation", `${beat.treatment} exige operation.kind=${requiredOperation} com seus dados neste beat ou em um estado anterior que continua em cena. Declare a relação real; trocar só o nome do tratamento não cria a operação.`, index);
      if (beat.treatment === "flow_diagram" && !(stage.connections ?? []).some((edge: any) => edge.from === beat.target_id || edge.to === beat.target_id)) add("error", "missing-flow", "flow_diagram exige uma conexão do alvo em stage.connections. Reserve o corredor para mostrar a relação; se não há relação, descreva o tratamento que de fato aparece.", index);
      if (target) {
        if (beat.treatment === "depth_photo" && (target.kind !== "photo" || !["push", "pan"].includes(target.image_motion))) add("error", "missing-photo-motion", "depth_photo no palco exige um alvo photo com image_motion push/pan. Em um recorte documental, use view/mark_ids para aproximar ou destacar a prova.", index);
        if (beat.treatment === "kinetic_type" && (!(["reveal", "update", "focus"].includes(beat.action)) || !([...textKinds, "object"].includes(target.kind)))) add("error", "missing-kinetic-text", "kinetic_type exige reveal/update/focus autoral de um rótulo de texto ou objeto. Documentos, fotos e gráficos usam seus próprios recursos.", index);
        if (beat.treatment === "giant_number" && (!textKinds.has(target.kind) || !target.value)) add("error", "missing-number", "giant_number exige value em um alvo de texto/metric. Declare o número verificado e sua região, ou escolha o tratamento pertinente à informação.", index);
        if (beat.treatment === "masked_emphasis" && !textKinds.has(target.kind)) add("error", "missing-emphasis-text", "masked_emphasis exige um rótulo de texto. Recortes documentais usam mark_ids/view; uma foto não recebe o grifo de texto do palco.", index);
        const documentaryRefocus = target.kind === "source_excerpt" && (beat.view || beat.mark_ids?.length);
        const cameraRequested = beat.camera || (beat.camera_mode !== "hold" && beat.action !== "retire" && beat.prominence !== "support" && (beat.camera_mode === "auto" || stage.camera_mode === "auto"));
        if (beat.behavior === "reframe" && !cameraRequested && !documentaryRefocus) add("error", "missing-reframe", "behavior=reframe não move o palco por si só. Declare camera/camera_mode auto, ou view/mark_ids para o recorte documental, conforme o enquadramento planejado.", index);
        if (cameraRequested && !cameraChanges.includes(index) && !documentaryRefocus) add("warning", "unchanged-camera", "a câmera declarada mantém o mesmo enquadramento ou está desativada pelo modo static/hold. Confira o percurso real; hold é uma pausa, não movimento.", index);
        if (beat.entrance && !changesVisibility) add("warning", "inactive-entrance", "entrance anima uma entrada/saída de visibilidade. Este beat não muda a visibilidade; revele/retire no ponto pertinente ou use o recurso de foco/atualização adequado.", index);
      }
      for (const id of beat.reveal_ids ?? []) visible.add(id);
      for (const id of beat.retire_ids ?? []) visible.delete(id);
      if (beat.action === "reveal" && beat.target_id) visible.add(beat.target_id);
      if (beat.action === "retire" && beat.target_id) visible.delete(beat.target_id);
    }
    if (stage) {
      for (const element of stage.elements ?? []) {
        if (element.svg_motion === "trace" && element.kind !== "object" && !element.icon) add("error", "missing-svg", "svg_motion=trace exige um objeto SVG ou icon. Declare a arte pertinente ou remova a opção sem efeito.", undefined, element.id);
      }
      if (stage.motion_profile === "static" && (beats.some((b: any) => b.entrance || ["kinetic_type", "masked_emphasis"].includes(b.treatment)) || stage.elements?.some((e: any) => e.svg_motion && e.svg_motion !== "none"))) add("warning", "suppressed-motion", "motion_profile=static desativa entradas, cascatas, grifos e desenho de SVG. Confirme que a pausa estável é intencional; para executar essas animações, use narrative.");
      if (stage.motion_profile === "static" && (stage.elements?.some((e: any) => e.sustain?.amplitude > 0) || stage.connections?.some((edge: any) => ["flow", "pulse"].includes(edge.motion)) || beats.some((b: any) => b.actuation))) add("warning", "suppressed-sustain", "O perfil static suprime movimento sustentado e atuação. Preserve a pausa documental ou selecione narrative para a ação que explica este trecho.");
      if (stage.captions?.enabled && !scene.audio_captions?.length) add("warning", "caption-timing-pending", "Legendas editoriais foram escolhidas; os tokens sincronizados serão preparados após a voz. O pedido no JSON não comprova sincronismo nem ocupação segura dos vazios.");
    }
    const rhythm = stage ? rhythmDiagnostics(stage, scene, beats, motionIndices, transformationIndices, project.fps ?? 30) : null;
    if (rhythm?.timing === "resolved-contract") {
      if ((rhythm.longest_without_visual_events_seconds ?? 0) > 0) add("warning", "visual-hold-duration", `O contrato contém um intervalo de ${rhythm.longest_without_visual_events_seconds} s sem eventos visuais ou movimento sustentado declarado. Confira no MP4 se é leitura/pausa intencional ou tela parada durante a explicação; não há limite obrigatório de segundos.`);
      if ((rhythm.longest_without_transformation_seconds ?? 0) > 0) add("warning", "transformation-gap-duration", `Há ${rhythm.longest_without_transformation_seconds} s entre transformações explicativas declaradas. Legendas e respiração podem manter atividade sem demonstrar a relação; revise a entrega da ideia no MP4, sem cota de transformações.`);
    }
    return {
      scene_id: scene.id ?? scene.index ?? sceneIndex,
      camera_mode: stage?.camera_mode ?? (stage?.motion_profile === "static" ? "static" : "manual"),
      camera_cues: cameraChanges.length,
      declared_camera_cues: beats.filter((b: any) => b.camera || b.camera_mode === "auto" || (stage?.camera_mode === "auto" && b.camera_mode !== "hold" && b.action !== "retire" && b.prominence !== "support")).length,
      moves: effectiveMoves,
      declared_moves: beats.reduce((n: number, b: any) => n + (b.moves?.length ?? 0), 0),
      operations: beats.flatMap((b: any) => b.operation ? [b.operation.kind] : []),
      text_treatments: beats.flatMap((b: any) => ["kinetic_type", "masked_emphasis"].includes(b.treatment) ? [b.treatment] : []),
      entrances: beats.flatMap((b: any) => b.entrance ? [b.entrance.style] : []),
      svg_choices: (stage?.elements ?? []).flatMap((e: any) => e.svg_motion ? [{id: e.id, motion: e.svg_motion}] : []),
      evidence_changes: beats.filter((b: any) => b.emphasis || b.view || b.mark_ids?.length || b.chart_focus).length,
      motion_durations: [...new Set(beats.map((b: any) => b.motion_seconds).filter((n: any) => n !== undefined))],
      transformations: transformationIndices.size,
      sustained_choices: (stage?.elements ?? []).flatMap((e: any) => e.sustain ? [{id: e.id, ...e.sustain}] : []),
      connection_motion: (stage?.connections ?? []).map((edge: any) => ({id: edge.id, motion: edge.motion ?? "once", period_seconds: edge.period_seconds})),
      actuation_choices: beats.flatMap((b: any, index: number) => b.actuation ? [{beat_index: index, target_id: b.target_id, actuation: b.actuation}] : []),
      surface_choices: (stage?.elements ?? []).flatMap((e: any) => e.surface ? [{id: e.id, surface: e.surface}] : []),
      captions_requested: Boolean(stage?.captions?.enabled),
      caption_tokens: scene.audio_captions?.length ?? 0,
      estimated_caption_tokens: (scene.audio_captions ?? []).filter((token: any) => token.timing_source !== "audio-word-alignment").length,
      caption_timing_source: scene.caption_timing?.source ?? null,
      rhythm,
      vocal_delivery: scene.tts?.delivery,
      vocal_intentions: cues.flatMap((c: any) => c.intent ? [c.intent] : []),
      vocal_arcs: cues.flatMap((c: any) => c.arc ? [c.arc] : []),
      emphasis_words: cues.flatMap((c: any) => c.emphasis_word ? [c.emphasis_word] : []),
    };
  });
  const addWarning = (code: string, message: string) => issues.push({severity: "warning", code, message});
  const beats = rawScenes.flatMap((s: any) => s.visual?.beats ?? []);
  if (beats.length > 1 && scenes.every((s: any) => s.camera_cues === 0) && beats.every((b: any) => b.treatment === "spotlight" && !b.operation && !b.moves?.length && !b.camera && b.camera_mode !== "auto" && !b.emphasis && !b.view && !b.mark_ids?.length && !b.chart_focus && !b.actuation)) {
    addWarning("repeated-spotlight", "Os eventos pontuais repetem apenas spotlight: revise se revelam relações e consequências, além de destacar objetos. Sustentação ou legendas podem manter atividade sem entregar uma nova explicação.");
  }
  const stagedScenes = scenes.filter((_: any, index: number) => rawScenes[index].visual?.stage);
  if (stagedScenes.length > 1 && stagedScenes.every((s: any) => s.camera_cues === 0 && s.moves === 0 && !s.sustained_choices.some((choice: any) => choice.amplitude > 0) && !s.connection_motion.some((edge: any) => ["flow", "pulse"].includes(edge.motion)) && !s.actuation_choices.length)) addWarning("stationary-plan", "Todas as cenas mantêm câmera e posições dos objetos, sem sustentação, fluxo contínuo ou atuação declarados. Revise onde o quadro estável ajuda a ler e onde um percurso ou transformação explica melhor a relação. Legendas não substituem essa explicação; a escolha é da pauta, sem cota de movimentos.");
  const durations = beats.map((b: any) => b.motion_seconds);
  if (durations.length > 1 && durations.every((n: any) => n !== undefined && n === durations[0])) {
    addWarning("uniform-duration", "Todos os eventos têm a mesma duração: confira se o ritmo acompanha as ideias e os tempos de leitura.");
  }
  if (scenes.length && scenes.every((s: any) => !s.vocal_intentions.length && !s.vocal_arcs.length && !s.emphasis_words.length)) {
    addWarning("missing-acting", "Não há atuação específica por trecho: confira a intenção das perguntas, descobertas, ressalvas e conclusões.");
  }
  return {
    scenes,
    issues,
    errors: issues.filter(issue => issue.severity === "error").map(issue => issue.message),
    warnings: issues.filter(issue => issue.severity === "warning").map(issue => issue.message),
    note: "Contagens e intervalos são diagnósticos, não cotas nem aprovação de originalidade ou ritmo. Segundos só aparecem com duration_frames e resolved_frame; descrevem o contrato, sem medir pixels, amplitude percebida ou confiança do alinhamento. Sustentação e legendas não substituem transformação explicativa. Rever voz, vazios, movimentos e sincronismo no MP4.",
  };
}
