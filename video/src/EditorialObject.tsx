import type {StageElement} from "../../src/lib/editorial-stage";

// Original schematic illustrations: no fabricated banking screenshot or evidence.
export const EditorialObject = ({type, accent, progress}: {type: NonNullable<StageElement["object_type"]>; accent: string; progress: number}) => <svg viewBox="0 0 400 400" width="100%" height="100%">
  <ellipse cx="200" cy="359" rx="139" ry="15" fill="#000" opacity=".28" />
  <g transform={`translate(0 ${12*(1-progress)})`} strokeLinejoin="round">
    {type === "factory" && <>
      <path d="M83 72 H125 L139 237 H69 Z" fill="#647a7b" stroke="#a2b6b4" strokeWidth="5" />
      <path d="M61 216 L143 168 V216 L225 168 V216 L307 168 V328 H61 Z" fill="#354b50" stroke="#9eb5b4" strokeWidth="6" />
      {[89,165,241].map(x=><rect key={x} x={x} y="238" width="38" height="40" rx="3" fill={accent} />)}
      <rect x="162" y="288" width="58" height="40" rx="3" fill="#17272d" />
      <path d="M55 339 H342" stroke="#647a7b" strokeWidth="12" strokeLinecap="round" />
    </>}
    {type === "truck" && <>
      <rect x="37" y="119" width="216" height="165" rx="12" fill="#405b62" stroke="#a2b6b4" strokeWidth="6" />
      <path d="M253 169 H302 L359 231 V285 H253 Z" fill={accent} stroke="#a2b6b4" strokeWidth="5" />
      <path d="M271 187 H295 L328 225 H271 Z" fill="#152730" />
      <path d="M38 286 H363" stroke="#647a7b" strokeWidth="13" />
      {[92,302].map(x=><g key={x}><circle cx={x} cy="292" r="34" fill="#111a20" stroke="#8ca09f" strokeWidth="6"/><circle cx={x} cy="292" r="13" fill="#8ca09f"/></g>)}
      <path d="M67 152 H224 M67 174 H224" stroke="#829996" strokeWidth="6" strokeLinecap="round" />
    </>}
    {type === "package" && <>
      <path d="M65 125 L200 66 L335 125 L200 188 Z" fill="#a38c66" stroke="#e0c99c" strokeWidth="5" />
      <path d="M65 125 L200 188 V332 L65 266 Z" fill="#746346" stroke="#c4ac82" strokeWidth="5" />
      <path d="M200 188 L335 125 V266 L200 332 Z" fill="#927b55" stroke="#c4ac82" strokeWidth="5" />
      <path d="M134 96 L267 156 L267 211 L231 228 V173 L99 113 Z" fill={accent} />
      <path d="M97 191 L162 223 V254 L97 222 Z" fill="#e9ddbf" />
    </>}
    {type === "component" && <>
      <path d="M70 88 H330 V312 H70 Z" fill="#24423a" stroke="#7faaa0" strokeWidth="6" />
      {[110,150,190,230,270].map(x=><g key={x} stroke={accent} strokeWidth="8"><path d={`M${x} 66 V102 M${x} 300 V336`} /></g>)}
      <path d="M94 146 H136 V184 M308 246 H270 V218 M92 268 H142 V236 M305 126 H265 V160" fill="none" stroke="#7faaa0" strokeWidth="7" />
      <rect x="144" y="148" width="112" height="108" rx="12" fill="#10191d" stroke={accent} strokeWidth="5" />
      <path d="M176 177 H224 M176 195 H213 M176 213 H224" stroke="#b5cec7" strokeWidth="7" strokeLinecap="round" />
      {[94,305].map(x=><circle key={x} cx={x} cy="290" r="7" fill={accent} />)}
    </>}
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
