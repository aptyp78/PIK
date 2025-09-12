import fs from 'fs';
import fsp from 'fs/promises';
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
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      if (!(key in process.env)) process.env[key] = val;
    }
  } catch {}
}

async function main() {
  loadEnvLocal();
  const { extractWithRawJob } = await import('../lib/pdf/adobeExtract');
  const input = process.argv[2] || path.join(process.cwd(), 'data', 'PIK 5-0 - Platform Experience - ENG.pdf');
  if (!fs.existsSync(input)) throw new Error(`PDF not found: ${input}`);
  // 1) Extract
  const { raw, blocks } = await extractWithRawJob(input);
  // 2) Upload raw JSON to GCS Adobe_Destination
  const bucket = process.env.GCS_RESULTS_BUCKET || '';
  const prefix = (process.env.GCS_ADOBE_DEST_PREFIX || 'Adobe_Destination').replace(/\/$/, '');
  if (!bucket) throw new Error('GCS_RESULTS_BUCKET is not set');
  const fileName = path.basename(input);
  const objectName = `${prefix}/${fileName}.json`;
  const uri = await uploadJson(bucket, objectName, raw);
  const maxPage = blocks.reduce((m, b) => (b.page > m ? b.page : m), 0);
  // eslint-disable-next-line no-console
  console.log(JSON.stringify({ message: 'Adobe parse saved to GCS', uri, pages: maxPage, blocks: blocks.length }, null, 2));
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e?.message || e);
  process.exit(1);
});
