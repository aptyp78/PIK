import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import fs from 'fs/promises';
import path from 'path';

export async function GET(_req: NextRequest) {
  try {
    const dir = path.join(process.cwd(), 'lib', 'mapping', 'templates');
    const names = await fs.readdir(dir);
    const items = names.filter(n => n.endsWith('.json')).map(n => ({ id: n.replace(/\.json$/,'') }));
    return NextResponse.json({ ok: true, templates: items });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'failed' }, { status: 500 });
  }
}

