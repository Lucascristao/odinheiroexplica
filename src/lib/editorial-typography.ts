export const EDITORIAL_FONT = "ODE Inter";
export const TYPOGRAPHY_VERSION = "2026-10-01.1";
export const textMinimums = {title: 36, label: 32, detail: 28, legend: 30, value: 48, caption: 24} as const;
export type TextRole = keyof typeof textMinimums;
export type MeasureWidth = (text: string, size: number) => number;
export type TextLayout = {lines: string[]; size: number; width: number; height: number; fits: boolean; requiredWidth: number; requiredHeight: number};

// The measurement adapter is injected: production uses the loaded font in Chromium.
// Pure composition can also be exercised without synthesizing narration.
export function composeText(text: string, width: number, height: number, maximum: number, minimum: number, measure: MeasureWidth): TextLayout {
  const words = text.trim().split(/\s+/).filter(Boolean);
  const wrap = (size: number) => {
    const lines: string[] = [];
    for (const word of words) {
      const last = lines.at(-1);
      if (last && measure(`${last} ${word}`, size) <= width) lines[lines.length - 1] += ` ${word}`;
      else lines.push(word);
    }
    return lines;
  };
  const upper = Math.max(minimum, Math.floor(maximum));
  for (let size = upper; size >= minimum; size--) {
    const lines = wrap(size);
    const requiredWidth = Math.max(0, ...lines.map(line => measure(line, size)));
    const requiredHeight = lines.length * size * 1.18;
    const fits = requiredWidth <= width + .1 && requiredHeight <= height + .1;
    if (fits || size === minimum) return {lines, size, width, height, fits, requiredWidth, requiredHeight};
  }
  throw new Error("Invalid typography minimum");
}
