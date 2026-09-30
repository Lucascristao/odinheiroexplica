import "@fontsource/inter/700.css";
import type {CSSProperties, ReactNode} from "react";
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from "remotion";

const GOLD = "#ffbd19";
const WHITE = "#f7f7f3";
const MUTED = "#aab2bb";
const ease = Easing.bezier(0.22, 1, 0.36, 1);
const clamped = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;

const range = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, end], [0, 1], {...clamped, easing: ease});

const titleStyle: CSSProperties = {
  color: WHITE,
  fontFamily: "Inter, Arial, sans-serif",
  fontWeight: 700,
  lineHeight: 0.95,
  letterSpacing: -5,
};

const Caption = ({children, x, y, opacity = 1}: {children: ReactNode; x: number; y: number; opacity?: number}) => (
  <div style={{position: "absolute", left: x, top: y, opacity, color: MUTED, font: "700 30px Inter, Arial, sans-serif", letterSpacing: 3}}>
    {children}
  </div>
);

const Wheat = ({progress}: {progress: number}) => (
  <svg viewBox="0 0 260 340" width="260" height="340" fill="none" stroke={GOLD} strokeWidth="13" strokeLinecap="round" strokeLinejoin="round">
    <path d="M130 312V45" strokeDasharray="270" strokeDashoffset={270 * (1 - progress)} />
    {[[128, 88, 72, 45], [132, 130, 190, 83], [128, 175, 68, 126], [132, 220, 191, 167]].map(([x1,y1,x2,y2], i) => (
      <path key={i} d={`M${x1} ${y1} Q${(x1+x2)/2} ${y2 + 24} ${x2} ${y2}`} opacity={range(progress, i * 0.16, i * 0.16 + 0.44)} />
    ))}
  </svg>
);

const Truck = ({progress}: {progress: number}) => (
  <svg width="390" height="240" viewBox="0 0 390 240" fill="none" stroke={WHITE} strokeWidth="11" strokeLinejoin="round">
    <path d="M20 50H230V165H20Z M230 90H305L360 145V165H230Z" strokeDasharray="950" strokeDashoffset={950 * (1 - progress)} />
    <circle cx="88" cy="174" r="31" fill="#0d1116" opacity={progress} />
    <circle cx="294" cy="174" r="31" fill="#0d1116" opacity={progress} />
    <path d="M268 104H299L330 136H268Z" fill={GOLD} stroke="none" opacity={progress} />
  </svg>
);

const Basket = ({progress}: {progress: number}) => (
  <svg width="420" height="340" viewBox="0 0 420 340" fill="none" stroke={WHITE} strokeWidth="12" strokeLinecap="round" strokeLinejoin="round">
    <path d="M55 128H365L323 292H97Z M118 128L174 42 M302 128L246 42" strokeDasharray="1000" strokeDashoffset={1000 * (1 - progress)} />
    {[150, 210, 270].map((x) => <path key={x} d={`M${x} 166L${x} 255`} stroke={GOLD} opacity={progress} />)}
  </svg>
);

/**
 * A silent art-direction proof. It deliberately uses a continuous camera and
 * causal transformations instead of the daily engine's repeated card layout.
 * No numerical claim is made: production data and narration belong to the
 * episode-specific editorial plan.
 */
