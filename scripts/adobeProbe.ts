#!/usr/bin/env tsx
import { extractWithRawJob } from '../lib/pdf/adobeExtract';
import fs from 'fs';
import path from 'path';

function loadEnvLocal() {
  try {
    const p = path.join(process.cwd(), '.env.local');
    if (!fs.existsSync(p)) return;
    const txt = fs.readFileSync(p, 'utf8');
    for (const line of txt.split(/\r?\n/)) {
      const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_\.]*)\s*=\s*(.*)\s*$/);
      if (!m) continue;
      const k = m[1];
      let v = m[2];
      if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
      if (!(k in process.env)) process.env[k] = v;
    }
  } catch {}
}

async function main() {
  loadEnvLocal();
  const file = process.argv[2];
  if (!file) throw new Error('Usage: tsx scripts/adobeProbe.ts <path-to-file>');
  const { blocks } = await extractWithRawJob(file);
  console.log('blocks', blocks.length);
  for (const b of blocks.slice(0, 5)) {
    console.log(JSON.stringify(b));
  }
}

main().catch((e) => { console.error(e?.message || e); process.exit(1); });
