import {
  ArrowRight,
  Ban,
  Banknote,
  BarChart3,
  CalendarDays,
  CircleDollarSign,
  Fuel,
  Gauge,
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
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type EditorialDirection = {
  concept?: string;
  world?: "minimal" | "digital" | "industrial" | "documentary" | "market" | "network" | "paper";
  secondary_color?: string;
  motifs?: string[];
  motion_language?: string[];
  avoid?: string[];
};

export type EditorialBeat = {
  anchor?: string;
  at?: number;
  kind?: string;
  headline: string;
  detail?: string;
  value?: string;
  from?: string;
  to?: string;
  behavior?: "cut" | "transform" | "reframe" | "overlay";
  treatment?:
    | "kinetic_type"
    | "giant_number"
    | "flow_diagram"
    | "timeline"
    | "split_compare"
    | "meter"
    | "spotlight"
    | "equation"
    | "stack"
    | "signal";
  transition?: "cut" | "fade" | "slide_left" | "slide_up" | "zoom" | "wipe";
  placement?: "left" | "center" | "right" | "full";
  sound?: "none" | "tick" | "impact" | "whoosh" | "alert";
  resolved_ratio?: number;
  resolved_frame?: number;
  timing_source?: string;
};

const BG = "#090b0d";
const SURFACE = "#12161a";
const WHITE = "#f6f7f8";
const MUTED = "#9ba4ae";
const GOLD = "#ffbd19";
const RED = "#ff6b6b";
const GREEN = "#79d99a";
const LINE = "#30363d";
const FONT = "Arial, Helvetica, sans-serif";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

export const findActiveBeat = (
  beats: EditorialBeat[],
  frame: number,
  durationFrames: number,
  audioDurationSeconds: number | undefined,
  fps: number,
) => {
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
  const audioEnd = Math.min(
    durationFrames,
    Math.max(1, Math.round((audioDurationSeconds ?? durationFrames / fps) * fps)),
  );
  const endFrame =
    activeIndex < resolved.length - 1
      ? resolved[activeIndex + 1].resolved_frame ?? audioEnd
      : audioEnd;

  return {
    beat,
    index: activeIndex,
    startFrame,
    endFrame: Math.max(startFrame + 1, endFrame),
    beats: resolved,
  };
};

const BeatIcon = ({kind, size = 74}: {kind?: string; size?: number}) => {
  const common = {size, strokeWidth: 1.7};
  switch (kind) {
    case "money":
    case "number":
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
    default:
      return <Info {...common} />;
  }
};

const accentFor = (beat: EditorialBeat, secondary: string) => {
  if (beat.kind === "warning" || beat.kind === "block") return RED;
  if (beat.kind === "trend_up") return GREEN;
  if (beat.kind === "trend_down") return RED;
  if (beat.kind === "fuel") return secondary;
  return GOLD;
};

const entranceStyle = ({
  transition,
  progress,
}: {
  transition?: EditorialBeat["transition"];
  progress: number;
}): React.CSSProperties => {
  switch (transition) {
    case "fade":
      return {opacity: progress};
    case "slide_left":
      return {
        opacity: progress,
        transform: `translateX(${(1 - progress) * 150}px)`,
      };
    case "slide_up":
      return {
        opacity: progress,
        transform: `translateY(${(1 - progress) * 110}px)`,
      };
    case "zoom":
      return {
        opacity: progress,
        transform: `scale(${0.88 + progress * 0.12})`,
      };
    case "wipe":
      return {
        opacity: 1,
        clipPath: `inset(0 ${(1 - progress) * 100}% 0 0)`,
      };
    case "cut":
    default:
      return {opacity: 1};
  }
};

const worldAccent = (direction?: EditorialDirection) =>
  direction?.secondary_color ?? "#ff7a1a";

export const StoryWorldBackground = ({
  direction,
}: {
  direction?: EditorialDirection;
}) => {
  const frame = useCurrentFrame();
  const secondary = worldAccent(direction);
  const world = direction?.world ?? "minimal";
  const drift = (frame * 0.35) % 90;

  if (world === "industrial") {
    return (
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 76% 28%, rgba(255,122,26,.17), transparent 34%), linear-gradient(145deg, #080a0c 0%, #0d1114 52%, #08090b 100%)",
          overflow: "hidden",
        }}
      >
        <AbsoluteFill
          style={{
            opacity: 0.17,
            backgroundImage:
              "repeating-linear-gradient(115deg, transparent 0 68px, rgba(255,255,255,.06) 69px 70px)",
            transform: `translateX(${drift - 90}px)`,
          }}
        />
        <div
          style={{
            position: "absolute",
            right: -120,
            bottom: -280,
            width: 760,
            height: 760,
            borderRadius: "50%",
            border: `2px solid ${secondary}35`,
            boxShadow: `0 0 90px ${secondary}18 inset`,
          }}
        />
      </AbsoluteFill>
    );
  }

  if (world === "digital" || world === "network") {
    return (
      <AbsoluteFill style={{backgroundColor: BG, overflow: "hidden"}}>
        <AbsoluteFill
          style={{
            opacity: 0.24,
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px)",
            backgroundSize: "72px 72px",
            backgroundPosition: `${drift}px ${drift * 0.4}px`,
          }}
        />
        <AbsoluteFill
          style={{
            background: `radial-gradient(circle at 35% 42%, ${secondary}20, transparent 38%)`,
          }}
        />
      </AbsoluteFill>
    );
  }

  if (world === "market") {
    const x = 120 + ((frame * 2.2) % 1450);
    return (
      <AbsoluteFill style={{backgroundColor: BG, overflow: "hidden"}}>
        <AbsoluteFill
          style={{
            opacity: 0.19,
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px)",
            backgroundSize: "96px 72px",
          }}
        />
        <svg width="1920" height="1080" style={{position: "absolute", inset: 0, opacity: 0.22}}>
          <polyline
            points={`0,760 240,690 430,720 620,540 820,590 1040,420 1260,470 1500,300 1920,360`}
            fill="none"
            stroke={secondary}
            strokeWidth="5"
            strokeLinecap="round"
          />
          <circle cx={x} cy="520" r="5" fill={GOLD} />
        </svg>
      </AbsoluteFill>
    );
  }

  if (world === "paper" || world === "documentary") {
    return (
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, #0d0f11, #080a0c), radial-gradient(circle at 18% 16%, rgba(255,255,255,.04), transparent 28%)",
          overflow: "hidden",
        }}
      >
        <AbsoluteFill
          style={{
            opacity: 0.1,
            backgroundImage:
              "repeating-linear-gradient(0deg, rgba(255,255,255,.08) 0 1px, transparent 1px 34px)",
            transform: `translateY(${-(drift % 34)}px)`,
          }}
        />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill
      style={{
        background:
          `radial-gradient(circle at ${52 + Math.sin(frame / 60) * 8}% 42%, ${secondary}18, transparent 38%), ${BG}`,
      }}
    />
  );
};

