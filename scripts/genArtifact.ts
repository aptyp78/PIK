#!/usr/bin/env tsx
import { extractWithRawJob } from '../lib/pdf/adobeExtract';
import extractUnstructured from '../lib/ingest/unstructured';
import fs from 'fs/promises';
import path from 'path';

function loadEnvLocal() {
  try {
    const p = path.join(process.cwd(), '.env.local');
    const txt = require('fs').readFileSync(p, 'utf8');
    for (const line of txt.split(/\r?\n/)) {
      const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_\.]*)\s*=\s*(.*)\s*$/);
      if (!m) continue;
      const key = m[1];
      let val = m[2];
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) val = val.slice(1, -1);
      if (!(key in process.env)) process.env[key] = val;
    }
  } catch {}
}

async function findPosterPath(): Promise<string | null> {
  const candidates = [
    'data/uploads/PIK-Platform-Business-Model.pdf',
    'data/uploads/PIK-Platform-Business-Model.png',
    'data/uploads/PIK 5-0 - Platform Business Model - ENG.pdf',
    'data/uploads/PIK 5-0 - Platform Business Model - ENG.png',
  ];
  for (const p of candidates) {
    try { await fs.access(p); return p; } catch {}
  }
  return null;
}

async function main() {
  loadEnvLocal();
  const p = await findPosterPath();
  if (!p) throw new Error('Poster not found in data/uploads');
  let raw: any, blocks: any[] = [];
  try {
    ({ raw, blocks } = await extractUnstructured(p, p.split('/').pop() || 'upload'));
  } catch {
    ({ raw, blocks } = await extractWithRawJob(p));
  }
  await fs.mkdir('data/artifacts', { recursive: true });
  await fs.writeFile('data/artifacts/last_partition.json', JSON.stringify(raw));
  await fs.writeFile('data/artifacts/last_blocks.json', JSON.stringify(blocks));
  // eslint-disable-next-line no-console
  console.log('Saved data/artifacts/last_partition.json');
}

main().catch((e) => { console.error(e?.message || e); process.exit(1); });
