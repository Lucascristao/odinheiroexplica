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
    let activeOperation: any;
    const elements = new Map<string, any>((stage?.elements ?? []).map((e: any) => [e.id, {...e}]));
    const positions = new Map<string, {x: number; y: number}>((stage?.elements ?? []).map((e: any) => [e.id, {x: e.x, y: e.y}]));
    const visible = new Set<string>((stage?.elements ?? []).filter((e: any) => e.initially_visible !== false).map((e: any) => e.id));
    for (const [index, beat] of beats.entries()) {
      for (const move of beat.moves ?? []) {
        const before = positions.get(move.id);
        if (before && (before.x !== move.x || before.y !== move.y)) effectiveMoves++;
        else if (before) add("warning", "unchanged-move", "moves repete a posição atual; reposicione o objeto se a intenção é deslocá-lo, ou retire a instrução sem efeito.", index, move.id);
        positions.set(move.id, {x: move.x, y: move.y});
      }
      if (!stage) continue; // Legacy treatments have another renderer.
      const target = elements.get(beat.target_id);
      if (target && beat.action === "update") {
        target.label = beat.headline;
        if (beat.value !== undefined) target.value = beat.value;
      }
      activeOperation = beat.operation ?? activeOperation;
      const requiredOperation = operationTreatments[beat.treatment];
      if (requiredOperation && activeOperation?.kind !== requiredOperation) add("error", "missing-operation", `${beat.treatment} exige operation.kind=${requiredOperation} com seus dados neste beat ou em um estado anterior que continua em cena. Declare a relação real; trocar só o nome do tratamento não cria a operação.`, index);
      if (beat.treatment === "flow_diagram" && !(stage.connections ?? []).some((edge: any) => edge.from === beat.target_id || edge.to === beat.target_id)) add("error", "missing-flow", "flow_diagram exige uma conexão do alvo em stage.connections. Reserve o corredor para mostrar a relação; se não há relação, descreva o tratamento que de fato aparece.", index);
      if (target) {
        if (beat.treatment === "depth_photo" && (target.kind !== "photo" || !["push", "pan"].includes(target.image_motion))) add("error", "missing-photo-motion", "depth_photo no palco exige um alvo photo com image_motion push/pan. Em um recorte documental, use view/mark_ids para aproximar ou destacar a prova.", index);
        if (beat.treatment === "kinetic_type" && (!(["reveal", "update"].includes(beat.action)) || !([...textKinds, "object"].includes(target.kind)))) add("error", "missing-kinetic-text", "kinetic_type exige reveal/update de um rótulo de texto ou objeto. Focus não reinicia a cascata; documentos, fotos e gráficos usam seus próprios recursos.", index);
        if (beat.treatment === "giant_number" && (!textKinds.has(target.kind) || !target.value)) add("error", "missing-number", "giant_number exige value em um alvo de texto/metric. Declare o número verificado e sua região, ou escolha o tratamento pertinente à informação.", index);
        if (beat.treatment === "masked_emphasis" && !textKinds.has(target.kind)) add("error", "missing-emphasis-text", "masked_emphasis exige um rótulo de texto. Recortes documentais usam mark_ids/view; uma foto não recebe o grifo de texto do palco.", index);
        const documentaryRefocus = target.kind === "source_excerpt" && (beat.view || beat.mark_ids?.length);
        const cameraRequested = beat.camera || (beat.camera_mode !== "hold" && beat.action !== "retire" && beat.prominence !== "support" && (beat.camera_mode === "auto" || stage.camera_mode === "auto"));
        if (beat.behavior === "reframe" && !cameraRequested && !documentaryRefocus) add("error", "missing-reframe", "behavior=reframe não move o palco por si só. Declare camera/camera_mode auto, ou view/mark_ids para o recorte documental, conforme o enquadramento planejado.", index);
        if (cameraRequested && !cameraChanges.includes(index) && !documentaryRefocus) add("warning", "unchanged-camera", "a câmera declarada mantém o mesmo enquadramento ou está desativada pelo modo static/hold. Confira o percurso real; hold é uma pausa, não movimento.", index);
        const changesVisibility = (beat.action === "reveal" && !visible.has(target.id)) || (beat.action === "retire" && visible.has(target.id)) || (beat.reveal_ids ?? []).some((id: string) => !visible.has(id)) || (beat.retire_ids ?? []).some((id: string) => visible.has(id));
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
      vocal_delivery: scene.tts?.delivery,
      vocal_intentions: cues.flatMap((c: any) => c.intent ? [c.intent] : []),
      vocal_arcs: cues.flatMap((c: any) => c.arc ? [c.arc] : []),
      emphasis_words: cues.flatMap((c: any) => c.emphasis_word ? [c.emphasis_word] : []),
    };
  });
  const addWarning = (code: string, message: string) => issues.push({severity: "warning", code, message});
  const beats = rawScenes.flatMap((s: any) => s.visual?.beats ?? []);
  if (beats.length > 1 && scenes.every((s: any) => s.camera_cues === 0) && beats.every((b: any) => b.treatment === "spotlight" && !b.operation && !b.moves?.length && !b.camera && b.camera_mode !== "auto" && !b.emphasis && !b.view && !b.mark_ids?.length && !b.chart_focus)) {
    addWarning("repeated-spotlight", "O plano repete apenas spotlight: revise se revela relações e consequências, além de destacar objetos.");
  }
  const stagedScenes = scenes.filter((_: any, index: number) => rawScenes[index].visual?.stage);
  if (stagedScenes.length > 1 && stagedScenes.every((s: any) => s.camera_cues === 0 && s.moves === 0)) addWarning("stationary-plan", "Todas as cenas mantêm câmera e posições dos objetos. Revise o storyboard: confirme onde o quadro estável ajuda a ler e onde um percurso ou transformação explica melhor a relação. A escolha é da pauta, sem cota de movimentos.");
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
    note: "Contagens são diagnósticos, não cotas nem aprovação de originalidade. Câmera descreve mudanças planejadas pelo resolver, antes do enquadramento e relógio do áudio real. Rever a voz e os movimentos no MP4.",
  };
}
