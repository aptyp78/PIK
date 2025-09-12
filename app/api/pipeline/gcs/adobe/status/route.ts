import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import { listPrefix } from '@/lib/gcs';

export async function GET(req: NextRequest) {
  try {
    const bucket = process.env.GCS_RESULTS_BUCKET || '';
    const prefix = (process.env.GCS_ADOBE_DEST_PREFIX || 'Adobe_Destination').replace(/\/$/, '') + '/';
    if (!bucket) return NextResponse.json({ ok: false, error: 'GCS_RESULTS_BUCKET missing' }, { status: 400 });
    const url = new URL(req.url);
    const limit = Math.min(500, Math.max(1, parseInt(url.searchParams.get('limit') || '200', 10)));
    const items = await listPrefix(bucket, prefix, limit);
    return NextResponse.json({ ok: true, bucket, prefix, count: items.length, files: items });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'status failed' }, { status: 500 });
  }
}

