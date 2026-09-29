import {Img, staticFile} from "remotion";
import {measureText} from "@remotion/layout-utils";
import type {StageElement} from "../../src/lib/editorial-stage";
import type {Chart, Region} from "../../src/lib/editorial-evidence";

const GOLD = "#FFBD19", WHITE = "#F6F7F8";

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
  const w = element.asset_width, h = element.asset_height;
  if (!element.asset_file || !w || !h) {
    throw new Error(`Recorte sem arquivo ou dimensões: ${element.id}`);
  }

  const crossSize = 14;
  const crossStroke = "#7E8B99";

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Halo Traseiro de Iluminação Suave (Efeito Atrás / Ambient Light) */}
      <div
        style={{
          position: "absolute",
          inset: -20,
          background: "radial-gradient(ellipse at center, rgba(255, 189, 25, 0.18) 0%, rgba(15, 17, 21, 0) 70%)",
          filter: "blur(24px)",
          pointerEvents: "none",
          zIndex: 0,
        }}
      />

      {/* Marcas de Registro / Enquadramento Técnico nos Cantos (+) */}
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

      {/* Card Físico com Borda de Papel Rasgado, Fundo Off-White e Sombra Volumétrica 3D */}
      <div
        style={{
          position: "relative",
          width: "100%",
          height: "100%",
          backgroundColor: "#FFFFFF",
          borderRadius: 6,
          boxShadow: "0 30px 80px -12px rgba(0, 0, 0, 0.95), 0 12px 28px -6px rgba(0, 0, 0, 0.72), 0 0 0 1px rgba(255, 255, 255, 0.12)",
          clipPath: RIPPED_PAPER_CLIP,
          padding: "12px 14px",
          boxSizing: "border-box",
          overflow: "hidden",
          zIndex: 1,
        }}
      >
        <svg
          width="100%"
          height="100%"
          viewBox={`${(view.x * w) / 100} ${(view.y * h) / 100} ${(view.width * w) / 100} ${(view.height * h) / 100}`}
          preserveAspectRatio="xMidYMid meet"
          style={{ overflow: "hidden", display: "block" }}
        >
          <foreignObject x={0} y={0} width={w} height={h}>
            <Img src={staticFile(element.asset_file)} style={{ width: w, height: h, display: "block" }} />
          </foreignObject>

          {/* Destaque com Marca-Texto Amarelo Ouro Encorpado e Vibrante (#FFBD19) */}
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
                    fill={GOLD}
                    opacity={0.88}
                    style={{ mixBlendMode: "multiply" }}
                  />
                );
              }

              const path =
                a.style === "circle"
                  ? `M${x + rw},${y + rh / 2} a${rw / 2},${rh / 2} 0 1 0 ${-rw},0 a${rw / 2},${rh / 2} 0 1 0 ${rw},0`
                  : `M${x},${y + rh * (a.style === "strike" ? 0.5 : 0.94)} L${x + rw},${y + rh * (a.style === "strike" ? 0.5 : 0.94)}`;

              return (
                <path
                  key={a.id}
                  d={path}
                  fill="none"
                  stroke={GOLD}
                  strokeWidth={6}
                  vectorEffect="non-scaling-stroke"
                  strokeLinecap="round"
                  pathLength={1}
                  strokeDasharray={1}
                  strokeDashoffset={1 - progress}
                />
              );
            })}
        </svg>
      </div>
    </div>
  );
};

const number = (v: number) => new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(v);

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
