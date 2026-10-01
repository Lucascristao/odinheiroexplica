import {z} from "zod";

export const speechDirectionSchema = z.object({
  delivery: z.enum(["hook", "explain", "contrast", "question", "closing"]).optional(),
  rate: z.string().regex(/^[+-]?\d+%$/).optional(),
  pitch: z.string().regex(/^[+-]?\d+%$/).optional(),
  pause_ms: z.number().int().min(90).max(300).optional(),
  pronunciations: z.record(z.string().min(1), z.string().min(1)).optional(),
  cues: z.array(z.object({
    text: z.string().trim().min(1).max(160),
    kind: z.enum(["emphasis", "number", "contrast"]),
    intent: z.enum(["curiosity", "discovery", "reassurance", "caution", "conviction"]).optional(),
    arc: z.enum(["question", "build", "resolve", "contrast"]).optional(),
    emphasis_word: z.string().min(1).max(80).regex(/^[\p{L}\p{N}]+$/u).optional(),
    pause_before_ms: z.number().int().min(0).max(300).default(0),
  })).max(6).default([]),
});

export function validateSpeechDirection(narration: string, raw: unknown): string[] {
  const parsed = speechDirectionSchema.safeParse(raw ?? {});
  if (!parsed.success) return [parsed.error.message];
  const errors: string[] = [];
  const ranges: {start: number; end: number}[] = [];
  for (const cue of parsed.data.cues) {
    const start = narration.indexOf(cue.text);
    const end = start + cue.text.length;
    if (start < 0 || narration.split(cue.text).length !== 2) {
      errors.push(`Direção de voz precisa de trecho literal único: ${cue.text}`);
      continue;
    }
    if (/[.!?]\s+/.test(cue.text)) errors.push(`Direção de voz atravessa frases: ${cue.text}`);
    const isWord = (s: string) => /[\p{L}\p{N}]/u.test(s);
    if ((start > 0 && isWord(narration[start-1]) && isWord(cue.text[0])) || (end < narration.length && isWord(narration[end]) && isWord(cue.text.at(-1)!))) errors.push(`Direção de voz corta palavra: ${cue.text}`);
    if (cue.emphasis_word) {
      const words = cue.text.match(/[\p{L}\p{N}]+/gu) ?? [];
      if (words.filter(word => word === cue.emphasis_word).length !== 1) {
        errors.push(`Palavra de ênfase precisa aparecer uma única vez no próprio trecho: ${cue.emphasis_word}`);
      }
    }
    ranges.push({start, end});
  }
  ranges.sort((a, b) => a.start - b.start);
  if (ranges.some((r, i) => i > 0 && ranges[i-1].end > r.start)) errors.push("Direções de voz sobrepostas.");
  return errors;
}