const KineticType = ({
  beat,
  accent,
  placement,
}: {
  beat: EditorialBeat;
  accent: string;
  placement: EditorialBeat["placement"];
}) => {
  const align =
    placement === "right" ? "flex-end" : placement === "center" ? "center" : "flex-start";
  const textAlign =
    placement === "right" ? "right" : placement === "center" ? "center" : "left";

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: align,
        padding: "0 150px",
        fontFamily: FONT,
      }}
    >
      {beat.value && (
        <div
          style={{
            color: accent,
            fontSize: 118,
            fontWeight: 950,
            letterSpacing: -3,
            marginBottom: 8,
            lineHeight: 0.95,
          }}
        >
          {beat.value}
        </div>
      )}
      <div
        style={{
          color: WHITE,
          fontSize: beat.value ? 78 : 108,
          maxWidth: 1450,
          fontWeight: 950,
          lineHeight: 0.98,
          letterSpacing: -2.2,
          textAlign,
          textTransform: "uppercase",
        }}
      >
        {beat.headline}
      </div>
      {beat.detail && (
        <div
          style={{
            color: MUTED,
            fontSize: 31,
            fontWeight: 700,
            maxWidth: 980,
            marginTop: 26,
            lineHeight: 1.3,
            textAlign,
          }}
        >
          {beat.detail}
        </div>
      )}
      <div
        style={{
          width: 260,
          height: 8,
          borderRadius: 99,
          background: accent,
          marginTop: 30,
          alignSelf: align,
        }}
      />
    </AbsoluteFill>
  );
};

