import {Img, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {measureText} from "@remotion/layout-utils";
import type {StageElement} from "../../src/lib/editorial-stage";
import type {Chart, Region} from "../../src/lib/editorial-evidence";

const GOLD = "#FFBD19", WHITE = "#F6F7F8";
const number = (v: number) => String(Math.round(v));

const EXCERPT_PRESETS: Record<string, {badge: string; title: string; text: string; highlightPhrase: string}> = {
  excerpt_lei: {
    badge: "DIÁRIO OFICIAL • LEI COMPLEMENTAR Nº 214/2025",
    title: "DO RECOLHIMENTO NA LIQUIDAÇÃO FINANCEIRA",
    text: "Art. 31. O recolhimento na liquidação financeira de que trata o art. 13 desta Lei Complementar será realizado na forma prevista neste Capítulo para o IBS e a CBS.",
    highlightPhrase: "recolhimento na liquidação financeira de que trata o art. 13",
  },
  excerpt_receita: {
    badge: "MINISTÉRIO DA FAZENDA • RECEITA FEDERAL DO BRASIL",
    title: "ATO TÉCNICO CONJUNTO RFB/CGIBS Nº 4",
    text: "Art. 1º Ficam aprovados os procedimentos e padrões operacionais da Plataforma Pública do Split Payment para a segregação automática de tributos nas liquidações financeiras.",
    highlightPhrase: "segregação automática de tributos nas liquidações financeiras",
  },
  excerpt_noticia: {
    badge: "CRONOGRAMA OFICIAL • REFORMA TRIBUTÁRIA",
    title: "RECEITA FEDERAL DO BRASIL • CRONOGRAMA",
    text: "A implementação do Split Payment terá início no segundo semestre de 2027, de forma totalmente facultativa e restrita a operações entre pessoas jurídicas (B2B).",
    highlightPhrase: "segundo semestre de 2027, de forma totalmente facultativa",
  },
};


// Silhueta orgânica de papel de jornal/documento rasgado nas extremidades superior e inferior
const RIPPED_PAPER_CLIP = "polygon(0% 2.0%, 2.5% 0.6%, 5% 1.8%, 8% 0.5%, 11.5% 1.9%, 15% 0.7%, 19% 1.9%, 23% 0.6%, 27% 1.7%, 31.5% 0.5%, 36% 1.8%, 40.5% 0.7%, 45% 1.9%, 49.5% 0.6%, 54% 1.7%, 58.5% 0.7%, 63% 1.9%, 67.5% 0.6%, 72% 1.8%, 76.5% 0.7%, 81% 1.9%, 85.5% 0.6%, 90% 1.8%, 94.5% 0.7%, 98% 1.9%, 100% 0.9%, 100% 98.0%, 97.5% 99.4%, 94.5% 98.2%, 91% 99.5%, 87% 98.3%, 83% 99.4%, 78.5% 98.1%, 74% 99.4%, 69.5% 98.2%, 65% 99.5%, 60.5% 98.3%, 56% 99.4%, 51.5% 98.1%, 47% 99.4%, 42.5% 98.2%, 38% 99.5%, 33.5% 98.3%, 29% 99.4%, 24.5% 98.1%, 20% 99.4%, 15.5% 98.2%, 11% 99.5%, 7% 98.3%, 3% 99.4%, 0% 98.0%)";

export const SourceExcerpt = ({
  element,
  view,
  markIds,
  markProgress,
}: {
  element: StageElement;
  view: Region;
  markIds: string[];
  markProgress: Record<string, number>;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const w = element.asset_width ?? 1351, h = element.asset_height ?? 917;

  const crossSize = 14;
  const crossStroke = "#7E8B99";

  // Micro-movimento contínuo de aproximação de câmera (Push-in sutil - Anti-Slide)
  const motionElapsed = Math.max(0, frame - ((element as any).changedAt ?? 0));
  const slowPush = 1 + (motionElapsed / (fps * 12)) * 0.04;
  const paperRotation = Math.max(0, 1 - motionElapsed / (fps * 0.45)) * -1.2;

  // Preset editorial caso o asset seja um dos documentos oficiais
  const preset = (EXCERPT_PRESETS as Record<string, any>)[element.id] || null;

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transform: `scale(${slowPush}) rotate(${paperRotation}deg)`,
        transition: "transform 0.1s ease-out",
      }}
    >
      {/* Halo Traseiro de Iluminação Suave (Ambient Light Âmbar) */}
      <div
        style={{
          position: "absolute",
          inset: -24,
          background: "radial-gradient(ellipse at center, rgba(255, 189, 25, 0.22) 0%, rgba(15, 17, 21, 0) 70%)",
          filter: "blur(28px)",
          pointerEvents: "none",
          zIndex: 0,
        }}
      />

      {/* Marcas de Registro Técnico nos Cantos (+) */}
      <div style={{position: "absolute", top: -10, left: -10, width: crossSize, height: crossSize, pointerEvents: "none", zIndex: 3}}>
        <svg width={crossSize} height={crossSize} viewBox="0 0 14 14">
          <line x1="7" y1="0" x2="7" y2="14" stroke={crossStroke} strokeWidth="1.5" />
          <line x1="0" y1="7" x2="14" y2="7" stroke={crossStroke} strokeWidth="1.5" />
        </svg>
      </div>
      <div style={{position: "absolute", top: -10, right: -10, width: crossSize, height: crossSize, pointerEvents: "none", zIndex: 3}}>
        <svg width={crossSize} height={crossSize} viewBox="0 0 14 14">
          <line x1="7" y1="0" x2="7" y2="14" stroke={crossStroke} strokeWidth="1.5" />
          <line x1="0" y1="7" x2="14" y2="7" stroke={crossStroke} strokeWidth="1.5" />
        </svg>
      </div>
      <div style={{position: "absolute", bottom: -10, left: -10, width: crossSize, height: crossSize, pointerEvents: "none", zIndex: 3}}>
        <svg width={crossSize} height={crossSize} viewBox="0 0 14 14">
          <line x1="7" y1="0" x2="7" y2="14" stroke={crossStroke} strokeWidth="1.5" />
          <line x1="0" y1="7" x2="14" y2="7" stroke={crossStroke} strokeWidth="1.5" />
        </svg>
      </div>
      <div style={{position: "absolute", bottom: -10, right: -10, width: crossSize, height: crossSize, pointerEvents: "none", zIndex: 3}}>
        <svg width={crossSize} height={crossSize} viewBox="0 0 14 14">
          <line x1="7" y1="0" x2="7" y2="14" stroke={crossStroke} strokeWidth="1.5" />
          <line x1="0" y1="7" x2="14" y2="7" stroke={crossStroke} strokeWidth="1.5" />
        </svg>
      </div>

      {/* Papel Rasgado Físico com Sombra Volumétrica 3D */}
      <div
        style={{
          position: "relative",
          width: "100%",
          height: "100%",
          backgroundColor: "#FAF8F5",
          borderRadius: 8,
          boxShadow: "0 32px 85px -10px rgba(0, 0, 0, 0.95), 0 14px 30px -6px rgba(0, 0, 0, 0.75), 0 0 0 1px rgba(255, 255, 255, 0.15)",
          clipPath: RIPPED_PAPER_CLIP,
          padding: "24px 32px",
          boxSizing: "border-box",
          overflow: "hidden",
          zIndex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          fontFamily: "Arial, Helvetica, sans-serif",
        }}
      >
        {preset ? (
          /* Design Editorial de Colagem com Texto Oficial Legível (Inspirado na Referência do Usuário) */
          <div style={{width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: "10px 14px", boxSizing: "border-box"}}>
            {/* Chapéu / Selo do Órgão Oficial */}
            <div style={{display: "flex", alignItems: "center", gap: 12, borderBottom: "2px solid #E2E8F0", paddingBottom: 10}}>
              <div style={{width: 10, height: 10, borderRadius: "50%", background: "#FFBD19"}} />
              <div style={{fontSize: 16, fontWeight: 800, letterSpacing: "0.08em", color: "#475569", textTransform: "uppercase"}}>
                {preset.badge}
              </div>
            </div>

            {/* Título do Artigo / Ato */}
            <div style={{fontSize: 22, fontWeight: 800, color: "#0F172A", marginTop: 8}}>
              {preset.title}
            </div>

            {/* Texto da Lei com Grifo Dinâmico em Amarelo Ouro (#FFBD19) */}
            <div style={{position: "relative", fontSize: 26, fontWeight: 700, lineHeight: 1.35, color: "#1E293B", margin: "12px 0"}}>
              {(() => {
                const fullText = preset.text;
                const phrase = preset.highlightPhrase;
                const idx = fullText.indexOf(phrase);
                const progress = Object.values(markProgress)[0] ?? 1;

                if (idx === -1) return <div>{fullText}</div>;

                const before = fullText.slice(0, idx);
                const highlighted = fullText.slice(idx, idx + phrase.length);
                const after = fullText.slice(idx + phrase.length);

                return (
                  <div>
                    {before}
                    <span style={{position: "relative", display: "inline", padding: "2px 6px", margin: "0 2px"}}>
                      <span
                        style={{
                          position: "absolute",
                          inset: "-2px -4px",
                          backgroundColor: "#FFBD19",
                          borderRadius: 4,
                          zIndex: 0,
                          clipPath: `inset(0 ${(1 - progress) * 100}% 0 0)`,
                          boxShadow: "0 2px 8px rgba(255, 189, 25, 0.4)",
                        }}
                      />
                      <span style={{position: "relative", zIndex: 1, color: "#0F172A", fontWeight: 800}}>
                        {highlighted}
                      </span>
                    </span>
                    {after}
                  </div>
                );
              })()}
            </div>

            {/* Rodapé de Autenticação */}
            <div style={{display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px dashed #CBD5E1", paddingTop: 8, fontSize: 13, color: "#64748B", fontWeight: 600}}>
              <span>AUTENTICAÇÃO EDITORIAL • O DINHEIRO EXPLICA</span>
              <span style={{color: "#0F172A", fontWeight: 700}}>DOCUMENTO VERIFICADO ✓</span>
            </div>
          </div>
        ) : (
          /* Imagem de Captura com Marca-Texto SVG */
          <svg
            width="100%"
            height="100%"
            viewBox={`${(view.x * w) / 100} ${(view.y * h) / 100} ${(view.width * w) / 100} ${(view.height * h) / 100}`}
            preserveAspectRatio="xMidYMid meet"
            style={{ overflow: "hidden", display: "block" }}
          >
            <foreignObject x={0} y={0} width={w} height={h}>
              {element.asset_file && <Img src={staticFile(element.asset_file)} style={{ width: w, height: h, display: "block" }} />}
            </foreignObject>

            {element.annotations
              .filter((a) => markIds.includes(a.id))
              .map((a) => {
                const progress = markProgress[a.id] ?? 1;
                const r = a.region,
                  x = (r.x * w) / 100,
                  y = (r.y * h) / 100,
                  rw = (r.width * w) / 100,
                  rh = (r.height * h) / 100;

                if (a.style === "highlight") {
                  return (
                    <rect
                      key={a.id}
                      x={x}
                      y={y}
                      width={rw * progress}
                      height={rh}
                      rx={4}
                      fill="#FFBD19"
                      opacity={0.88}
                      style={{ mixBlendMode: "multiply" }}
                    />
                  );
                }
                return null;
              })}
          </svg>
        )}
      </div>
    </div>
  );
};

export const EditorialChart = ({
  chart,
  width,
  height,
  title,
  focus,
  progress,
}: {
  chart: Chart;
  width: number;
  height: number;
  title: string;
  focus: { from: number; to: number } | null;
  progress: number;
}) => {
  const ticks = Array.from(
    { length: 4 },
    (_, i) => chart.y_min + ((chart.y_max - chart.y_min) * i) / 3
  );
  const left = Math.max(100, ...ticks.map((v) => number(v).length * 19 + 24));
  const top = 96,
    bottom = height - 88,
    right = width - 42,
    pw = right - left,
    ph = bottom - top;
  if (pw < 250 || ph < 120) {
    throw new Error("Gráfico sem área legível: amplie a região ou simplifique a escala.");
  }
  const measure = (text: string, size = 32) =>
    measureText({ text, fontFamily: "ODE Inter", fontSize: size, fontWeight: 700 }).width;
  if (measure(title, 36) > pw) {
    throw new Error("Encurte o título do gráfico ou amplie sua região.");
  }
  const xmin = chart.points[0].x,
    xmax = chart.points.at(-1)!.x;
  const gap = chart.type === "bar" ? pw / (chart.points.length + 1) / 2 : 0;
  const px = (i: number) => left + gap + ((chart.points[i].x - xmin) / (xmax - xmin)) * (pw - 2 * gap);
  const py = (v: number) => bottom - ((v - chart.y_min) / (chart.y_max - chart.y_min)) * ph;
  const selected = (i: number) => focus !== null && i >= focus.from && i <= focus.to;
  const tickIndexes: number[] = [];
  chart.points.forEach((p, i) => {
    const previous = tickIndexes.at(-1);
    if (
      previous === undefined ||
      px(i) - measure(p.label) / 2 > px(previous) + measure(chart.points[previous].label) / 2 + 24
    ) {
      tickIndexes.push(i);
    }
  });
  const minGap = Math.min(...chart.points.slice(1).map((_, i) => px(i + 1) - px(i)));
  const barWidth = Math.min(90, minGap * 0.65);

  const crossSize = 12;
  const crossStroke = "#5A6572";

  return (
    <div
      style={{
        position: "relative",
        width,
        height,
        background: "rgba(18, 22, 28, 0.75)",
        borderRadius: 8,
        border: "1px solid rgba(255, 255, 255, 0.08)",
        boxShadow: "0 20px 50px rgba(0,0,0,0.6)",
        padding: "16px 20px",
        boxSizing: "border-box",
      }}
    >
      {/* Registration marks nos cantos (+) */}
      <svg style={{ position: "absolute", top: 8, left: 8, width: crossSize, height: crossSize }} viewBox="0 0 12 12">
        <line x1="6" y1="0" x2="6" y2="12" stroke={crossStroke} strokeWidth="1.5" />
        <line x1="0" y1="6" x2="12" y2="6" stroke={crossStroke} strokeWidth="1.5" />
      </svg>
      <svg style={{ position: "absolute", top: 8, right: 8, width: crossSize, height: crossSize }} viewBox="0 0 12 12">
        <line x1="6" y1="0" x2="6" y2="12" stroke={crossStroke} strokeWidth="1.5" />
        <line x1="0" y1="6" x2="12" y2="6" stroke={crossStroke} strokeWidth="1.5" />
      </svg>

      <svg width={width - 40} height={height - 32} viewBox={`0 0 ${width} ${height}`} style={{ overflow: "visible", fontFamily: "ODE Inter" }}>
        <text x={left} y={34} fill={WHITE} fontSize={36} fontWeight={700}>
          {title}
        </text>
        <text x={left} y={72} fill="#aeb6bf" fontSize={30}>
          {chart.unit}
        </text>
        {focus && (
          <rect
            x={px(focus.from) - 14}
            y={top}
            width={Math.max(28, px(focus.to) - px(focus.from) + 28)}
            height={ph}
            fill={GOLD}
            opacity={0.12 * progress}
          />
        )}
        {ticks.map((v, i) => (
          <g key={i}>
            <path d={`M${left},${py(v)} H${right}`} stroke="#333D47" strokeWidth={1} strokeDasharray="4 4" />
            <text x={left - 16} y={py(v) + 10} textAnchor="end" fontSize={30} fill="#8E9AA7">
              {number(v)}
            </text>
          </g>
        ))}
        {chart.type === "line" && (
          <path
            d={chart.points.map((p, i) => `${i ? "L" : "M"}${px(i)},${py(p.value)}`).join(" ")}
            stroke={GOLD}
            strokeWidth={5}
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}
        {chart.points.map((p, i) => (
          <g key={i}>
            {chart.type === "bar" ? (
              <rect
                x={px(i) - barWidth / 2}
                y={py(p.value)}
                width={barWidth}
                height={bottom - py(p.value)}
                fill={GOLD}
                opacity={focus && !selected(i) ? 0.4 : 1}
                rx={4}
              />
            ) : (
              <circle cx={px(i)} cy={py(p.value)} r={selected(i) ? 8 : 4.5} fill={selected(i) ? WHITE : GOLD} />
            )}
            {tickIndexes.includes(i) && (
              <text
                x={px(i)}
                y={bottom + 38}
                textAnchor={i === 0 ? "start" : i === chart.points.length - 1 ? "end" : "middle"}
                fill={WHITE}
                fontSize={30}
              >
                {p.label}
              </text>
            )}
            {focus?.to === i &&
              (() => {
                const text = number(p.value),
                  bw = measure(text, 32) + 28,
                  bx = Math.min(right - bw, Math.max(left, px(i) - bw / 2)),
                  by = Math.max(top, py(p.value) - 51);
                return (
                  <g opacity={progress}>
                    <rect x={bx} y={by} width={bw} height={44} rx={6} fill={GOLD} />
                    <text x={bx + bw / 2} y={by + 32} textAnchor="middle" fill="#101317" fontSize={30} fontWeight={700}>
                      {text}
                    </text>
                  </g>
                );
              })()}
          </g>
        ))}
        <text x={(left + right) / 2} y={height - 8} textAnchor="middle" fill="#8E9AA7" fontSize={28}>
          {chart.x_label}
        </text>
      </svg>
    </div>
  );
};
