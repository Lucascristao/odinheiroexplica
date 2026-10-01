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
const stage = {camera_mode: "manual", elements: [{id: "a", kind: "step", label: "Origem", x: 10, y: 15, width: 20, height: 20}, {id: "b", kind: "step", label: "Destino", x: 55, y: 15, width: 20, height: 20}], connections: []};
const authored = summarizeEditorialDirection({scenes: [{id: "one", tts: {cues: [cue]}, visual: {stage, beats: [{target_id: "a", operation: {kind: "compare", element_ids: ["a", "b"]}, motion_seconds: .7, camera: {x: 45, y: 30, zoom: 1.1}}, {target_id: "b", moves: [{id: "b", x: 55, y: 50}], motion_seconds: 1.2}]}}]});
assert.deepEqual(authored.warnings, []);
assert.deepEqual(authored.errors, []);
assert.equal(authored.scenes[0].camera_cues, 1);
assert.equal(authored.scenes[0].moves, 1);
assert.deepEqual(authored.scenes[0].operations, ["compare"]);
assert.deepEqual(authored.scenes[0].vocal_intentions, ["curiosity"]);

// A nominally varied plan must expose missing executable relationships before
// any paid narration. Inert labels are not accepted as proof of animation.
const nominal = summarizeEditorialDirection({scenes: [{id: "nominal", tts: {cues: [cue]}, visual: {stage, beats: [
  {target_id: "a", treatment: "flow_diagram"},
  {target_id: "b", treatment: "stack"},
  {target_id: "a", treatment: "kinetic_type", action: "focus"},
  {target_id: "b", treatment: "spotlight", behavior: "reframe"},
]}}]});
assert.deepEqual(nominal.issues.filter(i => i.severity === "error").map(i => i.code), ["missing-flow", "missing-operation", "missing-kinetic-text", "missing-reframe"]);
assert(nominal.errors.every(message => message.includes("Cena nominal, beat")));
const connected = {...stage, connections: [{from: "a", to: "b"}]};
assert.deepEqual(summarizeEditorialDirection({scenes: [{visual: {stage: connected, beats: [{target_id: "a", treatment: "flow_diagram"}]}}]}).errors, []);
assert.deepEqual(summarizeEditorialDirection({scenes: [{visual: {stage, beats: [
  {target_id: "a", treatment: "split_compare", operation: {kind: "compare", element_ids: ["a", "b"]}},
  {target_id: "b", treatment: "split_compare", action: "focus"},
]}}]}).errors, []); // Existing operations persist while the explanation continues.
assert.deepEqual(summarizeEditorialDirection({scenes: [{visual: {stage, beats: [
  {target_id: "a", action: "update", headline: "Exemplo", value: "15", treatment: "spotlight"},
  {target_id: "a", treatment: "giant_number", action: "focus"},
]}}]}).errors, []); // An updated value remains the visible fact.

const documentaryStage = {elements: [{id: "proof", kind: "source_excerpt", label: "Documento", asset_id: "source", x: 5, y: 5, width: 90, height: 90}]};
assert(summarizeEditorialDirection({scenes: [{visual: {stage: documentaryStage, beats: [{target_id: "proof", treatment: "depth_photo"}]}}]}).errors.some(message => message.includes("photo")));
assert.deepEqual(summarizeEditorialDirection({scenes: [{visual: {stage: documentaryStage, beats: [{target_id: "proof", treatment: "spotlight", behavior: "reframe", view: {x: 10, y: 15, width: 60, height: 40}}]}}]}).errors, []);
assert.deepEqual(summarizeEditorialDirection({scenes: [{visual: {stage: documentaryStage, beats: [{target_id: "proof", treatment: "spotlight", behavior: "reframe", mark_ids: ["clause"]}]}}]}).errors, []); // ID integrity is the stage validator's job.
assert.deepEqual(summarizeEditorialDirection({scenes: [{visual: {beats: [{treatment: "depth_photo", behavior: "reframe"}, {treatment: "stack"}]}}]}).errors, []); // Legacy compositions keep their own renderer.

// A quiet documentary sequence is a review prompt, never a motion quota.
const quiet = summarizeEditorialDirection({scenes: [1, 2].map(id => ({id, tts: {cues: [cue]}, visual: {stage: {...stage, camera_mode: "static"}, beats: [{target_id: "a", treatment: "spotlight", camera: {x: 50, y: 50, zoom: 1}, moves: [{id: "a", x: 10, y: 15}]}]}}))});
assert.deepEqual(quiet.errors, []);
assert(quiet.issues.some(i => i.code === "stationary-plan"));
assert(quiet.issues.some(i => i.code === "unchanged-camera"));
assert(quiet.issues.some(i => i.code === "unchanged-move"));
assert(quiet.scenes.every(s => s.camera_cues === 0 && s.moves === 0 && s.declared_camera_cues === 1 && s.declared_moves === 1));
console.log("Direção autoral: atuação, recursos executáveis, refoco documental e diagnóstico sem cotas passaram.");
