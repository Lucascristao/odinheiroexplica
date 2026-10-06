import type {ReactNode} from "react";
import type {StageElement, StageEvent} from "../../src/lib/editorial-stage";
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

const Actuation = ({kind, progress, x, y, accent, locked, lockFrom, lockProgress}: {kind: StageEvent["actuation"]; progress: number; x: number; y: number; accent: string; locked?: boolean; lockFrom?: boolean; lockProgress?: number}) => {
  const p = svgPhase(progress), wave = p > 0 && p < 1 ? Math.sin(Math.PI * p) : 0;
  if (!kind && locked === undefined) return null;
  const lockState = locked ?? (kind === "lock" ? true : kind === "unlock" ? false : undefined);
  const fromLocked = lockFrom ?? (kind !== "lock");
  const opened = (fromLocked ? 0 : 1) + ((lockState ? 0 : 1) - (fromLocked ? 0 : 1)) * svgPhase(lockProgress ?? progress);
  return <g data-object-actuation={kind} transform={`translate(${x} ${y})`} strokeLinecap="round" strokeLinejoin="round">
    {kind === "tap" && wave > 0 && <g opacity={wave}><circle r={8 + 18 * wave} fill="none" stroke={accent} strokeWidth="4" /><path d="M25 24 L4 3" fill="none" stroke="#fff4cf" strokeWidth="7" /><circle r="6" fill={accent} /></g>}
    {lockState !== undefined && <g fill="#17272d" stroke={accent} strokeWidth="4">
      <rect x="-15" y="-3" width="30" height="25" rx="4" />
      <path d="M-9 -3 V-13 A9 9 0 0 1 9 -13 V-3" fill="none" transform={`rotate(${opened*34} 9 -3)`} />
      <path d="M0 6 V13" />
    </g>}
    {kind === "confirm" && p > 0 && <><circle r="24" fill="#17272d" stroke={accent} strokeWidth="3" /><Trace d="M-12 0 L-3 9 L13 -10" stroke={accent} width={6} progress={p} /></>}
    {kind === "signal" && wave > 0 && <g opacity={wave}><Trace d="M-25 -20 Q-43 0 -25 20 M25 -20 Q43 0 25 20" stroke={accent} width={5} progress={p} /></g>}
  </g>;
};

