import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import { simpleUpload } from '@/lib/google/gcs';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));
    const object = String(body.object || '').trim();
    if (!object) return NextResponse.json({ ok: false, error: 'object is required' }, { status: 400 });
    const bucket = body.bucket ? String(body.bucket) : process.env.GCS_SOURCE_BUCKET;
    const contentType = String(body.contentType || 'application/octet-stream');
    let content: Uint8Array;
    if (typeof body.bytes_base64 === 'string') {
      content = Uint8Array.from(Buffer.from(body.bytes_base64, 'base64'));
    } else if (typeof body.content === 'string') {
      content = new TextEncoder().encode(body.content);
    } else {
      return NextResponse.json({ ok: false, error: 'Provide content (string) or bytes_base64' }, { status: 400 });
    }
    const r = await simpleUpload(object, content, contentType, bucket);
    return NextResponse.json({ ok: true, result: { bucket, object, size: content.byteLength }, gcs: r });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'upload failed' }, { status: 500 });
  }
}

