"use client";
import { useEffect, useMemo, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
// @ts-ignore
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://unpkg.com/pdfjs-dist@4.7.76/build/pdf.worker.min.mjs';
import profile from '@/lib/canvas/profiles/PIK_BusinessModel_v5.json';

type Zone = { id: number; key: string; name: string; status: string; text?: string|null; confidence: number; owner?: string|null; tags?: string|null };

export default function BMPage() {
  const [init, setInit] = useState<{ ok: boolean; path?: string; type?: string; docId?: number; canvasTransform?: string; zones?: Zone[]; error?: string } | null>(null);
  const [zones, setZones] = useState<Zone[]>([]);
  const [active, setActive] = useState<Zone | null>(null);
  const [transform, setTransform] = useState<{ scaleX:number; scaleY:number; offsetX:number; offsetY:number; flipY?:boolean }>({ scaleX: 1, scaleY: 1, offsetX: 0, offsetY: 0, flipY: true });
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const [drawing, setDrawing] = useState(false);
  const [evidenceRect, setEvidenceRect] = useState<{x:number;y:number;w:number;h:number}|null>(null);

  useEffect(() => {
    (async () => {
      const res = await fetch('/api/bm/init');
      const json = await res.json();
      setInit(json);
      if (json?.canvasTransform) {
        try { setTransform(JSON.parse(json.canvasTransform)); } catch {}
      }
      if (json?.zones) setZones(json.zones);
      // Render poster if exists
      if (json?.path && canvasRef.current) {
        const path = json.path as string;
        if (path.toLowerCase().endsWith('.pdf')) {
          const data = await fetch('/api/docs/'+json.docId+'/pdf').then(r=>r.arrayBuffer());
          // @ts-ignore
          const pdf = await pdfjsLib.getDocument({ data }).promise;
          const page = await pdf.getPage(1);
          const viewport = page.getViewport({ scale: 1.5 });
          const canvas = canvasRef.current!; const ctx = canvas.getContext('2d')!;
          canvas.width = viewport.width; canvas.height = viewport.height;
          // @ts-ignore
          await page.render({ canvasContext: ctx, viewport }).promise;
        } else {
          const img = new Image(); img.onload = () => { const c = canvasRef.current!; const ctx = c.getContext('2d')!; c.width = img.width; c.height = img.height; ctx.drawImage(img,0,0); }; img.src = path;
        }
      }
    })();
  }, []);

  function changeActive<K extends keyof Zone>(k: K, v: Zone[K]) {
    if (!active) return;
    const next = { ...active, [k]: v } as Zone;
    setActive(next);
  }

  async function saveZone() {
    if (!active) return;
    const res = await fetch('/api/bm/zones', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: active.id, status: active.status, text: active.text, confidence: active.confidence, owner: active.owner, tags: active.tags }) });
    if (res.ok) {
      const idx = zones.findIndex(z => z.id === active.id);
      const z = await res.json();
      const nz = [...zones]; nz[idx] = z.zone; setZones(nz);
    }
  }

  async function acceptDraft() {
    if (!active) return; changeActive('status', 'Approved'); await saveZone();
  }

  function onMouseDown(e: React.MouseEvent) {
    if (!drawing) return;
    const rect = (e.target as HTMLCanvasElement).getBoundingClientRect();
    const x = e.clientX - rect.left; const y = e.clientY - rect.top;
    setEvidenceRect({ x, y, w: 0, h: 0 });
  }
  function onMouseMove(e: React.MouseEvent) {
    if (!drawing || !evidenceRect) return;
    const rect = (e.target as HTMLCanvasElement).getBoundingClientRect();
    const x = e.clientX - rect.left; const y = e.clientY - rect.top;
    setEvidenceRect({ ...evidenceRect, w: x - evidenceRect.x, h: y - evidenceRect.y });
  }
  async function onMouseUp() {
    if (!drawing || !evidenceRect || !active) return;
    setDrawing(false);
    const r = { page: 1, x: evidenceRect.x, y: evidenceRect.y, w: evidenceRect.w, h: evidenceRect.h };
    await fetch('/api/bm/evidence', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ zoneId: active.id, rect: r }) });
    setEvidenceRect(null);
  }

  const docId = init?.docId;
  const missing = init && init.ok === false;

  return (
    <main className="max-w-7xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-3">Platform Business Model</h1>
      {missing ? (
        <div className="p-4 border rounded bg-yellow-50 text-yellow-900">Положите файл `data/uploads/PIK-Platform-Business-Model.pdf` (или .png) и обновите страницу.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <div className="mb-2 flex gap-2 items-center text-sm">
              <label>scale
                <input type="number" step="0.1" value={transform.scaleX} onChange={(e)=>setTransform(t=>({ ...t, scaleX: Number(e.target.value)||1, scaleY: Number(e.target.value)||1 }))} className="border rounded px-2 py-1 w-24 ml-1" />
              </label>
              <label>offsetX
                <input type="number" value={transform.offsetX} onChange={(e)=>setTransform(t=>({ ...t, offsetX: Number(e.target.value)||0 }))} className="border rounded px-2 py-1 w-24 ml-1" />
              </label>
              <label>offsetY
                <input type="number" value={transform.offsetY} onChange={(e)=>setTransform(t=>({ ...t, offsetY: Number(e.target.value)||0 }))} className="border rounded px-2 py-1 w-24 ml-1" />
              </label>
              <label className="flex items-center gap-1"><input type="checkbox" checked={!!transform.flipY} onChange={(e)=>setTransform(t=>({ ...t, flipY: e.target.checked }))}/> flipY</label>
              <button className="px-3 py-1 border rounded" onClick={async()=>{ await fetch('/api/bm/calibration',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ docId, canvasTransform: transform })});}}>Save overlay</button>
              <a className="px-3 py-1 border rounded" href="/bm/export">Экспорт</a>
              <button className={`px-3 py-1 border rounded ${drawing? 'bg-green-600 text-white':''}`} onClick={()=>setDrawing(d=>!d)}>Evidence</button>
            </div>
            <div className="relative inline-block border rounded">
              <canvas ref={canvasRef} onMouseDown={onMouseDown} onMouseMove={onMouseMove} onMouseUp={onMouseUp} />
              {evidenceRect && (
                <div className="absolute border-2 border-red-500" style={{ left: evidenceRect.x, top: evidenceRect.y, width: evidenceRect.w, height: evidenceRect.h }} />
              )}
            </div>
          </div>
          <div className="border rounded p-3 overflow-auto max-h-[80vh]">
            <div className="font-semibold mb-2">Зоны</div>
            <ul className="space-y-1 text-sm">
              {zones.map(z => (
                <li key={z.id} className={`flex items-center justify-between px-2 py-1 rounded cursor-pointer ${active?.id===z.id? 'bg-blue-50':''}`} onClick={()=>setActive(z)}>
                  <span>{z.name}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${z.status==='Approved'?'bg-green-100 text-green-700': z.status==='Draft'?'bg-yellow-100 text-yellow-700':'bg-gray-100 text-gray-600'}`}>{z.status}</span>
                </li>
              ))}
            </ul>
            {active && (
              <div className="mt-3 border-t pt-3 text-sm space-y-2">
                <div className="font-semibold">{active.name}</div>
                <label className="block">Текст
                  <textarea className="w-full border rounded p-2" rows={6} value={active.text||''} onChange={(e)=>changeActive('text', e.target.value)} />
                </label>
                <div className="flex gap-2 items-center">
                  <label>Статус
                    <select className="border rounded px-2 py-1 ml-1" value={active.status} onChange={(e)=>changeActive('status', e.target.value)}>
                      {['Empty','Draft','Proposed','Approved','To review'].map(s => (<option key={s} value={s}>{s}</option>))}
                    </select>
                  </label>
                  <label>Уверенность
                    <input type="number" min={0} max={100} className="border rounded px-2 py-1 ml-1 w-20" value={active.confidence} onChange={(e)=>changeActive('confidence', Number(e.target.value)||0)} />
                  </label>
                </div>
                <label className="block">Ответственный
                  <input className="w-full border rounded px-2 py-1" value={active.owner||''} onChange={(e)=>changeActive('owner', e.target.value)} />
                </label>
                <label className="block">Метки
                  <input className="w-full border rounded px-2 py-1" value={active.tags||''} onChange={(e)=>changeActive('tags', e.target.value)} />
                </label>
                {/* Простые проверки TAM/SAM/SOM */}
                <BMHints zones={zones} />
                <div className="flex gap-2">
                  <button className="px-3 py-1 border rounded" onClick={saveZone}>Сохранить</button>
                  <button className="px-3 py-1 border rounded" onClick={acceptDraft}>Принять черновик</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}

function getNum(zs: Zone[], key: string): number | null {
  const z = zs.find(x => x.key === key);
  if (!z || !z.text) return null;
  const m = String(z.text).match(/\d+(?:[\.,]\d+)?/);
  return m ? Number(m[0].replace(',', '.')) : null;
}

function BMHints({ zones }: { zones: Zone[] }) {
  const tam = getNum(zones, 'tam');
  const sam = getNum(zones, 'sam');
  const som = getNum(zones, 'som');
  const core = zones.find(z => z.key==='core-services')?.text?.trim();
  const vc = zones.find(z => z.key==='value-capture')?.text?.trim();
  const issues: string[] = [];
  if (tam!=null && sam!=null && som!=null) {
    if (!(tam>=sam && sam>=som)) issues.push('TAM ≥ SAM ≥ SOM нарушено');
  }
  if (core && !vc) issues.push('Core Services заполнены, а Value Capture пуст — проверьте согласованность');
  if (issues.length===0) return null;
  return (
    <div className="p-2 bg-yellow-50 text-yellow-800 border border-yellow-200 rounded">
      {issues.map((s,i)=>(<div key={i}>• {s}</div>))}
    </div>
  );
}

