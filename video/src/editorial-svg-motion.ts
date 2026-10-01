// All SVG motion is sampled from a supplied frame progress. No browser clock,
// CSS keyframes or state: seeking and parallel rendering produce the same art.
export const svgProgress = (progress: number) => Number.isFinite(progress) ? Math.min(1, Math.max(0, progress)) : 1;

export function svgPhase(progress: number, start = 0, end = 1): number {
  const p = svgProgress((svgProgress(progress) - start) / Math.max(0.001, end - start));
  return p * p * (3 - 2 * p);
}

export function svgEmphasis(progress: number, active: boolean): number {
  const p = svgProgress(progress);
  // A single emphasis on the authored cue, then a completely settled hold.
  return active && p > 0 && p < 1 ? Math.sin(Math.PI * p) : 0;
}
