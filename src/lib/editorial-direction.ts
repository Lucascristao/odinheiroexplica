// Diagnostics describe authored choices. They never pick a topic, composition,
// camera path, acting intention or a quota of effects for the author.
export function summarizeEditorialDirection(project: any) {
  const scenes = (project.scenes ?? project.script?.scenes ?? []).map((scene: any) => {
    const stage = scene.visual?.stage;
    const beats = scene.visual?.beats ?? [];
    const cues = scene.tts?.cues ?? [];
    return {
      scene_id: scene.id,
      camera_mode: stage?.camera_mode ?? "manual",
      camera_cues: beats.filter((b: any) => b.camera || b.camera_mode === "auto" || (stage?.camera_mode === "auto" && b.camera_mode !== "hold" && b.action !== "retire" && b.prominence !== "support")).length,
      moves: beats.reduce((n: number, b: any) => n + (b.moves?.length ?? 0), 0),
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
  const warnings: string[] = [];
  const beats = (project.scenes ?? project.script?.scenes ?? []).flatMap((s: any) => s.visual?.beats ?? []);
  if (beats.length > 1 && scenes.every((s: any) => s.camera_cues === 0) && beats.every((b: any) => b.treatment === "spotlight" && !b.operation && !b.moves?.length && !b.camera && b.camera_mode !== "auto" && !b.emphasis && !b.view && !b.mark_ids?.length && !b.chart_focus)) {
    warnings.push("O plano repete apenas spotlight: revise se revela relações e consequências, além de destacar objetos.");
  }
  const durations = beats.map((b: any) => b.motion_seconds);
  if (durations.length > 1 && durations.every((n: any) => n !== undefined && n === durations[0])) {
    warnings.push("Todos os eventos têm a mesma duração: confira se o ritmo acompanha as ideias e os tempos de leitura.");
  }
  if (scenes.length && scenes.every((s: any) => !s.vocal_intentions.length && !s.vocal_arcs.length && !s.emphasis_words.length)) {
    warnings.push("Não há atuação específica por trecho: confira a intenção das perguntas, descobertas, ressalvas e conclusões.");
  }
  return {scenes, warnings, note: "Contagens são diagnósticos, não cotas nem aprovação de originalidade. Rever a voz e os movimentos no MP4."};
}
