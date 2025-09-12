import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import { downloadBuffer } from '@/lib/gcs';

// Streams a PDF from GCS source bucket.
// Accepts: ?name=<path relative to source bucket>
// Example: name=PIK-5-Core-Kit/Document.pdf
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const srcBucket = process.env.GCS_SOURCE_BUCKET || '';
    const name = url.searchParams.get('name') || '';
    if (!srcBucket) return NextResponse.json({ ok: false, error: 'GCS_SOURCE_BUCKET missing' }, { status: 400 });
    if (!name) return NextResponse.json({ ok: false, error: 'name required' }, { status: 400 });
    const buf = await downloadBuffer(srcBucket, name);
    return new NextResponse(buf, { status: 200, headers: { 'Content-Type': 'application/pdf', 'Cache-Control': 'no-store' } });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'pdf get failed' }, { status: 500 });
  }
}

