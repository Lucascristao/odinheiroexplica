import type {StageElement} from "../../src/lib/editorial-stage";

// Original schematic illustrations: no fabricated banking screenshot or evidence.
export const EditorialObject = ({type, accent, progress}: {type: NonNullable<StageElement["object_type"]>; accent: string; progress: number}) => <svg viewBox="0 0 400 400" width="100%" height="100%">
  <ellipse cx="200" cy="359" rx="139" ry="15" fill="#000" opacity=".28" />
  <g transform={`translate(0 ${12*(1-progress)})`} strokeLinejoin="round">
    {type === "receipt" && <>
      <path d="M90 36 H310 V348 L288 336 L266 348 L244 336 L222 348 L200 336 L178 348 L156 336 L134 348 L112 336 L90 348 Z" fill="#f0ebe1" />
      <path d="M125 88 H275 M125 120 H235 M125 174 H275 M125 203 H247" stroke="#a3aaa9" strokeWidth="12" strokeLinecap="round" />
      <circle cx="257" cy="282" r="59" fill={accent} />
      <path d="M257 248 V286 M257 303 V309" fill="none" stroke="#111a1c" strokeWidth="11" strokeLinecap="round" />
    </>}
    {type === "wallet" && <>
      <rect x="112" y="74" width="160" height="170" rx="8" fill={accent} transform="rotate(-12 192 160)" />
      <rect x="146" y="70" width="160" height="170" rx="8" fill="#8da99a" transform="rotate(8 226 155)" />
      <rect x="47" y="146" width="305" height="194" rx="25" fill="#35444b" />
      <path d="M72 172 H329 M72 313 H329" stroke="#65767d" strokeWidth="3" strokeDasharray="8 6" />
      <rect x="265" y="209" width="101" height="68" rx="15" fill={accent} />
      <circle cx="293" cy="243" r="10" fill="#35444b" />
    </>}
    {type === "bank" && <>
      <path d="M35 127 L200 44 L365 127 Z" fill={accent} />
      {[79,153,227,301].map(x=><rect key={x} x={x-17} y="144" width="34" height="163" rx="5" fill="#bcc8c9" />)}
      <path d="M47 322 H353 M31 343 H369" stroke="#62757c" strokeWidth="18" />
      <circle cx="200" cy="96" r="15" fill="#24353b" />
    </>}
  </g>
</svg>;