export const MotionDesignProof = () => {
  const frame = useCurrentFrame();
  const camera = interpolate(frame, [0, 60, 165, 300, 425], [0, 0, -610, -1500, -2200], clamped);
  const route = range(frame, 72, 355);
  const first = range(frame, 0, 34);
  const wheat = range(frame, 112, 170);
  const truck = range(frame, 218, 270);
  const basket = range(frame, 340, 400);
  const final = range(frame, 425, 465);

  return (
    <AbsoluteFill style={{overflow: "hidden", background: "#0d1116", fontFamily: "Inter, Arial, sans-serif"}}>
      <AbsoluteFill style={{background: "radial-gradient(ellipse at 50% 50%, #26301f 0%, #11171b 42%, #0d1116 80%)", opacity: 0.6}} />
      <div style={{position: "absolute", top: 50, left: 78, zIndex: 20, color: WHITE, fontSize: 26, fontWeight: 700}}>
        <span style={{color: GOLD}}>●</span> O Dinheiro Explica <span style={{color: MUTED, marginLeft: 30, fontSize: 20}}>ESTUDO DE MOTION DESIGN</span>
      </div>

      <div style={{position: "absolute", left: camera, top: 0, width: 4200, height: 1080}}>
        <svg width="4200" height="1080" style={{position: "absolute", inset: 0}}>
          <path d="M410 610 C630 610 660 615 820 615 S1130 615 1420 615 S1790 615 2060 615 S2480 615 2950 615"
            stroke="#3b444d" strokeWidth="8" fill="none" />
          <path d="M410 610 C630 610 660 615 820 615 S1130 615 1420 615 S1790 615 2060 615 S2480 615 2950 615"
            stroke={GOLD} strokeWidth="11" fill="none" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - route} />
        </svg>

        <div style={{position: "absolute", left: 105, top: 285, width: 530, opacity: first, transform: `translateY(${(1-first)*42}px)`}}>
          <Caption x={5} y={0}>01 / CÂMBIO</Caption>
          <div style={{...titleStyle, position: "absolute", top: 85, left: 0, fontSize: 107}}>Se o dólar<br /><span style={{color: GOLD}}>sobe...</span></div>
          <div style={{position: "absolute", top: 297, left: 0, width: 220, height: 220, borderRadius: "50%", border: `12px solid ${GOLD}`, display: "grid", placeItems: "center", color: GOLD, fontSize: 136, fontWeight: 700, background: "#10171b", boxShadow: `0 0 ${70 * route}px #ffbd1955`}}>$</div>
        </div>

        <div style={{position: "absolute", left: 920, top: 305, width: 680, height: 560}}>
          <Caption x={0} y={0} opacity={wheat}>02 / INSUMOS</Caption>
          <div style={{...titleStyle, position: "absolute", top: 82, left: 0, fontSize: 91, opacity: wheat}}>O custo<br />entra na cadeia.</div>
          <div style={{position: "absolute", top: 265, left: 80, transform: `translateY(${(1-wheat)*70}px)`, opacity: wheat}}><Wheat progress={wheat} /></div>
          <div style={{position: "absolute", top: 335, left: 375, color: WHITE, fontSize: 52, fontWeight: 700, opacity: wheat}}>trigo<br /><span style={{color: MUTED, fontSize: 30}}>importado</span></div>
        </div>

        <div style={{position: "absolute", left: 1780, top: 305, width: 700, height: 570}}>
          <Caption x={0} y={0} opacity={truck}>03 / TRANSPORTE</Caption>
          <div style={{...titleStyle, position: "absolute", top: 82, left: 0, fontSize: 91, opacity: truck}}>E percorre<br />o país.</div>
          <div style={{position: "absolute", top: 310, left: 100, transform: `translateX(${(1-truck)*110}px)`, opacity: truck}}><Truck progress={truck} /></div>
        </div>

        <div style={{position: "absolute", left: 2715, top: 305, width: 760, height: 600}}>
          <Caption x={0} y={0} opacity={basket}>04 / CONSEQUÊNCIA</Caption>
          <div style={{...titleStyle, position: "absolute", top: 80, left: 0, fontSize: 88, opacity: basket}}>Parte do custo<br /><span style={{color: GOLD}}>pode chegar.</span></div>
          <div style={{position: "absolute", top: 286, left: 170, transform: `scale(${0.85 + basket * 0.15})`, opacity: basket}}><Basket progress={basket} /></div>
        </div>
      </div>

      <div style={{position: "absolute", bottom: 55, left: 80, right: 80, display: "flex", alignItems: "center", gap: 16, opacity: final}}>
        <div style={{width: 70, height: 5, background: GOLD}} />
        <div style={{color: WHITE, fontWeight: 700, fontSize: 27}}>A câmera acompanha a causa, em vez de trocar cartões.</div>
      </div>
    </AbsoluteFill>
  );
};
