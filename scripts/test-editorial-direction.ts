import assert from "node:assert/strict";
import {speechDirectionSchema, validateSpeechDirection} from "../src/lib/speech-direction";
import {summarizeEditorialDirection} from "../src/lib/editorial-direction";

const narration = "Parece contraditório? A conta muda, mas não garante economia.";
const cue = {text: "Parece contraditório?", kind: "emphasis", intent: "curiosity", arc: "question", emphasis_word: "contraditório", pause_before_ms: 120};
assert.deepEqual(validateSpeechDirection(narration, {delivery: "hook", cues: [cue]}), []);
assert.deepEqual(speechDirectionSchema.parse({cues: [cue]}).cues[0], cue);
assert.deepEqual(validateSpeechDirection(narration, {cues: [{text: "não garante economia", kind: "contrast"}]}), []);
for (const invalid of [{...cue, intent: "alarm"}, {...cue, arc: "sing"}, {...cue, emphasis_word: "Parece contraditório"}, {...cue, emphasis_word: "economia"}]) {
  assert(validateSpeechDirection(narration, {cues: [invalid]}).length > 0);
}
assert(validateSpeechDirection("Conta e conta.", {cues: [{text: "Conta e conta.", kind: "emphasis", emphasis_word: "conta"}]}).length === 0); // Exact case is intentional.
assert(validateSpeechDirection("conta e conta.", {cues: [{text: "conta e conta.", kind: "emphasis", emphasis_word: "conta"}]}).length > 0);
assert(validateSpeechDirection(narration, {cues: [{...cue, text: "Parece contraditório? A conta"}]}).length > 0);
assert(validateSpeechDirection(narration, {cues: [cue, cue]}).length > 0);
const plain = summarizeEditorialDirection({scenes: [{id: "one", visual: {beats: [{treatment: "spotlight", motion_seconds: .55}, {treatment: "spotlight", motion_seconds: .55}]}}]});
assert.equal(plain.warnings.length, 3);
const authored = summarizeEditorialDirection({scenes: [{id: "one", tts: {cues: [cue]}, visual: {stage: {camera_mode: "auto"}, beats: [{target_id: "a", operation: {kind: "compare"}, motion_seconds: .7}, {target_id: "b", moves: [{id: "b", x: 30, y: 20}], motion_seconds: 1.2}]}}]});
assert.deepEqual(authored.warnings, []);
assert.equal(authored.scenes[0].moves, 1);
assert.deepEqual(authored.scenes[0].operations, ["compare"]);
assert.deepEqual(authored.scenes[0].vocal_intentions, ["curiosity"]);
console.log("Direção autoral: validação de atuação e diagnóstico sem cotas passaram.");
