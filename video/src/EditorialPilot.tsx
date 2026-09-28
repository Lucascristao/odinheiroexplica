import {Audio} from "@remotion/media";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import renderInput from "../generated/pilot-render-input.json";

type GenericRecord = Record<string, unknown>;

type Scene = {
  id: string;
  scene_index: number;
  title?: string;
  start_frame: number;
  duration_frames: number;
  audio_file: string;
  visual: {
    type: string;
    payload?: GenericRecord;
  };
};

const BG = "#090b0d";
const SURFACE = "#12161a";
const SURFACE_2 = "#171c21";
const GOLD = "#ffbd19";
const GOLD_DIM = "#7c5a00";
const WHITE = "#f6f7f8";
const MUTED = "#9ba4ae";
const LINE = "#30363d";
const RED = "#ff6b6b";
const GREEN = "#79d99a";
const FONT = "Arial, Helvetica, sans-serif";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const asString = (value: unknown, fallback = "") =>
  typeof value === "string" ? value : fallback;

const asArray = <T,>(value: unknown): T[] =>
  Array.isArray(value) ? (value as T[]) : [];

const MovingBackground = () => {
  const frame = useCurrentFrame();
  const x = (frame * 0.45) % 72;
  const y = (frame * 0.22) % 72;
  const glowX = 48 + Math.sin(frame / 45) * 14;
  const glowY = 44 + Math.cos(frame / 58) * 9;
  const pulse = 0.085 + (Math.sin(frame / 22) + 1) * 0.018;

  return (
    <AbsoluteFill style={{overflow: "hidden", backgroundColor: BG}}>
      <AbsoluteFill
        style={{
          opacity: 0.28,
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px)",
          backgroundSize: "72px 72px",
          backgroundPosition: `${x}px ${y}px`,
        }}
      />
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${glowX}% ${glowY}%, rgba(255,189,25,${pulse}) 0%, rgba(255,189,25,.025) 23%, transparent 49%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 630,
          height: 630,
          borderRadius: "50%",
          border: "1px solid rgba(255,189,25,.09)",
          right: -210 + Math.sin(frame / 54) * 28,
          top: 115 + Math.cos(frame / 47) * 22,
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 1000,
          height: 1,
          left: -260,
          bottom: 118,
          opacity: 0.75,
          background:
            "linear-gradient(90deg, transparent, rgba(255,189,25,.22), transparent)",
          transform: `translateX(${(frame * 2.6) % 1450}px) rotate(-7deg)`,
        }}
      />
    </AbsoluteFill>
  );
};

const Brand = () => (
  <div
    style={{
      position: "absolute",
      left: 82,
      top: 58,
      display: "flex",
      alignItems: "center",
      gap: 14,
      color: WHITE,
      fontFamily: FONT,
      fontSize: 25,
      fontWeight: 850,
      letterSpacing: -0.8,
      zIndex: 50,
    }}
  >
    <div
      style={{
        width: 31,
        height: 31,
        borderRadius: 9,
        background: GOLD,
        color: BG,
        display: "grid",
        placeItems: "center",
        fontWeight: 950,
      }}
    >
      ↗
    </div>
    O Dinheiro Explica
  </div>
);

const Source = ({text}: {text?: string}) => {
  if (!text) return null;

  return (
    <div
      style={{
        position: "absolute",
        right: 72,
        bottom: 46,
        color: "#707983",
        fontFamily: FONT,
        fontSize: 17,
        letterSpacing: 0.2,
      }}
    >
      Fonte: {text}
    </div>
  );
};