const GiantNumber = ({beat, accent}: {beat: EditorialBeat; accent: string}) => (
  <AbsoluteFill
    style={{
      justifyContent: "center",
      padding: "0 155px",
      fontFamily: FONT,
      overflow: "hidden",
    }}
  >
    <div
      style={{
        position: "absolute",
        right: 80,
        top: 120,
        fontSize: 520,
        fontWeight: 950,
        lineHeight: 0.8,
        color: accent,
        opacity: 0.085,
        letterSpacing: -20,
      }}
    >
      {beat.value ?? "01"}
    </div>
    <div style={{display: "flex", alignItems: "center", gap: 42}}>
      <div style={{color: accent}}>
        <BeatIcon kind={beat.kind} size={104} />
      </div>
      <div>
        <div
          style={{
            color: accent,
            fontSize: 150,
            fontWeight: 950,
            lineHeight: 0.88,
            letterSpacing: -4,
          }}
        >
          {beat.value ?? beat.headline}
        </div>
        {beat.value && (
          <div
            style={{
              color: WHITE,
              fontSize: 58,
              fontWeight: 900,
              marginTop: 28,
              maxWidth: 1120,
              lineHeight: 1.05,
            }}
          >
            {beat.headline}
          </div>
        )}
        {beat.detail && (
          <div style={{color: MUTED, fontSize: 28, marginTop: 20, maxWidth: 980}}>
            {beat.detail}
          </div>
        )}
      </div>
    </div>
  </AbsoluteFill>
);

const FlowDiagram = ({beat, accent}: {beat: EditorialBeat; accent: string}) => (
  <AbsoluteFill
    style={{
      justifyContent: "center",
      padding: "0 150px",
      fontFamily: FONT,
    }}
  >
    <div
      style={{
        color: WHITE,
        fontSize: 48,
        fontWeight: 900,
        marginBottom: 70,
        maxWidth: 1450,
      }}
    >
      {beat.headline}
    </div>
    <div style={{display: "grid", gridTemplateColumns: "1fr 250px 1fr", alignItems: "center"}}>
      <div
        style={{
          minHeight: 240,
          display: "grid",
          placeItems: "center",
          borderRadius: "50%",
          border: `2px solid ${LINE}`,
          color: WHITE,
          fontSize: 40,
          fontWeight: 950,
          textAlign: "center",
          padding: 40,
        }}
      >
        {beat.from ?? "ORIGEM"}
      </div>
      <div style={{display: "grid", placeItems: "center", color: accent}}>
        <ArrowRight size={118} strokeWidth={1.3} />
      </div>
      <div
        style={{
          minHeight: 240,
          display: "grid",
          placeItems: "center",
          borderRadius: 32,
          background: `${accent}16`,
          border: `2px solid ${accent}66`,
          color: accent,
          fontSize: 40,
          fontWeight: 950,
          textAlign: "center",
          padding: 40,
        }}
      >
        {beat.to ?? "DESTINO"}
      </div>
    </div>
    {beat.detail && (
      <div style={{color: MUTED, fontSize: 27, marginTop: 42, textAlign: "center"}}>
        {beat.detail}
      </div>
    )}
  </AbsoluteFill>
);

const TimelineTreatment = ({beat, accent}: {beat: EditorialBeat; accent: string}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const progress = spring({frame, fps, config: {damping: 20, stiffness: 95}});

  return (
    <AbsoluteFill style={{justifyContent: "center", padding: "0 145px", fontFamily: FONT}}>
      <div style={{color: WHITE, fontSize: 54, fontWeight: 950, marginBottom: 90}}>
        {beat.headline}
      </div>
      <div style={{position: "relative", height: 150}}>
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: 68,
            height: 6,
            background: LINE,
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 68,
            height: 6,
            width: `${progress * 100}%`,
            background: accent,
          }}
        />
        <div
          style={{
            position: "absolute",
            left: `${Math.max(2, progress * 82)}%`,
            top: 29,
            width: 82,
            height: 82,
            marginLeft: -41,
            borderRadius: "50%",
            display: "grid",
            placeItems: "center",
            background: accent,
            color: BG,
          }}
        >
          <CalendarDays size={40} strokeWidth={2} />
        </div>
      </div>
      <div style={{display: "flex", justifyContent: "space-between", alignItems: "flex-end"}}>
        <div style={{color: MUTED, fontSize: 28}}>{beat.from ?? "ANTES"}</div>
        <div style={{color: accent, fontSize: 86, fontWeight: 950}}>{beat.value ?? beat.to ?? "AGORA"}</div>
      </div>
      {beat.detail && <div style={{color: MUTED, fontSize: 27, marginTop: 24}}>{beat.detail}</div>}
    </AbsoluteFill>
  );
};

