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

const BG = "#090b0d";
const GOLD = "#ffbd19";
const GOLD_SOFT = "rgba(255,189,25,.18)";
const WHITE = "#f6f7f8";
const MUTED = "#9ba4ae";
const FONT = "Arial, Helvetica, sans-serif";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const MovingBackground = () => {
  const frame = useCurrentFrame();
  const driftX = (frame * 0.55) % 72;
  const driftY = (frame * 0.28) % 72;
  const glowX = 50 + Math.sin(frame / 38) * 13;
  const glowY = 44 + Math.cos(frame / 52) * 8;
  const pulse = 0.12 + (Math.sin(frame / 18) + 1) * 0.025;

  return (
    <AbsoluteFill style={{overflow: "hidden", backgroundColor: BG}}>
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.055) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.055) 1px, transparent 1px)",
          backgroundSize: "72px 72px",
          backgroundPosition: `${driftX}px ${driftY}px`,
          opacity: 0.42,
        }}
      />

      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${glowX}% ${glowY}%, rgba(255,189,25,${pulse}) 0%, rgba(255,189,25,.035) 20%, transparent 47%)`,
        }}
      />

      <div
        style={{
          position: "absolute",
          width: 520,
          height: 520,
          borderRadius: "50%",
          border: "1px solid rgba(255,189,25,.12)",
          right: -120 + Math.sin(frame / 45) * 24,
          top: 140 + Math.cos(frame / 40) * 18,
          transform: `scale(${1 + Math.sin(frame / 24) * 0.025})`,
        }}
      />

      <div
        style={{
          position: "absolute",
          width: 820,
          height: 2,
          left: -100,
          bottom: 150,
          background:
            "linear-gradient(90deg, transparent, rgba(255,189,25,.28), transparent)",
          transform: `translateX(${(frame * 3.3) % 1150}px) rotate(-8deg)`,
          filter: "blur(.3px)",
        }}
      />
    </AbsoluteFill>
  );
};

const Brand = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 12], [0, 1], clamp);

  return (
    <div
      style={{
        position: "absolute",
        left: 88,
        top: 64,
        display: "flex",
        alignItems: "center",
        gap: 16,
        color: WHITE,
        fontFamily: FONT,
        fontSize: 28,
        fontWeight: 850,
        letterSpacing: -1,
        opacity,
        zIndex: 20,
      }}
    >
      <div
        style={{
          width: 34,
          height: 34,
          borderRadius: 10,
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
};

const WordChip = ({
  text,
  delay,
  active = false,
}: {
  text: string;
  delay: number;
  active?: boolean;
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({
    frame: Math.max(0, frame - delay),
    fps,
    durationInFrames: 18,
    config: {damping: 18, stiffness: 115},
  });

  return (
    <span
      style={{
        display: "inline-block",
        padding: active ? "8px 13px" : "0",
        marginRight: active ? 10 : 8,
        borderRadius: active ? 10 : 0,
        background: active ? GOLD : "transparent",
        color: active ? BG : WHITE,
        transform: `translateY(${(1 - enter) * 24}px) scale(${0.95 + enter * 0.05})`,
        opacity: enter,
      }}
    >
      {text}
    </span>
  );
};

const Opening = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const kicker = spring({
    frame,
    fps,
    durationInFrames: 22,
    config: {damping: 20, stiffness: 105},
  });
  const underline = interpolate(frame, [20, 60], [0, 1], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });
  const numberFloat = Math.sin(frame / 7) * 4;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        padding: "0 155px",
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          color: GOLD,
          fontSize: 27,
          fontWeight: 850,
          textTransform: "uppercase",
          letterSpacing: 5,
          marginBottom: 28,
          transform: `translateX(${(1 - kicker) * -45}px)`,
          opacity: kicker,
        }}
      >
        Parece óbvio, mas não é.
      </div>

      <div
        style={{
          maxWidth: 1450,
          fontSize: 88,
          lineHeight: 1.06,
          letterSpacing: -4.5,
          fontWeight: 900,
          color: WHITE,
        }}
      >
        <WordChip text="A" delay={4} />
        <WordChip text="parte" delay={8} />
        <WordChip text="mais" delay={12} />
        <WordChip text="conhecida" delay={16} active />
        <WordChip text="de" delay={20} />
        <WordChip text="uma" delay={24} />
        <WordChip text="empresa" delay={28} />
        <br />
        <WordChip text="nem" delay={36} />
        <WordChip text="sempre" delay={40} />
        <WordChip text="é" delay={44} />
        <WordChip text="a" delay={48} />
        <WordChip text="que" delay={52} />
        <WordChip text="mais" delay={56} />
        <span
          style={{
            display: "inline-block",
            color: GOLD,
            marginLeft: 5,
            transform: `translateY(${numberFloat}px)`,
          }}
        >
          coloca dinheiro no caixa.
        </span>
      </div>

      <div
        style={{
          width: `${underline * 760}px`,
          height: 8,
          borderRadius: 999,
          background: GOLD,
          marginTop: 32,
          boxShadow: `0 0 ${18 + underline * 20}px ${GOLD_SOFT}`,
        }}
      />
    </AbsoluteFill>
  );
};

const DataBurst = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const labels = [
    {text: "SELIC", x: 190, y: 360},
    {text: "PIX", x: 450, y: 580},
    {text: "EBITDA", x: 1310, y: 320},
    {text: "NUBANK", x: 1200, y: 640},
    {text: "BANCO CENTRAL", x: 690, y: 245},
  ];

  const mainEnter = spring({
    frame,
    fps,
    durationInFrames: 24,
    config: {damping: 18, stiffness: 105},
  });

  return (
    <AbsoluteFill style={{fontFamily: FONT}}>
      <div
        style={{
          position: "absolute",
          left: 155,
          top: 400,
          fontSize: 84,
          lineHeight: 1.03,
          letterSpacing: -4,
          fontWeight: 900,
          color: WHITE,
          maxWidth: 1100,
          transform: `translateY(${(1 - mainEnter) * 38}px)`,
          opacity: mainEnter,
        }}
      >
        O desafio é transformar
        <span style={{color: GOLD}}> números e siglas </span>
        em uma história fácil de acompanhar.
      </div>

      {labels.map((item, index) => {
        const enter = spring({
          frame: Math.max(0, frame - 12 - index * 6),
          fps,
          durationInFrames: 18,
          config: {damping: 16, stiffness: 130},
        });
        const float = Math.sin((frame + index * 18) / 13) * 7;

        return (
          <div
            key={item.text}
            style={{
              position: "absolute",
              left: item.x,
              top: item.y + float,
              padding: "12px 17px",
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,.12)",
              background: index === 2 ? GOLD : "rgba(18,22,26,.92)",
              color: index === 2 ? BG : MUTED,
              fontSize: 22,
              fontWeight: 900,
              letterSpacing: 1.5,
              transform: `scale(${0.82 + enter * 0.18}) rotate(${(1 - enter) * -5}deg)`,
              opacity: enter * 0.92,
            }}
          >
            {item.text}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const NumberMoment = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({
    frame,
    fps,
    durationInFrames: 28,
    config: {damping: 15, stiffness: 95},
  });

  const count = Math.round(interpolate(frame, [8, 78], [0, 18], clamp)) / 10;
  const sweep = interpolate(frame, [18, 100], [-35, 130], clamp);
  const captionEnter = spring({
    frame: Math.max(0, frame - 42),
    fps,
    durationInFrames: 20,
    config: {damping: 20, stiffness: 105},
  });

  return (
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
          textTransform: "uppercase",
          letterSpacing: 6,
          fontSize: 25,
          fontWeight: 850,
          marginBottom: 18,
        }}
      >
        Um número chama atenção
      </div>

      <div
        style={{
          color: WHITE,
          fontSize: 170,
          fontWeight: 950,
          letterSpacing: -10,
          transform: `scale(${0.76 + pop * 0.24})`,
          position: "relative",
        }}
      >
        R$ <span style={{color: GOLD}}>{count.toFixed(1).replace(".", ",")} BI</span>
        <div
          style={{
            position: "absolute",
            left: `${sweep}%`,
            top: 15,
            width: 170,
            height: 175,
            background:
              "linear-gradient(90deg, transparent, rgba(255,255,255,.25), transparent)",
            transform: "skewX(-18deg)",
            filter: "blur(8px)",
          }}
        />
      </div>

      <div
        style={{
          marginTop: 28,
          color: WHITE,
          fontSize: 38,
          fontWeight: 780,
          transform: `translateY(${(1 - captionEnter) * 24}px)`,
          opacity: captionEnter,
        }}
      >
        Mas o que importa é <span style={{color: GOLD}}>de onde ele veio.</span>
      </div>

      <div
        style={{
          width: 960,
          height: 12,
          marginTop: 42,
          borderRadius: 999,
          overflow: "hidden",
          background: "#20252b",
        }}
      >
        <div
          style={{
            width: `${interpolate(frame, [40, 122], [0, 100], clamp)}%`,
            height: "100%",
            borderRadius: 999,
            background: "linear-gradient(90deg, #7c5a00, #ffbd19, #ffe08a)",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

const Ending = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({
    frame,
    fps,
    durationInFrames: 28,
    config: {damping: 20, stiffness: 95},
  });
  const pulse = 0.95 + Math.sin(frame / 10) * 0.02;

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        textAlign: "center",
        fontFamily: FONT,
        padding: "0 190px",
      }}
    >
      <div
        style={{
          color: GOLD,
          textTransform: "uppercase",
          letterSpacing: 7,
          fontSize: 25,
          fontWeight: 900,
          marginBottom: 24,
          opacity: enter,
        }}
      >
        O Dinheiro Explica
      </div>
      <div
        style={{
          color: WHITE,
          fontSize: 86,
          lineHeight: 1.04,
          letterSpacing: -4.5,
          fontWeight: 950,
          maxWidth: 1320,
          transform: `scale(${pulse * (0.9 + enter * 0.1)})`,
          opacity: enter,
        }}
      >
        Menos tela parada.
        <br />
        <span style={{color: GOLD}}>Mais informação em movimento.</span>
      </div>
    </AbsoluteFill>
  );
};

const SceneTransition = ({
  durationFrames,
  direction = "up",
  children,
}: {
  durationFrames: number;
  direction?: "up" | "left" | "right";
  children: React.ReactNode;
}) => {
  const frame = useCurrentFrame();

  const enter = interpolate(frame, [0, 8], [0, 1], clamp);
  const exit = interpolate(
    frame,
    [Math.max(10, durationFrames - 10), durationFrames - 1],
    [1, 0],
    clamp,
  );
  const opacity = Math.min(enter, exit);

  const enterOffset = interpolate(frame, [0, 10], [26, 0], clamp);
  const exitOffset = interpolate(
    frame,
    [Math.max(10, durationFrames - 10), durationFrames - 1],
    [0, -18],
    clamp,
  );
  const offset = enterOffset + exitOffset;

  const transform =
    direction === "left"
      ? `translateX(${offset}px)`
      : direction === "right"
        ? `translateX(${-offset}px)`
        : `translateY(${offset}px)`;

  return (
    <AbsoluteFill style={{opacity, transform}}>
      {children}
    </AbsoluteFill>
  );
};

const FlashCut = ({from}: {from: number}) => {
  const frame = useCurrentFrame();
  const local = frame - from;
  const opacity = interpolate(local, [-2, 0, 4, 9], [0, 0.55, 0.15, 0], clamp);

  return (
    <AbsoluteFill
      style={{
        background: GOLD,
        opacity,
        mixBlendMode: "screen",
        pointerEvents: "none",
      }}
    />
  );
};

export const DynamicMotionV2 = () => {
  return (
    <AbsoluteFill style={{backgroundColor: BG}}>
      <MovingBackground />
      <Brand />
      <Audio src={staticFile("voice-tests/macerio.mp3")} />

      <Sequence from={0} durationInFrames={180}>
        <SceneTransition durationFrames={180} direction="up">
          <Opening />
        </SceneTransition>
      </Sequence>

      <Sequence from={180} durationInFrames={195}>
        <SceneTransition durationFrames={195} direction="left">
          <DataBurst />
        </SceneTransition>
      </Sequence>

      <Sequence from={375} durationInFrames={210}>
        <SceneTransition durationFrames={210} direction="right">
          <NumberMoment />
        </SceneTransition>
      </Sequence>

      <Sequence from={585} durationInFrames={225}>
        <SceneTransition durationFrames={225} direction="up">
          <Ending />
        </SceneTransition>
      </Sequence>

      <FlashCut from={179} />
      <FlashCut from={374} />
      <FlashCut from={584} />
    </AbsoluteFill>
  );
};
