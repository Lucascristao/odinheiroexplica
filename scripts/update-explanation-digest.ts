import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { normalizeEditorialProject, explanationReviewContent, stableJson } from "../src/lib/editorial-project";

const path = process.argv[2] ?? "video/data/daily.json";
const raw = JSON.parse(readFileSync(path, "utf8"));

if (raw.script?.scenes) {
  raw.script.scenes = raw.scenes;
}

const normalized = normalizeEditorialProject(raw);
const digest = createHash("sha256").update(stableJson(explanationReviewContent(normalized))).digest("hex");
console.log("Calculated digest:", digest);

if (raw.editorial?.explanation?.review) {
  raw.editorial.explanation.review.content_sha256 = digest;
}
writeFileSync(path, JSON.stringify(raw, null, 2) + "\n", "utf8");
console.log("Updated", path, "with new content_sha256!");
