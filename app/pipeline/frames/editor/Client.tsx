"use client";
import { useEffect, useMemo, useRef, useState } from 'react';

type Zone = { id: string; title?: string; box: [number,number,number,number] };

export default function TemplateEditorClient({ name, templateId }: { name: string; templateId: string }) {
  const [tpl, setTpl] = useState<{ id:string; title?:string; version?:string; zones: Zone[] }|null>(null);
  const [err, setErr] = useState<string|null>(null);
  const canvasRef = useRef<HTMLCanvasElement|null>(null);
  const [dims, setDims] = useState<{ w:number; h:number }>({ w: 1200, h: 800 });

  useEffect(() => { (async () => {
    try {
      const r = await fetch(`/api/mapping/template?id=${encodeURIComponent(templateId)}`, { cache: 'no-store' });
      const j = await r.json(); if (!j?.ok) throw new Error(j?.error||'failed');
      setTpl(j.template);
    } catch (e:any) { setErr(e?.message||'failed'); }
  })(); }, [templateId]);

  function redraw() {
    const c = canvasRef.current; if (!c || !tpl) return;
    const ctx = c.getContext('2d'); if (!ctx) return;
    const cw = c.width, ch = c.height;
    ctx.clearRect(0,0,cw,ch);
    ctx.fillStyle = '#f8fafc'; ctx.fillRect(0,0,cw,ch);
    ctx.fillStyle = '#111827'; ctx.font = 'bold 14px system-ui';
    ctx.fillText(`${tpl.id}${tpl.version?(' v'+tpl.version):''}`, 10, 20);
    const cols = ['#ff3b30','#ff9500','#ffcc00','#34c759','#0a84ff','#5e5ce6','#bf5af2','#ff375f','#64d2ff','#ffd60a'];
    tpl.zones.forEach((z, i) => {
      const [x1,y1,x2,y2] = z.box; const col = cols[i%cols.length];
      const x = x1*cw, y = Math.max(0, ch - y2*ch); const w = Math.max(0,(x2-x1)*cw), h = Math.max(0,(y2-y1)*ch);
      ctx.fillStyle = col+'20'; ctx.fillRect(x,y,w,h);
      ctx.strokeStyle = col; ctx.setLineDash([6,4]); ctx.lineWidth = 2; ctx.strokeRect(x,y,w,h); ctx.setLineDash([]);
      ctx.fillStyle = '#111827'; ctx.font = '12px system-ui'; ctx.fillText(z.title||z.id, x+6, y+16);
    });
  }

  useEffect(() => { redraw(); }, [tpl, dims]);

  function updateZone(idx: number, field: keyof Zone| 'boxAt', value: any) {
    setTpl(t => {
      if (!t) return t; const zones = [...t.zones];
      if (field === 'boxAt') {
        const [k,v] = value as [number, number]; const b = [...zones[idx].box] as [number,number,number,number];
        b[k] = Math.min(1, Math.max(0, v)); zones[idx] = { ...zones[idx], box: b };
      } else { zones[idx] = { ...zones[idx], [field]: value } as any; }
      return { ...t, zones };
    });
  }

  async function save() {
    try {
      const r = await fetch(`/api/mapping/template?id=${encodeURIComponent(templateId)}`, { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ template: tpl }) });
      const j = await r.json(); if (!j?.ok) throw new Error(j?.error||'save failed');
      alert('Сохранено');
    } catch (e:any) { alert(e?.message||'failed'); }
  }

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div className="xl:col-span-2 border rounded p-3">
        <div className="font-semibold mb-2">Шаблон: {tpl?.id||templateId}</div>
        <canvas ref={canvasRef} width={dims.w} height={dims.h} className="border rounded w-full h-auto" />
      </div>
      <div className="border rounded p-3 text-sm">
        <div className="font-semibold mb-2">Зоны</div>
        {!tpl ? (<div className="text-gray-600">{err || 'Загрузка…'}</div>) : (
          <div className="space-y-3">
            {tpl.zones.map((z, i) => (
              <div key={i} className="border rounded p-2">
                <div className="font-medium mb-1">{z.id}</div>
                <label className="block mb-1">Title <input className="border rounded px-2 py-1 w-full" value={z.title||''} onChange={e=>updateZone(i,'title', e.target.value)} /></label>
                <div className="grid grid-cols-4 gap-2">
                  {(['x1','y1','x2','y2'] as const).map((k, kidx) => (
                    <label key={k} className="text-xs">{k}<input type="number" step="0.01" min={0} max={1} className="border rounded px-1 py-0.5 w-full" value={z.box[kidx]} onChange={e=>updateZone(i,'boxAt',[kidx, parseFloat(e.target.value)||0])} /></label>
                  ))}
                </div>
              </div>
            ))}
            <div className="flex gap-2">
              <button className="px-3 py-1 border rounded" onClick={save}>Сохранить</button>
              <a className="px-3 py-1 border rounded" href={`/api/mapping/template?id=${encodeURIComponent(templateId)}`} target="_blank">JSON</a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

