import { writeFileSync, mkdirSync } from 'fs';
import { resolve, dirname } from 'path';

interface MusicOptions {
  durationSeconds: number;
  sampleRate?: number;
  world?: string;
  seedStr?: string;
}

// Simple seeded PRNG (LCG)
class SeededRandom {
  private seed: number;
  constructor(seedStr: string) {
    let h = 0x811c9dc5;
    for (let i = 0; i < seedStr.length; i++) {
      h ^= seedStr.charCodeAt(i);
      h = Math.imul(h, 0x01000193);
    }
    this.seed = h >>> 0;
  }
  next(): number {
    this.seed = (1664525 * this.seed + 1013904223) >>> 0;
    return this.seed / 4294967296;
  }
}

// Musical profiles for O Dinheiro Explica
interface Profile {
  name: string;
  bpm: number;
  // Frequencies for chord progression (4 bars)
  chords: number[][]; // [chordIndex][noteFrequencies]
  bassNotes: number[]; // bass freq per bar
}

const PROFILES: Record<string, Profile> = {
  finance: {
    name: 'Editorial Finance (Dm9 -> Bbmaj7 -> Gm7 -> C9sus4)',
    bpm: 108,
    chords: [
      [146.83, 220.00, 261.63, 329.63, 349.23], // Dm9 (D3, A3, C4, E4, F4)
      [116.54, 174.61, 220.00, 293.66, 349.23], // Bbmaj7 (Bb2, F3, A3, D4, F4)
      [98.00,  146.83, 174.61, 233.08, 293.66], // Gm7 (G2, D3, F3, Bb3, D4)
      [130.81, 196.00, 261.63, 293.66, 329.63], // C9sus4 (C3, G3, C4, D4, E4)
    ],
    bassNotes: [73.42, 58.27, 49.00, 65.41], // D2, Bb1, G1, C2
  },
  market: {
    name: 'Dynamic Market (Am7 -> Fmaj9 -> Dm7 -> Gsus4)',
    bpm: 114,
    chords: [
      [110.00, 164.81, 196.00, 246.94, 261.63], // Am7 (A2, E3, G3, B3, C4)
      [87.31,  130.81, 174.61, 220.00, 261.63], // Fmaj9 (F2, C3, F3, A3, C4)
      [146.83, 220.00, 261.63, 349.23, 440.00], // Dm7 (D3, A3, C4, F4, A4)
      [98.00,  146.83, 196.00, 261.63, 293.66], // Gsus4 (G2, D3, G3, C4, D4)
    ],
    bassNotes: [55.00, 43.65, 73.42, 49.00], // A1, F1, D2, G1
  },
  alert: {
    name: 'Tension Alert (Em -> Cmaj7 -> Am9 -> Bm7)',
    bpm: 104,
    chords: [
      [82.41,  123.47, 164.81, 196.00, 246.94], // Em (E2, B2, E3, G3, B3)
      [130.81, 164.81, 196.00, 246.94, 329.63], // Cmaj7 (C3, E3, G3, B3, E4)
      [110.00, 164.81, 220.00, 261.63, 329.63], // Am9 (A2, E3, A3, C4, E4)
      [123.47, 185.00, 220.00, 293.66, 370.00], // Bm7 (B2, F#3, A3, D4, F#4)
    ],
    bassNotes: [41.20, 65.41, 55.00, 61.74], // E1, C2, A1, B1
  },
  personal_finance: {
    name: 'Clear Financial Plan (Gmaj7 -> Em9 -> Cmaj7 -> D9sus4)',
    bpm: 106,
    chords: [
      [98.00,  146.83, 196.00, 246.94, 293.66], // Gmaj7 (G2, D3, G3, B3, D4)
      [82.41,  123.47, 164.81, 246.94, 293.66], // Em9 (E2, B2, E3, B3, D4)
      [130.81, 164.81, 196.00, 246.94, 329.63], // Cmaj7 (C3, E3, G3, B3, E4)
      [146.83, 220.00, 261.63, 293.66, 370.00], // D9sus4 (D3, A3, C4, D4, F#4)
    ],
    bassNotes: [49.00, 41.20, 65.41, 73.42], // G1, E1, C2, D2
  },
};

