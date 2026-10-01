import {readFileSync, writeFileSync, appendFileSync} from "node:fs";
import {summarizeEditorialDirection} from "../src/lib/editorial-direction";

const flag = (name: string, fallback: string) => {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
};
const input = flag("--input", "video/generated/daily-render-input.json");
const output = flag("--output", "video/generated/daily-rhythm-report.json");
const project = JSON.parse(readFileSync(input, "utf8"));
const direction = summarizeEditorialDirection(project);
const report = {
  project_id: project.project_id,
  fps: project.fps,
  scope: "Direção declarada com os tempos do áudio. Não é teste nem aprovação da percepção de movimento no MP4.",
  ...direction,
};
writeFileSync(output, JSON.stringify(report, null, 2) + "\n");
console.log(`Direção e ritmo: ${report.scenes.length} cenas; relatório ${output}.`);
if (process.env.GITHUB_STEP_SUMMARY) {
  const rows = report.scenes.map(scene => `| ${scene.scene_id} | ${scene.rhythm?.longest_without_visual_events_seconds ?? "aguardando"} | ${scene.rhythm?.longest_without_transformation_seconds ?? "aguardando"} | ${scene.caption_tokens} | ${scene.caption_timing_source ?? "sem legenda"} |`).join("\n");
  appendFileSync(process.env.GITHUB_STEP_SUMMARY, `\n### Ritmo declarado após a narração\n\n${report.scope}\n\n| Cena | Maior intervalo sem evento visual (s) | Sem transformação explicativa (s) | Palavras de legenda | Tempos das palavras |\n| --- | --- | --- | --- | --- |\n${rows}\n\nContagens e intervalos ajudam a revisar o vídeo real; não impõem uma montagem nem uma quantidade de efeitos.\n`);
}
