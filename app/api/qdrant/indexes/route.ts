import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';

function getEnv() {
  const url = process.env.QDRANT_URL?.replace(/\/$/, '');
  const collection = process.env.QDRANT_COLLECTION;
  const key = process.env.QDRANT_API_KEY_RW || process.env.QDRANT_API_KEY_RO;
  if (!url || !collection || !key) throw new Error('Qdrant env incomplete');
  return { url, collection, key };
}

async function qdrantIndex(field_name: string, field_schema: string) {
  const { url, collection, key } = getEnv();
  const res = await fetch(`${url}/collections/${encodeURIComponent(collection)}/index`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'api-key': key },
    body: JSON.stringify({ field_name, field_schema }),
  });
  const text = await res.text().catch(() => '');
  if (!res.ok) {
    // Treat already-exists as ok if Qdrant returns conflict-style errors
    if (/already|exists/i.test(text)) return { ok: true, status: res.status, message: 'exists' };
    throw new Error(`Qdrant ${res.status}: ${text.slice(0, 300)}`);
  }
  let json: any = {};
  try { json = JSON.parse(text); } catch { json = { raw: text }; }
  return { ok: true, status: res.status, result: json?.result ?? json };
}

export async function POST(_req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const fields: { name: string; schema: string }[] = [
      { name: 'metadata-filename', schema: 'keyword' },
      { name: 'metadata-data_source-record_locator-file_id', schema: 'keyword' },
    ];
    const results: any[] = [];
    for (const f of fields) {
      try { results.push({ field: f.name, ...(await qdrantIndex(f.name, f.schema)) }); }
      catch (e: any) { results.push({ field: f.name, ok: false, error: e?.message || String(e) }); }
    }
    return NextResponse.json({ ok: results.every(r => r.ok !== false), results, requestId: rid, durationMs: Date.now() - t0 });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'index failed', requestId: rid }, { status: 500 });
  }
}
