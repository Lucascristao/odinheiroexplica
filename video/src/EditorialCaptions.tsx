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
type CaptionPlacement = {box: Box; freeRegion: Box; size: number; lines: string[]};
const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;
const SCREEN_GAP = 32;
const PADDING = 16;
const joinsNext = (word: string) => /^(a|o|as|os|um|uma|uns|umas|de|da|do|das|dos|em|na|no|nas|nos|ao|aos|à|às|para|por|com|sem|que|e|ou|não|se)$/i.test(word);
const terminal = (word: string) => /[.!?;:]$/.test(word);

// The illustration is composed first. Screen-space occupancy follows that
// composition, including camera poses, route corridors and retiring objects.
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

// Find a contiguous empty rectangle, not a sum of disconnected gaps or merely
// a box large enough for the letters. The minimum is a fraction of the VIDEO.
const freeRegions = (safe: Box, occupied: Box[], minimumArea: number): Box[] => {
  const obstacles = occupied.map(b => {
    const x = Math.max(safe.x, b.x - SCREEN_GAP), y = Math.max(safe.y, b.y - SCREEN_GAP);
    return {x, y, w: Math.min(safe.x + safe.w, b.x + b.w + SCREEN_GAP) - x,
      h: Math.min(safe.y + safe.h, b.y + b.h + SCREEN_GAP) - y};
  }).filter(b => b.w > 0 && b.h > 0);
  const xs = [...new Set([safe.x, safe.x + safe.w, ...obstacles.flatMap(b => [b.x, b.x + b.w])])].sort((a, b) => a - b);
  const result: Box[] = [];
  for (let left = 0; left < xs.length - 1; left++) for (let right = left + 1; right < xs.length; right++) {
    const x = xs[left], w = xs[right] - x;
    if (w * safe.h < minimumArea) continue;
    const blocked = obstacles.filter(b => b.x < xs[right] - .01 && b.x + b.w > x + .01).sort((a, b) => a.y - b.y);
    let cursor = safe.y;
    const add = (bottom: number) => {
      const h = bottom - cursor;
      if (w * h >= minimumArea) result.push({x, y: cursor, w, h});
    };
    for (const b of blocked) {
      if (b.y > cursor) add(b.y);
      cursor = Math.max(cursor, b.y + b.h);
    }
    add(safe.y + safe.h);
  }
  return result.sort((a, b) => b.w * b.h - a.w * a.h);
};

const phraseChunks = (words: CaptionWord[], stage: EditorialStage, fps: number): CaptionWord[][] => {
  const perLine = Math.max(3, stage.captions?.words_per_line ?? 3);
  const lines = stage.captions?.max_lines ?? 2;
  // Importing an old max_words:1 project must not restore word-by-word motion.
  const configured = stage.captions?.max_words ?? 6;
  const limit = Math.min(perLine * lines, configured < 3 ? 6 : configured);
  const chunks: CaptionWord[][] = [];
  let index = 0;
  while (index < words.length) {
    let phraseEnd = index + 1;
    while (phraseEnd < words.length && !terminal(words[phraseEnd - 1].text)
      && words[phraseEnd].start_frame - words[phraseEnd - 1].end_frame < fps * .8) phraseEnd++;
    let end = Math.min(phraseEnd, index + limit);
    // Balance the final blocks instead of flashing a lone leftover word.
    if (phraseEnd - end > 0 && phraseEnd - end < 3 && end - index > 2) end -= 3 - (phraseEnd - end);
    if (end < phraseEnd && !terminal(words[end - 1].text)) {
      while (end - index > 3 && joinsNext(words[end - 1].text)) end--;
    }
    chunks.push(words.slice(index, end));
    index = end;
  }
  return chunks;
};

const lineOptions = (words: CaptionWord[], stage: EditorialStage): string[][] => {
  const text = words.map(word => word.text);
  const perLine = Math.max(3, stage.captions?.words_per_line ?? 3);
  if (text.length <= perLine || stage.captions?.max_lines === 1) return [[text.join(" ")]];
  const splits = Array.from({length: text.length - 1}, (_, i) => i + 1)
    .filter(at => at <= perLine + 1 && text.length - at <= perLine + 1)
    .sort((a, b) => {
      const score = (at: number) => (joinsNext(text[at - 1]) ? 20 : 0)
        + Math.abs(at - perLine) + Math.abs(at - (text.length - at)) * .3
        + (at === 1 || text.length - at === 1 ? 3 : 0);
      return score(a) - score(b);
    });
  return splits.map(at => [text.slice(0, at).join(" "), text.slice(at).join(" ")]);
};