const SplitCompare = ({beat, accent}: {beat: EditorialBeat; accent: string}) => (
  <AbsoluteFill style={{fontFamily: FONT}}>
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
      }}
    >
      <div
        style={{
          display: "grid",
          placeItems: "center",
          padding: "120px 100px",
          borderRight: `1px solid ${LINE}`,
          background: "rgba(255,255,255,.015)",
        }}
      >
        <div style={{textAlign: "center"}}>
          <div style={{color: MUTED, fontSize: 24, letterSpacing: 4, textTransform: "uppercase"}}>
            Antes / origem
          </div>
          <div style={{color: WHITE, fontSize: 68, fontWeight: 950, marginTop: 25}}>
            {beat.from ?? beat.value ?? "ANTES"}
          </div>
        </div>
      </div>
      <div
        style={{
          display: "grid",
          placeItems: "center",
          padding: "120px 100px",
          background: `${accent}0c`,
        }}
      >
        <div style={{textAlign: "center"}}>
          <div style={{color: accent, fontSize: 24, letterSpacing: 4, textTransform: "uppercase"}}>
            Agora / efeito
          </div>
          <div style={{color: accent, fontSize: 68, fontWeight: 950, marginTop: 25}}>
            {beat.to ?? beat.headline}
          </div>
        </div>
      </div>
    </div>
    <div
      style={{
        position: "absolute",
        left: 160,
        right: 160,
        bottom: 92,
        textAlign: "center",
        color: WHITE,
        fontSize: 38,
        fontWeight: 900,
      }}
    >
      {beat.detail ?? beat.headline}
    </div>
  </AbsoluteFill>
);

