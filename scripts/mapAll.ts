import { listPrefix } from '../lib/gcs';

async function main() {
  const bucket = process.env.GCS_RESULTS_BUCKET || '';
  const prefix = (process.env.GCS_ADOBE_DEST_PREFIX || 'Adobe_Destination').replace(/\/$/,'') + '/';
  const template = process.env.MAP_TEMPLATE_ID || 'PIK_PBM_v5';
  if (!bucket) throw new Error('GCS_RESULTS_BUCKET missing');
  const files = await listPrefix(bucket, prefix, 5000);
  const jsons = files.filter(f => /\.json$/i.test(f.name));
  let ok=0, fail=0;
  const base = `http://localhost:${process.env.PORT || '3002'}`;
  for (const f of jsons) {
    try {
      const r = await fetch(`${base}/api/mapping/map`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ name: f.name, template, save: true }), cache:'no-store' } as any);
      const j = await r.json();
      if (!j?.ok) throw new Error(j?.error || 'map failed');
      ok++;
    } catch { fail++; }
  }
  console.log(JSON.stringify({ ok: fail===0, total: jsons.length, okCount: ok, failCount: fail }));
}

main().catch(e=>{ console.error(e?.message||e); process.exit(1); });
