"use client";
import { useState } from 'react';

type Res = { ok?: boolean; [k: string]: any } | null;

export default function MenuClient() {
  const [job, setJob] = useState<{ id?: string; status?: string } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [out, setOut] = useState<Res>(null);
  const [fileId, setFileId] = useState<string>("");
  const [filename, setFilename] = useState<string>("");

  async function runIngest() {
    setBusy('ingest'); setOut(null);
    try {
      const r = await fetch('/api/ingest/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
      const j = await r.json(); setOut(j);
      if (j?.jobId) {
        setJob({ id: j.jobId, status: 'scheduled' });
        // poll
        let attempts = 0;
        const poll = async () => {
          if (!j.jobId) return;
          const s = await fetch(`/api/ingest/status?jobId=${encodeURIComponent(j.jobId)}`, { cache: 'no-store' });
          const sj = await s.json(); setOut((prev: any)=>({ ...prev, status: sj?.status, finishedAt: sj?.finishedAt }));
          setJob({ id: j.jobId, status: sj?.status });
          attempts++;
          if (/finished|completed|succeeded|done|failed|error/i.test(String(sj?.status||''))) { setBusy(null); return; }
          if (attempts < 60) setTimeout(poll, 2000);
          else setBusy(null);
        };
        poll();
      } else { setBusy(null); }
    } catch (e) { setBusy(null); setOut({ ok:false, error: (e as any)?.message || 'run failed' }); }
  }

  async function createIndexes() {
    setBusy('indexes'); setOut(null);
    try { const r=await fetch('/api/qdrant/indexes', { method:'POST' }); const j=await r.json(); setOut(j); } finally { setBusy(null); }
  }

  async function annotateAll() {
    setBusy('annotate-all'); setOut(null);
    try {
      const r = await fetch('/api/pipeline/gdrive/annotate-all?recursive=1&limit=500', { method: 'POST' });
      const j = await r.json(); setOut(j);
    } finally { setBusy(null); }
  }

  async function clearAdobe() {
    setBusy('clear-adobe'); setOut(null);
    try { const r=await fetch('/api/pipeline/gdrive/adobe/clear', { method:'POST' }); const j=await r.json(); setOut(j);} finally { setBusy(null); }
  }

  async function runAdobe() {
    setBusy('adobe-run'); setOut(null);
    try { const r=await fetch('/api/pipeline/gdrive/adobe/run', { method:'POST' }); const j=await r.json(); setOut(j);} finally { setBusy(null); }
  }

  async function annotateOne() {
    setBusy('annotate-one'); setOut(null);
    try {
      const qs = new URLSearchParams();
      if (fileId) qs.set('fileId', fileId);
      if (filename) qs.set('filename', filename);
      qs.set('limit','500');
      const r = await fetch(`/api/pipeline/qdrant/annotate?${qs.toString()}`, { method: 'POST' });
      const j = await r.json(); setOut(j);
    } finally { setBusy(null); }
  }

  async function sampleQdrant() {
    setBusy('sample'); setOut(null);
    try { const r=await fetch('/api/qdrant/sample?limit=10',{ cache:'no-store'}); const j=await r.json(); setOut(j); } finally { setBusy(null); }
  }

  async function bmBlocks() {
    setBusy('blocks'); setOut(null);
    try { const r=await fetch('/api/bm/blocks?limit=50',{ cache:'no-store'}); const j=await r.json(); setOut(j); } finally { setBusy(null); }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <a className="px-4 py-3 border rounded hover:bg-gray-50" href="/results">Open Results</a>
        <button className="px-4 py-3 border rounded" onClick={runIngest} disabled={!!busy}>Run Platform Workflow {busy==='ingest' && '…'}</button>
        <button className="px-4 py-3 border rounded" onClick={createIndexes} disabled={!!busy}>Create Qdrant Indexes {busy==='indexes' && '…'}</button>
        <button className="px-4 py-3 border rounded" onClick={annotateAll} disabled={!!busy}>Annotate All (Drive→Qdrant bbox) {busy==='annotate-all' && '…'}</button>
        <button className="px-4 py-3 border rounded" onClick={clearAdobe} disabled={!!busy}>Adobe: Clear folder {busy==='clear-adobe' && '…'}</button>
        <button className="px-4 py-3 border rounded" onClick={runAdobe} disabled={!!busy}>Adobe: Parse Drive → Adobe {busy==='adobe-run' && '…'}</button>
        <a className="px-4 py-3 border rounded hover:bg-gray-50" href="/pipeline/adobe">Adobe Results</a>
        <a className="px-4 py-3 border rounded hover:bg-gray-50" href="/pipeline/final">Final Sample</a>
      </div>
      <div className="border rounded p-3">
        <div className="font-medium mb-2">Annotate One</div>
        <div className="flex flex-col md:flex-row gap-2 mb-2">
          <input value={fileId} onChange={e=>setFileId(e.target.value)} placeholder="Drive fileId" className="border rounded px-2 py-1 flex-1" />
          <input value={filename} onChange={e=>setFilename(e.target.value)} placeholder="Filename (optional)" className="border rounded px-2 py-1 flex-1" />
          <button className="px-3 py-1 border rounded" onClick={annotateOne} disabled={!!busy}>Annotate {busy==='annotate-one' && '…'}</button>
        </div>
        <div className="text-xs text-gray-500">Укажите только fileId (или только filename). По возможности используется скачивание из Drive.</div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <button className="px-4 py-3 border rounded" onClick={sampleQdrant} disabled={!!busy}>Qdrant Sample {busy==='sample' && '…'}</button>
        <button className="px-4 py-3 border rounded" onClick={bmBlocks} disabled={!!busy}>Preview BM Blocks {busy==='blocks' && '…'}</button>
      </div>
      {job?.id && (
        <div className="text-sm">Job: <span className="font-mono">{job.id}</span> · Status: {job.status || '—'}</div>
      )}
      <div className="border rounded p-3 bg-gray-50 text-sm overflow-auto max-h-96">
        <div className="font-medium mb-1">Output</div>
        <pre className="whitespace-pre-wrap break-all">{out ? JSON.stringify(out, null, 2) : '—'}</pre>
      </div>
    </div>
  );
}
