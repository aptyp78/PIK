import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import { deleteAllInFolder } from '@/lib/google/drive';

export async function POST(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  try {
    const url = new URL(req.url);
    const folderId = url.searchParams.get('folderId') || process.env.GDRIVE_ADOBE_FOLDER_ID || '';
    if (!folderId) return NextResponse.json({ ok: false, error: 'GDRIVE_ADOBE_FOLDER_ID missing' }, { status: 400 });
    const res = await deleteAllInFolder(folderId);
    return NextResponse.json({ ok: true, ...res, requestId: rid });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'clear failed', requestId: rid }, { status: 500 });
  }
}

