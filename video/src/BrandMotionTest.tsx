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

const GOLD = "#ffbd19";
const BG = "#090b0d";
const MUTED = "#9ba4ae";
const WHITE = "#f6f7f8";

const Grid = () => (
  <AbsoluteFill
    style={{
      opacity: 0.16,
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
      fontFamily: "Arial, Helvetica, sans-serif",
      color: WHITE,
      fontWeight: 800,
      fontSize: 30,
      letterSpacing: -1,
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

const SceneOne = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 16, stiffness: 95}});
  const opacity = interpolate(frame, [0, 18, 155, 178], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        opacity,
        justifyContent: "center",
        padding: "0 170px",
        fontFamily: "Arial, Helvetica, sans-serif",
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
          transform: `translateY(${(1 - enter) * 34}px)`,
        }}
      >
        O que sustenta um negócio?
      </div>
      <div
        style={{
          color: WHITE,
          fontWeight: 900,
          fontSize: 92,
          lineHeight: 1.03,
          letterSpacing: -5,
          maxWidth: 1450,
          transform: `translateY(${(1 - enter) * 42}px)`,
        }}
      >
        A parte mais conhecida nem sempre é a que mais coloca dinheiro no caixa.
      </div>
    </AbsoluteFill>
  );
};

const SceneTwo = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 18, stiffness: 85}});
  const bar = interpolate(frame, [18, 130], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "Arial, Helvetica, sans-serif",
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
        Exemplo visual
      </div>
      <div
        style={{
          color: WHITE,
          fontSize: 158,
          fontWeight: 900,
          letterSpacing: -9,
          transform: `scale(${0.82 + enter * 0.18})`,
        }}
      >
        R$ <span style={{color: GOLD}}>1,8 BI</span>
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
            width: `${bar * 100}%`,
            height: "100%",
            backgroundColor: GOLD,
            borderRadius: 999,
          }}
        />
      </div>
      <div
        style={{
          width: 1080,
          display: "flex",
          justifyContent: "space-between",
          marginTop: 16,
          color: MUTED,
          fontSize: 23,
        }}
      >
        <span>Receita</span>
        <span>O número só importa quando existe contexto.</span>
      </div>
    </AbsoluteFill>
  );
};

const SceneThree = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const terms = ["SELIC", "PIX", "EBITDA", "NUBANK", "BANCO CENTRAL"];

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "Arial, Helvetica, sans-serif",
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
        Clareza até nos termos difíceis.
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
          const local = frame - index * 6;
          const enter = spring({
            frame: Math.max(0, local),
            fps,
            config: {damping: 15, stiffness: 110},
          });

          return (
            <div
              key={term}
              style={{
                padding: "20px 30px",
                borderRadius: 18,
                border: "1px solid #30363d",
                backgroundColor: "#12161a",
                color: index === 2 ? GOLD : WHITE,
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
  );
};

const SceneFour = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 18, 175, 205], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        opacity,
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "Arial, Helvetica, sans-serif",
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
        O Dinheiro Explica
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
        Os números contam a história. Nosso trabalho é fazer você entendê-la.
      </div>
    </AbsoluteFill>
  );
};

export const BrandMotionTest = () => {
  return (
    <AbsoluteFill style={{backgroundColor: BG}}>
      <Grid />
      <Brand />
      <Audio src={staticFile("voice-tests/macerio.mp3")} />

      <Sequence from={0} durationInFrames={180}>
        <SceneOne />
      </Sequence>
      <Sequence from={180} durationInFrames={240}>
        <SceneTwo />
      </Sequence>
      <Sequence from={420} durationInFrames={190}>
        <SceneThree />
      </Sequence>
      <Sequence from={610} durationInFrames={200}>
        <SceneFour />
      </Sequence>
    </AbsoluteFill>
  );
};
