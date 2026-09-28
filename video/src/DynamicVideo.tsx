import {Audio} from "@remotion/media";
import {
  AbsoluteFill,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import renderInput from "../generated/render-input.json";

type VisualPayload = {
  kicker?: string;
  eyebrow?: string;
  headline?: string;
  number?: string;
  caption?: string;
  terms?: string[];
};

type Scene = {
  id: string;
  title?: string;
  start_frame: number;
  duration_frames: number;
  audio_file: string;
  visual: {
    type: string;
    payload?: VisualPayload;
  };
};

const GOLD = "#ffbd19";
const BG = "#090b0d";
const SURFACE = "#12161a";
const LINE = "#30363d";
const MUTED = "#9ba4ae";
const WHITE = "#f6f7f8";
const FONT = "Arial, Helvetica, sans-serif";

const Grid = () => (
  <AbsoluteFill
    style={{
      opacity: 0.15,
      backgroundImage:
        "linear-gradient(rgba(255,255,255,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.07) 1px, transparent 1px)",
      backgroundSize: "72px 72px",
    }}
  />
);

const Brand = () => (
  <div
    style={{
      position: "absolute",
      left: 92,
      top: 74,
      display: "flex",
      alignItems: "center",
      gap: 18,
      fontFamily: FONT,
      color: WHITE,
      fontWeight: 800,
      fontSize: 30,
      letterSpacing: -1,
      zIndex: 5,
    }}
  >
    <div
      style={{
        width: 34,
        height: 34,
        borderRadius: 10,
        backgroundColor: GOLD,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: BG,
        fontSize: 21,
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
  const fadeOutStart = Math.max(10, durationFrames - 14);
  const opacity = interpolate(
    frame,
    [0, 10, fadeOutStart, durationFrames],
    [0, 1, 1, 0],
    {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
  );

  return (
    <AbsoluteFill style={{opacity}}>
      {children}
    </AbsoluteFill>
  );
};

const HeadlineScene = ({
  payload,
  durationFrames,
}: {
  payload: VisualPayload;
  durationFrames: number;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 16, stiffness: 95}});

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          padding: "0 170px",
          fontFamily: FONT,
        }}
      >
        <div
          style={{
            color: GOLD,
            fontSize: 28,
            fontWeight: 800,
            textTransform: "uppercase",
            letterSpacing: 5,
            marginBottom: 34,
            transform: `translateY(${(1 - enter) * 32}px)`,
          }}
        >
          {payload.kicker ?? "O Dinheiro Explica"}
        </div>
        <div
          style={{
            color: WHITE,
            fontWeight: 900,
            fontSize: 92,
            lineHeight: 1.03,
            letterSpacing: -5,
            maxWidth: 1460,
            transform: `translateY(${(1 - enter) * 40}px)`,
          }}
        >
          {payload.headline}
        </div>
      </AbsoluteFill>
    </SceneShell>
  );
};