export function generateEditorialBed(options: MusicOptions): { buffer: Buffer; duration: number } {
  const sampleRate = options.sampleRate || 48000;
  const duration = options.durationSeconds;
  const totalSamples = Math.floor(sampleRate * duration);
  const rng = new SeededRandom(options.seedStr || 'odinheiroexplica');
  
  const world = options.world || 'finance';
  const profile = PROFILES[world] || PROFILES.finance;

  const secondsPerBeat = 60 / profile.bpm;
  const secondsPerBar = secondsPerBeat * 4;

  const leftChannel = new Float32Array(totalSamples);
  const rightChannel = new Float32Array(totalSamples);

  // Pad phase registers
  const padPhasesL: number[] = [0, 0, 0, 0, 0];
  const padPhasesR: number[] = [0, 0, 0, 0, 0];
  let bassPhase = 0;

  // Gentle analog room-tone noise seed
  let lastNoise = 0;

  for (let n = 0; n < totalSamples; n++) {
    const t = n / sampleRate;
    const currentBarFloat = t / secondsPerBar;
    const currentBarIdx = Math.floor(currentBarFloat) % profile.chords.length;
    const barProgress = (t % secondsPerBar) / secondsPerBar;

    // --- 1. Ambient Warm Pad Layer ---
    const chord = profile.chords[currentBarIdx];
    // Smooth crossfade envelope within bar
    const barFade = Math.sin(Math.PI * barProgress);
    let padSampleL = 0;
    let padSampleR = 0;

    for (let k = 0; k < chord.length; k++) {
      const freq = chord[k];
      // Subtle stereo detune (+/- 0.35 Hz) for lush stereo width
      const fL = freq - 0.35;
      const fR = freq + 0.35;
      padPhasesL[k] = (padPhasesL[k] + (2 * Math.PI * fL) / sampleRate) % (2 * Math.PI);
      padPhasesR[k] = (padPhasesR[k] + (2 * Math.PI * fR) / sampleRate) % (2 * Math.PI);

      // Warm overtone mix (fundamental + soft 2nd harmonic)
      const vL = Math.sin(padPhasesL[k]) * 0.7 + Math.sin(padPhasesL[k] * 2) * 0.15;
      const vR = Math.sin(padPhasesR[k]) * 0.7 + Math.sin(padPhasesR[k] * 2) * 0.15;
      padSampleL += vL;
      padSampleR += vR;
    }
    padSampleL = (padSampleL / chord.length) * (0.65 + 0.35 * barFade);
    padSampleR = (padSampleR / chord.length) * (0.65 + 0.35 * barFade);

    // --- 2. Warm Sub-Bass Layer ---
    const bassFreq = profile.bassNotes[currentBarIdx];
    bassPhase = (bassPhase + (2 * Math.PI * bassFreq) / sampleRate) % (2 * Math.PI);
    // Bass pulse on beat 1 and beat 3
    const beatInBar = (t % secondsPerBar) / secondsPerBeat;
    const beatFraction = beatInBar % 1.0;
    const bassEnv = Math.exp(-3.5 * beatFraction);
    const bassVal = (Math.sin(bassPhase) + 0.25 * Math.sin(bassPhase * 2)) * bassEnv * 0.55;

    // --- 3. Rhythmic Pluck / Arpeggio Layer ---
    // 16th note pattern
    const sixteenth = Math.floor(beatInBar * 4) % 16;
    const noteInChord = chord[sixteenth % chord.length] * 2; // one octave higher
    const sixteenthFract = (beatInBar * 4) % 1.0;
    const pluckEnv = Math.exp(-22 * sixteenthFract);
    const pluckFreq = noteInChord;
    const pluckVal = Math.sin(2 * Math.PI * pluckFreq * t) * pluckEnv * 0.18;
    // Ping-pong delay: alternate L / R
    const pluckL = (sixteenth % 2 === 0 ? 1.0 : 0.25) * pluckVal;
    const pluckR = (sixteenth % 2 === 1 ? 1.0 : 0.25) * pluckVal;

    // --- 4. Organic Studio Ambience Floor (Pink-ish filtered noise at -52 dBFS) ---
    const whiteNoise = rng.next() * 2 - 1;
    lastNoise = 0.96 * lastNoise + 0.04 * whiteNoise; // 1-pole lowpass
    const roomTone = lastNoise * 0.0035;

    // --- Master Mix & Fades ---
    // Fade in: first 2.0s; Fade out: last 3.5s
    const fadeIn = Math.min(1.0, t / 2.0);
    const fadeOut = Math.min(1.0, Math.max(0.0, (duration - t) / 3.5));
    const masterGain = fadeIn * fadeOut * 0.32; // Master target ~ -24 dBFS RMS

    leftChannel[n] = (padSampleL * 0.38 + bassVal * 0.32 + pluckL + roomTone) * masterGain;
    rightChannel[n] = (padSampleR * 0.38 + bassVal * 0.32 + pluckR + roomTone) * masterGain;
  }

  // Create 16-bit Stereo PCM WAV
  const headerSize = 44;
  const pcmBytes = totalSamples * 2 * 2; // 2 channels, 2 bytes/sample
  const wavBuffer = Buffer.alloc(headerSize + pcmBytes);

  // RIFF header
  wavBuffer.write('RIFF', 0);
  wavBuffer.writeUInt32LE(36 + pcmBytes, 4);
  wavBuffer.write('WAVE', 8);

  // fmt chunk
  wavBuffer.write('fmt ', 12);
  wavBuffer.writeUInt32LE(16, 16);
  wavBuffer.writeUInt16LE(1, 20); // PCM
  wavBuffer.writeUInt16LE(2, 22); // Stereo
  wavBuffer.writeUInt32LE(sampleRate, 24);
  wavBuffer.writeUInt32LE(sampleRate * 2 * 2, 28); // byte rate
  wavBuffer.writeUInt16LE(4, 32); // block align
  wavBuffer.writeUInt16LE(16, 34); // bits per sample

  // data chunk
  wavBuffer.write('data', 36);
  wavBuffer.writeUInt32LE(pcmBytes, 40);

  let offset = headerSize;
  for (let i = 0; i < totalSamples; i++) {
    // Left
    const sL = Math.max(-1, Math.min(1, leftChannel[i]));
    wavBuffer.writeInt16LE(Math.floor(sL < 0 ? sL * 32768 : sL * 32767), offset);
    offset += 2;
    // Right
    const sR = Math.max(-1, Math.min(1, rightChannel[i]));
    wavBuffer.writeInt16LE(Math.floor(sR < 0 ? sR * 32768 : sR * 32767), offset);
    offset += 2;
  }

  return { buffer: wavBuffer, duration };
}

