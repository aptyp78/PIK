import fs from 'fs';
import path from 'path';
// Adobe parsing → GCS only
import { uploadJson } from '../lib/gcs';
import '../lib/runtime/net';

function loadEnvLocal() {
  try {
    const p = path.join(process.cwd(), '.env.local');
    if (!fs.existsSync(p)) return;
    const txt = fs.readFileSync(p, 'utf8');
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

async function ingestOne(absPath: string) {
  const { extractWithRawJob } = await import('../lib/pdf/adobeExtract');
  const { raw, blocks } = await extractWithRawJob(absPath);
  const bucket = process.env.GCS_RESULTS_BUCKET || '';
  const prefix = (process.env.GCS_ADOBE_DEST_PREFIX || 'Adobe_Destination').replace(/\/$/, '');
  if (!bucket) throw new Error('GCS_RESULTS_BUCKET is not set');
  const base = path.basename(absPath);
  const objectName = `${prefix}/${base}.json`;
  const uri = await uploadJson(bucket, objectName, raw);
  const maxPage = blocks.reduce((m, b: any) => (b.page > m ? b.page : m), 0);
  return { uri, pages: maxPage || null, blocks: blocks.length };
}

async function main() {
  loadEnvLocal();
  // Ensure mock is disabled for real run unless user overrides
  if (!('MOCK_ADOBE' in process.env)) process.env.MOCK_ADOBE = '0';
  if (!('MOCK_ADOBE_AUTO' in process.env)) process.env.MOCK_ADOBE_AUTO = '0';

  const baseDir = path.join(process.cwd(), 'data');
  const files = [
    'PIK 5-0 - Platform Experience - ENG.pdf',
    'PIK 5-0 - Ecosystem Forces Scan - ENG.pdf',
    'PIK 5-0 - Platform Business Model - ENG.pdf',
    'PIK 5-0 - NFX Reinforcement Engines - ENG.pdf',
    'PIK 5-0 - Platform Value Network Canvas - ENG.pdf',
    'PIK 5-0 - Introduction - English.pdf',
  ].map((n) => path.join(baseDir, n));

  const existing = files.filter((p) => fs.existsSync(p));
  const missing = files.filter((p) => !fs.existsSync(p));
  const results: any[] = [];
  let totalBlocks = 0;
  let firstUri: string | undefined;
  let lastUri: string | undefined;
  for (const p of existing) {
    try {
      const r = await ingestOne(p);
      results.push({ path: p, ok: true, ...r });
      totalBlocks += r.blocks;
      if (!firstUri) firstUri = r.uri;
      lastUri = r.uri;
    } catch (e: any) {
      results.push({ path: p, ok: false, error: e?.message || String(e) });
    }
  }
  // eslint-disable-next-line no-console
  console.log(JSON.stringify({ ok: results.some((i) => i.ok), results, missing, totalBlocks, firstUri, lastUri }, null, 2));
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e?.message || e);
  process.exit(1);
});
