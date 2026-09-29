import React from "react";
import {AbsoluteFill, Img, interpolate, staticFile} from "remotion";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const WHITE = "#f6f7f8";
const MUTED = "#9ba4ae";
const BG = "#090b0d";

const phase = (progress: number, start: number, end: number) =>
  interpolate(progress, [start, end], [0, 1], clamp);

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

const hexToRgb = (hex: string) => {
  const normalized = hex.replace("#", "");
  const full =
    normalized.length === 3
      ? normalized
          .split("")
          .map((char) => char + char)
          .join("")
      : normalized;
  const numeric = Number.parseInt(full, 16);
  return {
    r: (numeric >> 16) & 255,
    g: (numeric >> 8) & 255,
    b: numeric & 255,
  };
};

const rgbToHex = (r: number, g: number, b: number) =>
  `#${[r, g, b]
    .map((value) =>
      Math.round(Math.max(0, Math.min(255, value)))
        .toString(16)
        .padStart(2, "0"),
    )
    .join("")}`;

const mixHex = (a: string, b: string, amount: number) => {
  const left = hexToRgb(a);
  const right = hexToRgb(b);
  const t = clamp01(amount);
  return rgbToHex(
    left.r + (right.r - left.r) * t,
    left.g + (right.g - left.g) * t,
    left.b + (right.b - left.b) * t,
  );
};

export const deriveEditorialPalette = (primary: string) => ({
  primary,
  bright: mixHex(primary, "#ffffff", 0.26),
  soft: mixHex(primary, "#ffffff", 0.58),
  dark: mixHex(primary, "#000000", 0.42),
  deep: mixHex(primary, "#000000", 0.7),
});

export const WordCascadeHeadline = ({
  text,
  progress,
  accent,
  fontSize = 96,
  textAlign = "left",
  uppercase = true,
  maxWidth = 1450,
}: {
  text: string;
  progress: number;
  accent: string;
  fontSize?: number;
  textAlign?: "left" | "center" | "right";
  uppercase?: boolean;
  maxWidth?: number;
}) => {
  const words = text.trim().split(/\s+/).filter(Boolean);
  const count = Math.max(1, words.length);
  const staggerSpan = Math.min(0.42, 0.07 * Math.max(0, count - 1));
  const unitWindow = Math.max(0.22, 0.52 - staggerSpan * 0.35);

  return (
    <div
      style={{
        maxWidth,
        textAlign,
        lineHeight: 0.98,
        letterSpacing: -2.2,
        fontSize,
        fontWeight: 950,
        textTransform: uppercase ? "uppercase" : undefined,
      }}
    >
      {words.map((word, index) => {
        const start = count === 1 ? 0.03 : 0.03 + (index / (count - 1)) * staggerSpan;
        const local = phase(progress, start, Math.min(0.76, start + unitWindow));
        const colorMix = phase(progress, Math.min(0.82, start + 0.11), Math.min(0.94, start + 0.34));
        const color = mixHex(accent, WHITE, colorMix);

        return (
          <React.Fragment key={`${word}-${index}`}>
            <span
              style={{
                display: "inline-block",
                whiteSpace: "pre",
                color,
                opacity: local,
                transform: `translateY(${(1 - local) * 54}px) scale(${0.94 + local * 0.06})`,
                filter: local < 0.985 ? `blur(${(1 - local) * 10}px)` : "none",
                willChange: "transform, opacity, filter, color",
              }}
            >
              {word}
            </span>
            {index < words.length - 1 ? " " : null}
          </React.Fragment>
        );
      })}
    </div>
  );
};

type ParsedAnimatedNumber = {
  prefix: string;
  suffix: string;
  numeric: number;
  decimals: number;
  decimalSeparator: "." | ",";
};

const parseAnimatedNumber = (value: string): ParsedAnimatedNumber | null => {
  const match = value.match(/-?\d+(?:[.,]\d+)?/);
  if (!match || match.index === undefined) return null;

  const raw = match[0];
  const decimalSeparator = raw.includes(",") ? "," : ".";
  const decimalPart = raw.includes(decimalSeparator)
    ? raw.split(decimalSeparator)[1] ?? ""
    : "";
  const numeric = Number.parseFloat(raw.replace(",", "."));
  if (!Number.isFinite(numeric)) return null;

  return {
    prefix: value.slice(0, match.index),
    suffix: value.slice(match.index + raw.length),
    numeric,
    decimals: decimalPart.length,
    decimalSeparator,
  };
};

export const AnimatedNumberText = ({
  value,
  progress,
}: {
  value: string;
  progress: number;
}) => {
  const parsed = parseAnimatedNumber(value);
  if (!parsed) return <>{value}</>;

  const countProgress = phase(progress, 0.08, 0.72);
  const current = parsed.numeric * countProgress;
  let rendered = current.toFixed(parsed.decimals);
  if (parsed.decimalSeparator === ",") rendered = rendered.replace(".", ",");

  return (
    <>
      {parsed.prefix}
      {rendered}
      {parsed.suffix}
    </>
  );
};

