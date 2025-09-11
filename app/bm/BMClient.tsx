"use client";
import { useEffect, useMemo, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
// @ts-ignore
(pdfjsLib as any).GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${(pdfjsLib as any).version}/build/pdf.worker.min.mjs`;
import profile from '@/lib/canvas/profiles/PIK_BusinessModel_v5.json';

type Zone = { id: number; key: string; name: string; status: string; text?: string|null; confidence: number; owner?: string|null; tags?: string|null };

function BMHints({ zones }: { zones: Zone[] }) {
  function getNum(key: string): number | null {
    const z = zones.find(x => x.key === key);
    if (!z || !z.text) return null;
    const m = String(z.text).match(/\d+(?:[\.,]\d+)?/);
    return m ? Number(m[0].replace(',', '.')) : null;
  }
  const tam = getNum('tam');
  const sam = getNum('sam');
  const som = getNum('som');
  const core = zones.find(z => z.key==='core-services')?.text?.trim();
  const vc = zones.find(z => z.key==='value-capture')?.text?.trim();
  const issues: string[] = [];
  if (tam!=null && sam!=null && som!=null) { if (!(tam>=sam && sam>=som)) issues.push('TAM ≥ SAM ≥ SOM нарушено'); }
  if (core && !vc) issues.push('Core Services заполнены, а Value Capture пуст — проверьте согласованность');
  if (issues.length===0) return null;
  return (<div className="p-2 bg-yellow-50 text-yellow-800 border border-yellow-200 rounded">{issues.map((s,i)=>(<div key={i}>• {s}</div>))}</div>);
}

export default function BMClient() {
  const [init, setInit] = useState<any>(null);
  const [zones, setZones] = useState<Zone[]>([]);
  const [active, setActive] = useState<Zone | null>(null);
  const [transform, setTransform] = useState({ scaleX:1, scaleY:1, offsetX:0, offsetY:0, flipY:true });
  const [drawing, setDrawing] = useState(false);
  const [evidenceRect, setEvidenceRect] = useState<{x:number;y:number;w:number;h:number}|null>(null);
  const [qdrantItems, setQdrantItems] = useState<{ id: string|number; payload: any }[] | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const [pageSize, setPageSize] = useState<{ width: number; height: number } | null>(null);
  const [runJobId, setRunJobId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<string | null>(null);
  const [bmBlocks, setBmBlocks] = useState<{ id: string|number; page: number; bbox: { x:number;y:number;w:number;h:number }; text?: string; zone?: string|null }[]>([]);
  const [loadingBlocks, setLoadingBlocks] = useState(false);

  useEffect(() => {
    const renderTaskRef: { current: any } = { current: null };
    let cancelled = false;
    (async () => {
      const res = await fetch('/api/bm/init');
      const json = await res.json();
      setInit(json);
      if (json?.canvasTransform) { try { setTransform(JSON.parse(json.canvasTransform)); } catch {} }
      if (json?.zones) setZones(json.zones);
      if (json?.path && canvasRef.current) {
        const path = json.path as string;
        if (path.toLowerCase().endsWith('.pdf')) {
          const data = await fetch('/api/docs/'+json.docId+'/pdf').then(r=>r.arrayBuffer());
          const pdf = await pdfjsLib.getDocument({ data }).promise; const page = await pdf.getPage(1);
          const viewport = page.getViewport({ scale: 1.5 }); const canvas = canvasRef.current!; const ctx = canvas.getContext('2d')!;
          canvas.width = viewport.width; canvas.height = viewport.height; setPageSize({ width: viewport.width, height: viewport.height });
          try { renderTaskRef.current?.cancel?.(); } catch {}
          const task = page.render({ canvasContext: ctx, viewport }); renderTaskRef.current = task; try { await task.promise; } catch {}
          if (cancelled) return;
        } else {
          const img = new Image(); img.onload = ()=>{ const c=canvasRef.current!; const ctx=c.getContext('2d')!; c.width=img.width; c.height=img.height; setPageSize({ width: img.width, height: img.height }); ctx.drawImage(img,0,0); }; img.src = path;
        }
      }
    })();
    return () => { cancelled = true; try { renderTaskRef.current?.cancel?.(); } catch {} };
  }, []);

  async function saveZone(active: Zone) {
    const res = await fetch('/api/bm/zones', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ id: active.id, status: active.status, text: active.text, confidence: active.confidence, owner: active.owner, tags: active.tags }) });
    if (res.ok) { const j=await res.json(); setZones(zs=>zs.map(z=>z.id===active.id? j.zone : z)); }
  }

  const missing = init && init.ok === false;
  const docId = init?.docId;

  async function refreshBlocks() {
    if (!docId) return;
    setLoadingBlocks(true);
    try {
      const res = await fetch(`/api/bm/blocks?docId=${encodeURIComponent(String(docId))}`, { cache: 'no-store' });
      const j = await res.json();
      if (j?.ok) setBmBlocks(j.items || []);
    } finally {
      setLoadingBlocks(false);
    }
  }

  async function runIngestion() {
    setRunStatus('starting');
    try {
      const res = await fetch('/api/ingest/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
      const j = await res.json();
      if (!j?.ok) throw new Error(j?.error || 'Failed to start');
      setRunJobId(j.jobId);
      setRunStatus('queued');
      let attempts = 0;
      const poll = async () => {
        if (!j.jobId) return;
        const sres = await fetch(`/api/ingest/status?jobId=${encodeURIComponent(j.jobId)}${j.workflowId ? `&workflowId=${encodeURIComponent(j.workflowId)}`:''}`, { cache: 'no-store' });
        const sj = await sres.json();
        const st = String(sj?.status || 'unknown');
        setRunStatus(st);
        if (/finished|succeeded|done/i.test(st)) { await refreshBlocks(); return; }
        if (/failed|error/i.test(st)) return;
        attempts += 1; setTimeout(poll, Math.min(5000, 1000 + attempts * 500));
      };
      poll();
    } catch {
      setRunStatus('error');
    }
  }

  useEffect(() => { if (docId) refreshBlocks(); }, [docId]);

  return (
    <main className="max-w-7xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-3">Platform Business Model</h1>
      {missing ? (
        <div className="p-4 border rounded bg-yellow-50 text-yellow-900">Положите файл <code>data/uploads/PIK-Platform-Business-Model.pdf</code> (или .png) и обновите страницу.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <div className="mb-2 flex gap-2 items-center text-sm">
              <button className="px-3 py-1 border rounded" onClick={runIngestion} disabled={!!runJobId && runStatus!==null && !/error|finished|succeeded|done/i.test(runStatus||'')}>
                {runStatus && !/error|finished|succeeded|done/i.test(runStatus) ? `Running: ${runStatus}` : 'Run'}
              </button>
              <button className="px-3 py-1 border rounded" onClick={refreshBlocks} disabled={loadingBlocks}>{loadingBlocks ? 'Refreshing…' : 'Reload Blocks'}</button>
            </div>
            <div className="mb-2 flex gap-2 items-center text-sm">
              <label>scale <input type="number" step="0.1" value={transform.scaleX} onChange={(e)=>setTransform(t=>({ ...t, scaleX:+e.target.value||1, scaleY:+e.target.value||1 }))} className="border rounded px-2 py-1 w-24 ml-1" /></label>
              <label>offsetX <input type="number" value={transform.offsetX} onChange={(e)=>setTransform(t=>({ ...t, offsetX:+e.target.value||0 }))} className="border rounded px-2 py-1 w-24 ml-1" /></label>
              <label>offsetY <input type="number" value={transform.offsetY} onChange={(e)=>setTransform(t=>({ ...t, offsetY:+e.target.value||0 }))} className="border rounded px-2 py-1 w-24 ml-1" /></label>
              <label className="flex items-center gap-1"><input type="checkbox" checked={!!transform.flipY} onChange={(e)=>setTransform(t=>({ ...t, flipY:e.target.checked }))}/> flipY</label>
              <button className="px-3 py-1 border rounded" onClick={async()=>{ await fetch('/api/bm/calibration',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ docId, canvasTransform: transform })});}}>Save overlay</button>
              <a className="px-3 py-1 border rounded" href="/bm/export">Экспорт</a>
              <button className={`px-3 py-1 border rounded ${drawing? 'bg-green-600 text-white':''}`} onClick={()=>setDrawing(d=>!d)}>Evidence</button>
            </div>
            <div className="relative inline-block border rounded">
              <canvas ref={canvasRef} onMouseDown={(e)=>{ if(!drawing)return; const r=(e.target as HTMLCanvasElement).getBoundingClientRect(); setEvidenceRect({ x:e.clientX-r.left, y:e.clientY-r.top, w:0, h:0 }); }} onMouseMove={(e)=>{ if(!drawing||!evidenceRect)return; const r=(e.target as HTMLCanvasElement).getBoundingClientRect(); setEvidenceRect({ ...evidenceRect, w:e.clientX-r.left-evidenceRect.x, h:e.clientY-r.top-evidenceRect.y }); }} onMouseUp={async()=>{ if(!drawing||!evidenceRect||!active)return; setDrawing(false); await fetch('/api/bm/evidence',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ zoneId: active.id, rect: { page:1, ...evidenceRect } })}); setEvidenceRect(null); }} />
              {pageSize && (
                <div ref={overlayRef} className="absolute left-0 top-0 pointer-events-none" style={{ width: pageSize.width, height: pageSize.height }}>
                  {bmBlocks.filter(b => (b.page ?? 0) === 0).map(b => {
                    const cw = pageSize.width, ch = pageSize.height;
                    // @ts-ignore
                    const pw = (profile as any).canonical?.width || cw; // fallback
                    // @ts-ignore
                    const ph = (profile as any).canonical?.height || ch;
                    const sx = pw ? cw / pw : 1, sy = ph ? ch / ph : 1;
                    const x = b.bbox.x * sx, y = b.bbox.y * sy, w = b.bbox.w * sx, h = b.bbox.h * sy;
                    return <div key={String(b.id)} title={b.zone || ''} style={{ position: 'absolute', left: x, top: y, width: w, height: h, border: '2px solid rgba(0,153,255,0.7)', background: 'rgba(0,153,255,0.12)' }} />
                  })}
                </div>
              )}
              {evidenceRect && (<div className="absolute border-2 border-red-500" style={{ left: evidenceRect.x, top: evidenceRect.y, width: evidenceRect.w, height: evidenceRect.h }} />)}
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
                  <textarea className="w-full border rounded p-2" rows={6} value={active.text||''} onChange={(e)=>setActive({ ...active, text: e.target.value })} />
                </label>
                <div className="flex gap-2 items-center">
                  <label>Статус
                    <select className="border rounded px-2 py-1 ml-1" value={active.status} onChange={(e)=>setActive({ ...active, status: e.target.value })}>
                      {['Empty','Draft','Proposed','Approved','To review'].map(s => (<option key={s} value={s}>{s}</option>))}
                    </select>
                  </label>
                  <label>Уверенность <input type="number" min={0} max={100} className="border rounded px-2 py-1 ml-1 w-20" value={active.confidence} onChange={(e)=>setActive({ ...active, confidence: +e.target.value||0 })} /></label>
                </div>
                <label className="block">Ответственный <input className="w-full border rounded px-2 py-1" value={active.owner||''} onChange={(e)=>setActive({ ...active, owner: e.target.value })} /></label>
                <label className="block">Метки <input className="w-full border rounded px-2 py-1" value={active.tags||''} onChange={(e)=>setActive({ ...active, tags: e.target.value })} /></label>
                <BMHints zones={zones} />
                <div className="flex gap-2">
                  <button className="px-3 py-1 border rounded" onClick={()=>active && saveZone(active)}>Сохранить</button>
                  <button className="px-3 py-1 border rounded" onClick={()=>active && (setActive({ ...active, status:'Approved' }), saveZone({ ...active, status:'Approved' }))}>Принять черновик</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      <div className="mt-4 border rounded p-3 text-sm">
        <div className="font-semibold mb-2">Qdrant preview</div>
        <div className="flex gap-2 mb-2">
          <button className="px-3 py-1 border rounded" onClick={async()=>{ try{ const res=await fetch('/api/qdrant/sample?limit=10'); const j=await res.json(); setQdrantItems(j?.ok? j.items||[]: []);}catch{ setQdrantItems([]);} }}>Load 10</button>
        </div>
        {qdrantItems && (<ul className="space-y-1 max-h-60 overflow-auto">{qdrantItems.map((it,i)=>(<li key={i} className="border rounded px-2 py-1"><div className="text-xs text-gray-500">id: {String(it.id)}</div><div className="text-xs whitespace-nowrap overflow-hidden text-ellipsis">{JSON.stringify(it.payload).slice(0,160)}</div></li>))}</ul>)}
      </div>
    </main>
  );
}
