// Quick diagnostic: load .env.local, query Qdrant sample, and inspect payloads
import fs from 'fs';
import path from 'path';

function loadDotEnv(file: string) {
  try {
    const txt = fs.readFileSync(file, 'utf8');
    for (const line of txt.split(/\r?\n/)) {
      const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
      if (!m) continue;
      const [, k, vraw] = m;
      // Support simple unquoted and quoted values
      const v = vraw.startsWith('"') && vraw.endsWith('"')
        ? vraw.slice(1, -1)
        : vraw;
      if (!(k in process.env)) process.env[k] = v;
    }
  } catch {}
}

async function main() {
  // Load env from project root .env.local
  loadDotEnv(path.join(process.cwd(), '.env.local'));

  // Dynamically import TS helper (works with tsx)
  const q = await import('../lib/qdrant');
  const { scroll } = q as any;

  const limit = 10;
  const sc = await scroll({ limit });
  const items = (sc?.items || []).slice(0, limit);

  // Inspect payload keys for job info
  const summary = items.map((it: any) => {
    const pl = it?.payload || {};
    const keys = Object.keys(pl);
    const jobLike = Object.entries(pl)
      .filter(([k, _]) => /job|workflow|external_id/i.test(k))
      .map(([k, v]) => ({ key: k, value: typeof v === 'string' ? v.slice(0, 100) : v }));
    const filename = pl['metadata-filename'] || pl['filename'] || null;
    const fileId = pl['metadata-data_source-record_locator-file_id'] || pl['file_id'] || null;
    const page = pl['page'] ?? pl['metadata-page_number'] ?? null;
    return { id: it.id, filename, fileId, page, jobLikeKeys: jobLike, payloadKeys: keys.slice(0, 12) };
  });

  const coll = process.env.QDRANT_COLLECTION || '(unset)';
  console.log(JSON.stringify({ ok: true, collection: coll, sampleCount: items.length, items: summary }, null, 2));
}

main().catch((e) => {
  console.error(JSON.stringify({ ok: false, error: e?.message || String(e) }));
  process.exit(1);
});