export const MaskedSweepHeadline = ({
  text,
  progress,
  accent,
  detail,
  value,
}: {
  text: string;
  progress: number;
  accent: string;
  detail?: string;
  value?: string;
}) => {
  const palette = deriveEditorialPalette(accent);
  const enter = phase(progress, 0.02, 0.25);
  const sweep = phase(progress, 0.14, 0.82);
  const sweepX = -28 + sweep * 156;
  const detailEnter = phase(progress, 0.5, 0.82);

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        padding: "0 150px",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          width: 860,
          height: 860,
          borderRadius: "50%",
          background: `radial-gradient(circle, ${palette.primary}20 0%, ${palette.deep}08 48%, transparent 72%)`,
          transform: `scale(${0.78 + sweep * 0.38})`,
          opacity: 0.35 + sweep * 0.24,
        }}
      />

      {value && (
        <div
          style={{
            color: accent,
            fontSize: 92,
            fontWeight: 950,
            marginBottom: 18,
            opacity: enter,
            transform: `translateY(${(1 - enter) * 24}px)`,
          }}
        >
          <AnimatedNumberText value={value} progress={progress} />
        </div>
      )}

      <div
        style={{
          position: "relative",
          textAlign: "center",
          fontSize: value ? 82 : 108,
          lineHeight: 0.96,
          fontWeight: 950,
          letterSpacing: -2.6,
          textTransform: "uppercase",
          maxWidth: 1500,
          opacity: enter,
          color: WHITE,
        }}
      >
        <span style={{color: WHITE}}>{text}</span>
        <span
          aria-hidden
          style={{
            position: "absolute",
            inset: 0,
            color: palette.bright,
            clipPath: `polygon(${sweepX - 18}% 0, ${sweepX + 18}% 0, ${sweepX + 10}% 100%, ${sweepX - 26}% 100%)`,
            filter: `drop-shadow(0 0 20px ${palette.primary}88)`,
          }}
        >
          {text}
        </span>
      </div>

      {detail && (
        <div
          style={{
            color: MUTED,
            fontSize: 29,
            fontWeight: 700,
            lineHeight: 1.32,
            maxWidth: 950,
            textAlign: "center",
            marginTop: 28,
            opacity: detailEnter,
          }}
        >
          {detail}
        </div>
      )}
    </AbsoluteFill>
  );
};

export const DepthPhotoComposition = ({
  src,
  headline,
  detail,
  value,
  accent,
  progress,
  imageSide = "left",
}: {
  src: string;
  headline: string;
  detail?: string;
  value?: string;
  accent: string;
  progress: number;
  imageSide?: "left" | "right";
}) => {
  const imageEnter = phase(progress, 0.03, 0.28);
  const backTextEnter = phase(progress, 0.07, 0.34);
  const foregroundEnter = phase(progress, 0.36, 0.68);
  const slowMove = phase(progress, 0.2, 0.94);
  const imageOnLeft = imageSide === "left";

  return (
    <AbsoluteFill style={{overflow: "hidden"}}>
      <div
        style={{
          position: "absolute",
          left: 90,
          right: 90,
          top: 175,
          zIndex: 1,
          color: WHITE,
          fontSize: headline.length > 28 ? 92 : 122,
          lineHeight: 0.88,
          letterSpacing: -4,
          fontWeight: 950,
          textTransform: "uppercase",
          opacity: backTextEnter * 0.92,
          textAlign: imageOnLeft ? "center" : "center",
          transform: `translateY(${(1 - backTextEnter) * 38}px) scale(${1 + slowMove * 0.025})`,
        }}
      >
        {headline}
      </div>

      <div
        style={{
          position: "absolute",
          zIndex: 2,
          top: 30,
          bottom: -35,
          width: "62%",
          left: imageOnLeft ? -35 : undefined,
          right: imageOnLeft ? undefined : -35,
          display: "flex",
          justifyContent: "center",
          alignItems: "flex-end",
          opacity: imageEnter,
          transform: `translateX(${(1 - imageEnter) * (imageOnLeft ? -115 : 115)}px) scale(${0.95 + slowMove * 0.08})`,
          transformOrigin: imageOnLeft ? "left bottom" : "right bottom",
          filter: "drop-shadow(0 38px 54px rgba(0,0,0,.58))",
        }}
      >
        <Img
          src={staticFile(src)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
            objectPosition: imageOnLeft ? "left bottom" : "right bottom",
          }}
        />
      </div>

      <div
        style={{
          position: "absolute",
          zIndex: 3,
          left: imageOnLeft ? "54%" : 135,
          right: imageOnLeft ? 135 : "54%",
          bottom: 128,
          textAlign: imageOnLeft ? "left" : "right",
          opacity: foregroundEnter,
          transform: `translateY(${(1 - foregroundEnter) * 24}px)`,
        }}
      >
        {value && (
          <div
            style={{
              color: accent,
              fontSize: 76,
              lineHeight: 0.95,
              fontWeight: 950,
              marginBottom: 12,
            }}
          >
            <AnimatedNumberText value={value} progress={progress} />
          </div>
        )}
        {detail && (
          <div
            style={{
              color: WHITE,
              fontSize: 31,
              lineHeight: 1.22,
              fontWeight: 800,
              maxWidth: 690,
              marginLeft: imageOnLeft ? 0 : "auto",
            }}
          >
            {detail}
          </div>
        )}
        <div
          style={{
            width: 250 * phase(progress, 0.42, 0.88),
            height: 7,
            borderRadius: 999,
            background: accent,
            marginTop: 24,
            marginLeft: imageOnLeft ? 0 : "auto",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

export const BloomAccent = ({
  progress,
  accent,
}: {
  progress: number;
  accent: string;
}) => {
  const palette = deriveEditorialPalette(accent);
  const grow = phase(progress, 0, 0.72);
  const fade = 1 - phase(progress, 0.48, 1);

  return (
    <AbsoluteFill style={{pointerEvents: "none", overflow: "hidden"}}>
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: 620,
          height: 420,
          marginLeft: -310,
          marginTop: -210,
          borderRadius: "50%",
          background: `radial-gradient(ellipse, ${palette.bright}aa 0%, ${palette.primary}66 32%, ${palette.dark}20 58%, transparent 75%)`,
          filter: "blur(38px)",
          opacity: fade * 0.78,
          transform: `scale(${0.02 + grow * 4.2})`,
          transformOrigin: "center",
        }}
      />
    </AbsoluteFill>
  );
};
