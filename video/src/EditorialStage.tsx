import {SourceExcerpt, NewsDocumentFrame, EditorialChart} from "./EditorialEvidence";
import type {Emphasis} from "../../src/lib/editorial-evidence";
import {EditorialIcon} from "./EditorialIcon";
import {EditorialObject} from "./EditorialObject";
import {EditorialOperation} from "./EditorialOperation";
import {useId, useMemo} from "react";
import {AbsoluteFill, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {useEditorialFont, measureEditorialText} from "./editorial-font";
import {composeText, EDITORIAL_FONT} from "../../src/lib/editorial-typography";
import {entranceMotion, layoutStage, nodeContent, objectContentLayout, pointOnRoute} from "../../src/lib/editorial-layout";
import {editorialStageSchema, kineticWordProgress, type EditorialStage as Stage, type StageEvent} from "../../src/lib/editorial-stage";
import {connectionCycle, documentSupportShadow, surfaceBackground, sustainedTransform} from "./editorial-sustained-motion";

const FONT = EDITORIAL_FONT;
const WHITE = "#f6f7f8";
const GOLD = "#ffbd19";
const MUTED = "#9ba4ae";
const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;

const TextBox = ({text, width, height, maxSize = 42, minSize = 32, color = WHITE, emphasis, progress = 1, kinetic = false, wordProgress = 1}: {emphasis?: Emphasis | null; progress?: number; kinetic?: boolean; wordProgress?: number; text: string; width: number; height: number; maxSize?: number; minSize?: number; color?: string}) => {
  const layout=composeText(text,width,height,maxSize,minSize,measureEditorialText);
  if(!layout.fits) throw new Error(`Texto não cabe na fonte mínima ${minSize}: “${text}” (${Math.ceil(layout.requiredWidth)} × ${Math.ceil(layout.requiredHeight)} px; disponíveis ${Math.floor(width)} × ${Math.floor(height)}).`);
  const {size,lines}=layout;
  const normalized=text.trim().replace(/\s+/g," ");
  const start=emphasis ? normalized.indexOf(emphasis.phrase.trim().replace(/\s+/g," ")) : -1;
  const end=start+(emphasis?.phrase.trim().replace(/\s+/g," ").length??0);
  const wordCount=lines.join(" ").trim().split(/\s+/).length;
  const wordTravel=Math.max(0,Math.min(size*.35,(height-layout.requiredHeight)*.5));
  let cursor=0, wordIndex=0;
  return <div data-text-minimum={minSize} data-text-size={size} style={{fontSize:size,lineHeight:1.18,fontWeight:700,color,whiteSpace:"pre",letterSpacing:0}}>{lines.map((line,i)=>{
    const offset=cursor;cursor+=line.length+1;
    let lineCursor=0;
    return <div key={i}>{line.split(/(\s+)/).filter(Boolean).map((token,index)=>{
      const tokenOffset=offset+lineCursor;lineCursor+=token.length;
      if(/^\s+$/.test(token))return token;
      const p=kinetic?kineticWordProgress(wordProgress,wordIndex,wordCount):1;wordIndex++;
      const a=Math.max(0,start-tokenOffset),b=Math.min(token.length,end-tokenOffset);
      const marked=start>=0&&b>a;
      const markProgress=Math.max(0,Math.min(1,(progress*(end-start)-(tokenOffset+a-start))/Math.max(1,b-a)));
      return <span key={index} data-motion-word={kinetic?wordIndex:undefined} style={{display:"inline-block",opacity:p,transform:kinetic?`translateY(${(1-p)*wordTravel}px) scale(${.76+.24*p})`:undefined,transformOrigin:"left bottom",filter:kinetic&&p<1?`blur(${(1-p)*1.8}px)`:undefined}}>
        {marked?<>{token.slice(0,a)}<span style={{position:"relative",display:"inline-block"}}>
          {token.slice(a,b)}
          {emphasis?.style==="highlight" && <span style={{position:"absolute",inset:0,color:"#101317",background:GOLD,clipPath:`inset(0 ${(1-markProgress)*100}% 0 0)`}}>{token.slice(a,b)}</span>}
          {emphasis?.style!=="highlight" && <span style={{position:"absolute",left:0,top:emphasis?.style==="strike"?"52%":"95%",height:Math.max(3,size*.085),width:`${markProgress*100}%`,background:GOLD}}/>}
        </span>{token.slice(b)}</>:token}
      </span>;
    })}</div>;
  })}</div>;
};

export const EditorialStage = ({stage, beats, title, frameOverride}: {stage: Stage; beats: StageEvent[]; title?: string; frameOverride?: number}) => {
  const accent = GOLD;
  const actualFrame = useCurrentFrame();
  const frame = frameOverride ?? actualFrame;
  const {fps, width, height} = useVideoConfig();
  const ready = useEditorialFont();
  const arrowId = useId().replace(/:/g, "");
  const checkedStage = useMemo(() => editorialStageSchema.parse(stage), [stage]);
  if (!ready) return null;
  const solved=layoutStage(checkedStage,beats,frame,fps,width,height,measureEditorialText,title);
  const {elements,active,canvas,camera}=solved;
  if(solved.issues.length) throw new Error(solved.issues.map(i=>`${i.element??i.connection??"Palco"}: ${i.message}`).join("\n"));
  const routeNodes = new Set(checkedStage.connections.flatMap(({from, to}) => [from, to]));
  const cameraX = (50 - camera.x) * canvas.width * camera.zoom / 100;
  const cameraY = (50 - camera.y) * canvas.height * camera.zoom / 100;
  const rect = (e: typeof elements[number]) => ({x:e.x*canvas.width/100,y:e.y*canvas.height/100,w:e.width*canvas.width/100,h:e.height*canvas.height/100});
  const revealMotion = entranceMotion;
  // Camera capacity is checked in the solver. Never conceal an information
  // box to make an invalid close-up look valid.
  const cameraOpacity = (_e: typeof elements[number]) => 1;
  const focus = checkedStage.motion_profile === "static" ? 1 : interpolate(frame - (active?.resolved_frame ?? 0), [0, (active?.motion_seconds??0.45)*fps], [0, 1], clamp);
  const takeover = active?.prominence === "takeover";
  return <AbsoluteFill style={{fontFamily: FONT}}>
    {checkedStage.show_title && <div style={{position: "absolute", top: 118, left: 130}}>
      <TextBox text={title ?? ""} width={canvas.width} height={90} maxSize={46} minSize={36} />
    </div>}
    <div data-editorial-canvas style={{position: "absolute", left: canvas.x, top: canvas.y, width: canvas.width, height: canvas.height, overflow: "hidden"}}>
    <div style={{position: "absolute", inset: 0, transformOrigin: "50% 50%", transform: `translate(${cameraX}px, ${cameraY}px) scale(${camera.zoom})`}}>
      <svg width={canvas.width} height={canvas.height} style={{position: "absolute", inset: 0}}>
        <defs><marker id={arrowId} markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#78858e" strokeWidth="1.5" /></marker></defs>
        {checkedStage.connections.map((edge, i) => {
          const from = elements.find(e => e.id === edge.from)!;
          const to = elements.find(e => e.id === edge.to)!;
          const cameraAlpha = Math.min(cameraOpacity(from), cameraOpacity(to));
          const presence=(e:typeof from)=>{const p=revealMotion(e,frame).reveal;return e.visible?p:e.wasVisible?1-p:0;};
          if (presence(from)===0 || presence(to)===0 || cameraAlpha === 0) return null;
          const connection=solved.connections[i];
          const path=connection.path;
          const arrival = beats.filter(beat => [edge.from, edge.to].includes(beat.target_id ?? "") && beat.action !== "retire" &&
            typeof beat.resolved_frame === "number" && beat.resolved_frame <= frame).at(-1);
          const routeDuration = Math.max(arrival?.motion_seconds ?? 0.45, 1.15) * fps;
          const sustainedEdge = checkedStage.motion_profile !== "static" && edge.motion !== "once";
          const routeProgress = arrival ? checkedStage.motion_profile === "static" ? 1 : interpolate(frame - arrival.resolved_frame!, [0, routeDuration], [0, 1], clamp) : sustainedEdge ? 1 : 0;
          const cycle = connectionCycle(frame, fps, arrival?.resolved_frame ?? Math.max(from.changedAt, to.changedAt), edge.period_seconds);
          const flow = sustainedEdge && edge.motion === "flow";
          const pulse = sustainedEdge && edge.motion === "pulse" ? 0.38 + 0.62 * Math.pow(Math.sin(cycle * Math.PI), 2) : 1;
          const selected = flow || (checkedStage.motion_profile !== "static" && Boolean(arrival && frame - arrival.resolved_frame! < routeDuration));
          const dot=pointOnRoute(connection.points,flow ? cycle : routeProgress);
          const dotX=dot.x,dotY=dot.y;
          const edgeEnter = Math.min(presence(from),presence(to));
          return <g key={`${edge.from}-${edge.to}-${i}`} opacity={edgeEnter * cameraAlpha * (takeover ? 0.15 : 1)}>
            <path d={path} fill="none" stroke="#45515a" strokeWidth={2} strokeDasharray="8 10" markerEnd={`url(#${arrowId})`} />
            {routeProgress > 0 && <path d={path} fill="none" pathLength={1} stroke={accent} strokeWidth={5} strokeLinecap="round" strokeDasharray={1} strokeDashoffset={1-routeProgress} opacity={pulse * (flow ? 0.45 : 1)} />}
            {flow && <path d={path} fill="none" stroke={accent} strokeWidth={3} strokeLinecap="round" strokeDasharray="10 22" strokeDashoffset={-cycle * 32} opacity={0.8} />}
            {selected && routeProgress > 0 && edge.semantic !== "transfer" && <circle cx={dotX} cy={dotY} r={8} fill={accent} stroke="#101317" strokeWidth={3} />}
            {selected && edge.semantic === "transfer" && [0, 0.22, 0.44].map((delay, coin) => {
              const p = flow ? (cycle + coin / 3) % 1 : (routeProgress - delay) / (1 - delay);
              if (p < 0 || p > 1) return null;
              const {x,y}=pointOnRoute(connection.points,p);
              return <g key={coin} transform={`translate(${x},${y})`}><circle r={edge.token_label?17:9} fill={GOLD} stroke="#101317" strokeWidth={3}/>{edge.token_label&&<text textAnchor="middle" dominantBaseline="central" fontSize={20} fontWeight={700} fill="#101317">{edge.token_label}</text>}</g>;
            })}
            {connection.label && <foreignObject data-connection-id={connection.id} x={connection.label.box.x} y={connection.label.box.y} width={connection.label.box.w} height={connection.label.box.h}>
              <div style={{padding:"8px 10px",boxSizing:"border-box",background:"rgba(10,14,18,.94)",borderRadius:8}}>
                <TextBox text={connection.label.text} width={connection.label.box.w-20} height={connection.label.box.h-16} maxSize={connection.label.layout.size} minSize={30} color={routeProgress===1?accent:MUTED}/>
              </div>
            </foreignObject>}
          </g>;
        })}
      </svg>
      {solved.operation&&<EditorialOperation operation={solved.operation} frame={frame} fps={fps}/>}
      {elements.slice().sort((a,b)=>Number(Boolean(a.overlay_on))-Number(Boolean(b.overlay_on))).map(element => {
        const cameraAlpha = cameraOpacity(element);
        if (cameraAlpha === 0) return null;
        const box = rect(element);
        const isExcerpt = element.kind === "source_excerpt";
        const selected = active?.target_id === element.id && active.action !== "retire";
        const motion = revealMotion(element, frame);
        const reveal = motion.reveal;
        const opacity = (element.visible ? reveal : element.wasVisible ? 1-reveal : 0) * cameraAlpha * (takeover && !selected ? 0.15 : 1);
        if (opacity === 0) return null;

        // Surface follows the information: large figures and causal steps live
        // directly in the scene; only notes and small figures need a panel.
        const isHeroMetric = element.kind === "metric" && element.width >= 40 && !element.overlay_on;
        const isDiagramStep = element.kind === "step" && !element.overlay_on;
        const isCard = element.kind === "note" || (element.kind === "metric" && !isHeroMetric);
        const isRouteNode = !element.overlay_on && routeNodes.has(element.id) && ["step", "note", "metric"].includes(element.kind);

        const cardBg = isRouteNode
          ? (selected ? "radial-gradient(circle at 50% 45%, rgba(255, 189, 25, 0.13), transparent 75%)" : "transparent")
          : isCard
          ? (selected ? "linear-gradient(145deg, rgba(30, 36, 46, 0.96) 0%, rgba(16, 20, 26, 0.98) 100%)" : "linear-gradient(145deg, rgba(20, 25, 32, 0.88) 0%, rgba(12, 15, 20, 0.94) 100%)")
          : (element.overlay_on ? "rgba(12,16,20,0.88)" : undefined);
        const cardBorder = isCard && !isRouteNode
          ? (selected ? "2px solid #FFBD19" : "1px solid rgba(255, 255, 255, 0.10)")
          : undefined;
        const cardShadow = isCard && !isRouteNode
          ? (selected ? "0 10px 26px rgba(0,0,0,0.65)" : "0 12px 30px rgba(0, 0, 0, 0.6)")
          : undefined;

        const content=nodeContent(element,box,isRouteNode);
        const objectContent=element.kind==="object"?objectContentLayout(element,box,measureEditorialText):undefined;
        const {wide:isWideBanner,stacked,padding,iconSize,innerW,valueH,detailH,labelH}=content;
        const cardPadding = checkedStage.full_bleed_news && element.kind === "photo" ? 0 : padding;

        const cueProgress = checkedStage.motion_profile === "static" ? 1 : interpolate(frame - element.cueFrame, [0, element.cueDuration], [0, 1], clamp);
        const cueEase = cueProgress * cueProgress * (3 - 2 * cueProgress);
        const actuationProgress = checkedStage.motion_profile === "static" ? 1 : interpolate(frame - element.actuationFrame, [0, element.actuationDuration], [0, 1], clamp);
        const lockProgress = checkedStage.motion_profile === "static" ? 1 : interpolate(frame - element.lockFrame, [0, element.lockDuration], [0, 1], clamp);
        const sustain = checkedStage.motion_profile === "static" ? undefined : element.sustain;
        const mediaSustain = checkedStage.elements.some(child=>child.overlay_on===element.id) ? undefined : sustain;
        const surface = surfaceBackground(element.surface, selected ? cueEase : 0, frame, fps, sustain, element.changedAt);
        // An authored surface also opts out of the legacy panel/rule styling.
        // `none` means clean typography/art; glow remains light, not a card.
        const authoredSurface = element.surface !== undefined;
        // Treatments alter the targeted information at its authored cue. Their
        // transforms stay inside the reserved box, preserving complete framing.
        const giantNumber = element.treatment === "giant_number";
        const kineticLabel = checkedStage.motion_profile !== "static" && element.treatment === "kinetic_type" && ["focus", "reveal", "update"].includes(element.cueAction ?? "");
        const maskedEmphasis = element.treatment === "masked_emphasis" && !element.emphasis;
        const color = selected && active?.prominence !== "support" ? accent : WHITE;
        // Facts are displayed exactly as authored. String parsing cannot infer
        // whether a changing amount is a measured fact or a didactic counter.
        const displayedValue = element.value;

        // Entrances follow speech cues; continued motion requires the author's
        // explicit sustain/connection direction and stays inside media boxes.
        const scalePop = motion.scale;
        const translateY = motion.y;
        const translateX = motion.x;

        return (
          <div
            key={element.id}
            data-element-id={element.id}
            style={{
              position: "absolute",
              left: box.x,
              top: box.y,
              width: box.w,
              height: box.h,
              padding: cardPadding,
              opacity,
              zIndex: element.overlay_on ? 2 : 1,
              background: authoredSurface ? (!["photo","object"].includes(element.kind) ? surface : undefined) : cardBg,
              border: authoredSurface ? undefined : cardBorder,
              borderLeft: !authoredSurface && isDiagramStep && !isRouteNode ? `5px solid ${selected ? GOLD : "#45515a"}` : undefined,
              boxShadow: isExcerpt && authoredSurface ? documentSupportShadow(element.surface,frame,fps,sustain,element.changedAt) : authoredSurface ? undefined : cardShadow,
              borderRadius: isExcerpt && authoredSurface ? 8 : isCard && !isRouteNode ? 18 : (element.overlay_on ? 12 : undefined),
              transform: `translate(${translateX}px, ${translateY}px) scale(${scalePop})`,
              boxSizing: "border-box",
              display: "flex",
              flexDirection: isWideBanner ? "row" : stacked ? "column" : "row",
              alignItems: stacked && element.content_layout !== "column" ? "flex-start" : "center",
              justifyContent: isWideBanner ? "flex-start" : "center",
              gap: element.icon ? 20 : 0,
            }}
          >
            {element.kind === "source_excerpt" ? (
              checkedStage.full_bleed_news ? (
                <NewsDocumentFrame
                  element={element}
                  view={element.view}
                  markIds={element.markIds}
                  markProgress={Object.fromEntries(
                    Object.entries(element.markTiming).map(([id, t]) => [
                      id,
                      interpolate(frame - t.frame, [0, t.duration], [0, 1], clamp),
                    ])
                  )}
                  width={box.w-cardPadding*2}
                  height={box.h-cardPadding*2}
                />
              ) : (
                <SourceExcerpt
                  element={element}
                  view={element.view}
                  markIds={element.markIds}
                  markProgress={Object.fromEntries(
                    Object.entries(element.markTiming).map(([id, t]) => [
                      id,
                      interpolate(frame - t.frame, [0, t.duration], [0, 1], clamp),
                    ])
                  )}
                />
              )
            )
            ) : element.kind === "chart" && element.chart ? (
              <EditorialChart
                chart={element.chart}
                title={element.label}
                width={box.w - 32}
                height={box.h - 32}
                focus={element.chartFocus}
                progress={cueProgress}
                revealTo={element.chart_reveal_to}
                revealFrom={element.chartRevealFrom}
                revealProgress={checkedStage.motion_profile === "static" ? 1 : interpolate(frame - element.chartRevealFrame, [0, element.chartRevealDuration], [0, 1], clamp)}
              />
            ) : element.kind === "object" && element.object_type ? (
              <div style={{width: "100%", height: "100%", display: "flex", flexDirection: "column"}}>
                <div style={{flex: 1, minHeight: 0, position:"relative", clipPath:motion.clip}}>
                  {surface && <div data-editorial-surface={element.surface} aria-hidden style={{position:"absolute",inset:0,background:surface,borderRadius:element.surface==="paper"?6:0}} />}
                  <div style={{width:"100%",height:"100%",position:"relative",transform:sustainedTransform(mediaSustain,frame,fps,objectContent!.media.w,objectContent!.media.h,element.changedAt),transformOrigin:"center"}}>
                    {element.clip_file ? <OffthreadVideo muted src={staticFile(element.clip_file)} style={{width:"100%",height:"100%",objectFit:"contain"}} /> : <EditorialObject type={element.object_type} accent={accent} progress={reveal} emphasisProgress={cueEase} active={selected && checkedStage.motion_profile !== "static"} actuation={element.actuation} actuationProgress={actuationProgress} locked={element.locked} lockFrom={element.lockFrom} lockProgress={lockProgress} contentFraction={element.content_fraction} motion={checkedStage.motion_profile === "static" ? "none" : element.svg_motion} />}
                  </div>
                </div>
                {objectContent!.label && <div style={{height:objectContent!.labelHeight,marginTop:objectContent!.gap,flexShrink:0}}><TextBox text={element.label} width={objectContent!.width} height={objectContent!.labelHeight} maxSize={objectContent!.label.size} kinetic={kineticLabel} wordProgress={cueProgress} /></div>}
              </div>
            ) : element.kind === "photo" ? (
              <div
                style={{
                  position: "relative",
                  width: "100%",
                  height: "100%",
                  padding: element.photo_style === "paper" ? 14 : 0,
                  boxSizing:"border-box",
                  overflow: "hidden",
                  background: surface ?? (element.photo_style === "paper" ? "#eee8dc" : "transparent"),
                  clipPath: element.photo_style === "paper" ? "polygon(1% 2%, 18% 0, 35% 2%, 51% 0, 72% 2%, 99% 0, 98% 23%, 100% 47%, 98% 71%, 100% 99%, 77% 97%, 52% 100%, 29% 98%, 0 100%, 2% 73%, 0 48%)" : undefined,
                }}
              >
                <div style={{width:"100%",height:"100%",transform:sustainedTransform(mediaSustain,frame,fps,Math.max(1,box.w-cardPadding*2-(element.photo_style==="paper"?28:0)),Math.max(1,box.h-cardPadding*2-(element.photo_style==="paper"?28:0)),element.changedAt),transformOrigin:"center",overflow:"hidden"}}>{element.asset_file ? (
                  <Img
                    src={staticFile(element.asset_file)}
                    style={{
                      height: "100%",
                      width: "100%",
                      objectFit: element.image_fit,
                      objectPosition: `${element.focal_x}% ${element.focal_y}%`,
                      transform: checkedStage.motion_profile === "static" ? undefined : element.image_motion === "push" ? `scale(${1 + Math.min(1, Math.max(0, frame - element.changedAt) / (fps * 8)) * 0.06})` : element.image_motion === "pan" ? `translateX(${-3 + 6 * Math.min(1, Math.max(0, frame - element.changedAt) / (fps * 12))}%) scale(1.12)` : undefined,
                    }}
                  />
                ) : (
                  <div style={{color: "#252a30", fontSize: 32}}>Foto: {element.label}</div>
                )}</div>
              </div>
            ) : (
              <>
                {element.icon && (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      width: iconSize + 12,
                      height: iconSize + 12,
                      borderRadius: element.surface === "none" ? undefined : "50%",
                      background: element.surface === "none" ? undefined : selected ? "rgba(255, 189, 25, 0.16)" : "rgba(255, 255, 255, 0.05)",
                      boxShadow: element.surface !== "none" && selected ? "0 0 20px rgba(255, 189, 25, 0.35)" : undefined,
                      flexShrink: 0,
                      clipPath:motion.clip,
                    }}
                  >
                    <div style={{width:iconSize,height:iconSize,transform:sustainedTransform(sustain,frame,fps,iconSize,iconSize,element.changedAt),transformOrigin:"center"}}>
                      <EditorialIcon name={element.icon} size={iconSize} color={color} progress={reveal} emphasisProgress={cueEase} active={selected && checkedStage.motion_profile !== "static"} actuation={element.actuation} actuationProgress={actuationProgress} locked={element.locked} lockFrom={element.lockFrom} lockProgress={lockProgress} motion={checkedStage.motion_profile === "static" || element.svg_motion === "none" ? "none" : element.svg_motion === "trace" ? "draw" : undefined} />
                    </div>
                  </div>
                )}
                <div style={{width: innerW, flexShrink: 0, display: "flex", flexDirection: "column", justifyContent: "center"}}>
                  {element.value && (
                    <div style={{marginBottom: 4, transformOrigin:"left center", transform: giantNumber ? `scale(${0.9 + 0.1 * cueEase})` : undefined}}>
                      <TextBox
                        text={displayedValue ?? element.value}
                        width={innerW}
                        height={valueH}
                        minSize={48}
                        maxSize={isHeroMetric || giantNumber ? Math.max(108, element.value_size ?? 72) : element.value_size ?? 52}
                        color={GOLD}
                      />
                    </div>
                  )}
                  <TextBox
                    text={element.label}
                    width={innerW}
                    height={labelH}
                    maxSize={element.label_size ?? (isHeroMetric ? 58 : element.kind === "step" ? 38 : 46)}
                    color={WHITE}
                    kinetic={kineticLabel}
                    wordProgress={cueProgress}
                    emphasis={maskedEmphasis ? {phrase:element.label,style:"highlight"} : element.emphasis}
                    progress={checkedStage.motion_profile === "static" ? 1 : maskedEmphasis ? cueEase : interpolate(
                      frame - element.emphasisTiming.frame,
                      [0, element.emphasisTiming.duration],
                      [0, 1],
                      clamp
                    )}
                  />
                  {element.detail && (
                    <div style={{marginTop: 6}}>
                      <TextBox
                        text={element.detail}
                        width={innerW}
                        height={detailH}
                        maxSize={30}
                        minSize={28}
                        color={MUTED}
                      />
                    </div>
                  )}
                </div>
              </>
            )}
            {selected && !authoredSurface && !maskedEmphasis && !element.emphasis && !["photo", "source_excerpt", "chart"].includes(element.kind) && (
              <div
                style={{
                  position: "absolute",
                  left: cardPadding,
                  bottom: 3,
                  width: (box.w - cardPadding * 2) * focus,
                  height: active?.prominence === "support" ? 2 : 4,
                  background: accent,
                  borderRadius: 2,
                }}
              />
            )}
          </div>
        );
      })}
    </div>
    </div>
    {solved.photo_captions.map(caption => {
      const element=elements.find(e=>e.id===caption.id)!;
      // Screen-space caption capacity is solved and validated with the photo's
      // current transform; an insufficient region fails instead of disappearing.
      const p=revealMotion(element,frame).reveal;
      return <div key={`caption-${element.id}`} data-photo-caption-id={element.id} style={{position: "absolute", left: caption.box.x, top: caption.box.y, width: caption.box.w, height: caption.box.h, padding: "10px 12px", boxSizing: "border-box", borderRadius: 8, background: "rgba(8,12,16,0.88)", opacity: element.visible?p:element.wasVisible?1-p:0}}>
        <TextBox text={caption.text} width={caption.box.w-24} height={64} maxSize={27} minSize={24} />
      </div>;
    })}
  </AbsoluteFill>;
};
