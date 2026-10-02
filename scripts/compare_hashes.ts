import { readFileSync, existsSync } from 'fs';
import { createHash } from 'crypto';

function hashFile(path: string) {
  if (!existsSync(path)) return 'NOT_FOUND';
  const buf = readFileSync(path);
  return createHash('md5').update(buf).digest('hex') + ' (' + buf.length + ' bytes)';
}

console.log('--- COMPARAÇÃO HASH MD5 (RUN ANTERIOR vs RUN ATUAL) ---');
for (let i = 0; i < 5; i++) {
  const genOld = hashFile('render-output/review-82m/public/generated-audio/daily/scene-0' + i + '.wav');
  const genNew = hashFile('render-output/analysis-v2/public/generated-audio/daily/scene-0' + i + '.wav');
  console.log('scene-0' + i + ' generated-audio:');
  console.log('   Old (review-82m) :', genOld);
  console.log('   New (analysis-v2):', genNew);
  console.log('   IGUAIS?:', genOld === genNew ? 'SIM (100% IDÊNTICO - MESMO ÁUDIO BRUTO)' : 'NÃO (DIFERENTE)');
}

console.log('\n--- COMPARAÇÃO PROCESSED-AUDIO ---');
for (let i = 0; i < 5; i++) {
  const procOld = hashFile('render-output/review-82m/public/processed-audio/daily/scene-0' + i + '.wav');
  const procNew = hashFile('render-output/analysis-v2/public/processed-audio/daily/scene-0' + i + '.wav');
  console.log('scene-0' + i + ' processed-audio:');
  console.log('   Old (review-82m) :', procOld);
  console.log('   New (analysis-v2):', procNew);
  console.log('   IGUAIS?:', procOld === procNew ? 'SIM (100% IDÊNTICO)' : 'NÃO (DIFERENTE)');
}