const SceneShell = ({
  durationFrames,
  children,
}: {
  durationFrames: number;
  children: React.ReactNode;
}) => {
  const frame = useCurrentFrame();

  const inOpacity = interpolate(frame, [0, 8], [0, 1], clamp);
  const outOpacity = interpolate(
    frame,
    [Math.max(10, durationFrames - 10), durationFrames - 1],
    [1, 0],
    clamp,
  );
  const opacity = Math.min(inOpacity, outOpacity);

  const inY = interpolate(frame, [0, 11], [24, 0], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });
  const outY = interpolate(
    frame,
    [Math.max(10, durationFrames - 10), durationFrames - 1],
    [0, -14],
    clamp,
  );

  return (
    <AbsoluteFill
      style={{
        opacity,
        transform: `translateY(${inY + outY}px)`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

const TransitionSweep = ({sceneIndex}: {sceneIndex: number}) => {
  const frame = useCurrentFrame();
  if (sceneIndex === 0) return null;

  const progress = interpolate(frame, [0, 7, 13], [-25, 115, 130], clamp);
  const opacity = interpolate(frame, [0, 2, 10, 14], [0, 0.8, 0.3, 0], clamp);

  return (
    <div
      style={{
        position: "absolute",
        zIndex: 80,
        left: `${progress}%`,
        top: 0,
        width: 220,
        height: "100%",
        opacity,
        transform: "skewX(-12deg)",
        background:
          "linear-gradient(90deg, transparent, rgba(255,189,25,.55), transparent)",
        filter: "blur(7px)",
        pointerEvents: "none",
      }}
    />
  );
};

const Eyebrow = ({children}: {children: React.ReactNode}) => (
  <div
    style={{
      color: GOLD,
      fontSize: 26,
      fontWeight: 900,
      textTransform: "uppercase",
      letterSpacing: 5,
      marginBottom: 26,
    }}
  >
    {children}
  </div>
);

const HeadlineScene = ({
  payload,
  durationFrames,
}: {
  payload: GenericRecord;
  durationFrames: number;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({
    frame,
    fps,
    durationInFrames: 26,
    config: {damping: 18, stiffness: 96},
  });

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          padding: "0 155px",
          fontFamily: FONT,
        }}
      >
        <Eyebrow>{asString(payload.kicker, "O Dinheiro Explica")}</Eyebrow>
        <div
          style={{
            maxWidth: 1470,
            color: WHITE,
            fontSize: 88,
            fontWeight: 950,
            lineHeight: 1.04,
            letterSpacing: -4.8,
            transform: `scale(${0.96 + enter * 0.04})`,
          }}
        >
          {asString(payload.headline)}
        </div>
        <div
          style={{
            width: `${interpolate(frame, [14, 54], [0, 760], clamp)}px`,
            height: 7,
            borderRadius: 999,
            background: GOLD,
            marginTop: 34,
            boxShadow: "0 0 28px rgba(255,189,25,.14)",
          }}
        />
        <Source text={asString(payload.source)} />
      </AbsoluteFill>
    </SceneShell>
  );
};

const StatGridScene = ({
  payload,
  durationFrames,
}: {
  payload: GenericRecord;
  durationFrames: number;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const stats = asArray<{value?: string; label?: string}>(payload.stats);

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          padding: "0 165px",
          fontFamily: FONT,
        }}
      >
        <Eyebrow>{asString(payload.eyebrow, "Em números")}</Eyebrow>
        <div style={{display: "flex", gap: 28}}>
          {stats.map((stat, index) => {
            const enter = spring({
              frame: Math.max(0, frame - index * 10),
              fps,
              durationInFrames: 24,
              config: {damping: 18, stiffness: 105},
            });
            return (
              <div
                key={index}
                style={{
                  flex: 1,
                  minHeight: 300,
                  padding: "42px 44px",
                  borderRadius: 24,
                  border: `1px solid ${index === 0 ? "rgba(255,189,25,.38)" : LINE}`,
                  background: index === 0 ? "rgba(255,189,25,.05)" : SURFACE,
                  transform: `translateY(${(1 - enter) * 36}px)`,
                  opacity: enter,
                }}
              >
                <div
                  style={{
                    color: index === 0 ? GOLD : WHITE,
                    fontSize: 104,
                    fontWeight: 950,
                    letterSpacing: -6,
                  }}
                >
                  {stat.value}
                </div>
                <div
                  style={{
                    marginTop: 14,
                    color: MUTED,
                    fontSize: 28,
                    fontWeight: 750,
                  }}
                >
                  {stat.label}
                </div>
              </div>
            );
          })}
        </div>
        <div style={{marginTop: 30, color: MUTED, fontSize: 27}}>
          {asString(payload.caption)}
        </div>
        <Source text={asString(payload.source)} />
      </AbsoluteFill>
    </SceneShell>
  );
};

