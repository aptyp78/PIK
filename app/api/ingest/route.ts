import { NextRequest, NextResponse } from 'next/server';

// Ensure this route runs on the Node.js runtime rather than the Edge runtime.
export const runtime = 'nodejs';
import '@/lib/runtime/net';
import { extractWithRawJob, ConfigError as ExtractConfigError, ExtractError } from '@/lib/pdf/adobeExtract';
import prisma from '@/lib/prisma';
import path from 'path';
import fs from 'fs/promises';

/*
 * API route: POST /api/ingest
 * Body: { "path": "/absolute/path/to/file.pdf" }
 */
export async function POST(_req: NextRequest) {
  // Upload-by-path is disabled in uploads-only mode
  try {
    const rid = (globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2));
    const { logEvent } = await import('@/lib/log');
    await logEvent('ingest:path:attempt', { requestId: rid });
  } catch {}
  return NextResponse.json(
    { error: 'Загрузка из репозитория отключена. Используйте /api/ingest/upload или страницу /upload.' },
    { status: 410 }
  );
}
