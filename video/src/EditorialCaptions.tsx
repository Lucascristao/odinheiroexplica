import {useMemo} from "react";
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from "remotion";
import {editorialStageSchema, type EditorialStage, type StageEvent} from "../../src/lib/editorial-stage";
import {contains, entranceMotion, intersects, layoutStage, transformedRect, type Box} from "../../src/lib/editorial-layout";
import {EDITORIAL_FONT} from "../../src/lib/editorial-typography";
import {measureEditorialText, useEditorialFont} from "./editorial-font";

export type CaptionWord = {
  text: string;
  start_frame: number;
  end_frame: number;
  timing_source: string;
};
type CaptionPlacement = {box: Box; size: number; multiline: boolean};
const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;
const SCREEN_GAP = 24;
const CAPTION_PADDING = 16;

// Screen-space occupancy comes from the same camera and geometry as the scene.
// Captions yield to evidence, labels, route corridors and operations, including
// incoming/retiring elements. They never infer that empty image pixels are free.
const occupiedAt = (stage: EditorialStage, beats: StageEvent[], frame: number, fps: number, width: number, height: number, title?: string) => {
  const solved = layoutStage(stage, beats, frame, fps, width, height, measureEditorialText, title);
  const {canvas, camera} = solved;
  const screen = (box: Box): Box => ({
    x: canvas.x + canvas.width / 2 + (box.x - camera.x * canvas.width / 100) * camera.zoom,
    y: canvas.y + canvas.height / 2 + (box.y - camera.y * canvas.height / 100) * camera.zoom,
    w: box.w * camera.zoom, h: box.h * camera.zoom,
  });
  const visible = solved.elements.filter(element => {
    const p = entranceMotion(element, frame).reveal;
    return element.visible ? p > .001 : element.wasVisible && p < .999;
  });
  const boxes = visible.map(element => screen(transformedRect(element, frame, canvas)));
  for (const route of solved.connections) {
    if (visible.some(e => e.id === route.from) && visible.some(e => e.id === route.to)) boxes.push(screen(route.bounds));
  }
  if (solved.operation) boxes.push(...solved.operation.boxes.map(screen));
  boxes.push(...solved.photo_captions.map(caption => caption.box));
  return {boxes, safe: {x: canvas.x + 12, y: canvas.y + 12, w: canvas.width - 24, h: canvas.height - 24}};
};

const placeCaption = (stage: EditorialStage, beats: StageEvent[], words: CaptionWord[], fps: number, width: number, height: number, title?: string): CaptionPlacement | null => {
  if (!words.length) return null;
  const first = words[0].start_frame, last = words.at(-1)!.end_frame;
  const samples = [...new Set([first, first + 1, Math.round((first + last) / 2), Math.max(first, last - 1), ...beats.flatMap(b => {
    const at = b.resolved_frame ?? -1;
    return at >= first && at < last ? [at, Math.min(last - 1, at + 1)] : [];
  })])];
  const layouts = samples.map(at => occupiedAt(stage, beats, at, fps, width, height, title));
  const canvasSafe = layouts[0].safe;
  const region = stage.captions?.region;
  // The author's region is preferred. A smaller region must not suppress a
  // readable caption when another unoccupied area of the scene is available.
  const regions = region ? [{
    x: canvasSafe.x + region.x * canvasSafe.w / 100,
    y: canvasSafe.y + region.y * canvasSafe.h / 100,
    w: canvasSafe.w * region.width / 100,
    h: canvasSafe.h * region.height / 100,
  }, canvasSafe] : [canvasSafe];
  const occupied = layouts.flatMap(l => l.boxes);
  const side = stage.captions?.preferred_side ?? "auto";
  const requested = stage.captions?.font_size ?? 112;
  const text = words.map(word => word.text.toLocaleUpperCase("pt-BR"));
  const sizes = [...new Set([requested, ...Array.from({length: Math.ceil((requested - 72) / 8)}, (_, i) => Math.max(72, requested - (i + 1) * 8)), 72])];
  for (const size of sizes) for (const multiline of words.length > 1 ? [false, true] : [false]) {
    const lines = multiline ? text : [text.join(" ")];
    const w = (multiline ? Math.max(...lines.map(line => measureEditorialText(line, size)))
      : text.reduce((sum, word) => sum + measureEditorialText(word, size), 0) + Math.max(0, text.length - 1) * size * .28) + CAPTION_PADDING * 2;
    const h = lines.length * size * 1.12 + CAPTION_PADDING * 2;
    for (const safe of regions) {
      if (w > safe.w || h > safe.h) continue;
      const targetX = side === "left" ? safe.x + safe.w * .25 : side === "right" ? safe.x + safe.w * .75 : safe.x + safe.w / 2;
      const xs = [safe.x, safe.x + (safe.w - w) / 2, safe.x + safe.w - w, targetX - w / 2,
        ...occupied.flatMap(b => [b.x - w - SCREEN_GAP, b.x + b.w + SCREEN_GAP])];
      const ys = [safe.y + (safe.h - h) / 2, safe.y, safe.y + safe.h - h,
        ...occupied.flatMap(b => [b.y - h - SCREEN_GAP, b.y + b.h + SCREEN_GAP])];
      const candidates = xs.flatMap(x => ys.map(y => ({x, y, w, h})))
        .filter(box => contains(safe, box) && occupied.every(b => !intersects(box, b, SCREEN_GAP)))
        .sort((a, b) => (Math.abs(a.x + w / 2 - targetX) + Math.abs(a.y + h / 2 - safe.y - safe.h / 2) * .35)
          - (Math.abs(b.x + w / 2 - targetX) + Math.abs(b.y + h / 2 - safe.y - safe.h / 2) * .35));
      if (candidates[0]) return {box: candidates[0], size, multiline};
    }
  }
  return null;
};

