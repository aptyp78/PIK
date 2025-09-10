import { NextRequest, NextResponse } from 'next/server';

// Ensure this route runs on the Node.js runtime rather than the Edge runtime.
export const runtime = 'nodejs';
import prisma from '@/lib/prisma';

/*
 * API route: GET /api/search?q=…
 * Simple LIKE-based search over Block.text for MVP.
 */
export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const q = (searchParams.get('q') ?? '').trim();
  if (!q) return NextResponse.json({ query: q, results: [] });

  try {
    const results = await prisma.block.findMany({
      where: { text: { contains: q } },
      take: 20,
      select: { id: true, sourceDocId: true, page: true, role: true, text: true }
    });
    const mapped = results.map(r => ({
      id: r.id, docId: r.sourceDocId, page: r.page, role: r.role,
      snippet: r.text && r.text.length > 200 ? r.text.slice(0, 197) + '…' : r.text
    }));
    return NextResponse.json({ query: q, results: mapped });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? 'Unknown error' }, { status: 500 });
  }
}