const BeforeAfterScene = ({
  payload,
  durationFrames,
}: {
  payload: GenericRecord;
  durationFrames: number;
}) => {
  const frame = useCurrentFrame();
  const split = interpolate(frame, [18, 72], [0, 1], clamp);

  const card = (
    side: "before" | "after",
    active: boolean,
  ) => {
    const title = asString(payload[`${side}_title`]);
    const text = asString(payload[`${side}_text`]);
    return (
      <div
        style={{
          flex: 1,
          padding: "48px 50px",
          minHeight: 350,
          borderRadius: 26,
          border: active ? "1px solid rgba(255,189,25,.42)" : `1px solid ${LINE}`,
          background: active ? "rgba(255,189,25,.055)" : SURFACE,
          opacity: active ? split : 1,
        }}
      >
        <div
          style={{
            fontSize: 30,
            textTransform: "uppercase",
            letterSpacing: 4,
            color: active ? GOLD : MUTED,
            fontWeight: 900,
          }}
        >
          {side === "before" ? "Antes" : "Agora"}
        </div>
        <div style={{fontSize: 74, color: WHITE, fontWeight: 950, marginTop: 25}}>
          {title}
        </div>
        <div style={{fontSize: 29, color: MUTED, marginTop: 24, lineHeight: 1.35}}>
          {text}
        </div>
      </div>
    );
  };

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          padding: "0 155px",
          fontFamily: FONT,
        }}
      >
        <Eyebrow>{asString(payload.eyebrow, "Antes x agora")}</Eyebrow>
        <div style={{display: "flex", gap: 30}}>
          {card("before", false)}
          <div style={{alignSelf: "center", color: GOLD, fontSize: 54}}>→</div>
          {card("after", true)}
        </div>
        <Source text={asString(payload.source)} />
      </AbsoluteFill>
    </SceneShell>
  );
};

const NetworkScene = ({
  payload,
  durationFrames,
}: {
  payload: GenericRecord;
  durationFrames: number;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const nodes = asArray<string>(payload.nodes);
  const paths = asArray<[number, number]>(payload.paths);

  const positions = [
    {x: 260, y: 600},
    {x: 660, y: 600},
    {x: 1110, y: 440},
    {x: 1110, y: 735},
    {x: 1530, y: 440},
  ];

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill style={{fontFamily: FONT}}>
        <div style={{position: "absolute", left: 145, top: 185}}>
          <Eyebrow>{asString(payload.eyebrow, "Rastreamento")}</Eyebrow>
          <div
            style={{
              color: WHITE,
              fontSize: 58,
              fontWeight: 950,
              letterSpacing: -3,
              maxWidth: 850,
              lineHeight: 1.04,
            }}
          >
            {asString(payload.headline)}
          </div>
        </div>

        <svg
          width="1920"
          height="1080"
          style={{position: "absolute", inset: 0}}
        >
          {paths.map(([from, to], index) => {
            const a = positions[from];
            const b = positions[to];
            const progress = interpolate(
              frame,
              [20 + index * 10, 65 + index * 10],
              [0, 1],
              clamp,
            );
            const startX = a.x + 96;
            const targetX = b.x - 96;
            const x2 = startX + (targetX - startX) * progress;
            const y2 = a.y + (b.y - a.y) * progress;
            return (
              <line
                key={index}
                x1={startX}
                y1={a.y}
                x2={x2}
                y2={y2}
                stroke={index === 0 ? GOLD : "#ad7f0b"}
                strokeWidth={index === 0 ? 8 : 5}
                strokeLinecap="round"
                opacity={0.92}
              />
            );
          })}
        </svg>

        {nodes.map((node, index) => {
          const pos = positions[index];
          const enter = spring({
            frame: Math.max(0, frame - 10 - index * 8),
            fps,
            durationInFrames: 20,
            config: {damping: 17, stiffness: 110},
          });
          const pulse = 1 + Math.sin((frame + index * 12) / 11) * 0.018;
          return (
            <div
              key={node}
              style={{
                position: "absolute",
                left: pos.x - 92,
                top: pos.y - 56,
                width: 184,
                height: 112,
                borderRadius: 20,
                background: index === 0 ? "#17130a" : SURFACE,
                border: index === 0 ? "2px solid rgba(255,189,25,.55)" : `1px solid ${LINE}`,
                color: index === 0 ? GOLD : WHITE,
                display: "grid",
                placeItems: "center",
                fontSize: 24,
                fontWeight: 900,
                transform: `scale(${(0.86 + enter * 0.14) * pulse})`,
                opacity: enter,
              }}
            >
              {node}
            </div>
          );
        })}
        <Source text={asString(payload.source)} />
      </AbsoluteFill>
    </SceneShell>
  );
};