const MeterTreatment = ({beat, accent}: {beat: EditorialBeat; accent: string}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const progress = spring({frame, fps, config: {damping: 18, stiffness: 90}});

  return (
    <AbsoluteFill style={{justifyContent: "center", padding: "0 150px", fontFamily: FONT}}>
      <div style={{display: "flex", alignItems: "center", gap: 90}}>
        <div style={{color: accent}}>
          <Gauge size={210} strokeWidth={1.25} />
        </div>
        <div style={{flex: 1}}>
          <div style={{color: WHITE, fontSize: 65, fontWeight: 950, lineHeight: 1.02}}>
            {beat.headline}
          </div>
          {beat.value && (
            <div style={{color: accent, fontSize: 110, fontWeight: 950, marginTop: 16}}>
              {beat.value}
            </div>
          )}
          <div
            style={{
              height: 22,
              borderRadius: 99,
              background: "#20252b",
              marginTop: 45,
              overflow: "hidden",
            }}
          >
            <div style={{height: "100%", width: `${Math.max(8, progress * 88)}%`, background: accent}} />
          </div>
          {beat.detail && <div style={{color: MUTED, fontSize: 27, marginTop: 20}}>{beat.detail}</div>}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Spotlight = ({beat, accent}: {beat: EditorialBeat; accent: string}) => (
  <AbsoluteFill style={{justifyContent: "center", alignItems: "center", fontFamily: FONT}}>
    <div
      style={{
        width: 300,
        height: 300,
        borderRadius: "50%",
        display: "grid",
        placeItems: "center",
        color: accent,
        background: `radial-gradient(circle, ${accent}20, ${accent}08 56%, transparent 70%)`,
        border: `1px solid ${accent}45`,
        boxShadow: `0 0 100px ${accent}22`,
      }}
    >
      <BeatIcon kind={beat.kind} size={150} />
    </div>
    <div style={{color: WHITE, fontSize: 70, fontWeight: 950, marginTop: 36, textAlign: "center", maxWidth: 1400}}>
      {beat.headline}
    </div>
    {beat.value && <div style={{color: accent, fontSize: 92, fontWeight: 950, marginTop: 12}}>{beat.value}</div>}
    {beat.detail && <div style={{color: MUTED, fontSize: 28, marginTop: 18, maxWidth: 960, textAlign: "center"}}>{beat.detail}</div>}
  </AbsoluteFill>
);

const EquationTreatment = ({beat, accent}: {beat: EditorialBeat; accent: string}) => (
  <AbsoluteFill style={{justifyContent: "center", padding: "0 145px", fontFamily: FONT}}>
    <div style={{color: MUTED, fontSize: 27, letterSpacing: 4, textTransform: "uppercase", marginBottom: 40}}>
      Como a conta se conecta
    </div>
    <div style={{display: "flex", alignItems: "center", gap: 34, flexWrap: "wrap"}}>
      <div style={{color: WHITE, fontSize: 74, fontWeight: 950}}>{beat.from ?? beat.value ?? "CUSTO"}</div>
      <div style={{color: accent, fontSize: 74, fontWeight: 950}}>+</div>
      <div style={{color: WHITE, fontSize: 74, fontWeight: 950}}>{beat.to ?? "OUTRAS PARCELAS"}</div>
      <div style={{color: accent, fontSize: 74, fontWeight: 950}}>=</div>
      <div style={{color: accent, fontSize: 74, fontWeight: 950}}>{beat.headline}</div>
    </div>
    {beat.detail && <div style={{color: MUTED, fontSize: 28, marginTop: 42, maxWidth: 1150}}>{beat.detail}</div>}
  </AbsoluteFill>
);

const StackTreatment = ({beat, accent}: {beat: EditorialBeat; accent: string}) => {
  const labels = (beat.detail ?? beat.headline)
    .split(/[,;•]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 5);

  return (
    <AbsoluteFill style={{justifyContent: "center", padding: "0 150px", fontFamily: FONT}}>
      <div style={{color: WHITE, fontSize: 58, fontWeight: 950, marginBottom: 55}}>
        {beat.headline}
      </div>
      <div style={{display: "grid", gap: 12, maxWidth: 1200}}>
        {(labels.length ? labels : ["Etapa 1", "Etapa 2", "Etapa 3"]).map((label, index) => (
          <div
            key={label}
            style={{
              height: 82,
              width: `${94 - index * 9}%`,
              display: "flex",
              alignItems: "center",
              padding: "0 28px",
              background: index === 0 ? accent : `${accent}${index === 1 ? "2b" : "18"}`,
              color: index === 0 ? BG : WHITE,
              fontSize: 28,
              fontWeight: 900,
              borderRadius: 12,
            }}
          >
            {label}
          </div>
        ))}
      </div>
      {beat.value && <div style={{color: accent, fontSize: 86, fontWeight: 950, marginTop: 40}}>{beat.value}</div>}
    </AbsoluteFill>
  );
};

const SignalTreatment = ({beat, accent}: {beat: EditorialBeat; accent: string}) => (
  <AbsoluteFill style={{fontFamily: FONT, overflow: "hidden"}}>
    <div
      style={{
        position: "absolute",
        left: -180,
        top: -120,
        width: 780,
        height: 1350,
        background: accent,
        transform: "rotate(12deg)",
        opacity: 0.88,
      }}
    />
    <div
      style={{
        position: "absolute",
        left: 170,
        top: 210,
        color: BG,
      }}
    >
      <BeatIcon kind={beat.kind} size={150} />
    </div>
    <div
      style={{
        position: "absolute",
        left: 690,
        top: 255,
        right: 150,
      }}
    >
      {beat.value && <div style={{color: accent, fontSize: 102, fontWeight: 950}}>{beat.value}</div>}
      <div style={{color: WHITE, fontSize: 79, fontWeight: 950, lineHeight: 0.98}}>
        {beat.headline}
      </div>
      {beat.detail && <div style={{color: MUTED, fontSize: 29, marginTop: 28, maxWidth: 900}}>{beat.detail}</div>}
    </div>
  </AbsoluteFill>
);

const OverlayTreatment = ({beat, accent}: {beat: EditorialBeat; accent: string}) => (
  <AbsoluteFill style={{fontFamily: FONT, pointerEvents: "none"}}>
    <div
      style={{
        position: "absolute",
        left: 145,
        bottom: 110,
        display: "flex",
        alignItems: "center",
        gap: 20,
        color: WHITE,
        maxWidth: 1220,
      }}
    >
      <div style={{width: 10, alignSelf: "stretch", background: accent, borderRadius: 99}} />
      <div>
        {beat.value && <div style={{color: accent, fontSize: 48, fontWeight: 950}}>{beat.value}</div>}
        <div style={{fontSize: 38, fontWeight: 900}}>{beat.headline}</div>
      </div>
    </div>
  </AbsoluteFill>
);

export const EditorialMicroScene = ({
  beats,
  direction,
  durationFrames,
  audioDurationSeconds,
}: {
  beats: EditorialBeat[];
  direction?: EditorialDirection;
  durationFrames: number;
  audioDurationSeconds?: number;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const active = findActiveBeat(
    beats,
    frame,
    durationFrames,
    audioDurationSeconds,
    fps,
  );

  if (!active) return null;

  const {beat, startFrame, endFrame} = active;
  const localFrame = Math.max(0, frame - startFrame);
  const introFrames = Math.max(1, Math.round(fps * 0.22));
  const enter = interpolate(localFrame, [0, introFrames], [0, 1], clamp);
  const exitStart = Math.max(startFrame, endFrame - Math.round(fps * 0.12));
  const exit = interpolate(frame, [exitStart, endFrame], [1, 0], clamp);
  const transitionStyle = entranceStyle({
    transition: beat.transition ?? "cut",
    progress: enter,
  });
  const secondary = worldAccent(direction);
  const accent = accentFor(beat, secondary);
  const behavior = beat.behavior ?? "cut";
  const treatment = beat.treatment ?? "kinetic_type";

  if (behavior === "overlay") {
    return (
      <AbsoluteFill style={{zIndex: 66, opacity: exit, ...transitionStyle}}>
        <OverlayTreatment beat={beat} accent={accent} />
      </AbsoluteFill>
    );
  }

  let body: React.ReactNode;
  switch (treatment) {
    case "giant_number":
      body = <GiantNumber beat={beat} accent={accent} />;
      break;
    case "flow_diagram":
      body = <FlowDiagram beat={beat} accent={accent} />;
      break;
    case "timeline":
      body = <TimelineTreatment beat={beat} accent={accent} />;
      break;
    case "split_compare":
      body = <SplitCompare beat={beat} accent={accent} />;
      break;
    case "meter":
      body = <MeterTreatment beat={beat} accent={accent} />;
      break;
    case "spotlight":
      body = <Spotlight beat={beat} accent={accent} />;
      break;
    case "equation":
      body = <EquationTreatment beat={beat} accent={accent} />;
      break;
    case "stack":
      body = <StackTreatment beat={beat} accent={accent} />;
      break;
    case "signal":
      body = <SignalTreatment beat={beat} accent={accent} />;
      break;
    case "kinetic_type":
    default:
      body = (
        <KineticType
          beat={beat}
          accent={accent}
          placement={beat.placement ?? "left"}
        />
      );
      break;
  }

  return (
    <AbsoluteFill
      style={{
        zIndex: 64,
        background:
          behavior === "reframe"
            ? "linear-gradient(90deg, rgba(9,11,13,.95), rgba(9,11,13,.72))"
            : "rgba(9,11,13,.96)",
        opacity: exit,
        overflow: "hidden",
        ...transitionStyle,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(circle at 72% 36%, ${accent}16, transparent 38%)`,
        }}
      />
      {body}
    </AbsoluteFill>
  );
};

export const SceneTransitionAccent = ({
  type,
  sceneIndex,
  secondaryColor,
}: {
  type?: EditorialBeat["transition"];
  sceneIndex: number;
  secondaryColor?: string;
}) => {
  const frame = useCurrentFrame();
  if (!type || type === "cut" || sceneIndex === 0) return null;

  const p = interpolate(frame, [0, 11], [0, 1], clamp);
  const accent = secondaryColor ?? GOLD;

  if (type === "wipe") {
    return (
      <div
        style={{
          position: "absolute",
          zIndex: 90,
          inset: 0,
          background: accent,
          clipPath: `inset(0 ${p * 100}% 0 0)`,
          opacity: 0.22,
          pointerEvents: "none",
        }}
      />
    );
  }

  if (type === "zoom") {
    return (
      <div
        style={{
          position: "absolute",
          zIndex: 90,
          inset: 0,
          background: `radial-gradient(circle, ${accent}35, transparent 48%)`,
          opacity: 1 - p,
          transform: `scale(${0.75 + p * 0.55})`,
          pointerEvents: "none",
        }}
      />
    );
  }

  if (type === "slide_left" || type === "slide_up") {
    return (
      <div
        style={{
          position: "absolute",
          zIndex: 90,
          width: type === "slide_left" ? 260 : "100%",
          height: type === "slide_up" ? 180 : "100%",
          left: type === "slide_left" ? `${-20 + p * 130}%` : 0,
          top: type === "slide_up" ? `${-20 + p * 130}%` : 0,
          background: `linear-gradient(90deg, transparent, ${accent}55, transparent)`,
          filter: "blur(8px)",
          opacity: 1 - p * 0.6,
          pointerEvents: "none",
        }}
      />
    );
  }

  return (
    <AbsoluteFill
      style={{
        zIndex: 90,
        background: accent,
        opacity: (1 - p) * 0.12,
        pointerEvents: "none",
      }}
    />
  );
};
