import { NextRequest, NextResponse } from 'next/server';

// Ensure this route runs on the Node.js runtime rather than the Edge runtime.
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';

/*
 * API route: GET /api/docs
 * Returns a list of all ingested documents.
 */
export async function GET(_req: NextRequest) {
  try {
    const docs = await prisma.sourceDoc.findMany({
      orderBy: { id: 'desc' },
      // Do not expose absolute file paths in public API
      select: { id: true, title: true, type: true, pages: true }
    });
    return NextResponse.json({ documents: docs });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? 'Unknown error' }, { status: 500 });
  }
}
