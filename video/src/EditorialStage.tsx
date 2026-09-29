import {SourceExcerpt, EditorialChart} from "./EditorialEvidence";
import type {Emphasis} from "../../src/lib/editorial-evidence";
import {EditorialIcon} from "./EditorialIcon";
import {EditorialObject} from "./EditorialObject";
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

const TextBox = ({text, width, height, maxSize = 42, minSize = 32, color = WHITE, emphasis, progress = 1}: {emphasis?: Emphasis | null; progress?: number; text: string; width: number; height: number; maxSize?: number; minSize?: number; color?: string}) => {
  let size = maxSize;
  let lines = wrap(text, size, width);
  const fits = () => lines.length * size * 1.18 <= height && lines.every(line => measureText({text: line, fontFamily: FONT, fontSize: size, fontWeight: 700}).width <= width);
  while (size > 18 && !fits()) {size -= 1; lines = wrap(text, size, width);}
  if (!fits()) {
    size = Math.max(16, Math.min(size, Math.floor(height / Math.max(1, lines.length * 1.18))));
  }
  const normalized=text.trim().replace(/\s+/g," ");
  const start=emphasis ? normalized.indexOf(emphasis.phrase.trim().replace(/\s+/g," ")) : -1;
  const end=start+(emphasis?.phrase.trim().replace(/\s+/g," ").length??0);
  let cursor=0;
  return <div style={{fontSize:size,lineHeight:1.18,fontWeight:700,color,whiteSpace:"pre",letterSpacing:0}}>{lines.map((line,i)=>{
    const offset=cursor;cursor+=line.length+1;
    const a=Math.max(0,start-offset),b=Math.min(line.length,end-offset);
    if(start<0||b<=a)return <div key={i}>{line}</div>;
    return <div key={i}>{line.slice(0,a)}<span style={{position:"relative",display:"inline-block"}}>
      {line.slice(a,b)}
      {emphasis?.style==="highlight" && <span style={{position:"absolute",inset:0,color:"#101317",background:GOLD,clipPath:`inset(0 ${(1-progress)*100}% 0 0)`}}>{line.slice(a,b)}</span>}
      {emphasis?.style!=="highlight" && <span style={{position:"absolute",left:0,top:emphasis?.style==="strike"?"52%":"95%",height:5,width:`${progress*100}%`,background:GOLD}}/>}
    </span>{line.slice(b)}</div>;
  })}</div>;
};