const MoneyFlowScene = ({
  payload,
  durationFrames,
}: {
  payload: GenericRecord;
  durationFrames: number;
}) => {
  const frame = useCurrentFrame();
  const flows = asArray<{from?: string; to?: string; value?: string}>(payload.flows);

  const columns = [
    {label: "A", x: 420, y: 540},
    {label: "B", x: 890, y: 370},
    {label: "C", x: 890, y: 700},
    {label: "D", x: 1370, y: 370},
  ];

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill style={{fontFamily: FONT}}>
        <div style={{position: "absolute", left: 145, top: 165}}>
          <Eyebrow>{asString(payload.eyebrow)}</Eyebrow>
          <div style={{color: GOLD, fontSize: 94, fontWeight: 950, letterSpacing: -5}}>
            {asString(payload.amount)}
          </div>
        </div>

        <svg width="1920" height="1080" style={{position: "absolute", inset: 0}}>
          {flows.map((flow, index) => {
            const a = columns.find((item) => item.label === flow.from);
            const b = columns.find((item) => item.label === flow.to);
            if (!a || !b) return null;
            const progress = interpolate(
              frame,
              [30 + index * 22, 80 + index * 22],
              [0, 1],
              clamp,
            );
            const x2 = a.x + (b.x - a.x) * progress;
            const y2 = a.y + (b.y - a.y) * progress;
            return (
              <g key={index}>
                <line
                  x1={a.x}
                  y1={a.y}
                  x2={x2}
                  y2={y2}
                  stroke={GOLD}
                  strokeWidth={6}
                  strokeLinecap="round"
                />
                <text
                  x={(a.x + b.x) / 2}
                  y={(a.y + b.y) / 2 - 18}
                  textAnchor="middle"
                  fill={WHITE}
                  fontSize={24}
                  fontWeight={800}
                >
                  {flow.value}
                </text>
              </g>
            );
          })}
        </svg>

        {columns.map((item, index) => (
          <div
            key={item.label}
            style={{
              position: "absolute",
              left: item.x - 72,
              top: item.y - 72,
              width: 144,
              height: 144,
              borderRadius: "50%",
              display: "grid",
              placeItems: "center",
              color: index === 0 ? BG : WHITE,
              background: index === 0 ? GOLD : SURFACE_2,
              border: index === 0 ? "none" : `1px solid ${LINE}`,
              fontSize: 48,
              fontWeight: 950,
            }}
          >
            {item.label}
          </div>
        ))}
        <Source text={asString(payload.source)} />
      </AbsoluteFill>
    </SceneShell>
  );
};

const ProcessScene = ({
  payload,
  durationFrames,
}: {
  payload: GenericRecord;
  durationFrames: number;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const steps = asArray<string>(payload.steps);

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          padding: "0 145px",
          fontFamily: FONT,
        }}
      >
        <Eyebrow>{asString(payload.eyebrow)}</Eyebrow>
        <div style={{display: "flex", alignItems: "center", gap: 16}}>
          {steps.map((step, index) => {
            const enter = spring({
              frame: Math.max(0, frame - index * 13),
              fps,
              durationInFrames: 19,
              config: {damping: 18, stiffness: 110},
            });
            return (
              <div key={step} style={{display: "flex", alignItems: "center", flex: 1}}>
                <div
                  style={{
                    flex: 1,
                    padding: "34px 18px",
                    borderRadius: 20,
                    textAlign: "center",
                    background: index === 2 ? "rgba(255,189,25,.08)" : SURFACE,
                    border: index === 2 ? "1px solid rgba(255,189,25,.45)" : `1px solid ${LINE}`,
                    color: index === 2 ? GOLD : WHITE,
                    fontSize: 27,
                    fontWeight: 900,
                    transform: `scale(${0.92 + enter * 0.08})`,
                    opacity: enter,
                  }}
                >
                  {step}
                </div>
                {index < steps.length - 1 && (
                  <div style={{color: GOLD, fontSize: 36, margin: "0 11px"}}>→</div>
                )}
              </div>
            );
          })}
        </div>
        <div style={{marginTop: 35, color: MUTED, fontSize: 28}}>
          {asString(payload.caption)}
        </div>
        <Source text={asString(payload.source)} />
      </AbsoluteFill>
    </SceneShell>
  );
};

