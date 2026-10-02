import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';

interface WavData {
  numChannels: number;
  sampleRate: number;
  bitsPerSample: number;
  samples: Float32Array;
  durationSec: number;
}

function parseWav(buffer: Buffer): WavData {
  const numChannels = buffer.readInt16LE(22);
  const sampleRate = buffer.readInt32LE(24);
  const bitsPerSample = buffer.readInt16LE(34);
  
  let pos = 12;
  let dataOffset = -1;
  let chunkSize = 0;
  
  while (pos < buffer.length - 8) {
    const chunkId = buffer.toString('ascii', pos, pos + 4);
    const size = buffer.readInt32LE(pos + 4);
    if (chunkId === 'data') {
      dataOffset = pos + 8;
      chunkSize = size;
      break;
    }
    pos += 8 + size;
  }
  
  if (dataOffset === -1) {
    throw new Error('No data chunk found in WAV');
  }

  const sampleCount = Math.floor(chunkSize / (bitsPerSample / 8) / numChannels);
  const samples = new Float32Array(sampleCount);

  if (bitsPerSample === 16) {
    for (let i = 0; i < sampleCount; i++) {
      let monoSample = 0;
      for (let ch = 0; ch < numChannels; ch++) {
        monoSample += buffer.readInt16LE(dataOffset + (i * numChannels + ch) * 2) / 32768.0;
      }
      samples[i] = monoSample / numChannels;
    }
  } else {
    throw new Error(`Unsupported bitsPerSample: ${bitsPerSample}`);
  }

  return {
    numChannels,
    sampleRate,
    bitsPerSample,
    samples,
    durationSec: sampleCount / sampleRate,
  };
}

function computeRmsDb(samples: Float32Array, startIdx = 0, length = samples.length): number {
  if (length <= 0) return -100;
  let sum = 0;
  const end = Math.min(startIdx + length, samples.length);
  const count = end - startIdx;
  if (count <= 0) return -100;

  for (let i = startIdx; i < end; i++) {
    sum += samples[i] * samples[i];
  }
  const rms = Math.sqrt(sum / count);
  return 20 * Math.log10(Math.max(1e-9, rms));
}

function computePeakDb(samples: Float32Array, startIdx = 0, length = samples.length): number {
  const end = Math.min(startIdx + length, samples.length);
  let maxAbs = 0;
  for (let i = startIdx; i < end; i++) {
    const abs = Math.abs(samples[i]);
    if (abs > maxAbs) maxAbs = abs;
  }
  return 20 * Math.log10(Math.max(1e-9, maxAbs));
}

// Normalized auto-correlation for Pitch (F0)
function computePitchFrames(
  samples: Float32Array,
  sampleRate: number,
  startSample: number,
  lengthSamples: number
): { mean: number; median: number; std: number; min: number; max: number; voicedRatio: number } {
  const frameSize = Math.floor(sampleRate * 0.04); // 40ms frame
  const hopSize = Math.floor(sampleRate * 0.03);   // 30ms hop
  const minF0 = 80;   // Hz
  const maxF0 = 260;  // Hz
  const minLag = Math.floor(sampleRate / maxF0);
  const maxLag = Math.floor(sampleRate / minF0);

  const pitches: number[] = [];
  let totalFrames = 0;

  const endSample = Math.min(startSample + lengthSamples, samples.length) - frameSize;

  for (let s = startSample; s < endSample; s += hopSize) {
    totalFrames++;
    let energy = 0;
    for (let i = 0; i < frameSize; i++) {
      energy += samples[s + i] * samples[s + i];
    }
    const frameRms = Math.sqrt(energy / frameSize);
    if (frameRms < 0.03) continue; // silence or unvoiced

    let bestLag = -1;
    let maxCorr = -1;

    for (let lag = minLag; lag <= maxLag; lag++) {
      let corr = 0;
      let eLag = 0;
      for (let i = 0; i < frameSize - lag; i++) {
        corr += samples[s + i] * samples[s + lag + i];
        eLag += samples[s + lag + i] * samples[s + lag + i];
      }
      const normCorr = corr / Math.max(1e-9, Math.sqrt(energy * eLag));
      if (normCorr > maxCorr) {
        maxCorr = normCorr;
        bestLag = lag;
      }
    }

    if (bestLag > 0 && maxCorr > 0.45) {
      pitches.push(sampleRate / bestLag);
    }
  }

  if (pitches.length === 0) {
    return { mean: 0, median: 0, std: 0, min: 0, max: 0, voicedRatio: 0 };
  }

  pitches.sort((a, b) => a - b);
  const median = pitches[Math.floor(pitches.length / 2)];
  const mean = pitches.reduce((a, b) => a + b, 0) / pitches.length;
  const variance = pitches.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / pitches.length;
  const std = Math.sqrt(variance);

  return {
    mean,
    median,
    std,
    min: pitches[0],
    max: pitches[pitches.length - 1],
    voicedRatio: pitches.length / Math.max(1, totalFrames)
  };
}

