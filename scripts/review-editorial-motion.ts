import {mkdirSync, writeFileSync} from "node:fs";
import {resolve} from "node:path";
import {bundle} from "@remotion/bundler";
import {openBrowser, renderStill, selectComposition} from "@remotion/renderer";
import {engineMotionFixtures} from "../video/src/engine-motion-fixtures";

const directory = resolve(process.argv[2] ?? "render-output/engine-review");
mkdirSync(directory, {recursive: true});
writeFileSync(resolve(directory, "fixtures.json"), JSON.stringify({project_id: "technical-engine-review", fps: 30, scenes: engineMotionFixtures}, null, 2) + "\n");
const serveUrl = await bundle({entryPoint: resolve("video/src/EngineMotionReview.tsx"), publicDir: resolve("public")});
const browser = await openBrowser("chrome");
try {
  const composition = await selectComposition({serveUrl, id: "EngineMotionReview", puppeteerInstance: browser});
  // Includes initial poses, intermediate text/SVG/camera/operation frames and
  // settled holds from two independently authored compositions, without TTS.
  for (const frame of [8, 20, 45, 95, 110, 175, 195, 240, 275, 308, 320, 345, 405, 475, 495, 552, 580]) {
    await renderStill({serveUrl, composition, puppeteerInstance: browser, frame, output: resolve(directory, `frame-${String(frame).padStart(3, "0")}.png`)});
  }
  console.log(`Revisão técnica: 17 quadros em ${directory}; sem síntese ou alteração do episódio.`);
} finally {
  await browser.close({silent: true});
}
