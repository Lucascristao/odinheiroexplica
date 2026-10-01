import type {ReactNode} from "react";
import type {StageElement} from "../../src/lib/editorial-stage";
import {svgEmphasis, svgPhase} from "./editorial-svg-motion";

const Layer = ({children, progress, start = 0, end = 1, y = 0, name}: {
  children: ReactNode; progress: number; start?: number; end?: number; y?: number; name: string;
}) => {
  const p = svgPhase(progress, start, end);
  return <g data-svg-layer={name} opacity={p} transform={`translate(0 ${y * (1 - p)})`}>{children}</g>;
};

const Trace = ({d, stroke, width, progress, start = 0, end = 1}: {
  d: string; stroke: string; width: number; progress: number; start?: number; end?: number;
}) => <path d={d} fill="none" stroke={stroke} strokeWidth={width} strokeLinecap="round" pathLength={1}
  strokeDasharray={1} strokeDashoffset={1 - svgPhase(progress, start, end)} />;

const FocusTrace = ({d, progress, emphasis}: {d: string; progress: number; emphasis: number}) =>
  emphasis > 0 ? <g opacity={emphasis * 0.72}><Trace d={d} stroke="#fff4cf" width={5} progress={progress} end={0.72} /></g> : null;

// Original schematic illustrations, assembled at their reveal cue. These are
// primitives for the authored scene, not a mandatory motion template. Focusing
// an object never hides/rebuilds it, changes a value or starts an ambient loop.
export const EditorialObject = ({type, accent, progress, emphasisProgress = 1, active = false, motion = "assemble"}: {
  type: NonNullable<StageElement["object_type"]>;
  accent: string;
  progress: number;
  emphasisProgress?: number;
  active?: boolean;
  motion?: "assemble" | "trace" | "none";
}) => {
  const layers = motion === "assemble" ? progress : 1;
  const strokes = motion === "none" ? 1 : progress;
  const enter = svgPhase(layers);
  const emphasis = motion === "none" ? 0 : svgEmphasis(emphasisProgress, active);
  return <svg data-svg-motion={motion} data-object-type={type} aria-hidden viewBox="0 0 400 400" width="100%" height="100%">
    <ellipse cx="200" cy="359" rx={132 + enter * 7} ry="15" fill="#000" opacity={0.28 * enter} />
    <g transform={`translate(0 ${8 * (1 - enter)})`} strokeLinejoin="round">
      {type === "factory" && <>
        <Layer name="chimney" progress={layers} end={0.58} y={7}>
          <path d="M83 72 H125 L139 237 H69 Z" fill="#647a7b" stroke="#a2b6b4" strokeWidth="5" />
        </Layer>
        <Layer name="building" progress={layers} start={0.1} end={0.66} y={5}>
          <path d="M61 216 L143 168 V216 L225 168 V216 L307 168 V328 H61 Z" fill="#354b50" stroke="#9eb5b4" strokeWidth="6" />
          <rect x="162" y="288" width="58" height="40" rx="3" fill="#17272d" />
        </Layer>
        {[89, 165, 241].map((x, i) => <Layer key={x} name={`window-${i}`} progress={layers} start={0.36 + i * 0.1} end={0.7 + i * 0.1} y={4}>
          <rect x={x} y="238" width="38" height="40" rx="3" fill={accent} />
          {emphasis > 0 && <rect x={x} y="238" width="38" height="40" rx="3" fill="#fff4cf" opacity={emphasis * 0.34} />}
        </Layer>)}
        <Trace d="M55 339 H342" stroke="#647a7b" width={12} progress={strokes} start={0.16} end={0.76} />
        <FocusTrace d="M65 216 L143 171 M147 216 L225 171 M229 216 L307 171" progress={emphasisProgress} emphasis={emphasis} />
      </>}
      {type === "truck" && <>
        <Layer name="cargo" progress={layers} end={0.62} y={5}>
          <rect x="37" y="119" width="216" height="165" rx="12" fill="#405b62" stroke="#a2b6b4" strokeWidth="6" />
        </Layer>
        <Layer name="cab" progress={layers} start={0.16} end={0.74} y={5}>
          <path d="M253 169 H302 L359 231 V285 H253 Z" fill={accent} stroke="#a2b6b4" strokeWidth="5" />
          <path d="M271 187 H295 L328 225 H271 Z" fill="#152730" />
        </Layer>
        <Trace d="M38 286 H363" stroke="#647a7b" width={13} progress={strokes} start={0.2} end={0.8} />
        {[92, 302].map((x, i) => <Layer key={x} name={`wheel-${i}`} progress={layers} start={0.36 + i * 0.1} end={0.8 + i * 0.1}>
          <circle cx={x} cy="292" r="34" fill="#111a20" stroke="#8ca09f" strokeWidth="6" />
          <circle cx={x} cy="292" r="13" fill="#8ca09f" />
        </Layer>)}
        <Trace d="M67 152 H224 M67 174 H224" stroke="#829996" width={6} progress={strokes} start={0.4} end={0.96} />
        <FocusTrace d="M255 169 H302 L359 231 V285" progress={emphasisProgress} emphasis={emphasis} />
      </>}
      {type === "package" && <>
        <Layer name="left-face" progress={layers} end={0.64} y={5}>
          <path d="M65 125 L200 188 V332 L65 266 Z" fill="#746346" stroke="#c4ac82" strokeWidth="5" />
        </Layer>
        <Layer name="right-face" progress={layers} start={0.12} end={0.72} y={4}>
          <path d="M200 188 L335 125 V266 L200 332 Z" fill="#927b55" stroke="#c4ac82" strokeWidth="5" />
        </Layer>
        <Layer name="top-face" progress={layers} start={0.24} end={0.8} y={-5}>
          <path d="M65 125 L200 66 L335 125 L200 188 Z" fill="#a38c66" stroke="#e0c99c" strokeWidth="5" />
        </Layer>
        <Layer name="seal" progress={layers} start={0.48} end={0.96}>
          <path d="M134 96 L267 156 L267 211 L231 228 V173 L99 113 Z" fill={accent} />
          <path d="M97 191 L162 223 V254 L97 222 Z" fill="#e9ddbf" />
        </Layer>
        <FocusTrace d="M134 96 L267 156 V211 M97 191 L162 223" progress={emphasisProgress} emphasis={emphasis} />
      </>}
      {type === "component" && <>
        <Layer name="board" progress={layers} end={0.54}>
          <path d="M70 88 H330 V312 H70 Z" fill="#24423a" stroke="#7faaa0" strokeWidth="6" />
        </Layer>
        {[110, 150, 190, 230, 270].map((x, i) => <Trace key={x} d={`M${x} 66 V102 M${x} 300 V336`} stroke={accent} width={8} progress={strokes} start={0.2 + i * 0.055} end={0.7 + i * 0.055} />)}
        <Trace d="M94 146 H136 V184 M308 246 H270 V218 M92 268 H142 V236 M305 126 H265 V160" stroke="#7faaa0" width={7} progress={strokes} start={0.26} end={0.92} />
        <Layer name="chip" progress={layers} start={0.32} end={0.82} y={4}>
          <rect x="144" y="148" width="112" height="108" rx="12" fill="#10191d" stroke={accent} strokeWidth="5" />
        </Layer>
        <Trace d="M176 177 H224 M176 195 H213 M176 213 H224" stroke="#b5cec7" width={7} progress={strokes} start={0.55} end={1} />
        <Layer name="contacts" progress={layers} start={0.6}>
          {[94, 305].map(x => <circle key={x} cx={x} cy="290" r="7" fill={accent} />)}
        </Layer>
        <FocusTrace d="M94 146 H136 V184 M308 246 H270 V218 M305 126 H265 V160" progress={emphasisProgress} emphasis={emphasis} />
      </>}
      {type === "receipt" && <>
        <Layer name="paper" progress={layers} end={0.56} y={5}>
          <path d="M90 36 H310 V348 L288 336 L266 348 L244 336 L222 348 L200 336 L178 348 L156 336 L134 348 L112 336 L90 348 Z" fill="#f0ebe1" />
        </Layer>
        {["M125 88 H275", "M125 120 H235", "M125 174 H275", "M125 203 H247"].map((d, i) =>
          <Trace key={d} d={d} stroke="#a3aaa9" width={12} progress={strokes} start={0.2 + i * 0.1} end={0.6 + i * 0.1} />)}
        <Layer name="receipt-signal" progress={layers} start={0.55} end={0.96} y={4}>
          <circle cx="257" cy="282" r="59" fill={accent} />
          <Trace d="M257 248 V286 M257 303 V309" stroke="#111a1c" width={11} progress={strokes} start={0.66} />
        </Layer>
        <FocusTrace d="M125 174 H275 M125 203 H247" progress={emphasisProgress} emphasis={emphasis} />
        {emphasis > 0 && <circle cx="257" cy="282" r="55" fill="none" stroke="#fff4cf" strokeWidth="4" opacity={emphasis * 0.7} />}
      </>}
      {type === "wallet" && <>
        <Layer name="back-note" progress={layers} end={0.62} y={8}>
          <rect x="112" y="74" width="160" height="170" rx="8" fill={accent} transform="rotate(-12 192 160)" />
        </Layer>
        <Layer name="front-note" progress={layers} start={0.14} end={0.74} y={7}>
          <rect x="146" y="70" width="160" height="170" rx="8" fill="#8da99a" transform="rotate(8 226 155)" />
        </Layer>
        <Layer name="wallet-body" progress={layers} start={0.18} end={0.76} y={4}>
          <rect x="47" y="146" width="305" height="194" rx="25" fill="#35444b" />
        </Layer>
        <Layer name="stitching" progress={layers} start={0.45} end={0.94}>
          <path d="M72 172 H329 M72 313 H329" stroke="#65767d" strokeWidth="3" strokeDasharray="8 6" />
        </Layer>
        <Layer name="latch" progress={layers} start={0.56} y={3}>
          <rect x="265" y="209" width="101" height="68" rx="15" fill={accent} />
          <circle cx="293" cy="243" r="10" fill="#35444b" />
        </Layer>
        <FocusTrace d="M280 211 H349 Q364 211 364 226 V262 Q364 275 349 275 H280" progress={emphasisProgress} emphasis={emphasis} />
      </>}
      {type === "bank" && <>
        <Layer name="roof" progress={layers} end={0.6} y={-5}>
          <path d="M35 127 L200 44 L365 127 Z" fill={accent} />
          <circle cx="200" cy="96" r="15" fill="#24353b" />
        </Layer>
        {[79, 153, 227, 301].map((x, i) => <Layer key={x} name={`column-${i}`} progress={layers} start={0.18 + i * 0.085} end={0.66 + i * 0.085} y={5}>
          <rect x={x - 17} y="144" width="34" height="163" rx="5" fill="#bcc8c9" />
        </Layer>)}
        <Trace d="M47 322 H353" stroke="#62757c" width={18} progress={strokes} start={0.36} end={0.84} />
        <Trace d="M31 343 H369" stroke="#62757c" width={18} progress={strokes} start={0.5} />
        <FocusTrace d="M40 125 L200 44 L360 125" progress={emphasisProgress} emphasis={emphasis} />
      </>}
    </g>
  </svg>;
};