export const EditorialStage = ({stage, beats, title}: {stage: Stage; beats: StageEvent[]; title?: string}) => {
  const accent = GOLD;
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const ready = useEditorialFont();
  const arrowId = useId().replace(/:/g, "");
  const checkedStage = useMemo(() => editorialStageSchema.parse(stage), [stage]);
  if (!ready) return null;
  const {elements, active} = resolveStage(checkedStage, beats, frame, fps);
  const canvas = {x: 130, y: checkedStage.show_title ? 230 : 130, width: width - 260, height: height - (checkedStage.show_title ? 360 : 230)};
  const rect = (e: typeof elements[number]) => ({x: e.x * canvas.width / 100, y: e.y * canvas.height / 100, w: e.width * canvas.width / 100, h: e.height * canvas.height / 100});
  const focus = interpolate(frame - (active?.resolved_frame ?? 0), [0, (active?.motion_seconds??0.45)*fps], [0, 1], clamp);
  const takeover = active?.prominence === "takeover";
  return <AbsoluteFill style={{fontFamily: FONT}}>
    {checkedStage.show_title && <div style={{position: "absolute", top: 118, left: 130}}>
      <TextBox text={title ?? ""} width={canvas.width} height={90} maxSize={46} />
    </div>}
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
            {selected && focus < 1 && <circle cx={x1+(x2-x1)*focus} cy={y1+(y2-y1)*focus} r={7} fill={accent} />}
            {edge.label && <text x={(x1+x2)/2} y={(y1+y2)/2-14} textAnchor="middle" fill={MUTED} fontSize={32}>{edge.label}</text>}
          </g>;
        })}
      </svg>
      {elements.slice().sort((a,b)=>Number(Boolean(a.overlay_on))-Number(Boolean(b.overlay_on))).map(element => {
        const box = rect(element);
        const isExcerpt = element.kind === "source_excerpt";
        const padding = isExcerpt ? 0 : 16;
        const selected = active?.target_id === element.id && active.action !== "retire";
        const reveal = interpolate(frame - element.changedAt, [0, element.visibilityDuration], [0, 1], clamp);
        const opacity = (element.visible ? reveal : element.wasVisible ? 1-reveal : 0) * (takeover && !selected ? 0.15 : 1);
        if (opacity === 0) return null;
        const cueProgress=interpolate(frame-element.cueFrame,[0,element.cueDuration],[0,1],clamp);
        const color = selected && active?.prominence !== "support" ? accent : WHITE;
        const iconSize = element.icon ? Math.min(140, Math.max(68, box.h * 0.42)) : 0;
        const stacked = element.kind === "step";
        const iconSpace = element.icon ? iconSize + 18 : 0;
        const innerW = box.w - padding*2 - (stacked ? 0 : iconSpace);
        const innerH = box.h - padding*2 - (stacked ? iconSpace : 0);
        const valueH = element.value ? innerH * (element.value_size>100 ? 0.72 : 0.4) : 0;
        const detailH = element.detail ? innerH * (element.value ? (element.value_size>100 ? 0.12 : 0.3) : 0.45) : 0;
        const labelH = innerH - valueH - detailH;
        const isCard = !isExcerpt && !["photo", "chart", "label"].includes(element.kind);
        const cardBg = isCard
          ? (selected ? "linear-gradient(145deg, rgba(32, 38, 48, 0.95) 0%, rgba(18, 22, 28, 0.98) 100%)" : "linear-gradient(145deg, rgba(22, 27, 34, 0.85) 0%, rgba(13, 16, 21, 0.92) 100%)")
          : (element.overlay_on ? "rgba(12,16,20,0.88)" : undefined);
        const cardBorder = isCard
          ? (selected ? "2px solid #FFBD19" : "1px solid rgba(255, 255, 255, 0.12)")
          : undefined;
        const cardShadow = isCard
          ? (selected ? "0 22px 50px rgba(255, 189, 25, 0.22), 0 8px 24px rgba(0,0,0,0.8)" : "0 14px 34px rgba(0, 0, 0, 0.65)")
          : undefined;
        const cardRadius = isCard ? 18 : (element.overlay_on ? 12 : undefined);
        const cardPadding = isExcerpt ? 0 : isCard ? 22 : padding;

        return <div key={element.id} data-element-id={element.id} style={{position: "absolute", left: box.x, top: box.y, width: box.w, height: box.h, padding: cardPadding, opacity, zIndex: element.overlay_on ? 2 : 1, background: cardBg, border: cardBorder, boxShadow: cardShadow, borderRadius: cardRadius, transform: isExcerpt ? `translateY(${element.visible ? (1-reveal)*16 : 0}px) scale(${element.visible ? 0.96 + 0.04*reveal : 0.96})` : `translateY(${element.visible ? (1-reveal)*16 : 0}px) scale(${element.visible ? 0.94 + 0.06*reveal : 0.94})`, boxSizing: "border-box", display: "flex", flexDirection: stacked ? "column" : "row", alignItems: stacked ? "flex-start" : "center", justifyContent: "center", gap: element.icon ? 22 : 0}}>
          {element.kind === "source_excerpt" ? <SourceExcerpt element={element} view={element.view} markIds={element.markIds} markProgress={Object.fromEntries(Object.entries(element.markTiming).map(([id,t])=>[id,interpolate(frame-t.frame,[0,t.duration],[0,1],clamp)]))} /> : element.kind === "chart" && element.chart ? <EditorialChart chart={element.chart} title={element.label} width={box.w-32} height={box.h-32} focus={element.chartFocus} progress={cueProgress} /> : element.kind === "object" && element.object_type ? <div style={{width: "100%", height: "100%", display: "flex", flexDirection: "column"}}><div style={{flex: 1, minHeight: 0}}><EditorialObject type={element.object_type} accent={accent} progress={reveal} /></div><TextBox text={element.label} width={box.w-32} height={90} maxSize={42} /></div> : element.kind === "photo" ? <div style={{width: "100%", height: "100%", padding: element.photo_style === "paper" ? 14 : 0, overflow: "hidden", background: element.photo_style === "paper" ? "#eee8dc" : "transparent", clipPath: element.photo_style === "paper" ? "polygon(1% 2%, 18% 0, 35% 2%, 51% 0, 72% 2%, 99% 0, 98% 23%, 100% 47%, 98% 71%, 100% 99%, 77% 97%, 52% 100%, 29% 98%, 0 100%, 2% 73%, 0 48%)" : undefined}}>
            {element.asset_file ? <Img src={staticFile(element.asset_file)} style={{height: "100%", width: "100%", objectFit: element.image_fit, objectPosition: `${element.focal_x}% ${element.focal_y}%`, transform: element.image_motion === "push" ? `scale(${1 + Math.min(1, Math.max(0, frame-element.changedAt)/(fps*8))*0.06})` : element.image_motion === "pan" ? `scale(1.06) translateX(${interpolate(frame-element.changedAt, [0, fps*8], [-2, 2], clamp)}%)` : undefined}} /> : <div style={{color: "#252a30", fontSize: 32}}>Foto: {element.label}</div>}
          </div> : <>
            {element.icon && <EditorialIcon name={element.icon} size={iconSize} color={color} progress={selected ? focus : reveal} />}
            <div style={{width: innerW, flexShrink: 0}}>
            {element.value && <TextBox text={element.value} width={innerW} height={valueH} maxSize={element.value_size} color={color} />}
            <TextBox text={element.label} width={innerW} height={labelH} maxSize={element.label_size ?? (element.kind === "step" ? 38 : 46)} color={color} emphasis={element.emphasis} progress={interpolate(frame-element.emphasisTiming.frame,[0,element.emphasisTiming.duration],[0,1],clamp)} />
            {element.detail && <TextBox text={element.detail} width={innerW} height={detailH} maxSize={34} color={MUTED} />}
            </div>
          </>}
          {selected && !["photo","source_excerpt","chart"].includes(element.kind) && <div style={{position: "absolute", left: padding, bottom: 3, width: (box.w-padding*2)*focus, height: active?.prominence === "support" ? 2 : 4, background: accent}} />}
        </div>;
      })}
    </div>
  </AbsoluteFill>;
};