const BigNumberScene = ({
  payload,
  durationFrames,
}: {
  payload: GenericRecord;
  durationFrames: number;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({
    frame,
    fps,
    durationInFrames: 28,
    config: {damping: 16, stiffness: 98},
  });
  const shine = interpolate(frame, [20, 110], [-40, 140], clamp);

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          fontFamily: FONT,
          textAlign: "center",
        }}
      >
        <Eyebrow>{asString(payload.eyebrow)}</Eyebrow>
        <div
          style={{
            color: GOLD,
            fontSize: 172,
            fontWeight: 950,
            letterSpacing: -9,
            transform: `scale(${0.82 + pop * 0.18})`,
            position: "relative",
            overflow: "hidden",
            padding: "0 20px",
          }}
        >
          {asString(payload.number)}
          <div
            style={{
              position: "absolute",
              left: `${shine}%`,
              top: 0,
              width: 160,
              height: "100%",
              transform: "skewX(-18deg)",
              background:
                "linear-gradient(90deg, transparent, rgba(255,255,255,.27), transparent)",
              filter: "blur(8px)",
            }}
          />
        </div>
        <div style={{color: WHITE, fontSize: 34, fontWeight: 800, marginTop: 18}}>
          {asString(payload.caption)}
        </div>
        <div
          style={{
            marginTop: 34,
            padding: "14px 22px",
            borderRadius: 14,
            color: "#ffd2d2",
            background: "rgba(255,107,107,.07)",
            border: "1px solid rgba(255,107,107,.24)",
            fontSize: 24,
            fontWeight: 800,
          }}
        >
          {asString(payload.warning)}
        </div>
        <Source text={asString(payload.source)} />
      </AbsoluteFill>
    </SceneShell>
  );
};

const DoDontScene = ({
  payload,
  durationFrames,
}: {
  payload: GenericRecord;
  durationFrames: number;
}) => {
  const yes = asArray<string>(payload.yes);
  const no = asArray<string>(payload.no);

  const list = (items: string[], good: boolean) => (
    <div
      style={{
        flex: 1,
        borderRadius: 25,
        padding: "38px 42px",
        background: SURFACE,
        border: `1px solid ${good ? "rgba(121,217,154,.32)" : "rgba(255,107,107,.30)"}`,
      }}
    >
      <div
        style={{
          color: good ? GREEN : RED,
          fontWeight: 950,
          fontSize: 28,
          marginBottom: 24,
          textTransform: "uppercase",
          letterSpacing: 4,
        }}
      >
        {good ? "Serve para" : "Não serve para"}
      </div>
      {items.map((item) => (
        <div
          key={item}
          style={{
            padding: "17px 0",
            borderBottom: "1px solid rgba(255,255,255,.07)",
            color: WHITE,
            fontSize: 31,
            fontWeight: 850,
          }}
        >
          <span style={{color: good ? GREEN : RED, marginRight: 15}}>
            {good ? "✓" : "×"}
          </span>
          {item}
        </div>
      ))}
    </div>
  );

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          padding: "0 150px",
          fontFamily: FONT,
        }}
      >
        <Eyebrow>{asString(payload.eyebrow)}</Eyebrow>
        <div style={{display: "flex", gap: 28}}>
          {list(yes, true)}
          {list(no, false)}
        </div>
        <Source text={asString(payload.source)} />
      </AbsoluteFill>
    </SceneShell>
  );
};

