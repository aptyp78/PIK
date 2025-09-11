import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import { listFilesInFolder } from '@/lib/google/drive';

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const folderId = url.searchParams.get('folderId') || process.env.GDRIVE_ADOBE_FOLDER_ID || '';
    if (!folderId) return NextResponse.json({ ok: false, error: 'GDRIVE_ADOBE_FOLDER_ID missing' }, { status: 400 });
    const files = await listFilesInFolder(folderId, true, ['pdf','png']);
    return NextResponse.json({ ok: true, count: files.length, files });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'status failed' }, { status: 500 });
  }
}