// Zero-Crossing Rate & High-Frequency brightness estimator (voice timbre consistency)
function computeTimbreMetrics(
  samples: Float32Array,
  sampleRate: number,
  startSample: number,
  lengthSamples: number
): { zcrHz: number; hfRatioPct: number } {
  const endSample = Math.min(startSample + lengthSamples, samples.length);
  let zeroCrossings = 0;
  let totalEnergy = 0;
  let diffEnergy = 0; // high frequencies emphasize derivative

  for (let i = startSample; i < endSample - 1; i++) {
    const s1 = samples[i];
    const s2 = samples[i + 1];
    if ((s1 >= 0 && s2 < 0) || (s1 < 0 && s2 >= 0)) {
      zeroCrossings++;
    }
    totalEnergy += s1 * s1;
    const diff = s2 - s1;
    diffEnergy += diff * diff;
  }

  const durationSec = (endSample - startSample) / sampleRate;
  const zcrHz = zeroCrossings / (2 * Math.max(1e-5, durationSec));
  const hfRatioPct = (diffEnergy / Math.max(1e-9, totalEnergy)) * 100;

  return { zcrHz, hfRatioPct };
}

function runAnalysis() {
  console.log('=============================================================================');
  console.log('  RELATÓRIO ACÚSTICO COMPLETO: VÍDEO R$ 82 MILHÕES (PRODUÇÃO CONTÍNUA)');
  console.log('=============================================================================\n');

  const dailyPath = resolve('render-output/analysis-v2/video/generated/daily-render-input.json');
  const continuousWavPath = resolve('render-output/analysis-v2/public/processed-audio/daily/daily-continuous-narration.wav');
  
  if (!existsSync(dailyPath)) {
    console.error('daily-render-input.json não encontrado');
    return;
  }
  if (!existsSync(continuousWavPath)) {
    console.error('daily-continuous-narration.wav não encontrado');
    return;
  }

  const daily = JSON.parse(readFileSync(dailyPath, 'utf8'));
  const wavBuf = readFileSync(continuousWavPath);
  const wav = parseWav(wavBuf);

  console.log(`Informações do Arquivo Mestre (daily-continuous-narration.wav):`);
  console.log(`- Taxa de Amostragem: ${wav.sampleRate} Hz`);
  console.log(`- Canais: ${wav.numChannels} (Mono)`);
  console.log(`- Duração Total do Áudio: ${wav.durationSec.toFixed(2)}s (${(wav.durationSec / 60).toFixed(2)} min)`);
  console.log(`- Duração do Vídeo (FPS ${daily.fps}): ${(daily.duration_in_frames / daily.fps).toFixed(2)}s (${daily.duration_in_frames} frames)`);
  console.log(`- Amostras Totais: ${wav.samples.length} (Exatamente ${daily.duration_in_frames * (wav.sampleRate / daily.fps)} amostras esperadas)`);
  console.log(`- RMS Global: ${computeRmsDb(wav.samples).toFixed(2)} dBFS`);
  console.log(`- Pico Absoluto: ${computePeakDb(wav.samples).toFixed(2)} dBFS`);
  console.log(`-----------------------------------------------------------------------------\n`);

  let currentFrame = 0;
  const sceneInfos: Array<{
    id: string;
    startSec: number;
    endSec: number;
    durationSec: number;
    startSample: number;
    endSample: number;
  }> = [];

  for (const scene of daily.scenes) {
    const durationFrames = scene.duration_frames || scene.durationInFrames;
    const startSec = currentFrame / daily.fps;
    currentFrame += durationFrames;
    const endSec = currentFrame / daily.fps;
    const durationSec = endSec - startSec;
    const startSample = Math.floor(startSec * wav.sampleRate);
    const endSample = Math.floor(endSec * wav.sampleRate);

    sceneInfos.push({
      id: scene.id,
      startSec,
      endSec,
      durationSec,
      startSample,
      endSample
    });
  }

  console.log('--- 1. ANÁLISE POR CENA (VOLUME, PITCH MÉDIO, BRILHO/TIMBRE) ---');
  sceneInfos.forEach((info, idx) => {
    const sceneLen = info.endSample - info.startSample;
    const rms = computeRmsDb(wav.samples, info.startSample, sceneLen);
    const peak = computePeakDb(wav.samples, info.startSample, sceneLen);
    const pitch = computePitchFrames(wav.samples, wav.sampleRate, info.startSample, sceneLen);
    const timbre = computeTimbreMetrics(wav.samples, wav.sampleRate, info.startSample, sceneLen);

    // Split scene into: Head (first 3.5s) vs Body (after 3.5s)
    const headLen = Math.min(sceneLen, Math.floor(wav.sampleRate * 3.5));
    const headRms = computeRmsDb(wav.samples, info.startSample, headLen);
    const headPitch = computePitchFrames(wav.samples, wav.sampleRate, info.startSample, headLen);
    const headTimbre = computeTimbreMetrics(wav.samples, wav.sampleRate, info.startSample, headLen);

    const bodyStart = info.startSample + headLen;
    const bodyLen = Math.max(0, sceneLen - headLen);
    const bodyRms = computeRmsDb(wav.samples, bodyStart, bodyLen);
    const bodyPitch = computePitchFrames(wav.samples, wav.sampleRate, bodyStart, bodyLen);
    const bodyTimbre = computeTimbreMetrics(wav.samples, wav.sampleRate, bodyStart, bodyLen);

    console.log(`[Cena 0${idx}: ${info.id}] (${info.startSec.toFixed(1)}s -> ${info.endSec.toFixed(1)}s, dur: ${info.durationSec.toFixed(1)}s)`);
    console.log(`   Cena Inteira : RMS = ${rms.toFixed(2)} dBFS | Pico = ${peak.toFixed(2)} dBFS | Pitch = ${pitch.mean.toFixed(1)} Hz (±${pitch.std.toFixed(1)}) | Timbre ZCR = ${timbre.zcrHz.toFixed(0)} Hz`);
    console.log(`   Início (0-3.5s): RMS = ${headRms.toFixed(2)} dBFS | Pitch = ${headPitch.mean.toFixed(1)} Hz | Timbre ZCR = ${headTimbre.zcrHz.toFixed(0)} Hz`);
    console.log(`   Corpo (>3.5s) : RMS = ${bodyRms.toFixed(2)} dBFS | Pitch = ${bodyPitch.mean.toFixed(1)} Hz | Timbre ZCR = ${bodyTimbre.zcrHz.toFixed(0)} Hz`);
    const deltaPitch = bodyPitch.mean - headPitch.mean;
    const deltaRms = bodyRms - headRms;
    const deltaTimbre = bodyTimbre.zcrHz - headTimbre.zcrHz;
    console.log(`   Variação Interna (Corpo - Início): ΔPitch = ${deltaPitch >= 0 ? '+' : ''}${deltaPitch.toFixed(1)} Hz | ΔRMS = ${deltaRms >= 0 ? '+' : ''}${deltaRms.toFixed(2)} dB | ΔTimbre = ${deltaTimbre >= 0 ? '+' : ''}${deltaTimbre.toFixed(0)} Hz\n`);
  });

  console.log('--- 2. ANÁLISE DE CONTINUIDADE NAS FRONTEIRAS DE TRANSIÇÃO ENTRE CENAS ---');
  console.log('(Checagem de descontinuidade, cortes de volume, silêncio artificial ou saltos nas emendas)\n');

  for (let i = 0; i < sceneInfos.length - 1; i++) {
    const sCurr = sceneInfos[i];
    const sNext = sceneInfos[i + 1];
    const boundarySec = sCurr.endSec;
    const boundarySample = sCurr.endSample;

    // Check windows: 1s before, 100ms before, 100ms after, 1s after
    const win1sSamples = Math.floor(wav.sampleRate * 1.0);
    const win100ms = Math.floor(wav.sampleRate * 0.1);
    const win20ms = Math.floor(wav.sampleRate * 0.02);

    const rmsTail1s = computeRmsDb(wav.samples, boundarySample - win1sSamples, win1sSamples);
    const rmsTail100ms = computeRmsDb(wav.samples, boundarySample - win100ms, win100ms);
    const rmsHead100ms = computeRmsDb(wav.samples, boundarySample, win100ms);
    const rmsHead1s = computeRmsDb(wav.samples, boundarySample, win1sSamples);

    // Check instantaneous step across 20ms boundary (click / cut detector)
    let maxStep = 0;
    for (let s = boundarySample - win20ms; s < boundarySample + win20ms - 1; s++) {
      const step = Math.abs(wav.samples[s + 1] - wav.samples[s]);
      if (step > maxStep) maxStep = step;
    }

    const pitchTail = computePitchFrames(wav.samples, wav.sampleRate, boundarySample - Math.floor(wav.sampleRate * 2.5), Math.floor(wav.sampleRate * 2.5));
    const pitchHead = computePitchFrames(wav.samples, wav.sampleRate, boundarySample, Math.floor(wav.sampleRate * 2.5));

    console.log(`Transição CENA 0${i} ➔ CENA 0${i + 1} em t = ${boundarySec.toFixed(2)}s:`);
    console.log(`   - RMS Último 1.0s da Cena 0${i}: ${rmsTail1s.toFixed(2)} dBFS`);
    console.log(`   - RMS Imediato (-100ms): ${rmsTail100ms.toFixed(2)} dBFS  ➔  RMS Imediato (+100ms): ${rmsHead100ms.toFixed(2)} dBFS`);
    console.log(`   - RMS Primeiro 1.0s da Cena 0${i + 1}: ${rmsHead1s.toFixed(2)} dBFS`);
    console.log(`   - Salto instantâneo max da forma de onda: ${(maxStep * 100).toFixed(2)}% (Corte abrupto/clique se > 15%)`);
    console.log(`   - Pitch no final da Cena 0${i}: ${pitchTail.mean.toFixed(1)} Hz  ➔  Pitch no início da Cena 0${i + 1}: ${pitchHead.mean.toFixed(1)} Hz (Δ = ${(pitchHead.mean - pitchTail.mean).toFixed(1)} Hz)`);
    console.log(`   - Diagnóstico: ${maxStep < 0.15 ? '✓ Transição limpa e contínua (sem corte/pop/estalo)' : '⚠️ Possível descontinuidade'}\n`);
  }

  console.log('--- 3. COMPARATIVO GERAL DE ESTABILIDADE ENTRE TODAS AS CENAS ---');
  const allScenePitches = sceneInfos.map(s => {
    return computePitchFrames(wav.samples, wav.sampleRate, s.startSample, s.endSample - s.startSample).mean;
  });
  const allSceneRms = sceneInfos.map(s => {
    return computeRmsDb(wav.samples, s.startSample, s.endSample - s.startSample);
  });
  const allSceneTimbres = sceneInfos.map(s => {
    return computeTimbreMetrics(wav.samples, wav.sampleRate, s.startSample, s.endSample - s.startSample).zcrHz;
  });

  const avgPitch = allScenePitches.reduce((a, b) => a + b, 0) / allScenePitches.length;
  const maxPitchDiff = Math.max(...allScenePitches) - Math.min(...allScenePitches);
  const avgRms = allSceneRms.reduce((a, b) => a + b, 0) / allSceneRms.length;
  const maxRmsDiff = Math.max(...allSceneRms) - Math.min(...allSceneRms);
  const avgTimbre = allSceneTimbres.reduce((a, b) => a + b, 0) / allSceneTimbres.length;
  const maxTimbreDiff = Math.max(...allSceneTimbres) - Math.min(...allSceneTimbres);

  console.log(`- Média Geral de Pitch (F0): ${avgPitch.toFixed(1)} Hz (Variação máxima entre cenas: ${maxPitchDiff.toFixed(1)} Hz)`);
  console.log(`- Média Geral de RMS: ${avgRms.toFixed(2)} dBFS (Variação máxima entre cenas: ${maxRmsDiff.toFixed(2)} dB)`);
  console.log(`- Média de Timbre/Brilho (ZCR): ${avgTimbre.toFixed(0)} Hz (Variação máxima entre cenas: ${maxTimbreDiff.toFixed(0)} Hz)`);
  console.log('=============================================================================');
}

runAnalysis();