export const EditorialCaptions = ({stage: rawStage, beats, words, title}: {
  stage: EditorialStage; beats: StageEvent[]; words: CaptionWord[]; title?: string;
}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const ready = useEditorialFont();
  const stage = useMemo(() => editorialStageSchema.parse(rawStage), [rawStage]);
  const chunks = useMemo(() => {
    const result: CaptionWord[][] = [];
    for (const word of words) {
      const previous = result.at(-1);
      if (previous && previous.length < (stage.captions?.max_words ?? 2) && !/[.!?;:]$/.test(previous.at(-1)!.text)
        && word.start_frame - previous.at(-1)!.end_frame < fps * .8) previous.push(word);
      else result.push([word]);
    }
    return result;
  }, [words, stage.captions?.max_words, fps]);
  const chunkIndex = chunks.findIndex(chunk => frame >= chunk[0].start_frame && frame < chunk.at(-1)!.end_frame);
  const chunk = chunkIndex >= 0 ? chunks[chunkIndex] : undefined;
  const placement = useMemo(() => !ready || !stage.captions?.enabled || !chunk ? null
    : placeCaption(stage, beats, chunk, fps, width, height, title), [ready, stage, beats, chunk, fps, width, height, title]);
  const currentWord = chunk?.find(word => frame >= word.start_frame && frame < word.end_frame);
  const singlePlacement = useMemo(() => !ready || placement || !currentWord || !stage.captions?.enabled ? null
    : placeCaption(stage, beats, [currentWord], fps, width, height, title), [ready, placement, currentWord, stage, beats, fps, width, height, title]);
  const layout = placement ?? singlePlacement;
  const shown = placement ? chunk : currentWord ? [currentWord] : undefined;
  if (!ready || !stage.captions?.enabled || !layout || !shown) return null;
  // Re-check the current frame as well as the chunk envelope: a caption must
  // disappear rather than cover an unexpected intermediate camera/route pose.
  if (occupiedAt(stage, beats, frame, fps, width, height, title).boxes.some(b => intersects(layout.box, b, SCREEN_GAP))) return null;
  const end = shown.at(-1)!.end_frame;
  const outgoing = interpolate(frame, [end - Math.min(3, (end - shown[0].start_frame) / 4), end], [1, 0], clamp);
  const animate = stage.motion_profile !== "static";
  return <AbsoluteFill style={{pointerEvents: "none"}}>
    <div data-editorial-caption="narration" data-caption-timing={shown.some(w => w.timing_source !== "audio-word-alignment") ? "estimated" : "aligned"}
      style={{position: "absolute", left: layout.box.x, top: layout.box.y, width: layout.box.w, height: layout.box.h,
        boxSizing: "border-box", padding: CAPTION_PADDING, display: "flex", flexDirection: layout.multiline ? "column" : "row",
        justifyContent: "center", alignItems: "center", gap: layout.multiline ? 0 : layout.size * .28,
        fontFamily: EDITORIAL_FONT, fontWeight: 700, fontSize: layout.size, lineHeight: 1.12,
        textAlign: "center", color: "#f6f7f8", opacity: animate ? outgoing : 1,
        textShadow: "0 4px 18px rgba(0,0,0,.85)"}}>
      {shown.map(word => {
        const duration = Math.max(1, word.end_frame - word.start_frame);
        const p = animate ? interpolate(frame - word.start_frame + 1, [0, Math.min(5, duration)], [0, 1], clamp) : 1;
        const ease = 1 - Math.pow(1 - p, 3);
        const active = frame >= word.start_frame && frame < word.end_frame;
        return <span key={word.start_frame + word.text} style={{display: "inline-block", position: "relative", whiteSpace: "nowrap",
          opacity: p, transform: `translateY(${(1 - ease) * 14}px) scale(${.94 + .06 * ease})`,
          color: active ? "#ffbd19" : "#f6f7f8"}}>
          {word.text.toLocaleUpperCase("pt-BR")}
          {active && <span style={{position: "absolute", left: 0, bottom: -4, height: 5, borderRadius: 4,
            width: `${ease * 100}%`, background: "#ffbd19", opacity: .8}} />}
        </span>;
      })}
    </div>
  </AbsoluteFill>;
};
