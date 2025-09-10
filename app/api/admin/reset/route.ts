import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';
import { logEvent } from '@/lib/log';
import fs from 'fs/promises';
import path from 'path';

async function clearDir(dir: string) {
  try {
    const entries = await fs.readdir(dir).catch(() => []);
    await Promise.all(
      entries
        .filter((n) => n !== '.gitkeep')
        .map((n) => fs.rm(path.join(dir, n), { recursive: true, force: true }))
    );
  } catch {}
}

export async function POST(req: NextRequest) {
  const rid = (globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2));
  // Auth: in prod require ADMIN_RESET_TOKEN; in dev allow if not set
  const token = process.env.ADMIN_RESET_TOKEN;
  if (token) {
    const hdr = req.headers.get('x-admin-reset') || '';
    if (hdr !== token) return NextResponse.json({ ok: false, error: 'Forbidden' }, { status: 403 });
  } else if (process.env.NODE_ENV === 'production') {
    return NextResponse.json({ ok: false, error: 'Forbidden' }, { status: 403 });
  }

  const started = Date.now();
  const dataDir = path.join(process.cwd(), 'data');
  const rawDir = path.join(dataDir, 'raw');
  const normDir = path.join(dataDir, 'normalized');
  const uploadsDir = path.join(dataDir, 'uploads');
  const eventsDir = path.join(process.cwd(), 'logs', 'events');

  try {
    // Clear data files
    await clearDir(rawDir);
    await clearDir(normDir);
    await clearDir(uploadsDir);
    // Clear DB content (docs + blocks only)
    const delBlocks = await prisma.block.deleteMany();
    const delDocs = await prisma.sourceDoc.deleteMany();
    // Clear event logs
    await clearDir(eventsDir);

    await logEvent('admin:reset', { requestId: rid, delBlocks: delBlocks.count, delDocs: delDocs.count });
    const res = NextResponse.json({ ok: true, delBlocks: delBlocks.count, delDocs: delDocs.count, durationMs: Date.now() - started });
    res.headers.set('x-request-id', rid);
    return res;
  } catch (e: any) {
    await logEvent('admin:reset:error', { requestId: rid, error: e?.message || String(e) }, 'error');
    const res = NextResponse.json({ ok: false, error: e?.message || 'reset failed' }, { status: 500 });
    res.headers.set('x-request-id', rid);
    return res;
  }
}

