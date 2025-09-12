import { NextRequest, NextResponse } from 'next/server';
export const runtime = 'nodejs';
import fs from 'fs/promises';
import path from 'path';

function pathFor(id: string) {
  return path.join(process.cwd(), 'lib', 'mapping', 'templates', `${id}.json`);
}

export async function GET(req: NextRequest) {
  try {
    const id = req.nextUrl.searchParams.get('id') || 'PIK_PBM_v5';
    const p = pathFor(id);
    const txt = await fs.readFile(p, 'utf8');
    return NextResponse.json({ ok: true, template: JSON.parse(txt) });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'failed' }, { status: 500 });
  }
}

export async function PUT(req: NextRequest) {
  try {
    const id = req.nextUrl.searchParams.get('id') || 'PIK_PBM_v5';
    const body = await req.json();
    const tpl = body?.template;
    if (!tpl || !tpl?.zones) return NextResponse.json({ ok: false, error: 'template with zones required' }, { status: 400 });
    const p = pathFor(id);
    await fs.writeFile(p, JSON.stringify(tpl, null, 2), 'utf8');
    return NextResponse.json({ ok: true, id });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message || 'failed' }, { status: 500 });
  }
}