const placeCaption = (stage: EditorialStage, beats: StageEvent[], words: CaptionWord[], fps: number, width: number, height: number, title?: string): CaptionPlacement | null => {
  if (!words.length) return null;
  const first = words[0].start_frame, last = words.at(-1)!.end_frame;
  const samples = [...new Set([first, Math.min(last - 1, first + 1), Math.round((first + last - 1) / 2), last - 1,
    ...beats.flatMap(beat => {
      const at = beat.resolved_frame ?? -1;
      const finish = at + Math.ceil((beat.motion_seconds ?? .45) * fps);
      return [at, at + 1, finish].filter(frame => frame >= first && frame < last);
    })])];
  const layouts = samples.map(at => occupiedAt(stage, beats, at, fps, width, height, title));
  const occupied = [...new Map<string, Box>(layouts.flatMap(l => l.boxes).map(b => [[b.x, b.y, b.w, b.h].join(","), b] as const)).values()];
  // Legacy region/side fields cannot reserve space or override the area rule.
  const regions = freeRegions(layouts[0].safe, occupied, width * height * (stage.captions?.min_free_area_ratio ?? .30));
  if (!regions.length) return null;
  const requested = Math.min(96, stage.captions?.font_size ?? 64);
  const sizes = [...new Set([requested, ...Array.from({length: Math.ceil((requested - 48) / 4)}, (_, i) => Math.max(48, requested - (i + 1) * 4)), 48])];
  const options = lineOptions(words, stage);
  for (const size of sizes) for (const lines of options) {
    const w = Math.max(...lines.map(line => measureEditorialText(line, size))) + PADDING * 2;
    const h = lines.length * size * 1.16 + PADDING * 2;
    for (const freeRegion of regions) {
      const box = {x: freeRegion.x + (freeRegion.w - w) / 2, y: freeRegion.y + (freeRegion.h - h) / 2, w, h};
      if (contains(freeRegion, box) && occupied.every(b => !intersects(box, b, SCREEN_GAP))) return {box, freeRegion, size, lines};
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
  const chunks = useMemo(() => phraseChunks(words, stage, fps), [words, stage, fps]);
  const chunk = chunks.find(part => frame >= part[0].start_frame && frame < part.at(-1)!.end_frame);
  const placement = useMemo(() => !ready || !stage.captions?.enabled || !chunk ? null
    : placeCaption(stage, beats, chunk, fps, width, height, title), [ready, stage, beats, chunk, fps, width, height, title]);
  if (!placement || !chunk) return null;
  // If an intermediate camera/entrance pose consumes the substantial empty
  // region, suppress this caption. Never move the illustration to recover it.
  const current = occupiedAt(stage, beats, frame, fps, width, height, title);
  if (!contains(current.safe, placement.freeRegion) || current.boxes.some(b => intersects(placement.freeRegion, b, SCREEN_GAP - .1))) return null;
  const start = chunk[0].start_frame, end = chunk.at(-1)!.end_frame;
  const duration = Math.max(1, end - start);
  const enter = interpolate(frame - start + 1, [0, Math.min(5, duration)], [0, 1], clamp);
  const leave = interpolate(frame, [end - Math.min(3, duration / 4), end], [1, 0], clamp);
  const animate = stage.motion_profile !== "static";
  return <AbsoluteFill style={{pointerEvents: "none"}}>
    <div data-editorial-caption="phrase" data-caption-timing={chunk.some(w => w.timing_source !== "audio-word-alignment") ? "estimated" : "aligned"}
      data-free-area-ratio={(placement.freeRegion.w * placement.freeRegion.h / (width * height)).toFixed(3)}
      style={{position: "absolute", left: placement.box.x, top: placement.box.y, width: placement.box.w, height: placement.box.h,
        boxSizing: "border-box", padding: PADDING, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center",
        fontFamily: EDITORIAL_FONT, fontWeight: 700, fontSize: placement.size, lineHeight: 1.16, textAlign: "center", color: "#f6f7f8",
        opacity: animate ? enter * leave : 1, transform: animate ? `translateY(${(1 - enter) * 6}px)` : undefined,
        textShadow: "0 3px 10px rgba(0,0,0,.9)"}}>
      {placement.lines.map((line, index) => <span key={index} style={{display: "block", whiteSpace: "nowrap"}}>{line}</span>)}
    </div>
  </AbsoluteFill>;
};
