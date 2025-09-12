"use client";
import { useEffect, useMemo, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
// @ts-ignore align worker version dynamically
(pdfjsLib as any).GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${(pdfjsLib as any).version}/build/pdf.worker.min.mjs`;

type Block = { id: number; page: number; bbox: string; role: string; text: string | null };

type View = {
  // scale: -1 означает авто-подбор по ширине страницы
  scale: number;
  offsetX: number;
  offsetY: number;
  flipY: boolean;
};

const DEFAULT_VIEW: View = { scale: -1, offsetX: 0, offsetY: 0, flipY: true };

export default function OverlayPdf({ docId, pages }: { docId: number; pages?: number }) {
  const [pageNum, setPageNum] = useState(1);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [loading, setLoading] = useState(false);
  const [showOverlay, setShowOverlay] = useState(true);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const [pageSize, setPageSize] = useState<{ width: number; height: number } | null>(null);
  const storageKey = `doc:${docId}:overlayView`;
  const [view, setView] = useState<View>(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) return JSON.parse(raw);
    } catch {}
    return DEFAULT_VIEW;
  });

  useEffect(() => {
    try { localStorage.setItem(storageKey, JSON.stringify(view)); } catch {}
  }, [view, storageKey]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/docs/${docId}`, { cache: 'no-store' });
        const json = await res.json();
        const arr = (json?.blocks || []) as Block[];
        setBlocks(arr);
        // no canvas/profile metadata anymore
      } finally {
        setLoading(false);
      }
    })();
  }, [docId]);

  // Render the page via pdf.js
  useEffect(() => {
    let canceled = false;
    const ref: { current: any } = { current: null };
    (async () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const pdfjsLib = await import('pdfjs-dist');
      // Set worker via CDN to avoid bundling complexity
      // @ts-ignore
      pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://unpkg.com/pdfjs-dist@4.7.76/build/pdf.worker.min.mjs';
      const loadingTask = pdfjsLib.getDocument(`/api/docs/${docId}/pdf`);
      const pdf = await loadingTask.promise;
      const num = Math.min(Math.max(1, pageNum), pdf.numPages);
      const page = await pdf.getPage(num);
      const viewport = page.getViewport({ scale: 1.5 });
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      setPageSize({ width: viewport.width, height: viewport.height });
      const renderContext = { canvasContext: ctx, viewport } as any;
      try { ref.current?.cancel?.(); } catch {}
      const task = page.render(renderContext);
      ref.current = task;
      try { await task.promise; } catch {}
      if (!canceled) {
        // Nothing else; overlay is drawn via absolutely positioned div over the canvas
      }
    })().catch(() => {});
    return () => { canceled = true; try { ref.current?.cancel?.(); } catch {} };
  }, [docId, pageNum]);

  const pageBlocks = useMemo(() => blocks.filter(b => b.page === pageNum - 1), [blocks, pageNum]);

  const rects = useMemo(() => {
    if (!pageSize) return [] as { id: number; x: number; y: number; w: number; h: number; role: string }[];
    const { width, height } = pageSize;
    // Автомасштабирование: если scale == -1, подбираем по максимальному x1
    let autoK = 1;
    try {
      const maxX = pageBlocks.reduce((m, b) => {
        const arr = JSON.parse(b.bbox) as [number, number, number, number];
        return Math.max(m, Number(arr?.[2]) || 0);
      }, 1);
      if (maxX > 1) autoK = width / maxX;
    } catch {}
    const k = view.scale > 0 ? view.scale : autoK;
    return pageBlocks.map(b => {
      let [x0,y0,x1,y1] = JSON.parse(b.bbox) as [number,number,number,number];
      // normalize coordinates
      if (view.flipY) {
        const ny0 = height - y1;
        const ny1 = height - y0;
        y0 = ny0; y1 = ny1;
      }
      // unit conversion: assume points->px heuristic; user tunes with scale
      let x = x0 * k + view.offsetX;
      let y = y0 * k + view.offsetY;
      let w = (x1 - x0) * k;
      let h = (y1 - y0) * k;
      return { id: b.id, x, y, w, h, role: b.role };
    });
  }, [pageBlocks, pageSize, view]);

  return (
    <div className="mb-6">
      <div className="flex flex-wrap gap-3 items-end mb-2 text-sm">
        <label className="flex items-center gap-1">Page
          <input type="number" min={1} max={pages || 9999} value={pageNum}
                 onChange={(e)=>setPageNum(Number(e.target.value)||1)} className="border rounded px-2 py-1 w-20" />
        </label>
        <label className="flex items-center gap-1">Scale
          <input type="number" step="0.1" value={view.scale}
                 onChange={(e)=>setView(p=>({ ...p, scale: Number(e.target.value)||1 }))}
                 className="border rounded px-2 py-1 w-24" />
        </label>
        <label className="flex items-center gap-1">offsetX
          <input type="number" step="1" value={view.offsetX}
                 onChange={(e)=>setView(p=>({ ...p, offsetX: Number(e.target.value)||0 }))}
                 className="border rounded px-2 py-1 w-24" />
        </label>
        <label className="flex items-center gap-1">offsetY
          <input type="number" step="1" value={view.offsetY}
                 onChange={(e)=>setView(p=>({ ...p, offsetY: Number(e.target.value)||0 }))}
                 className="border rounded px-2 py-1 w-24" />
        </label>
        <label className="flex items-center gap-1">
          <input type="checkbox" checked={view.flipY}
                 onChange={(e)=>setView(p=>({ ...p, flipY: e.target.checked }))} /> flipY
        </label>
        <button className="px-3 py-1 border rounded" onClick={()=>setShowOverlay(s=>!s)}>
          {showOverlay ? 'Hide Overlay' : 'Show Overlay'}
        </button>
        <button className="px-3 py-1 border rounded" onClick={()=>setView(DEFAULT_VIEW)}>Reset</button>
        <span className="text-gray-500">{loading ? 'Loading blocks…' : `${pageBlocks.length} blocks on page`}</span>
      </div>
      <div className="relative inline-block border rounded">
        <canvas ref={canvasRef} className="block" />
        {showOverlay && (
          <div ref={overlayRef} className="absolute left-0 top-0 pointer-events-none">
            {pageSize && rects.map(r => (
              <div key={r.id}
                   title={`${r.role} #${r.id}`}
                   style={{
                     position: 'absolute',
                     left: `${r.x}px`, top: `${r.y}px`,
                     width: `${r.w}px`, height: `${r.h}px`,
                     border: '2px solid rgba(0, 153, 255, 0.7)',
                     background: 'rgba(0, 153, 255, 0.12)'
                   }} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
