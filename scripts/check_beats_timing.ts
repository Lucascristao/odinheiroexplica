import { readFileSync } from 'fs';

const manifest = JSON.parse(readFileSync('run_artifacts/current_run/video/generated/daily-aligned-tts-manifest.json', 'utf8'));

manifest.scenes.forEach((s: any) => {
  console.log(`\n=== ${s.id} (Duração: ${s.duration_seconds.toFixed(2)}s) ===`);
  (s.beat_timings || []).forEach((b: any) => {
    console.log(`  Beat ${b.beat_index} em ${b.audio_offset_seconds.toFixed(2)}s: "${b.anchor.slice(0, 48)}..." (Fonte: ${b.timing_source}, Conf: ${b.alignment_confidence ?? 'est'})`);
  });
});