const TimelineScene = ({
  payload,
  durationFrames,
}: {
  payload: GenericRecord;
  durationFrames: number;
}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [16, 82], [0, 1], clamp);

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          padding: "0 160px",
          fontFamily: FONT,
        }}
      >
        <Eyebrow>{asString(payload.eyebrow)}</Eyebrow>
        <div
          style={{
            color: GOLD,
            fontSize: 94,
            fontWeight: 950,
            letterSpacing: -5,
          }}
        >
          {asString(payload.date)}
        </div>
        <div
          style={{
            marginTop: 30,
            color: WHITE,
            fontSize: 61,
            fontWeight: 900,
            lineHeight: 1.08,
            maxWidth: 1320,
          }}
        >
          {asString(payload.headline)}
        </div>
        <div
          style={{
            width: 1100,
            height: 11,
            borderRadius: 999,
            background: "#20252b",
            marginTop: 48,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${progress * 100}%`,
              height: "100%",
              borderRadius: 999,
              background: GOLD,
            }}
          />
        </div>
        <Source text={asString(payload.source)} />
      </AbsoluteFill>
    </SceneShell>
  );
};

const ClosingScene = ({
  payload,
  durationFrames,
}: {
  payload: GenericRecord;
  durationFrames: number;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({
    frame,
    fps,
    durationInFrames: 28,
    config: {damping: 20, stiffness: 95},
  });
  const pulse = 1 + Math.sin(frame / 13) * 0.012;

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          padding: "0 180px",
          textAlign: "center",
          fontFamily: FONT,
        }}
      >
        <Eyebrow>{asString(payload.eyebrow, "O Dinheiro Explica")}</Eyebrow>
        <div
          style={{
            maxWidth: 1380,
            color: WHITE,
            fontSize: 82,
            fontWeight: 950,
            lineHeight: 1.04,
            letterSpacing: -4.5,
            transform: `scale(${pulse * (0.94 + enter * 0.06)})`,
            opacity: enter,
          }}
        >
          {asString(payload.headline)}
        </div>
        <Source text={asString(payload.source)} />
      </AbsoluteFill>
    </SceneShell>
  );
};

const FallbackScene = ({
  title,
  durationFrames,
}: {
  title?: string;
  durationFrames: number;
}) => (
  <SceneShell durationFrames={durationFrames}>
    <AbsoluteFill
      style={{
        justifyContent: "center",
        padding: "0 160px",
        fontFamily: FONT,
      }}
    >
      <Eyebrow>O Dinheiro Explica</Eyebrow>
      <div style={{fontSize: 80, fontWeight: 950, color: WHITE}}>
        {title ?? "Cena"}
      </div>
    </AbsoluteFill>
  </SceneShell>
);

const Visual = ({scene}: {scene: Scene}) => {
  const payload = scene.visual?.payload ?? {};
  switch (scene.visual?.type) {
    case "HEADLINE":
      return <HeadlineScene payload={payload} durationFrames={scene.duration_frames} />;
    case "STAT_GRID":
      return <StatGridScene payload={payload} durationFrames={scene.duration_frames} />;
    case "BEFORE_AFTER":
      return <BeforeAfterScene payload={payload} durationFrames={scene.duration_frames} />;
    case "NETWORK":
      return <NetworkScene payload={payload} durationFrames={scene.duration_frames} />;
    case "MONEY_FLOW":
      return <MoneyFlowScene payload={payload} durationFrames={scene.duration_frames} />;
    case "PROCESS":
      return <ProcessScene payload={payload} durationFrames={scene.duration_frames} />;
    case "BIG_NUMBER":
      return <BigNumberScene payload={payload} durationFrames={scene.duration_frames} />;
    case "DO_DONT":
      return <DoDontScene payload={payload} durationFrames={scene.duration_frames} />;
    case "TIMELINE":
      return <TimelineScene payload={payload} durationFrames={scene.duration_frames} />;
    case "CLOSING":
      return <ClosingScene payload={payload} durationFrames={scene.duration_frames} />;
    default:
      return <FallbackScene title={scene.title} durationFrames={scene.duration_frames} />;
  }
};

export const EditorialPilot = () => {
  const scenes = renderInput.scenes as Scene[];

  return (
    <AbsoluteFill style={{backgroundColor: BG}}>
      <MovingBackground />
      <Brand />
      {scenes.map((scene) => (
        <Sequence
          key={scene.id}
          from={scene.start_frame}
          durationInFrames={scene.duration_frames}
        >
          <Visual scene={scene} />
          <TransitionSweep sceneIndex={scene.scene_index} />
          <Audio src={staticFile(scene.audio_file)} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

type ThumbnailVariant = "A" | "B" | "C";

export const PixPilotThumbnail = ({
  variant = "A",
}: {
  variant?: ThumbnailVariant;
}) => {
  const copy = {
    A: {top: "O PIX", main: "VAI ATRÁS", badge: "MED 2.0"},
    B: {top: "O RASTRO", main: "DO GOLPE", badge: "NOVO PIX"},
    C: {top: "ATÉ OUTRAS", main: "CONTAS", badge: "RASTREAMENTO"},
  }[variant];

  const nodes = [
    {x: 835, y: 358, label: "A"},
    {x: 1002, y: 258, label: "B"},
    {x: 1010, y: 470, label: "C"},
    {x: 1160, y: 258, label: "D"},
  ];
  const paths = [[0, 1], [0, 2], [1, 3]];

  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG,
        fontFamily: FONT,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 79% 48%, rgba(255,189,25,.13), transparent 35%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 58,
          top: 48,
          color: GOLD,
          fontSize: 20,
          fontWeight: 950,
          letterSpacing: 4,
        }}
      >
        O DINHEIRO EXPLICA
      </div>

      <div
        style={{
          position: "absolute",
          left: 62,
          top: 155,
          width: 650,
          color: WHITE,
          lineHeight: 0.91,
          letterSpacing: -5,
          fontWeight: 950,
        }}
      >
        <div style={{fontSize: 70}}>{copy.top}</div>
        <div style={{fontSize: 100, color: GOLD, marginTop: 8}}>{copy.main}</div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 66,
          top: 395,
          display: "inline-flex",
          alignItems: "center",
          gap: 10,
          padding: "10px 15px",
          borderRadius: 999,
          background: "rgba(255,107,107,.10)",
          border: "1px solid rgba(255,107,107,.38)",
          color: "#ff9494",
          fontSize: 19,
          fontWeight: 900,
          letterSpacing: 2,
        }}
      >
        GOLPE
      </div>
      <div
        style={{
          position: "absolute",
          left: 170,
          top: 400,
          color: MUTED,
          fontSize: 19,
          fontWeight: 800,
        }}
      >
        R$ 1.000 saem da primeira conta
      </div>

      <div
        style={{
          position: "absolute",
          right: 55,
          top: 105,
          width: 500,
          height: 515,
          borderRadius: 42,
          transform: "rotate(2deg)",
          background: "#0d1115",
          border: "1px solid #2b323a",
          boxShadow: "0 28px 80px rgba(0,0,0,.5)",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 32,
            top: 28,
            display: "flex",
            alignItems: "center",
            gap: 12,
            color: WHITE,
            fontSize: 24,
            fontWeight: 950,
          }}
        >
          <div
            style={{
              width: 42,
              height: 42,
              borderRadius: 13,
              background: GOLD,
              color: BG,
              display: "grid",
              placeItems: "center",
              fontSize: 18,
            }}
          >
            PIX
          </div>
          Transferência contestada
        </div>
        <div
          style={{
            position: "absolute",
            left: 32,
            top: 92,
            color: GOLD,
            fontSize: 44,
            fontWeight: 950,
            letterSpacing: -2,
          }}
        >
          R$ 1.000
        </div>
        <div
          style={{
            position: "absolute",
            left: 32,
            top: 150,
            color: MUTED,
            fontSize: 17,
            fontWeight: 750,
          }}
        >
          O rastro continua
        </div>
      </div>

      <svg width="1280" height="720" style={{position: "absolute", inset: 0}}>
        {paths.map(([aIndex, bIndex], index) => {
          const a = nodes[aIndex];
          const b = nodes[bIndex];
          return (
            <line
              key={index}
              x1={a.x + 47}
              y1={a.y}
              x2={b.x - 47}
              y2={b.y}
              stroke={GOLD}
              strokeWidth={7}
              strokeLinecap="round"
              opacity={index === 0 ? 1 : 0.78}
            />
          );
        })}
      </svg>

      {nodes.map((node, index) => (
        <div
          key={node.label}
          style={{
            position: "absolute",
            left: node.x - 47,
            top: node.y - 47,
            width: 94,
            height: 94,
            borderRadius: "50%",
            display: "grid",
            placeItems: "center",
            background: index === 0 ? GOLD : "#171c21",
            color: index === 0 ? BG : WHITE,
            border: index === 0 ? "none" : "2px solid #3b434c",
            fontSize: 30,
            fontWeight: 950,
            boxShadow:
              index === 0
                ? "0 0 42px rgba(255,189,25,.22)"
                : "0 14px 28px rgba(0,0,0,.24)",
          }}
        >
          {node.label}
        </div>
      ))}

      <div
        style={{
          position: "absolute",
          right: 65,
          bottom: 45,
          padding: "8px 12px",
          borderRadius: 10,
          color: GOLD,
          background: "rgba(255,189,25,.08)",
          border: "1px solid rgba(255,189,25,.20)",
          fontSize: 17,
          fontWeight: 900,
          letterSpacing: 1.5,
        }}
      >
        {copy.badge}
      </div>
    </AbsoluteFill>
  );
};