const BigNumberScene = ({
  payload,
  durationFrames,
}: {
  payload: VisualPayload;
  durationFrames: number;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 18, stiffness: 86}});
  const progress = interpolate(frame, [12, Math.max(40, durationFrames - 28)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          fontFamily: FONT,
        }}
      >
        <div
          style={{
            color: MUTED,
            fontSize: 27,
            letterSpacing: 4,
            textTransform: "uppercase",
            fontWeight: 800,
            marginBottom: 24,
          }}
        >
          {payload.eyebrow ?? "Número central"}
        </div>
        <div
          style={{
            color: GOLD,
            fontSize: 164,
            fontWeight: 900,
            letterSpacing: -9,
            transform: `scale(${0.84 + enter * 0.16})`,
          }}
        >
          {payload.number}
        </div>
        <div
          style={{
            width: 1080,
            height: 18,
            marginTop: 58,
            borderRadius: 999,
            backgroundColor: "#20252b",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${progress * 100}%`,
              height: "100%",
              backgroundColor: GOLD,
              borderRadius: 999,
            }}
          />
        </div>
        <div
          style={{
            width: 1080,
            marginTop: 18,
            textAlign: "center",
            color: MUTED,
            fontSize: 24,
          }}
        >
          {payload.caption}
        </div>
      </AbsoluteFill>
    </SceneShell>
  );
};

const TermsScene = ({
  payload,
  durationFrames,
}: {
  payload: VisualPayload;
  durationFrames: number;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const terms = payload.terms ?? [];

  return (
    <SceneShell durationFrames={durationFrames}>
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          fontFamily: FONT,
        }}
      >
        <div
          style={{
            color: WHITE,
            fontSize: 70,
            fontWeight: 900,
            letterSpacing: -3,
            marginBottom: 48,
          }}
        >
          {payload.headline}
        </div>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "center",
            gap: 18,
            maxWidth: 1280,
          }}
        >
          {terms.map((term, index) => {
            const local = Math.max(0, frame - index * 6);
            const enter = spring({
              frame: local,
              fps,
              config: {damping: 15, stiffness: 110},
            });
            return (
              <div
                key={term}
                style={{
                  padding: "20px 30px",
                  borderRadius: 18,
                  border: `1px solid ${LINE}`,
                  backgroundColor: SURFACE,
                  color: term === "EBITDA" ? GOLD : WHITE,
                  fontSize: 31,
                  fontWeight: 850,
                  transform: `translateY(${(1 - enter) * 25}px)`,
                  opacity: enter,
                }}
              >
                {term}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
    </SceneShell>
  );
};

const ClosingScene = ({
  payload,
  durationFrames,
}: {
  payload: VisualPayload;
  durationFrames: number;
}) => (
  <SceneShell durationFrames={durationFrames}>
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        fontFamily: FONT,
        textAlign: "center",
        padding: 170,
      }}
    >
      <div
        style={{
          color: GOLD,
          fontSize: 28,
          letterSpacing: 5,
          fontWeight: 850,
          textTransform: "uppercase",
          marginBottom: 28,
        }}
      >
        {payload.eyebrow ?? "O Dinheiro Explica"}
      </div>
      <div
        style={{
          color: WHITE,
          fontSize: 92,
          lineHeight: 1.04,
          letterSpacing: -5,
          fontWeight: 900,
          maxWidth: 1320,
        }}
      >
        {payload.headline}
      </div>
    </AbsoluteFill>
  </SceneShell>
);

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
        padding: "0 170px",
        fontFamily: FONT,
      }}
    >
      <div style={{color: GOLD, fontSize: 28, fontWeight: 800, marginBottom: 24}}>
        O Dinheiro Explica
      </div>
      <div style={{color: WHITE, fontSize: 84, fontWeight: 900, letterSpacing: -4}}>
        {title ?? "Cena"}
      </div>
    </AbsoluteFill>
  </SceneShell>
);

const DynamicScene = ({scene}: {scene: Scene}) => {
  const payload = scene.visual?.payload ?? {};
  const type = scene.visual?.type ?? "FALLBACK";

  if (type === "HEADLINE") {
    return <HeadlineScene payload={payload} durationFrames={scene.duration_frames} />;
  }
  if (type === "BIG_NUMBER") {
    return <BigNumberScene payload={payload} durationFrames={scene.duration_frames} />;
  }
  if (type === "TERMS") {
    return <TermsScene payload={payload} durationFrames={scene.duration_frames} />;
  }
  if (type === "CLOSING") {
    return <ClosingScene payload={payload} durationFrames={scene.duration_frames} />;
  }

  return <FallbackScene title={scene.title} durationFrames={scene.duration_frames} />;
};

export const DynamicVideo = () => {
  const scenes = renderInput.scenes as Scene[];

  return (
    <AbsoluteFill style={{backgroundColor: BG}}>
      <Grid />
      <Brand />

      {scenes.map((scene) => (
        <Sequence
          key={scene.id}
          from={scene.start_frame}
          durationInFrames={scene.duration_frames}
        >
          <DynamicScene scene={scene} />
          <Audio src={staticFile(scene.audio_file)} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
