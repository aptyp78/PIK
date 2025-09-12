import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import { downloadText } from '@/lib/gcs';

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const bucket = process.env.GCS_RESULTS_BUCKET || '';
    const prefix = (process.env.GCS_ADOBE_DEST_PREFIX || 'Adobe_Destination').replace(/\/$/, '') + '/';
    const name = url.searchParams.get('name') || '';
    if (!bucket) return NextResponse.json({ ok: false, error: 'GCS_RESULTS_BUCKET missing' }, { status: 400 });
    if (!name) return NextResponse.json({ ok: false, error: 'name required' }, { status: 400 });
    if (!name.startsWith(prefix)) return NextResponse.json({ ok: false, error: 'invalid object path' }, { status: 400 });
    const text = await downloadText(bucket, name);
    let json: any;
    try { json = JSON.parse(text); } catch { json = null; }
    return NextResponse.json({ ok: true, name, size: Buffer.byteLength(text, 'utf8'), json, raw: json ? undefined : text });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'get failed' }, { status: 500 });
  }
}

