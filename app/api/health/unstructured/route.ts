import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';

export async function GET(_req: NextRequest) {
  const base = process.env.UNSTRUCTURED_API_URL || '';
  const key = process.env.UNSTRUCTURED_API_KEY || '';
  const okEnv = Boolean(base && key);
  const rid = (globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2));
  if (!okEnv) return NextResponse.json({ ok: false, error: 'UNSTRUCTURED_API_URL or KEY missing', requestId: rid }, { status: 400 });
  try {
    const url = base.replace(/\/$/, '') + '/general/v0/general';
    const fd = new FormData();
    const blob = new Blob([new TextEncoder().encode('ping')], { type: 'text/plain' });
    fd.append('files', blob, 'ping.txt');
    fd.append('coordinates', 'false');
    fd.append('hi_res', 'false');
    const t0 = Date.now();
    const res = await fetch(url, { method: 'POST', headers: { 'unstructured-api-key': key, 'Accept': 'application/json' }, body: fd, cache: 'no-store' });
    const dur = Date.now() - t0;
    const text = await res.text().catch(() => '');
    const ok = res.ok || res.status === 200;
    return NextResponse.json({ ok, status: res.status, durationMs: dur, sample: text.slice(0, 200), requestId: rid });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'fetch failed', requestId: rid }, { status: 500 });
  }
}
