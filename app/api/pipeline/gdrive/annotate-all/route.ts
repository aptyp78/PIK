import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import { listFilesInFolder } from '@/lib/google/drive';

export async function POST(req: NextRequest) {
  const rid = globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2);
  const t0 = Date.now();
  try {
    const url = new URL(req.url);
    const folderId = url.searchParams.get('folderId') || process.env.DRIVE_FILE_ID || '';
    const recursive = /^(1|true|yes)$/i.test(url.searchParams.get('recursive') || '0');
    const limitPerFile = Number(url.searchParams.get('limit') || '500');
    if (!folderId) return NextResponse.json({ ok: false, error: 'folderId missing' }, { status: 400 });

    const files = await listFilesInFolder(folderId, recursive, ['pdf','png']);
    const results: any[] = [];
    for (const f of files) {
      const qs = new URLSearchParams({ fileId: f.id, limit: String(limitPerFile) });
      const res = await fetch(`${url.origin}/api/pipeline/qdrant/annotate?${qs.toString()}`, { method: 'POST' });
      const j = await res.json().catch(()=>({ ok:false, error:'bad json' }));
      results.push({ fileId: f.id, name: f.name, ok: j?.ok, matched: j?.matched ?? 0, total: j?.total ?? 0, error: j?.ok? undefined : j?.error });
    }
    const matched = results.reduce((a,b)=>a+(b.matched||0),0);
    return NextResponse.json({ ok: true, count: files.length, matched, results, requestId: rid, durationMs: Date.now() - t0 });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'annotate-all failed', requestId: rid }, { status: 500 });
  }
}

