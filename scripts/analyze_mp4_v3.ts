import { readFileSync } from 'fs';
import { resolve } from 'path';

function parseWav(buffer: Buffer) {
  const sampleRate = buffer.readInt32LE(24);
  let pos = 12;
  while (pos < buffer.length - 8) {
    const chunkId = buffer.toString('ascii', pos, pos + 4);
    const size = buffer.readInt32LE(pos + 4);
    if (chunkId === 'data') {
      const dataOffset = pos + 8;
      const count = size / 2;
      const samples = new Float32Array(count);
      for (let i = 0; i < count; i++) {
        samples[i] = buffer.readInt16LE(dataOffset + i * 2) / 32768.0;
      }
      return { sampleRate, samples };
    }
    pos += 8 + size;
  }
  throw new Error('No data chunk');
}

function computeRms(samples: Float32Array, start: number, len: number) {
  let s = 0;
  const end = Math.min(start + len, samples.length);
  const count = end - start;
  if (count <= 0) return -100;
  for (let i = start; i < end; i++) s += samples[i] * samples[i];
  return 20 * Math.log10(Math.max(1e-9, Math.sqrt(s / count)));
}

const wav = parseWav(readFileSync(resolve('render-output/analysis-v3/extracted_mp4_v3.wav')));
console.log('--- ANÁLISE DO ÁUDIO FINAL EXTRAÍDO DO MP4 V3 (COM TRILHA EDITORIAL DO MOTOR) ---');
console.log('SampleRate:', wav.sampleRate, 'Total Samples:', wav.samples.length, 'Duration:', (wav.samples.length / wav.sampleRate).toFixed(2) + 's');
console.log('RMS Global do MP4 (Narração + Trilha Bed Music):', computeRms(wav.samples, 0, wav.samples.length).toFixed(2), 'dBFS');

const boundaries = [33.67, 72.30, 109.00, 145.63];
boundaries.forEach((sec, idx) => {
  const centerSample = Math.floor(sec * wav.sampleRate);
  console.log(`\nFronteira Cena 0${idx} -> 0${idx+1} (t = ${sec}s):`);
  const sliceSize = Math.floor(wav.sampleRate * 0.2); // 200ms
  for (let offset = -3; offset <= 3; offset++) {
    const sStart = centerSample + offset * sliceSize;
    const rms = computeRms(wav.samples, sStart, sliceSize);
    console.log(`   [${offset * 200 >= 0 ? '+' : ''}${offset * 200}ms]: RMS = ${rms.toFixed(2)} dBFS`);
  }
});
