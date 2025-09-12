"use client";
import { useEffect, useMemo, useRef, useState } from 'react';

type GcsItem = { name: string; size: number; updated?: string };
type Zone = { id: string; title?: string; box: [number,number,number,number] };

type Card = {
  name: string;
  zones: Zone[];
  counts: Record<string, number>;
  dims: { w: number; h: number } | null;
};

const colors = [ '#ff3b30', '#ff9500', '#ffcc00', '#34c759', '#0a84ff', '#5e5ce6', '#bf5af2', '#ff375f', '#64d2ff', '#ffd60a' ];

function drawCard(canvas: HTMLCanvasElement, card: Card) {
  const ctx = canvas.getContext('2d'); if (!ctx) return;
  const cw = canvas.width, ch = canvas.height;
  ctx.clearRect(0,0,cw,ch);
  // Background
  ctx.fillStyle = '#f8fafc';
  ctx.fillRect(0,0,cw,ch);
  // Title watermark
  ctx.fillStyle = '#e5e7eb';
  ctx.font = 'bold 14px system-ui, -apple-system, Segoe UI, Roboto';
  ctx.fillText('Template: PIK_PBM_v5', 8, 20);
  // Zones
  const zones = card.zones || [];
  zones.forEach((z, i) => {
    const col = colors[i % colors.length];
    const [nx1, ny1, nx2, ny2] = z.box;
    const x = nx1 * cw; const y = Math.max(0, ch - ny2 * ch);
    const w = Math.max(0, (nx2 - nx1) * cw); const h = Math.max(0, (ny2 - ny1) * ch);
    // fill
    ctx.fillStyle = col + '20';
    ctx.fillRect(x, y, w, h);
    // border
    ctx.strokeStyle = col;
    ctx.lineWidth = 2;
    ctx.setLineDash([6,4]);
    ctx.strokeRect(x, y, w, h);
    ctx.setLineDash([]);
    // label
    const label = z.title || z.id;
    ctx.fillStyle = '#111827';
    ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto';
    ctx.fillText(label, x + 6, y + 16);
    // badge with count
    const c = card.counts?.[z.id] || 0;
    const bx = x + w - 24, by = y + 6;
    ctx.fillStyle = col;
    ctx.fillRect(bx, by, 18, 18);
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 12px system-ui, -apple-system, Segoe UI, Roboto';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(String(c), bx + 9, by + 9);
    ctx.textAlign = 'start'; ctx.textBaseline = 'alphabetic';
  });
}

export default function FramesClient() {
  const [items, setItems] = useState<Card[]>([]);
  const [loading, setLoading] = useState(false);
  const canvasRefs = useRef<Record<string, HTMLCanvasElement | null>>({});

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const r = await fetch('/api/pipeline/gcs/adobe/status?limit=8', { cache: 'no-store' });
        const j = await r.json();
        const files: GcsItem[] = (j?.files || []).filter((f: any) => /\.json$/i.test(String(f?.name||'')) && !String(f?.name||'').endsWith('/'));
        const cards: Card[] = [];
        for (const f of files) {
          try {
            const m = await fetch('/api/mapping/map', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: f.name, template: 'PIK_PBM_v5', save: false }) });
            const mj = await m.json();
            if (mj?.ok) {
              const dimsObj = mj?.dims || {};
              const firstKey = Object.keys(dimsObj)[0];
              const d = firstKey ? dimsObj[firstKey] : null;
              cards.push({ name: f.name, zones: mj.zones || [], counts: mj.counts || {}, dims: d });
            }
          } catch {}
          if (cards.length >= 6) break;
        }
        setItems(cards);
      } finally { setLoading(false); }
    })();
  }, []);

  useEffect(() => {
    for (const card of items) {
      const c = canvasRefs.current[card.name];
      if (c) drawCard(c, card);
    }
  }, [items]);

  return (
    <div>
      <div className="text-sm text-gray-600 mb-3">Первые {items.length || 0} артефактов из GCS Adobe_Destination, шаблон PIK_PBM_v5.</div>
      {loading && <div className="text-sm text-gray-600">Загрузка…</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {items.map((card, idx) => (
          <a key={card.name} href={`/pipeline/adobe/viewer?name=${encodeURIComponent(card.name)}`} className="block border rounded-lg overflow-hidden hover:shadow">
            <div className="p-3 bg-white">
              <canvas ref={el => { canvasRefs.current[card.name] = el; }} width={540} height={340} className="w-full h-auto border rounded" />
            </div>
            <div className="px-3 py-2 bg-gray-900 text-gray-100 text-sm flex items-center justify-between">
              <div className="truncate" title={card.name}>{card.name.replace(/^Adobe_Destination\//,'')}</div>
              <div className="ml-2 text-xs text-gray-400">PIK_PBM_v5</div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}

