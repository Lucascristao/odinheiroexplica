import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';
import { execSync } from 'child_process';

function parseWav(buffer: Buffer) {
  const sampleRate = buffer.readInt32LE(24);
  const channels = buffer.readInt16LE(22);
  const bitsPerSample = buffer.readInt16LE(34);
  let pos = 12;
  while (pos < buffer.length - 8) {
    const chunkId = buffer.toString('ascii', pos, pos + 4);
    const size = buffer.readInt32LE(pos + 4);
    if (chunkId === 'data') {
      const dataOffset = pos + 8;
      const count = size / (bitsPerSample / 8) / channels;
      const samples = new Float32Array(count);
      for (let i = 0; i < count; i++) {
        // mono or average channels
        if (bitsPerSample === 16) {
          let sum = 0;
          for (let c = 0; c < channels; c++) {
            sum += buffer.readInt16LE(dataOffset + (i * channels + c) * 2) / 32768.0;
          }
          samples[i] = sum / channels;
        } else if (bitsPerSample === 24) {
          let sum = 0;
          for (let c = 0; c < channels; c++) {
            const idx = dataOffset + (i * channels + c) * 3;
            const b0 = buffer[idx];
            const b1 = buffer[idx + 1];
            const b2 = buffer[idx + 2];
            const val = (b2 & 0x80) ? ((b2 << 16) | (b1 << 8) | b0) - 16777216 : ((b2 << 16) | (b1 << 8) | b0);
            sum += val / 8388608.0;
          }
          samples[i] = sum / channels;
        } else if (bitsPerSample === 32) {
          let sum = 0;
          for (let c = 0; c < channels; c++) {
            sum += buffer.readFloatLE(dataOffset + (i * channels + c) * 4);
          }
          samples[i] = sum / channels;
        }
      }
      return { sampleRate, channels, samples };
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

function computeZeroCrossingRate(samples: Float32Array, start: number, len: number) {
  const end = Math.min(start + len, samples.length);
  let crossings = 0;
  for (let i = start + 1; i < end; i++) {
    if ((samples[i] >= 0 && samples[i - 1] < 0) || (samples[i] < 0 && samples[i - 1] >= 0)) {
      crossings++;
    }
  }
  return crossings / (end - start);
}

// 1. Extrair audio do MP4 renderizado
const mp4Path = resolve('run_artifacts/current_run/render-output/daily-video.mp4');
const wavOutPath = resolve('run_artifacts/current_run/render-output/extracted_final.wav');

if (!existsSync(wavOutPath)) {
  console.log('Extraindo áudio do daily-video.mp4...');
  execSync(`ffmpeg -y -i "${mp4Path}" -vn -acodec pcm_s16le -ar 48000 -ac 1 "${wavOutPath}"`, { stdio: 'inherit' });
}

const wavFinal = parseWav(readFileSync(wavOutPath));
console.log(`\n=== ANÁLISE DE ENGENHARIA DE ÁUDIO DO VÍDEO FINAL ===`);
console.log(`Taxa de amostragem: ${wavFinal.sampleRate} Hz`);
console.log(`Duração total: ${(wavFinal.samples.length / wavFinal.sampleRate).toFixed(2)}s`);

const boundaries = [
  { from: 'scene-00', to: 'scene-01', time: 37.40 },
  { from: 'scene-01', to: 'scene-02', time: 76.30 },
  { from: 'scene-02', to: 'scene-03', time: 120.40 },
  { from: 'scene-03', to: 'scene-04', time: 161.93 },
  { from: 'scene-04', to: 'scene-05', time: 207.07 },
];

const scenes = [
  { id: 'scene-00', start: 0, end: 37.40, delivery: 'hook', text: 'Gancho inicial e pergunta provocativa' },
  { id: 'scene-01', start: 37.40, end: 76.30, delivery: 'explain', text: 'Juros rotativo 444,9% e prioridade' },
  { id: 'scene-02', start: 76.30, end: 120.40, delivery: 'explain', text: 'Regra dos três blocos 50-30-20' },
  { id: 'scene-03', start: 120.40, end: 161.93, delivery: 'contrast', text: 'Pague-se primeiro e CTA inscrição' },
  { id: 'scene-04', start: 161.93, end: 207.07, delivery: 'explain', text: 'Onde guardar a reserva (Tesouro/CDB)' },
  { id: 'scene-05', start: 207.07, end: 243.63, delivery: 'closing', text: 'Plano de 4 passos e encerramento' },
];

console.log('\n--- 1. VOLUME MÉDIO E BRILHO ESPECTRAL (TOM) POR CENA NO MP4 ---');
scenes.forEach((s) => {
  const startSample = Math.floor(s.start * wavFinal.sampleRate);
  const lenSamples = Math.floor((s.end - s.start) * wavFinal.sampleRate);
  const rms = computeRms(wavFinal.samples, startSample, lenSamples);
  const zcr = computeZeroCrossingRate(wavFinal.samples, startSample, lenSamples);
  const approxFreq = zcr * (wavFinal.sampleRate / 2);
  console.log(`[${s.id}] (${s.delivery.padEnd(8)}) de ${s.start.toFixed(1)}s a ${s.end.toFixed(1)}s:`);
  console.log(`   RMS Total: ${rms.toFixed(2)} dBFS | Freq. Média Estimada (ZCR): ${approxFreq.toFixed(0)} Hz`);
});

console.log('\n--- 2. TRANSIÇÃO DE VOLUME E ENTONAÇÃO NAS FRONTEIRAS (ÚLTIMOS 1.5s vs PRIMEIROS 1.5s) ---');
boundaries.forEach((b) => {
  const centerSample = Math.floor(b.time * wavFinal.sampleRate);
  const windowSamples = Math.floor(1.5 * wavFinal.sampleRate);
  
  // 1.5s antes da fronteira (final da cena anterior)
  const rmsBefore = computeRms(wavFinal.samples, centerSample - windowSamples, windowSamples);
  const zcrBefore = computeZeroCrossingRate(wavFinal.samples, centerSample - windowSamples, windowSamples);
  
  // 1.5s depois da fronteira (início da nova cena)
  const rmsAfter = computeRms(wavFinal.samples, centerSample, windowSamples);
  const zcrAfter = computeZeroCrossingRate(wavFinal.samples, centerSample, windowSamples);
  
  const deltaRms = rmsAfter - rmsBefore;
  const deltaPitch = (zcrAfter - zcrBefore) * (wavFinal.sampleRate / 2);
  
  console.log(`\nFronteira ${b.from} -> ${b.to} (em ${b.time.toFixed(2)}s):`);
  console.log(`   Final da ${b.from}:  RMS = ${rmsBefore.toFixed(2)} dBFS | Brilho/Tom = ${(zcrBefore * wavFinal.sampleRate / 2).toFixed(0)} Hz`);
  console.log(`   Início da ${b.to}:   RMS = ${rmsAfter.toFixed(2)} dBFS | Brilho/Tom = ${(zcrAfter * wavFinal.sampleRate / 2).toFixed(0)} Hz`);
  console.log(`   -> Salto de Volume: ${deltaRms >= 0 ? '+' : ''}${deltaRms.toFixed(2)} dB | Variação de Tom: ${deltaPitch >= 0 ? '+' : ''}${deltaPitch.toFixed(0)} Hz`);
});