// Original schematic illustrations, assembled at their reveal cue. These are
// primitives for the authored scene, not a mandatory motion template. Focusing
// an object never hides/rebuilds it, changes a value or starts an ambient loop.
export const EditorialObject = ({type, accent, progress, emphasisProgress = 1, active = false, motion = "assemble", actuation, actuationProgress = 1, locked, lockFrom, lockProgress, contentFraction = 1}: {
  type: NonNullable<StageElement["object_type"]>;
  accent: string;
  progress: number;
  emphasisProgress?: number;
  active?: boolean;
  motion?: "assemble" | "trace" | "none";
  actuation?: StageEvent["actuation"];
  actuationProgress?: number;
  locked?: boolean;
  lockFrom?: boolean;
  lockProgress?: number;
  contentFraction?: number;
}) => {
  const layers = motion === "assemble" ? progress : 1;
  const strokes = motion === "none" ? 1 : progress;
  const enter = svgPhase(layers);
  const emphasis = motion === "none" ? 0 : svgEmphasis(emphasisProgress, active);
  const action = svgPhase(actuationProgress);
  const countWave = actuation === "count" && action > 0 && action < 1 ? Math.sin(Math.PI * action) : 0;
  const actuationAnchor: Record<NonNullable<StageElement["object_type"]>, [number, number]> = {
    factory:[184,252],truck:[307,246],package:[260,178],component:[200,201],receipt:[257,282],wallet:[293,243],bank:[200,96],
    atm:[200,131],cash:[230,202],branch:[200,251],hub:[200,190],data:[200,184],store:[242,254],phone:[200,154],terminal:[200,142],grocery_package:[270,210],
  };
  const actionAnchor = actuation === "tap" ? type === "atm" ? [177,207] : type === "phone" ? [200,266] : type === "terminal" ? [247,288] : actuationAnchor[type] : actuationAnchor[type];
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
      {type === "grocery_package" && <>
        <Layer name="pouch" progress={layers} end={0.62} y={8}>
          <path d="M99 58 H301 L286 110 L312 330 Q200 354 88 330 L114 110 Z" fill="#252b32" stroke="#f6f7f8" strokeWidth="5" />
          <path d="M99 58 H301 L291 89 H109 Z" fill={accent} />
          <path d="M111 109 H289" stroke="#8b929a" strokeWidth="5" />
        </Layer>
        <Layer name="window" progress={layers} start={0.16} end={0.78}>
          <rect x="125" y="150" width="150" height="160" rx="12" fill="#101317" stroke="#89949e" strokeWidth="3" />
          <svg x="133" y="158" width="134" height="144" viewBox="0 0 134 144" overflow="hidden">
            <rect data-package-content="true" x="0" y={144*(1-contentFraction)} width="134" height={144*contentFraction} fill={accent} />
            {[0,1,2,3,4,5].map(row=><path key={row} d={`M8 ${139-row*24} H126`} stroke="#101317" strokeWidth="3" opacity={Math.max(0,Math.min(1,(contentFraction-row/6)*6))} />)}
          </svg>
          <path d="M131 131 H269" stroke="#f6f7f8" strokeWidth="7" strokeLinecap="round" />
        </Layer>
        <FocusTrace d="M99 58 H301 M125 310 H275" progress={emphasisProgress} emphasis={emphasis} />
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
      {type === "atm" && <>
        <Layer name="atm-cabinet" progress={layers} end={0.62} y={7}>
          <path d="M117 43 H283 V349 H117 Z" fill="#354851" stroke="#94a9ad" strokeWidth="6" />
          <path d="M117 43 L92 65 V349 H117" fill="#24353d" stroke="#647c83" strokeWidth="5" />
          <path d="M283 43 L304 65 V349 H283" fill="#24353d" stroke="#647c83" strokeWidth="5" />
        </Layer>
        <Layer name="atm-display" progress={layers} start={0.2} end={0.76}>
          <rect x="141" y="75" width="118" height="99" rx="7" fill="#12262d" stroke={accent} strokeWidth="4" />
          <Trace d="M161 94 H239 M161 113 H220" stroke="#91b0b2" width={5} progress={strokes} start={0.35} end={0.9} />
          <rect x="163" y="142" width="76" height="10" rx="4" fill={accent} />
        </Layer>
        <Layer name="atm-controls" progress={layers} start={0.36} end={0.88}>
          {[0,1,2].flatMap(row=>[0,1,2].map(column=><rect key={`${row}-${column}`} x={152+column*22} y={192+row*15} width="14" height="8" rx="2" fill="#c2cacc" />))}
          <rect x="234" y="190" width="27" height="11" rx="3" fill="#101a1f" />
          <Trace d="M234 196 H260" stroke={accent} width={3} progress={strokes} start={0.56} />
          <path d="M142 258 H258 V282 H142 Z" fill="#132127" stroke="#6f848c" strokeWidth="4" />
          <path d="M153 270 H247" stroke="#050b0e" strokeWidth="8" />
        </Layer>
        {actuation === "dispense" && action > 0 && <svg x="160" y="270" width="80" height="75" viewBox="0 0 80 75" overflow="hidden">
          <g transform={`translate(0 ${action * 48})`}>
            <rect x="4" y="-46" width="72" height="46" rx="2" fill="#a9c1a8" stroke="#d6e4cd" strokeWidth="3" />
            <ellipse cx="40" cy="-22" rx="16" ry="9" fill="none" stroke="#5f7d6a" strokeWidth="3" />
          </g>
        </svg>}
        <Trace d="M105 350 H294" stroke="#647c83" width={10} progress={strokes} start={0.46} />
        <FocusTrace d="M144 258 H258 V282 H144" progress={emphasisProgress} emphasis={emphasis} />
      </>}
      {type === "cash" && <>
        {[0,1,2].map((note,i)=><Layer key={note} name={`cash-note-${note}`} progress={layers} start={i*0.14} end={0.64+i*0.14} y={6}>
          <g transform={`translate(${i*14 + countWave*(i-1)*11} ${-i*22-countWave*i*5}) rotate(${(i-1)*3} 200 230)`}>
            <rect x="68" y="164" width="248" height="136" rx="7" fill={i===2?"#a9c1a8":"#6f9280"} stroke="#d2e0c7" strokeWidth="5" />
            <path d="M87 188 H296 V277 H87 Z" fill="none" stroke="#4e7460" strokeWidth="4" />
            <ellipse cx="192" cy="232" rx="35" ry="29" fill="none" stroke="#4e7460" strokeWidth="5" />
            <path d="M110 211 V248 M273 211 V248" stroke="#4e7460" strokeWidth="8" strokeLinecap="round" />
          </g>
        </Layer>)}
        <FocusTrace d="M97 143 H324 M97 255 H324" progress={emphasisProgress} emphasis={emphasis} />
      </>}
      {type === "branch" && <>
        <Layer name="branch-building" progress={layers} end={0.64} y={6}>
          <path d="M57 123 H343 V328 H57 Z" fill="#344950" stroke="#9db0b3" strokeWidth="6" />
          <path d="M45 92 H355 V136 H45 Z" fill={accent} />
          <circle cx="200" cy="114" r="13" fill="#24353b" />
        </Layer>
        <Layer name="branch-glazing" progress={layers} start={0.26} end={0.82}>
          <path d="M81 163 H150 V286 H81 Z M250 163 H319 V286 H250 Z" fill="#173039" stroke="#789da3" strokeWidth="4" />
          <path d="M169 163 H231 V328 H169 Z" fill="#163039" stroke="#789da3" strokeWidth="4" />
          <Trace d="M89 206 H143 M258 206 H312" stroke="#759298" width={4} progress={strokes} start={0.4} />
          <path d="M222 247 V274" stroke={accent} strokeWidth="5" strokeLinecap="round" />
        </Layer>
        <Trace d="M42 340 H359" stroke="#647a81" width={12} progress={strokes} start={0.5} />
      </>}
      {type === "hub" && <>
        {[{x:88,y:81},{x:312,y:81},{x:61,y:216},{x:339,y:216},{x:113,y:319},{x:287,y:319}].map((node,i)=><g key={i}>
          <Trace d={`M200 190 L${node.x} ${node.y}`} stroke="#6f939c" width={5} progress={strokes} start={0.08+i*0.065} end={0.6+i*0.065} />
          <Layer name={`hub-node-${i}`} progress={layers} start={0.2+i*0.08} end={0.6+i*0.08}>
            <circle cx={node.x} cy={node.y} r="27" fill="#233e49" stroke={accent} strokeWidth="4" />
            <circle cx={node.x} cy={node.y} r="8" fill="#a8c3c7" />
          </Layer>
        </g>)}
        <Layer name="hub-core" progress={layers} start={0.15} end={0.7}>
          <circle cx="200" cy="190" r="61" fill="#162a33" stroke={accent} strokeWidth="7" />
          <path d="M173 164 H227 V215 H173 Z" fill="#355763" stroke="#9fbfc5" strokeWidth="4" />
          <Trace d="M186 178 H214 M186 191 H207 M186 204 H214" stroke={accent} width={4} progress={strokes} start={0.45} />
        </Layer>
      </>}
      {type === "data" && <>
        {[0,1,2].map((row,i)=><Layer key={row} name={`data-rack-${row}`} progress={layers} start={i*0.14} end={0.7+i*0.14} y={5}>
          <rect x="91" y={73+i*88} width="218" height="70" rx="9" fill="#263e49" stroke="#9cb5bd" strokeWidth="5" />
          <circle cx="119" cy={108+i*88} r="9" fill={accent} />
          <Trace d={`M150 ${95+i*88} H276 M150 ${111+i*88} H245 M150 ${126+i*88} H276`} stroke="#6f939d" width={5} progress={strokes} start={0.25+i*0.13} />
        </Layer>)}
        <Trace d="M200 317 V342 M94 342 H306" stroke={accent} width={6} progress={strokes} start={0.5} />
      </>}
      {type === "store" && <>
        <Layer name="store-building" progress={layers} end={0.64} y={6}>
          <rect x="66" y="129" width="268" height="199" rx="4" fill="#35494e" stroke="#a2b7b8" strokeWidth="6" />
          <path d="M55 128 L78 74 H322 L345 128 Z" fill="#546f73" stroke="#a2b7b8" strokeWidth="5" />
        </Layer>
        <Layer name="store-awning" progress={layers} start={0.18} end={0.76}>
          {[0,1,2,3,4,5].map((stripe)=><path key={stripe} d={`M${55+stripe*48.3} 128 H${55+(stripe+1)*48.3} V159 Q${79+stripe*48.3} 182 ${55+stripe*48.3} 159 Z`} fill={stripe%2===0?accent:"#e4e2d9"} />)}
        </Layer>
        <Layer name="store-entrance" progress={layers} start={0.34} end={0.9}>
          <rect x="88" y="195" width="100" height="99" rx="2" fill="#1a333c" stroke="#7c9da5" strokeWidth="4" />
          <path d="M210 195 H301 V328 H210 Z" fill="#193039" stroke="#7c9da5" strokeWidth="4" />
          <Trace d="M104 218 H168 M104 236 H149" stroke="#7899a0" width={5} progress={strokes} start={0.52} />
          <path d="M289 248 V273" stroke={accent} strokeWidth="5" strokeLinecap="round" />
        </Layer>
        <Trace d="M53 340 H347" stroke="#647b82" width={12} progress={strokes} start={0.54} />
      </>}
      {type === "phone" && <>
        <Layer name="phone-body" progress={layers} end={0.62} y={7}>
          <rect x="115" y="38" width="170" height="312" rx="27" fill="#2d424b" stroke="#a4b8bc" strokeWidth="6" />
          <rect x="129" y="66" width="142" height="253" rx="9" fill="#10262e" />
          <path d="M178 53 H222" stroke="#9fb5b8" strokeWidth="5" strokeLinecap="round" />
        </Layer>
        <Layer name="phone-interface" progress={layers} start={0.28} end={0.86}>
          <circle cx="200" cy="126" r="25" fill="#355964" stroke={accent} strokeWidth="3" />
          <Trace d="M150 181 H250 M150 200 H226 M150 219 H240" stroke="#93b1b7" width={6} progress={strokes} start={0.34} />
          <rect x="150" y="251" width="100" height="31" rx="8" fill={accent} />
        </Layer>
        <Trace d="M177 333 H223" stroke="#9fb5b8" width={5} progress={strokes} start={0.56} />
      </>}
      {type === "terminal" && <>
        <Layer name="terminal-body" progress={layers} end={0.64} y={7}>
          <path d="M139 50 H261 Q282 50 287 72 L310 315 Q312 343 286 343 H114 Q88 343 90 315 L113 72 Q118 50 139 50 Z" fill="#314951" stroke="#9eb5b9" strokeWidth="6" />
          <rect x="138" y="78" width="124" height="120" rx="8" fill="#122a31" stroke="#7899a1" strokeWidth="4" />
        </Layer>
        <Trace d="M158 102 H242 M158 123 H219" stroke="#96b6bc" width={6} progress={strokes} start={0.32} />
        <Layer name="terminal-keypad" progress={layers} start={0.34} end={0.9}>
          {[0,1,2].flatMap(row=>[0,1,2].map(column=><rect key={`${row}-${column}`} x={135+column*47} y={218+row*30} width="36" height="21" rx="5" fill={row===2&&column===2?accent:"#bdc8c8"} />))}
          <path d="M153 322 H247" stroke="#13252c" strokeWidth="9" strokeLinecap="round" />
        </Layer>
      </>}
      <Actuation kind={actuation} progress={actuationProgress} x={actionAnchor[0]} y={actionAnchor[1]} accent={accent} locked={locked} lockFrom={lockFrom} lockProgress={lockProgress} />
    </g>
  </svg>;
};
