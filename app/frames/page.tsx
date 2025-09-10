import prisma from '@/lib/prisma';
import { frames as staticFrames } from '@/lib/data/frames';
// @ts-ignore - client component
import AutoAssignClient from './AutoAssignClient';

export const runtime = 'nodejs';

export default async function FramesPage() {
  let frames: { id?: number; name: string; slug: string; fields: { id?: number; name: string }[] }[] = [];
  try {
    const dbFrames = await prisma.frame.findMany({
      orderBy: { order: 'asc' },
      select: { id: true, name: true, slug: true, fields: { orderBy: { order: 'asc' }, select: { id: true, name: true } } },
    });
    if (dbFrames.length > 0) {
      frames = dbFrames.map((f) => ({ id: f.id, name: f.name, slug: f.slug, fields: f.fields }));
    }
  } catch {
    // ignore and use fallback
  }
  if (frames.length === 0) {
    frames = staticFrames.map((f) => ({ name: f.name, slug: f.slug, fields: f.fields.map((n) => ({ name: n })) }));
  }

  return (
    <main className="max-w-5xl mx-auto py-8">
      <h1 className="text-3xl font-bold mb-4">Frames</h1>
      <AutoAssignClient />
      <div className="space-y-6">
        {frames.map((f) => (
          <div key={f.slug} className="border rounded p-4">
            <div className="font-semibold text-lg mb-2">{f.name}</div>
            <ul className="list-disc pl-5 text-sm space-y-0.5">
              {f.fields.map((fld, idx) => (
                <li key={fld.id ?? `${f.slug}-${idx}`}>{fld.name}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </main>
  );
}
