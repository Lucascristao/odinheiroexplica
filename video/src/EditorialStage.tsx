import {useEffect, useId, useMemo, useState} from "react";
import {AbsoluteFill, Img, cancelRender, continueRender, delayRender, interpolate, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {loadFont} from "@remotion/fonts";
import {measureText} from "@remotion/layout-utils";
import {editorialStageSchema, resolveStage, type EditorialStage as Stage, type StageEvent} from "../../src/lib/editorial-stage";

const FONT = "ODE Inter";
const WHITE = "#f6f7f8";
const GOLD = "#ffbd19";
const MUTED = "#9ba4ae";
const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;
let fontPromise: Promise<unknown> | undefined;

function useEditorialFont() {
  const [handle] = useState(() => delayRender("Loading editorial font"));
  const [ready, setReady] = useState(false);
  useEffect(() => {
    fontPromise ??= loadFont({family: FONT, url: staticFile("fonts/inter-latin-700-normal.woff2"), weight: "700"});
    fontPromise.then(() => {setReady(true); continueRender(handle);}).catch(cancelRender);
  }, [handle]);
  return ready;
}

// Measure with the bundled font. Never squeeze letters or silently clip facts.
const wrap = (text: string, size: number, width: number) => {
  const lines: string[] = [];
  for (const word of text.trim().split(/\s+/)) {
    const last = lines.at(-1);
    const candidate = last ? `${last} ${word}` : word;
    if (last && measureText({text: candidate, fontFamily: FONT, fontSize: size, fontWeight: 700}).width > width) lines.push(word);
    else if (last) lines[lines.length - 1] = candidate;
    else lines.push(word);
  }
  return lines;
};

const TextBox = ({text, width, height, maxSize = 42, minSize = 25, color = WHITE}: {text: string; width: number; height: number; maxSize?: number; minSize?: number; color?: string}) => {
  let size = maxSize;
  let lines = wrap(text, size, width);
  const fits = () => lines.length * size * 1.18 <= height && lines.every(line => measureText({text: line, fontFamily: FONT, fontSize: size, fontWeight: 700}).width <= width);
  while (size > minSize && !fits()) {size -= 1; lines = wrap(text, size, width);}
  if (!fits()) throw new Error(`Texto não cabe com legibilidade: ${text}. Amplie a região ou reduza o texto.`);
  return <div style={{fontSize: size, lineHeight: 1.18, fontWeight: 700, color, whiteSpace: "pre", letterSpacing: 0}}>{lines.join("\n")}</div>;
};

export const EditorialStage = ({stage, beats, title, source, accent = GOLD}: {stage: Stage; beats: StageEvent[]; title?: string; source?: string; accent?: string}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const ready = useEditorialFont();
  const arrowId = useId().replace(/:/g, "");
  const checkedStage = useMemo(() => editorialStageSchema.parse(stage), [stage]);
  if (!ready) return null;
  const {elements, active} = resolveStage(checkedStage, beats, frame);
  const canvas = {x: 130, y: 230, width: width - 260, height: height - 360};
  const rect = (e: typeof elements[number]) => ({x: e.x * canvas.width / 100, y: e.y * canvas.height / 100, w: e.width * canvas.width / 100, h: e.height * canvas.height / 100});
  const focus = interpolate(frame - (active?.resolved_frame ?? 0), [0, fps * 0.45], [0, 1], clamp);
  const takeover = active?.prominence === "takeover";
  return <AbsoluteFill style={{fontFamily: FONT}}>
    <div style={{position: "absolute", top: 118, left: 130}}>
      <TextBox text={title ?? ""} width={canvas.width} height={90} maxSize={46} />
    </div>
    <div style={{position: "absolute", left: canvas.x, top: canvas.y, width: canvas.width, height: canvas.height}}>
      <svg width={canvas.width} height={canvas.height} style={{position: "absolute", inset: 0}}>
        <defs><marker id={arrowId} markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#78858e" strokeWidth="1.5" /></marker></defs>
        {checkedStage.connections.map((edge, i) => {
          const from = elements.find(e => e.id === edge.from)!;
          const to = elements.find(e => e.id === edge.to)!;
          if (!from.visible || !to.visible) return null;
          const a = rect(from), b = rect(to);
          const horizontal = Math.abs((b.x+b.w/2)-(a.x+a.w/2)) >= Math.abs((b.y+b.h/2)-(a.y+a.h/2));
          const forward = horizontal ? b.x > a.x : b.y > a.y;
          const x1 = horizontal ? a.x + (forward ? a.w : 0) : a.x+a.w/2;
          const x2 = horizontal ? b.x + (forward ? 0 : b.w) : b.x+b.w/2;
          const y1 = horizontal ? a.y+a.h/2 : a.y+(forward ? a.h : 0);
          const y2 = horizontal ? b.y+b.h/2 : b.y+(forward ? 0 : b.h);
          const selected = active?.target_id === edge.to;
          const edgeEnter = interpolate(frame - Math.max(from.changedAt, to.changedAt), [0, fps * 0.35], [0, 1], clamp);
          return <g key={`${edge.from}-${edge.to}-${i}`} opacity={edgeEnter * (takeover ? 0.15 : 1)}>
            <path d={`M${x1},${y1} L${x2},${y2}`} stroke="#45515a" strokeWidth={2} markerEnd={`url(#${arrowId})`} />
            {selected && <path d={`M${x1},${y1} L${x2},${y2}`} pathLength={1} stroke={accent} strokeWidth={4} strokeDasharray={1} strokeDashoffset={1-focus} />}
            {edge.label && <text x={(x1+x2)/2} y={(y1+y2)/2-14} textAnchor="middle" fill={MUTED} fontSize={24}>{edge.label}</text>}
          </g>;
        })}
      </svg>
      {elements.map(element => {
        const box = rect(element);
        const selected = active?.target_id === element.id && active.action !== "retire";
        const reveal = interpolate(frame - element.changedAt, [0, fps * 0.35], [0, 1], clamp);
        const opacity = (element.visible ? reveal : element.wasVisible ? 1-reveal : 0) * (takeover && !selected ? 0.15 : 1);
        if (opacity === 0) return null;
        const color = selected && active?.prominence !== "support" ? accent : WHITE;
        const padding = 16;
        const innerW = box.w - padding*2;
        const innerH = box.h - padding*2;
        const valueH = element.value ? innerH * 0.4 : 0;
        const detailH = element.detail ? innerH * (element.value ? 0.3 : 0.45) : 0;
        const labelH = innerH - valueH - detailH;
        return <div key={element.id} data-element-id={element.id} style={{position: "absolute", left: box.x, top: box.y, width: box.w, height: box.h, padding, opacity, transform: `translateY(${element.visible ? (1-reveal)*12 : 0}px)`, display: "flex", flexDirection: "column", justifyContent: "center", gap: 0}}>
          {element.kind === "photo" ? <div style={{width: "100%", height: "100%", padding: element.photo_style === "paper" ? 14 : 0, background: element.photo_style === "paper" ? "#eee8dc" : "transparent", clipPath: element.photo_style === "paper" ? "polygon(1% 2%, 18% 0, 35% 2%, 51% 0, 72% 2%, 99% 0, 98% 23%, 100% 47%, 98% 71%, 100% 99%, 77% 97%, 52% 100%, 29% 98%, 0 100%, 2% 73%, 0 48%)" : undefined}}>
            {element.asset_file ? <Img src={staticFile(element.asset_file)} style={{height: "100%", width: "100%", objectFit: "contain"}} /> : <div style={{color: "#252a30", fontSize: 32}}>Foto: {element.label}</div>}
          </div> : <>
            {element.value && <TextBox text={element.value} width={innerW} height={valueH} maxSize={72} color={color} />}
            <TextBox text={element.label} width={innerW} height={labelH} maxSize={element.kind === "metric" ? 40 : element.kind === "note" ? 32 : 42} color={color} />
            {element.detail && <TextBox text={element.detail} width={innerW} height={detailH} maxSize={28} color={MUTED} />}
          </>}
          {selected && element.kind !== "photo" && <div style={{position: "absolute", left: padding, bottom: 3, width: (box.w-padding*2)*focus, height: active?.prominence === "support" ? 2 : 4, background: accent}} />}
        </div>;
      })}
    </div>
    {source && <div style={{position: "absolute", left: 130, bottom: 46, fontSize: 22, color: MUTED}}>{source}</div>}
  </AbsoluteFill>;
};
