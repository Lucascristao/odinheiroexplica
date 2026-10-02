import type {StageElement} from "../../src/lib/editorial-stage";

export type Sustain = NonNullable<StageElement["sustain"]>;

// Sustained motion is explicit editorial direction. The original layout box is
// the envelope: translation, breathing and the worst tilt all fit inside it.
// Only illustrations/media use this transform; readable facts retain the exact
// measured line layout. Evaluation uses the Remotion frame, never wall time.
export function sustainedTransform(sustain: Sustain | undefined, frame: number, fps: number, width: number, height: number, startFrame = 0): string | undefined {
  if (!sustain || sustain.amplitude === 0 || width <= 0 || height <= 0) return undefined;
  const amplitude = Math.min(40, sustain.amplitude, width * 0.12, height * 0.12);
  const seconds = Math.max(0, frame - startFrame) / Math.max(1, fps);
  const angle = (seconds / sustain.period_seconds + (sustain.phase ?? 0)) * Math.PI * 2;
  const ramp = Math.min(1, seconds / 0.6);
  const wave = Math.sin(angle), companion = Math.sin(angle + Math.PI / 2);
  const maxRotation = sustain.kind === "tilt" ? Math.min(4 * Math.PI / 180, Math.atan2(amplitude, Math.max(width, height) / 2)) : 0;
  const cosine = Math.cos(maxRotation), sine = Math.sin(maxRotation);
  // Reserve only the axes that actually move. Breathing reaches the original
  // full size; tilt needs rotation capacity, not a fictitious translation gap.
  const travelX = sustain.kind === "drift" ? amplitude : 0;
  const travelY = sustain.kind === "float" ? amplitude : sustain.kind === "drift" ? amplitude * 0.6 : 0;
  const scale = Math.min(1, (width - travelX * 2) / (width * cosine + height * sine), (height - travelY * 2) / (height * cosine + width * sine));
  const x = sustain.kind === "drift" ? amplitude * companion * ramp : 0;
  const y = sustain.kind === "float" ? amplitude * wave * ramp : sustain.kind === "drift" ? amplitude * wave * 0.6 * ramp : 0;
  const rotation = sustain.kind === "tilt" ? maxRotation * wave * ramp * 180 / Math.PI : 0;
  const breathe = sustain.kind === "breathe" ? amplitude / Math.min(width, height) * (1 - wave) * 0.5 * ramp : 0;
  // Never raise this scale with a visual-size floor: that could exceed a thin
  // authored envelope at maximum tilt. Facts themselves are not transformed.
  return `translate(${x}px, ${y}px) rotate(${rotation}deg) scale(${Math.max(0.1, scale - breathe)})`;
}

export function connectionCycle(frame: number, fps: number, startFrame: number, periodSeconds = 4): number {
  const turns = Math.max(0, frame - startFrame) / (Math.max(1, fps) * Math.max(2, periodSeconds));
  return turns - Math.floor(turns);
}

export function surfaceBackground(surface: StageElement["surface"], emphasis: number, frame = 0, fps = 30, sustain?: Sustain, startFrame = 0): string | undefined {
  const seconds = Math.max(0, frame - startFrame) / Math.max(1, fps);
  const angle = sustain ? (seconds / sustain.period_seconds + (sustain.phase ?? 0)) * Math.PI * 2 : 0;
  const amplitude = Math.min(40, sustain?.amplitude ?? 0);
  const wave = Math.sin(angle), companion = Math.cos(angle);
  const x = sustain?.kind === "drift" || sustain?.kind === "tilt" ? amplitude * wave : 0;
  const y = sustain?.kind === "float" ? amplitude * wave : sustain?.kind === "drift" || sustain?.kind === "tilt" ? amplitude * companion * 0.45 : 0;
  const lightRange = Math.min(1, amplitude / 12) * 0.09 + Math.max(0, amplitude - 12) / 28 * 0.09;
  const light = sustain?.kind === "breathe" ? lightRange * (0.5 + wave * 0.5) : 0;
  // The moving light is painted behind the original facts/raster. Surface is
  // optional; without an authored sustain, only the finite focus changes it.
  if (surface === "glow") return `radial-gradient(ellipse at calc(50% + ${x}px) calc(44% + ${y}px), rgba(255,189,25,${0.1 + emphasis * 0.13 + light}) 0%, rgba(88,121,134,.07) 42%, transparent 74%)`;
  if (surface === "spotlight") return `radial-gradient(ellipse at calc(50% + ${x}px) calc(38% + ${y}px), rgba(237,243,245,${0.1 + emphasis * 0.1 + light}) 0%, rgba(255,189,25,.06) 45%, transparent 76%)`;
  if (surface === "paper") return "linear-gradient(145deg,#f3eee1 0%,#e1d9c7 100%)";
  return undefined;
}

// Exterior document support adds depth without padding, scaling, overlays or
// filters on the captured evidence. The asset/mark coordinate system is intact.
export function documentSupportShadow(surface: StageElement["surface"], frame: number, fps: number, sustain?: Sustain, startFrame = 0): string | undefined {
  if (!surface || surface === "none") return undefined;
  const seconds = Math.max(0, frame - startFrame) / Math.max(1, fps);
  const angle = sustain ? (seconds / sustain.period_seconds + (sustain.phase ?? 0)) * Math.PI * 2 : 0;
  const amplitude = Math.min(40, sustain?.amplitude ?? 0);
  const wave = Math.sin(angle), companion = Math.cos(angle);
  const x = sustain?.kind === "drift" || sustain?.kind === "tilt" ? wave * amplitude * 0.5 : 0;
  const y = sustain?.kind === "float" ? wave * amplitude * 0.35 : sustain?.kind === "drift" || sustain?.kind === "tilt" ? companion * amplitude * 0.2 : 0;
  const light = sustain?.kind === "breathe" ? (0.5 + wave * 0.5) * amplitude / 40 * 0.13 : 0;
  const tint = surface === "spotlight" ? "220,233,239" : "255,189,25";
  return `0 14px 34px rgba(0,0,0,.58), 0 0 0 1px rgba(218,228,235,.34), ${x}px ${y}px ${32+amplitude*0.2}px rgba(${tint},${0.13+light})`;
}