// CLI usage if called directly
const args = process.argv.slice(2);
let outPath = 'public/generated-music/daily-bed.wav';
let durSec = 182.08;
let world = 'finance';
let seed = 'quanto-rende-82-milhoes-poupanca-2026-10-02';

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--output' && args[i + 1]) outPath = args[++i];
  if (args[i] === '--duration' && args[i + 1]) durSec = parseFloat(args[++i]);
  if (args[i] === '--world' && args[i + 1]) world = args[++i];
  if (args[i] === '--seed' && args[i + 1]) seed = args[++i];
}

const resolvedOut = resolve(outPath);
mkdirSync(dirname(resolvedOut), { recursive: true });

console.log(`[Music Engine] Gerando trilha editorial:`);
console.log(`- Perfil: ${world} (${PROFILES[world]?.name || 'Padrão'})`);
console.log(`- Duração: ${durSec.toFixed(2)}s`);
console.log(`- Seed: ${seed}`);
console.log(`- Saída: ${resolvedOut}`);

const result = generateEditorialBed({
  durationSeconds: durSec,
  world,
  seedStr: seed,
});

writeFileSync(resolvedOut, result.buffer);
console.log(`[Music Engine] Trilha gerada com sucesso (${(result.buffer.length / 1024 / 1024).toFixed(2)} MB, ${result.duration.toFixed(2)}s)`);
