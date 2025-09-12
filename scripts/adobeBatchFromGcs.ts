// Batch Adobe parsing from GCS source bucket to GCS Adobe_Destination
import path from 'path';
import fs from 'fs/promises';
import { getStorage, uploadJson } from '../lib/gcs';
import { extractWithRawJob } from '../lib/pdf/adobeExtract';

function loadDotEnv(file = '.env.local') {
  try {
    const txt = require('fs').readFileSync(path.join(process.cwd(), file), 'utf8');
    for (const line of txt.split(/\r?\n/)) {
      const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
      if (!m) continue;
      const [, k, vraw] = m;
      const v = (vraw.startsWith('"') && vraw.endsWith('"')) || (vraw.startsWith("'") && vraw.endsWith("'")) ? vraw.slice(1, -1) : vraw;
      if (!(k in process.env)) process.env[k] = v;
    }
  } catch {}
}

async function main() {
  loadDotEnv();
  const srcBucket = process.env.GCS_SOURCE_BUCKET || '';
  const srcPrefix = (process.env.GCS_SOURCE_PREFIX || '').replace(/\/$/, '');
  const dstBucket = process.env.GCS_RESULTS_BUCKET || '';
  const dstPrefix = (process.env.GCS_ADOBE_DEST_PREFIX || 'Adobe_Destination').replace(/\/$/, '');
  if (!srcBucket || !dstBucket) throw new Error('GCS_SOURCE_BUCKET and GCS_RESULTS_BUCKET are required');

  const limit = Number(process.argv.find(a => /^--limit=/.test(a))?.split('=')[1] || '0') || 0;
  const storage = await getStorage();
  const [files] = await storage.bucket(srcBucket).getFiles({ prefix: srcPrefix ? srcPrefix + '/' : undefined, autoPaginate: true });
  const pdfs = files.filter((f: any) => /\.pdf$/i.test(f.name));
  const total = pdfs.length;
  const picked = limit > 0 ? pdfs.slice(0, limit) : pdfs;

  const tmpDir = path.join(process.cwd(), 'data', 'tmp_adobe');
  await fs.mkdir(tmpDir, { recursive: true });

  const results: any[] = [];
  let okCount = 0, failCount = 0;
  for (let i = 0; i < picked.length; i++) {
    const name = picked[i].name as string;
    const base = path.basename(name);
    const tmpPath = path.join(tmpDir, base);
    try {
      const [buf] = await storage.bucket(srcBucket).file(name).download();
      await fs.writeFile(tmpPath, buf);
      const { raw } = await extractWithRawJob(tmpPath);
      const objectName = `${dstPrefix}/${name}.json`;
      await uploadJson(dstBucket, objectName, raw);
      okCount++;
      results.push({ name, ok: true, object: objectName });
    } catch (e: any) {
      failCount++;
      results.push({ name, ok: false, error: e?.message || String(e) });
    } finally {
      try { await fs.unlink(tmpPath); } catch {}
    }
  }

  // eslint-disable-next-line no-console
  console.log(JSON.stringify({ ok: failCount === 0, total, processed: picked.length, okCount, failCount, results }, null, 2));
}

main().catch((e) => { console.error(e?.message || e); process.exit(1); });

