"use client";
import { useEffect, useMemo, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
// @ts-ignore
(pdfjsLib as any).GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${(pdfjsLib as any).version}/build/pdf.worker.min.mjs`;

type Item = { name: string; size: number; updated?: string };
type Box = { page: number; x0: number; y0: number; x1: number; y1: number; text?: string; type?: string };

function toBoxes(json: any): Box[] {
  const out: Box[] = [];
  const elements: any[] = Array.isArray(json?.content)
    ? json.content
    : Array.isArray(json?.elements)
    ? json.elements
    : [];
  for (const el of elements) {
    const page1 = ((): number => {
      const p = el?.page;
      if (typeof p === 'number' && !isNaN(p)) return p + 1; // many dumps use 0-based
      const P = el?.Page;
      if (typeof P === 'number' && !isNaN(P)) return P + 1;
      const m = el?.metadata;
      const pn = Number(m?.page_number ?? el?.page_number ?? 1) || 1;
      return pn;
    })();
    const page0 = Math.max(0, page1 - 1);
    let x0 = 0, y0 = 0, x1 = 0, y1 = 0;
    try {
      const pts: any[] = el?.coordinates?.points || el?.coordinates || [];
      if (Array.isArray(pts) && pts.length) {
        const xs = pts.map((p: any) => Number(p?.[0]) || 0);
        const ys = pts.map((p: any) => Number(p?.[1]) || 0);
        x0 = Math.min(...xs); y0 = Math.min(...ys); x1 = Math.max(...xs); y1 = Math.max(...ys);
      } else {
        const b = el?.bounds || el?.Bounds || el?.bound || el?.Boundary;
        if (Array.isArray(b) && b.length >= 4) {
          x0 = Number(b[0]) || 0; y0 = Number(b[1]) || 0; x1 = Number(b[2]) || 0; y1 = Number(b[3]) || 0;
        }
      }
    } catch {}
    const text = typeof el?.text === 'string' ? el.text : (typeof el?.Text === 'string' ? el.Text : undefined);
    const type = String(el?.type || el?.Type || '');
    out.push({ page: page0, x0, y0, x1, y1, text, type });
  }
  return out;
}

export default function AdobeViewerClient() {
  const [items, setItems] = useState<Item[]>([]);
  const [active, setActive] = useState<Item | null>(null);
  const [json, setJson] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [scale, setScale] = useState(1.0);
  const [page, setPage] = useState(0);
  const [onlyText, setOnlyText] = useState(false);
  const [noHuge, setNoHuge] = useState(true);
  const [pdfName, setPdfName] = useState<string | null>(null);
  const [pdfPages, setPdfPages] = useState<number>(0);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [templates, setTemplates] = useState<{ id: string }[]>([]);
  const [templateId, setTemplateId] = useState<string>('PIK_PBM_v5');
  const [mappedZones, setMappedZones] = useState<{ id: string; title?: string; box: [number,number,number,number] }[] | null>(null);
  const [mappedItems, setMappedItems] = useState<any[] | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch('/api/pipeline/gcs/adobe/status', { cache: 'no-store' });
        const j = await r.json();
        if (!j?.ok) throw new Error(j?.error || `HTTP ${r.status}`);
        const onlyJson = (j.files || []).filter((f: any) => /\.json$/i.test(String(f?.name || '')) && !String(f?.name || '').endsWith('/'));
        setItems(onlyJson);
        // Deep-link support: ?name=Adobe_Destination/...
        try {
          const sp = new URLSearchParams(window.location.search);
          const name = sp.get('name');
          if (name) {
            const it = onlyJson.find((f: any) => f.name === name) || { name, size: 0 };
            open(it);
          }
        } catch {}
      } catch (e: any) {
        setError(e?.message || 'failed');
      }
    })();
  }, []);

  // load templates list for mapping
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch('/api/mapping/templates', { cache: 'no-store' });
        const j = await r.json();
        if (j?.ok) setTemplates(j.templates || []);
      } catch {}
    })();
  }, []);

  async function open(it: Item) {
    setBusy(true); setError(null); setActive(it); setJson(null);
    try {
      const r = await fetch(`/api/pipeline/gcs/adobe/get?name=${encodeURIComponent(it.name)}`, { cache: 'no-store' });
      const j = await r.json();
      if (!j?.ok) throw new Error(j?.error || `HTTP ${r.status}`);
      setJson(j.json || null);
      setScale(1.0);
      setPage(0);
      try {
        const prefix = 'Adobe_Destination/';
        const n = it.name.startsWith(prefix) ? it.name.slice(prefix.length) : it.name;
        const pdf = n.replace(/\.json$/i, '');
        setPdfName(pdf);
      } catch {}
      // Run mapping with selected template
      try {
        const m = await fetch('/api/mapping/map', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: it.name, template: templateId }) });
        const mj = await m.json();
        if (mj?.ok) { setMappedZones(mj.zones||null); setMappedItems(mj.items||null); }
      } catch {}
    } catch (e: any) { setError(e?.message || 'failed'); }
    finally { setBusy(false); }
  }

  // re-map when template changes while item selected
  useEffect(() => {
    (async () => {
      if (!active) return;
      try {
        const m = await fetch('/api/mapping/map', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: active.name, template: templateId }) });
        const mj = await m.json();
        if (mj?.ok) { setMappedZones(mj.zones||null); setMappedItems(mj.items||null); }
      } catch {}
    })();
  }, [templateId]);

  const boxes = useMemo(() => json ? toBoxes(json) : [], [json]);
  const pages = useMemo(() => {
    const map = new Map<number, Box[]>();
    for (const b of boxes) { const arr = map.get(b.page) || []; arr.push(b); map.set(b.page, arr); }
    return map;
  }, [boxes]);
  const pageCount = Math.max(0, ...Array.from(pages.keys()).map(n => n + 1));
  let cur = pages.get(page) || [];
  // Optional filters
  if (onlyText) cur = cur.filter(b => /text/i.test(String(b.type||'')));
  const dims = useMemo(() => {
    const w = cur.reduce((m, b) => Math.max(m, b.x1), 0);
    const h = cur.reduce((m, b) => Math.max(m, b.y1), 0);
    return { w, h };
  }, [cur]);
  if (noHuge && dims.w > 0 && dims.h > 0) {
    const area = dims.w * dims.h;
    cur = cur.filter(b => ((b.x1 - b.x0) * (b.y1 - b.y0)) < area * 0.9);
  }
  // Draw larger first so мелкие прямоугольники остаются сверху
  const sorted = [...cur].sort((a, b) => ((b.x1-b.x0)*(b.y1-b.y0)) - ((a.x1-a.x0)*(a.y1-a.y0)));

  // Render PDF background for current page
  useEffect(() => {
    (async () => {
      const canvas = canvasRef.current; if (!canvas) return;
      const ctx = canvas.getContext('2d'); if (!ctx) return;
      if (!pdfName) { ctx.clearRect(0,0,canvas.width,canvas.height); return; }
      try {
        const loadingTask = pdfjsLib.getDocument(`/api/pipeline/gcs/pdf?name=${encodeURIComponent(pdfName)}`);
        const pdf = await loadingTask.promise;
        setPdfPages(pdf.numPages);
        const pNum = Math.min(Math.max(1, page+1), pdf.numPages);
        const p = await pdf.getPage(pNum);
        const viewport = p.getViewport({ scale: 1.5 });
        canvas.width = Math.round(viewport.width);
        canvas.height = Math.round(viewport.height);
        await p.render({ canvasContext: ctx, viewport } as any).promise;
      } catch {}
    })();
  }, [pdfName, page]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="md:col-span-1 border rounded p-3">
        <div className="font-semibold mb-2">Файлы</div>
        {error && <div className="text-sm text-red-700 mb-2">{error}</div>}
        <ul className="space-y-1 max-h-[70vh] overflow-auto">
          {items.map(it => (
            <li key={it.name} className={`px-2 py-1 border rounded cursor-pointer ${active?.name===it.name?'bg-blue-50':''}`} onClick={()=>open(it)}>
              <div className="truncate" title={it.name}>{it.name}</div>
              <div className="text-xs text-gray-500">{Math.round((it.size||0)/1024)} KB{it.updated?` • ${new Date(it.updated).toLocaleString()}`:''}</div>
            </li>
          ))}
        </ul>
      </div>
      <div className="md:col-span-2 border rounded p-3">
        <div className="flex items-center gap-2 mb-2 text-sm">
          <div className="font-semibold">Вьюер</div>
          <label>Шаблон
            <select className="ml-1 border rounded px-2 py-0.5" value={templateId} onChange={(e)=>setTemplateId(e.target.value)}>
              {[{id:'PIK_PBM_v5'}, ...templates.filter(t=>t.id!=='PIK_PBM_v5')].map(t => (<option key={t.id} value={t.id}>{t.id}</option>))}
            </select>
          </label>
          <label>Страница
            <input type="number" min={1} value={page+1} onChange={(e)=>setPage(Math.max(0, (Number(e.target.value)||1)-1))} className="ml-1 border rounded px-2 py-0.5 w-20" />
            <span className="ml-1 text-gray-500">/ {pageCount || '—'}</span>
          </label>
          <label>Масштаб
            <input type="number" step={0.1} value={scale} onChange={(e)=>setScale(Number(e.target.value)||1)} className="ml-1 border rounded px-2 py-0.5 w-24" />
          </label>
          <label className="ml-2 flex items-center gap-1"><input type="checkbox" checked={onlyText} onChange={e=>setOnlyText(e.target.checked)} /> Только текст</label>
          <label className="ml-2 flex items-center gap-1"><input type="checkbox" checked={noHuge} onChange={e=>setNoHuge(e.target.checked)} /> Без огромных</label>
          {busy && <span className="text-gray-500">Загрузка…</span>}
        </div>
        {/* PDF + overlay rendered below */}
        {!active ? (
          <div className="text-sm text-gray-600">Выберите файл слева</div>
        ) : !json ? (
          <div className="text-sm text-gray-600">Нет JSON</div>
        ) : sorted.length === 0 ? (
          <div className="text-sm text-gray-600">Графических элементов не найдено на этой странице (или JSON без координат)</div>
        ) : (
          <div className="relative border rounded bg-white inline-block">
            <canvas ref={canvasRef} className="block" />
            <div className="absolute left-0 top-0" style={{ width: (canvasRef.current?.width||0)+'px', height: (canvasRef.current?.height||0)+'px' }}>
              {(() => {
                const cw = canvasRef.current?.width || 0;
                const ch = canvasRef.current?.height || 0;
                const sx = dims.w ? cw / dims.w : 1;
                const sy = dims.h ? ch / dims.h : 1;
                const zoneColors = [ '#ff3b30', '#ff9500', '#ffcc00', '#34c759', '#0a84ff', '#5e5ce6', '#bf5af2', '#ff375f' ];
                const zones = (mappedZones || []).map((z, idx) => ({ ...z, color: zoneColors[idx % zoneColors.length] }));
                const zoneElems = zones.map((z, i) => {
                  const [nx1, ny1, nx2, ny2] = z.box;
                  const x = nx1 * cw;
                  const w = Math.max(0, (nx2 - nx1) * cw);
                  const h = Math.max(0, (ny2 - ny1) * ch);
                  const y = Math.max(0, ch - ny2 * ch);
                  return <div key={'zone-'+i} title={`${z.id}${z.title?(' · '+z.title):''}`} style={{ position:'absolute', left:x, top:y, width:w, height:h, border:'2px dashed '+z.color, background:'transparent' }} />;
                });
                const items = (mappedItems || sorted).map((b:any, i:number) => {
                  const x = b.x0 * sx;
                  const w = Math.max(0, (b.x1-b.x0) * sx);
                  const h = Math.max(0, (b.y1-b.y0) * sy);
                  const y = Math.max(0, ch - b.y1 * sy);
                  const area = (b.x1-b.x0) * (b.y1-b.y0);
                  const huge = dims.w>0 && dims.h>0 ? (area > dims.w*dims.h*0.9) : false;
                  const col = zones.find(z=>z.id===b.zoneId)?.color || 'rgba(0,153,255,0.8)';
                  return <div key={'it-'+i} title={(b.type||'') + (b.text? (': '+String(b.text).slice(0,100)) : '')} style={{ position:'absolute', left:x, top:y, width:w, height:h, border:'2px solid '+col, background: huge ? 'transparent' : 'rgba(0,153,255,0.08)' }} />;
                });
                return (<>{zoneElems}{items}</>);
              })()}
            </div>
          </div>
          {mappedZones && mappedZones.length>0 && (
            <div className="mt-2 text-xs text-gray-700 flex flex-wrap gap-2">
              {mappedZones.map((z, idx) => {
                const col = ['#ff3b30','#ff9500','#ffcc00','#34c759','#0a84ff','#5e5ce6','#bf5af2','#ff375f','#64d2ff','#ffd60a'][idx%10];
                return (
                  <span key={z.id} className="inline-flex items-center gap-1">
                    <span style={{ display:'inline-block', width:10, height:10, background:col, borderRadius:2 }} />
                    <span>{z.title || z.id}</span>
                  </span>
                );
              })}
            </div>
          )}
        )}
      </div>
    </div>
  );
}
