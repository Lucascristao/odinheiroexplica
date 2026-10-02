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
import {
  ArrowRight,
  Ban,
  Banknote,
  CalendarDays,
  CircleDollarSign,
  Fuel,
  Info,
  Landmark,
  ListChecks,
  Scale,
  ShieldAlert,
  TrendingDown,
  TrendingUp,
  WalletCards,
} from "lucide-react";
import {
  EditorialMicroScene,
  SceneTransitionAccent,
  StoryWorldBackground,
  findActiveBeat,
  type EditorialBeat,
  type EditorialDirection,
} from "./EditorialMicroScene";
import renderInput from "../generated/daily-render-input.json";
import {EditorialStage} from "./EditorialStage";
import {EditorialCaptions, type CaptionWord} from "./EditorialCaptions";
import type {EditorialStage as Stage} from "../../src/lib/editorial-stage";

type GenericRecord = Record<string, unknown>;

type VisualBeat = EditorialBeat;

type Scene = {
  id: string;
  scene_index: number;
  title?: string;
  start_frame: number;
  duration_frames: number;
  audio_duration_seconds?: number;
  audio_file: string;
  audio_captions?: CaptionWord[];
  audio_volume_multiplier?: number;
  visual: {
    type: string;
    payload?: GenericRecord;
    beats?: VisualBeat[];
    stage?: Stage;
    transition?: VisualBeat["transition"];
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

const sceneFrameAt = (durationFrames: number, ratio: number) =>
  Math.round(Math.max(1, durationFrames - 1) * Math.max(0, Math.min(1, ratio)));

const stagedSpring = ({
  frame,
  durationFrames,
  ratio,
  fps,
}: {
  frame: number;
  durationFrames: number;
  ratio: number;
  fps: number;
}) =>
  spring({
    frame: Math.max(0, frame - sceneFrameAt(durationFrames, ratio)),
    fps,
    durationInFrames: Math.max(16, Math.round(fps * 0.7)),
    config: {damping: 18, stiffness: 105},
  });

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
  const driftX = interpolate(
    frame,
    [0, Math.max(1, durationFrames - 1)],
    [-3, 3],
    clamp,
  );
  const breathe = 1 + Math.sin(frame / 70) * 0.0025;

  return (
    <AbsoluteFill
      style={{
        opacity,
        transform: `translate(${driftX}px, ${inY + outY}px) scale(${breathe})`,
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
  const accent = asString(payload.accent);
  const accentEnter = stagedSpring({
    frame,
    durationFrames,
    ratio: 0.38,
    fps,
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
            letterSpacing: -1.6,
            transform: `scale(${0.96 + enter * 0.04})`,
          }}
        >
          {asString(payload.headline)}
        </div>
        <div
          style={{
            width: `${interpolate(
              frame,
              [sceneFrameAt(durationFrames, 0.08), sceneFrameAt(durationFrames, 0.58)],
              [0, 760],
              clamp,
            )}px`,
            height: 7,
            borderRadius: 999,
            background: GOLD,
            marginTop: 34,
            boxShadow: "0 0 28px rgba(255,189,25,.14)",
          }}
        />
        {accent && (
          <div
            style={{
              marginTop: 24,
              width: "fit-content",
              padding: "11px 17px",
              borderRadius: 12,
              color: GOLD,
              background: "rgba(255,189,25,.06)",
              border: "1px solid rgba(255,189,25,.18)",
              fontSize: 23,
              fontWeight: 900,
              textTransform: "uppercase",
              letterSpacing: 2.4,
              opacity: accentEnter,
              transform: `translateY(${(1 - accentEnter) * 18}px)`,
            }}
          >
            {accent}
          </div>
        )}
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
            const ratio =
              0.08 + (index / Math.max(1, stats.length - 1)) * 0.5;
            const enter = stagedSpring({
              frame,
              durationFrames,
              ratio,
              fps,
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
                    letterSpacing: -1.8,
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
  const split = interpolate(
    frame,
    [sceneFrameAt(durationFrames, 0.18), sceneFrameAt(durationFrames, 0.62)],
    [0, 1],
    clamp,
  );

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
              letterSpacing: -1.2,
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
            const startRatio =
              0.12 + (index / Math.max(1, paths.length)) * 0.48;
            const progress = interpolate(
              frame,
              [
                sceneFrameAt(durationFrames, startRatio),
                sceneFrameAt(durationFrames, Math.min(0.86, startRatio + 0.24)),
              ],
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
          const enter = stagedSpring({
            frame,
            durationFrames,
            ratio: 0.06 + (index / Math.max(1, nodes.length - 1)) * 0.56,
            fps,
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
          <div style={{color: GOLD, fontSize: 94, fontWeight: 950, letterSpacing: -1.6}}>
            {asString(payload.amount)}
          </div>
        </div>

        <svg width="1920" height="1080" style={{position: "absolute", inset: 0}}>
          {flows.map((flow, index) => {
            const a = columns.find((item) => item.label === flow.from);
            const b = columns.find((item) => item.label === flow.to);
            if (!a || !b) return null;
            const startRatio =
              0.16 + (index / Math.max(1, flows.length)) * 0.48;
            const progress = interpolate(
              frame,
              [
                sceneFrameAt(durationFrames, startRatio),
                sceneFrameAt(durationFrames, Math.min(0.9, startRatio + 0.25)),
              ],
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
  const progress = frame / Math.max(1, durationFrames - 1);
  const activeIndex = Math.min(
    Math.max(0, steps.length - 1),
    Math.floor(progress * Math.max(1, steps.length)),
  );
  const captionEnter = stagedSpring({
    frame,
    durationFrames,
    ratio: 0.72,
    fps,
  });

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
            const ratio =
              0.06 + (index / Math.max(1, steps.length - 1)) * 0.6;
            const enter = stagedSpring({
              frame,
              durationFrames,
              ratio,
              fps,
            });
            const active = index === activeIndex;
            const completed = index < activeIndex;

            return (
              <div key={step} style={{display: "flex", alignItems: "center", flex: 1}}>
                <div
                  style={{
                    flex: 1,
                    padding: "34px 18px",
                    borderRadius: 20,
                    textAlign: "center",
                    background: active
                      ? "rgba(255,189,25,.10)"
                      : completed
                        ? "rgba(255,189,25,.035)"
                        : SURFACE,
                    border: active
                      ? "1px solid rgba(255,189,25,.62)"
                      : completed
                        ? "1px solid rgba(255,189,25,.20)"
                        : `1px solid ${LINE}`,
                    color: active ? GOLD : WHITE,
                    fontSize: 27,
                    fontWeight: 900,
                    transform: `scale(${(0.92 + enter * 0.08) * (active ? 1.025 : 1)})`,
                    opacity: enter,
                    boxShadow: active
                      ? "0 0 32px rgba(255,189,25,.08)"
                      : "none",
                  }}
                >
                  {step}
                </div>
                {index < steps.length - 1 && (
                  <div
                    style={{
                      color: GOLD,
                      fontSize: 36,
                      margin: "0 11px",
                      opacity: Math.max(0.22, index < activeIndex ? 1 : enter * 0.55),
                    }}
                  >
                    →
                  </div>
                )}
              </div>
            );
          })}
        </div>
        <div
          style={{
            marginTop: 35,
            color: MUTED,
            fontSize: 28,
            opacity: captionEnter,
            transform: `translateY(${(1 - captionEnter) * 16}px)`,
          }}
        >
          {asString(payload.caption)}
        </div>
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
  const cycle = Math.max(96, Math.round(durationFrames * 0.38));
  const shineFrame = frame % cycle;
  const shine = interpolate(
    shineFrame,
    [0, Math.max(1, Math.round(cycle * 0.62))],
    [-45, 145],
    clamp,
  );
  const captionEnter = stagedSpring({
    frame,
    durationFrames,
    ratio: 0.24,
    fps,
  });
  const warningEnter = stagedSpring({
    frame,
    durationFrames,
    ratio: 0.55,
    fps,
  });
  const pulse = 1 + Math.sin(frame / 22) * 0.008;

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
            letterSpacing: -2.2,
            transform: `scale(${(0.82 + pop * 0.18) * pulse})`,
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
        <div
          style={{
            color: WHITE,
            fontSize: 34,
            fontWeight: 800,
            marginTop: 18,
            opacity: captionEnter,
            transform: `translateY(${(1 - captionEnter) * 14}px)`,
          }}
        >
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
            opacity: warningEnter,
            transform: `translateY(${(1 - warningEnter) * 18}px) scale(${0.97 + warningEnter * 0.03})`,
          }}
        >
          {asString(payload.warning)}
        </div>
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
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const yes = asArray<string>(payload.yes);
  const no = asArray<string>(payload.no);
  const totalItems = Math.max(1, yes.length + no.length);
  const progress = frame / Math.max(1, durationFrames - 1);
  const activeItem = Math.min(totalItems - 1, Math.floor(progress * totalItems));

  const list = (items: string[], good: boolean, offset: number) => (
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
      {items.map((item, localIndex) => {
        const globalIndex = offset + localIndex;
        const enter = stagedSpring({
          frame,
          durationFrames,
          ratio:
            0.09 +
            (globalIndex / Math.max(1, totalItems - 1)) * 0.58,
          fps,
        });
        const active = globalIndex === activeItem;

        return (
          <div
            key={item}
            style={{
              padding: "17px 12px",
              borderBottom: "1px solid rgba(255,255,255,.07)",
              borderRadius: 10,
              color: WHITE,
              fontSize: 31,
              fontWeight: 850,
              opacity: enter,
              transform: `translateX(${(1 - enter) * 22}px)`,
              background: active
                ? good
                  ? "rgba(121,217,154,.055)"
                  : "rgba(255,107,107,.055)"
                : "transparent",
            }}
          >
            <span style={{color: good ? GREEN : RED, marginRight: 15}}>
              {good ? "✓" : "×"}
            </span>
            {item}
          </div>
        );
      })}
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
          {list(yes, true, 0)}
          {list(no, false, yes.length)}
        </div>
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
  const {fps} = useVideoConfig();
  const progress = interpolate(
    frame,
    [sceneFrameAt(durationFrames, 0.12), sceneFrameAt(durationFrames, 0.84)],
    [0, 1],
    clamp,
  );
  const headlineEnter = stagedSpring({
    frame,
    durationFrames,
    ratio: 0.24,
    fps,
  });
  const datePulse = 1 + Math.sin(frame / 24) * 0.006;

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
            letterSpacing: -1.6,
            transform: `scale(${datePulse})`,
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
            opacity: headlineEnter,
            transform: `translateY(${(1 - headlineEnter) * 18}px)`,
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
              boxShadow: "0 0 22px rgba(255,189,25,.14)",
            }}
          />
        </div>
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
  const headline = asString(payload.headline);
  const parts = headline
    .split(/(?<=[.!?])\s+/)
    .map((part) => part.trim())
    .filter(Boolean);
  const pulse = 1 + Math.sin(frame / 18) * 0.006;

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
            width: "100%",
            maxWidth: 1440,
            display: "grid",
            gap: 18,
            transform: `scale(${pulse})`,
          }}
        >
          {(parts.length ? parts : [headline]).map((part, index, all) => {
            const enter = stagedSpring({
              frame,
              durationFrames,
              ratio:
                0.08 +
                (index / Math.max(1, all.length - 1)) * 0.62,
              fps,
            });
            return (
              <div
                key={`${part}-${index}`}
                style={{
                  color: index === all.length - 1 ? GOLD : WHITE,
                  fontSize: all.length > 2 ? 64 : 78,
                  fontWeight: 950,
                  lineHeight: 1.03,
                  letterSpacing: -1.2,
                  opacity: enter,
                  transform: `translateY(${(1 - enter) * 22}px)`,
                }}
              >
                {part}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </SceneShell>
  );
};

const BeatIcon = ({kind}: {kind?: string}) => {
  const common = {size: 58, strokeWidth: 1.8};
  switch (kind) {
    case "number":
    case "money":
      return <CircleDollarSign {...common} />;
    case "bank":
      return <Landmark {...common} />;
    case "date":
      return <CalendarDays {...common} />;
    case "flow":
      return <ArrowRight {...common} />;
    case "process":
      return <ListChecks {...common} />;
    case "warning":
      return <ShieldAlert {...common} />;
    case "compare":
      return <Scale {...common} />;
    case "trend_up":
      return <TrendingUp {...common} />;
    case "trend_down":
      return <TrendingDown {...common} />;
    case "fuel":
      return <Fuel {...common} />;
    case "block":
      return <Ban {...common} />;
    case "fact":
    default:
      return <Info {...common} />;
  }
};

const InformationBeatLayer = ({scene}: {scene: Scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const beats = scene.visual?.beats ?? [];

  if (!beats.length) return null;

  const resolved = beats
    .filter((beat) => typeof beat.resolved_frame === "number")
    .sort((a, b) => (a.resolved_frame ?? 0) - (b.resolved_frame ?? 0));

  if (!resolved.length) return null;

  let activeIndex = -1;
  for (let index = 0; index < resolved.length; index += 1) {
    if (frame >= (resolved[index].resolved_frame ?? 0)) {
      activeIndex = index;
    }
  }

  if (activeIndex < 0) return null;

  const beat = resolved[activeIndex];
  const startFrame = beat.resolved_frame ?? 0;
  const nextFrame =
    activeIndex < resolved.length - 1
      ? resolved[activeIndex + 1].resolved_frame ?? scene.duration_frames
      : Math.min(
          scene.duration_frames,
          Math.max(
            startFrame + Math.round(fps * 2.2),
            Math.round((scene.audio_duration_seconds ?? 0) * fps),
          ),
        );

  const localFrame = Math.max(0, frame - startFrame);
  const enter = spring({
    frame: localFrame,
    fps,
    durationInFrames: Math.max(14, Math.round(fps * 0.55)),
    config: {damping: 18, stiffness: 108},
  });
  const exitStart = Math.max(startFrame + 10, nextFrame - 7);
  const exitOpacity = interpolate(
    frame,
    [exitStart, Math.max(exitStart + 1, nextFrame - 1)],
    [1, 0],
    clamp,
  );
  const opacity = Math.min(enter, exitOpacity);
  const kind = beat.kind ?? "fact";
  const warning = kind === "warning" || kind === "block";
  const positive = kind === "trend_up";
  const accent = warning ? RED : positive ? GREEN : GOLD;
  const variant = activeIndex % 3;
  const isWide = kind === "flow" || kind === "compare";
  const left =
    isWide || variant === 2 ? 260 : variant === 0 ? 150 : undefined;
  const right = !isWide && variant === 1 ? 150 : undefined;
  const width = isWide || variant === 2 ? 1400 : 790;
  const top = isWide ? 575 : variant === 2 ? 610 : 565;
  const value = asString(beat.value);
  const from = asString(beat.from);
  const to = asString(beat.to);

  return (
    <AbsoluteFill
      style={{
        zIndex: 65,
        pointerEvents: "none",
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          position: "absolute",
          left,
          right,
          top,
          width,
          minHeight: isWide ? 250 : 285,
          padding: isWide ? "30px 38px" : "34px 40px",
          borderRadius: 28,
          background:
            "linear-gradient(145deg, rgba(18,22,26,.97), rgba(10,12,14,.94))",
          border: `1px solid ${warning ? "rgba(255,107,107,.38)" : "rgba(255,189,25,.30)"}`,
          boxShadow: "0 28px 90px rgba(0,0,0,.38)",
          opacity,
          transform: `translateY(${(1 - enter) * 34}px) scale(${0.97 + enter * 0.03})`,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            opacity: 0.18,
            background: `radial-gradient(circle at 84% 20%, ${accent}55, transparent 34%)`,
          }}
        />

        {kind === "flow" && from && to ? (
          <div
            style={{
              position: "relative",
              display: "grid",
              gridTemplateColumns: "1fr auto 1fr",
              alignItems: "center",
              gap: 26,
              minHeight: 185,
            }}
          >
            <div
              style={{
                padding: "28px 26px",
                borderRadius: 20,
                border: `1px solid ${LINE}`,
                background: SURFACE_2,
                color: WHITE,
                fontSize: 34,
                fontWeight: 900,
                textAlign: "center",
              }}
            >
              {from}
            </div>
            <ArrowRight size={54} strokeWidth={1.8} color={GOLD} />
            <div
              style={{
                padding: "28px 26px",
                borderRadius: 20,
                border: "1px solid rgba(255,189,25,.40)",
                background: "rgba(255,189,25,.065)",
                color: GOLD,
                fontSize: 34,
                fontWeight: 900,
                textAlign: "center",
              }}
            >
              {to}
            </div>
          </div>
        ) : (
          <div
            style={{
              position: "relative",
              display: "flex",
              gap: 30,
              alignItems: "center",
            }}
          >
            <div
              style={{
                width: 104,
                height: 104,
                flex: "0 0 auto",
                borderRadius: 26,
                display: "grid",
                placeItems: "center",
                color: accent,
                background: `${accent}12`,
                border: `1px solid ${accent}40`,
              }}
            >
              <BeatIcon kind={kind} />
            </div>
            <div style={{minWidth: 0}}>
              {value && (
                <div
                  style={{
                    color: accent,
                    fontSize: 72,
                    lineHeight: 0.95,
                    fontWeight: 950,
                    letterSpacing: -1.4,
                    marginBottom: 12,
                  }}
                >
                  {value}
                </div>
              )}
              <div
                style={{
                  color: WHITE,
                  fontSize: value ? 39 : 48,
                  lineHeight: 1.04,
                  fontWeight: 940,
                  letterSpacing: -0.9,
                }}
              >
                {beat.headline}
              </div>
              {beat.detail && (
                <div
                  style={{
                    color: MUTED,
                    fontSize: 25,
                    lineHeight: 1.3,
                    fontWeight: 700,
                    marginTop: 15,
                    maxWidth: 1040,
                  }}
                >
                  {beat.detail}
                </div>
              )}
            </div>
          </div>
        )}

        {kind === "flow" && (
          <div
            style={{
              position: "relative",
              marginTop: 18,
              color: WHITE,
              fontSize: 32,
              fontWeight: 900,
              textAlign: "center",
            }}
          >
            {beat.headline}
            {beat.detail && (
              <span style={{color: MUTED, fontSize: 24, marginLeft: 14}}>
                {beat.detail}
              </span>
            )}
          </div>
        )}

        <div
          style={{
            position: "absolute",
            left: 0,
            bottom: 0,
            height: 5,
            width: `${interpolate(
              frame,
              [startFrame, Math.max(startFrame + 1, nextFrame)],
              [0, 100],
              clamp,
            )}%`,
            background: accent,
            opacity: 0.78,
          }}
        />
      </div>
    </AbsoluteFill>
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

type SoundEvent = {
  frame: number;
  file: "tick.wav" | "soft-impact.wav" | "soft-whoosh.wav" | "subtle-alert.wav" | "outro-signature.wav";
  volume: number;
  durationSeconds: number;
};

const SoundDesign = ({
  scene,
  isLast,
}: {
  scene: Scene;
  isLast: boolean;
}) => {
  const {fps} = useVideoConfig();
  const payload = scene.visual?.payload ?? {};
  const type = scene.visual?.type ?? "";
  const authoredBeats = scene.visual?.beats ?? [];
  const events: SoundEvent[] = [];

  const add = (
    ratio: number,
    file: SoundEvent["file"],
    volume: number,
    durationSeconds: number,
  ) => {
    events.push({
      frame: sceneFrameAt(scene.duration_frames, ratio),
      file,
      volume,
      durationSeconds,
    });
  };

  // Transições sonoras são espaçadas para não transformar o vídeo
  // em uma sequência de whooshes. A narração continua sempre em primeiro plano.
  if (!scene.visual.stage && scene.scene_index > 0 && scene.scene_index % 2 === 0 && type !== "CLOSING") {
    add(0.015, "soft-whoosh.wav", 0.08, 0.55);
  }

  const soundFile = (sound?: VisualBeat["sound"]): SoundEvent["file"] | null => {
    switch (sound) {
      case "tick":
        return "tick.wav";
      case "impact":
        return "soft-impact.wav";
      case "whoosh":
        return "soft-whoosh.wav";
      case "alert":
        return "subtle-alert.wav";
      default:
        return null;
    }
  };

  const orderedBeats = [...authoredBeats]
    .filter((beat) => typeof beat.resolved_frame === "number")
    .sort((a, b) => (a.resolved_frame ?? 0) - (b.resolved_frame ?? 0));

  orderedBeats.forEach((beat, index) => {
    const file = soundFile(beat.sound);
    if (file && typeof beat.resolved_frame === "number") {
      const durationSeconds =
        file === "soft-impact.wav"
          ? 0.5
          : file === "soft-whoosh.wav"
            ? 0.55
            : file === "subtle-alert.wav"
              ? 0.34
              : 0.12;

      const volume =
        file === "soft-impact.wav"
          ? 0.12
          : file === "soft-whoosh.wav"
            ? 0.085
            : file === "subtle-alert.wav"
              ? 0.095
              : 0.06;

      events.push({
        frame: beat.resolved_frame,
        file,
        volume,
        durationSeconds,
      });
    }

    // A persistent stage is driven by authored events. Do not invent sound
    // accents at percentages of a beat whose meaning may not match that sound.
    if (scene.visual.stage || typeof beat.resolved_frame !== "number") return;

    const nextFrame =
      index < orderedBeats.length - 1
        ? orderedBeats[index + 1].resolved_frame ?? scene.duration_frames
        : Math.min(
            scene.duration_frames - 1,
            Math.round((scene.audio_duration_seconds ?? scene.duration_frames / fps) * fps),
          );

    const beatLength = Math.max(0, nextFrame - beat.resolved_frame);
    if (beatLength < Math.round(fps * 1.8)) return;

    const developmentFrame =
      beat.resolved_frame + Math.round(beatLength * 0.62);

    if (
      beat.treatment === "flow_diagram" ||
      beat.treatment === "timeline" ||
      beat.treatment === "meter"
    ) {
      events.push({
        frame: developmentFrame,
        file: beat.treatment === "flow_diagram" ? "soft-whoosh.wav" : "tick.wav",
        volume: beat.treatment === "flow_diagram" ? 0.065 : 0.05,
        durationSeconds: beat.treatment === "flow_diagram" ? 0.55 : 0.12,
      });
    }

    if (
      beat.treatment === "equation" ||
      beat.treatment === "stack" ||
      beat.treatment === "split_compare"
    ) {
      events.push({
        frame: developmentFrame,
        file: "tick.wav",
        volume: 0.048,
        durationSeconds: 0.12,
      });
    }
  });

  if (!authoredBeats.length) {
    if (type === "HEADLINE") {
      add(0.38, "tick.wav", 0.045, 0.12);
    }
  
    if (type === "STAT_GRID") {
      const stats = asArray<unknown>(payload.stats);
      stats.forEach((_, index) => {
        const ratio = 0.08 + (index / Math.max(1, stats.length - 1)) * 0.5;
        add(ratio, index === 0 ? "soft-impact.wav" : "tick.wav", index === 0 ? 0.06 : 0.04, index === 0 ? 0.5 : 0.12);
      });
    }
  
    if (type === "BEFORE_AFTER") {
      add(0.18, "tick.wav", 0.035, 0.12);
      add(0.62, "soft-impact.wav", 0.055, 0.5);
    }
  
    if (type === "NETWORK") {
      add(0.12, "soft-whoosh.wav", 0.04, 0.55);
      add(0.56, "tick.wav", 0.04, 0.12);
    }
  
    if (type === "MONEY_FLOW") {
      add(0.16, "soft-whoosh.wav", 0.045, 0.55);
      add(0.58, "tick.wav", 0.04, 0.12);
    }
  
    if (type === "PROCESS") {
      const steps = asArray<unknown>(payload.steps);
      steps.forEach((_, index) => {
        const ratio = 0.06 + (index / Math.max(1, steps.length - 1)) * 0.6;
        add(ratio, "tick.wav", index === steps.length - 1 ? 0.05 : 0.035, 0.12);
      });
    }
  
    if (type === "BIG_NUMBER") {
      add(0.08, "soft-impact.wav", 0.065, 0.5);
      if (asString(payload.warning)) {
        add(0.55, "subtle-alert.wav", 0.045, 0.34);
      }
    }
  
    if (type === "DO_DONT") {
      const yes = asArray<unknown>(payload.yes);
      const no = asArray<unknown>(payload.no);
      const total = Math.max(1, yes.length + no.length);
  
      [...yes, ...no].forEach((_, index) => {
        const ratio = 0.09 + (index / Math.max(1, total - 1)) * 0.58;
        const firstNegative = index === yes.length && no.length > 0;
        add(
          ratio,
          firstNegative ? "subtle-alert.wav" : "tick.wav",
          firstNegative ? 0.04 : 0.033,
          firstNegative ? 0.34 : 0.12,
        );
      });
    }
  
    if (type === "TIMELINE") {
      add(0.12, "soft-whoosh.wav", 0.04, 0.55);
      add(0.84, "tick.wav", 0.035, 0.12);
    }
  
    }

  if (isLast) {
    const narrationEnd = Math.min(
      scene.duration_frames - 1,
      Math.max(0, Math.round((scene.audio_duration_seconds ?? 0) * fps)),
    );

    events.push({
      frame: narrationEnd,
      file: "outro-signature.wav",
      volume: 0.16,
      durationSeconds: 1.85,
    });
  }

  return (
    <>
      {events.map((event, index) => {
        const durationInFrames = Math.max(
          1,
          Math.min(
            Math.ceil(event.durationSeconds * fps),
            scene.duration_frames - event.frame,
          ),
        );

        return (
          <Sequence
            key={`${event.file}-${event.frame}-${index}`}
            from={event.frame}
            durationInFrames={durationInFrames}
          >
            <Audio
              src={staticFile(`generated-sfx/${event.file}`)}
              volume={event.volume}
            />
          </Sequence>
        );
      })}
    </>
  );
};

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

const SceneComposition = ({
  scene,
  isLast,
  direction,
  hasMasterAudio,
}: {
  scene: Scene;
  isLast: boolean;
  direction: EditorialDirection;
  hasMasterAudio?: boolean;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const beats = scene.visual?.beats ?? [];
  const active = findActiveBeat(
    beats,
    frame,
    scene.duration_frames,
    scene.audio_duration_seconds,
    fps,
  );

  const behavior = active?.beat.behavior ?? null;
  const baseOpacity =
    !active || behavior === "overlay"
      ? 1
      : behavior === "reframe"
        ? 0.2
        : 0;
  const baseScale = behavior === "reframe" ? 1.06 : 1;

  if (scene.visual.stage) {
    return <AbsoluteFill>
      <EditorialStage stage={scene.visual.stage} beats={beats} title={scene.title} />
      <EditorialCaptions stage={scene.visual.stage} beats={beats} words={scene.audio_captions ?? []} title={scene.title} />
      <SceneTransitionAccent type={scene.visual?.transition} sceneIndex={scene.scene_index} secondaryColor={direction.secondary_color} />
      <SoundDesign scene={scene} isLast={isLast} />
      {!hasMasterAudio && (
        <Audio
          src={staticFile(scene.audio_file)}
          volume={(f) => {
            const mult = scene.audio_volume_multiplier ?? 1;
            const total = scene.duration_frames || 30;
            const fadeIn = Math.min(1, Math.max(0, f / 2));
            const fadeOut = isLast ? Math.min(1, Math.max(0, (total - f) / 10)) : 1;
            return mult * Math.min(fadeIn, fadeOut);
          }}
        />
      )}
    </AbsoluteFill>;
  }

  return (
    <AbsoluteFill>
      <AbsoluteFill
        style={{
          opacity: baseOpacity,
          transform: `scale(${baseScale})`,
        }}
      >
        <Visual scene={scene} />
      </AbsoluteFill>

      <EditorialMicroScene
        beats={beats}
        direction={direction}
        durationFrames={scene.duration_frames}
        audioDurationSeconds={scene.audio_duration_seconds}
      />

      <SceneTransitionAccent
        type={scene.visual?.transition}
        sceneIndex={scene.scene_index}
        secondaryColor={direction.secondary_color}
      />

      <SoundDesign scene={scene} isLast={isLast} />
      {!hasMasterAudio && (
        <Audio
          src={staticFile(scene.audio_file)}
          volume={(f) => {
            const mult = scene.audio_volume_multiplier ?? 1;
            const total = scene.duration_frames || 30;
            const fadeIn = Math.min(1, Math.max(0, f / 2));
            const fadeOut = isLast ? Math.min(1, Math.max(0, (total - f) / 10)) : 1;
            return mult * Math.min(fadeIn, fadeOut);
          }}
        />
      )}
    </AbsoluteFill>
  );
};

export const DailyEditorial = () => {
  const scenes = renderInput.scenes as unknown as Scene[];
  const direction: EditorialDirection = {
    ...((renderInput as unknown as {visual_direction?: EditorialDirection}).visual_direction ?? {}),
    secondary_color: GOLD,
  };
  const masterAudio = (renderInput as unknown as {narration_master_audio?: string}).narration_master_audio;

  return (
    <AbsoluteFill style={{backgroundColor: BG}}>
      {direction.world === "market" ? <AbsoluteFill style={{background: "radial-gradient(ellipse at 60% 35%, rgba(255,189,25,0.035), transparent 65%), linear-gradient(145deg,#10161b,#080c10)"}} /> : <StoryWorldBackground direction={direction} />}
      <Brand />
      {/* Trilha Sonora Editorial Contínua */}
      <Audio
        src={staticFile("generated-music/daily-bed.wav")}
        volume={(f) => {
          const total = (renderInput as unknown as {duration_in_frames?: number}).duration_in_frames || 30;
          const fadeIn = Math.min(1, Math.max(0, f / 30));
          const fadeOut = Math.min(1, Math.max(0, (total - f) / 60));
          return 0.72 * fadeIn * fadeOut;
        }}
      />
      {masterAudio && (
        <Audio
          src={staticFile(masterAudio)}
          volume={(f) => {
            const total = (renderInput as unknown as {duration_in_frames?: number}).duration_in_frames || 30;
            const fadeIn = Math.min(1, Math.max(0, f / 2));
            const fadeOut = Math.min(1, Math.max(0, (total - f) / 10));
            return Math.min(fadeIn, fadeOut);
          }}
        />
      )}
      {scenes.map((scene, index) => (
        <Sequence
          key={scene.id}
          from={scene.start_frame}
          durationInFrames={scene.duration_frames}
        >
          <SceneComposition
            scene={scene}
            isLast={index === scenes.length - 1}
            direction={direction}
            hasMasterAudio={Boolean(masterAudio)}
          />
        </Sequence>
      ))}

    </AbsoluteFill>
  );
};
