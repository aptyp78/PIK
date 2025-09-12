"use client";
import { useEffect, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
// @ts-ignore worker from CDN
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://unpkg.com/pdfjs-dist@4.7.76/build/pdf.worker.min.mjs';
import { useRouter } from 'next/navigation';

type StepItem = { name: string; status: 'idle'|'running'|'ok'|'err'; info?: string };

const INITIAL_STEPS: StepItem[] = [
  { name: 'Upload File', status: 'idle' },
  { name: 'Extract', status: 'idle' },
  { name: 'Parse', status: 'idle' },
  { name: 'Insert', status: 'idle' },
  { name: 'Recalc Pages', status: 'idle' },
];

export default function UploadPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [engine, setEngine] = useState<string>(process.env.NEXT_PUBLIC_INGEST_ENGINE_DEFAULT || 'unstructured');
  const [steps, setSteps] = useState<StepItem[]>(INITIAL_STEPS);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  // Visual preview only (no BM alignment)

  async function renderPreview(f: File) {
    try {
      const canvas = canvasRef.current; if (!canvas) return;
      const ctx = canvas.getContext('2d'); if (!ctx) return;
      if (f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf')) {
        const ab = await f.arrayBuffer();
        // @ts-ignore
        const pdf = await pdfjsLib.getDocument({ data: ab }).promise;
        const page = await pdf.getPage(1);
        const viewport = page.getViewport({ scale: 1.5 });
        canvas.width = viewport.width; canvas.height = viewport.height;
        // @ts-ignore
        await page.render({ canvasContext: ctx, viewport }).promise;
      } else {
        // PNG/JPG preview
        const img = new Image();
        img.onload = () => {
          canvas.width = img.width; canvas.height = img.height;
          ctx.drawImage(img, 0, 0);
        };
        img.src = URL.createObjectURL(f);
      }
    } catch {}
  }

  function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] || null;
    setFile(f);
    if (f) renderPreview(f);
  }

  function onDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  }

  function onDragOver(e: React.DragEvent<HTMLDivElement>) { e.preventDefault(); }

  async function start() {
    if (!file) return;
    setBusy(true); setError(null);
    setSteps(s => s.map((it, i) => ({ ...it, status: i === 0 ? 'running' : 'idle' })));
    try {
      // Single-call API; UI simulates step progression while waiting
      const fd = new FormData();
      fd.set('file', file);
      fd.set('engine', engine);
      const res = await fetch('/api/ingest/upload', { method: 'POST', body: fd });
      if (!res.ok) {
        const t = await res.text().catch(()=> '');
        throw new Error(`HTTP ${res.status} ${t.slice(0,120)}`);
      }
      const json = await res.json();
      // Mark all steps green on success
      setSteps(s => s.map(it => ({ ...it, status: 'ok' })));
      // Route depends on engine
      if (engine === 'adobe') {
        // Show a toast-like inline message; do not redirect
        setError(null);
      } else {
        const id = json.docId as number;
        setTimeout(() => router.push(`/docs/${id}`), 600);
      }
    } catch (e: any) {
      setSteps(s => s.map(it => ({ ...it, status: it.status === 'running' ? 'err' : it.status })));
      setError(e?.message || 'Upload failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="max-w-3xl mx-auto py-8 space-y-6">
      <h1 className="text-3xl font-bold">Upload</h1>
      <div
        className="border-2 border-dashed rounded p-8 text-center bg-gray-50"
        onDrop={onDrop}
        onDragOver={onDragOver}
        onClick={(e) => {
          // Открываем диалог только при клике по самой зоне, не по дочерним элементам
          if (e.currentTarget === e.target) inputRef.current?.click();
        }}
      >
        <div className="mb-3">Перетащите PDF/PNG сюда или выберите файл</div>
        <div className="mb-2">
          <label
            htmlFor="file-input"
            className="px-4 py-2 border rounded bg-white cursor-pointer inline-block"
            onClick={(e) => e.stopPropagation()} // не пузырить, чтобы не кликалась зона второй раз
          >
            Выбрать файл
          </label>
          <input id="file-input" ref={inputRef} type="file" accept=".pdf,.png" className="hidden" onChange={onPick} />
        </div>
        <div className="text-sm text-gray-600">{file ? `${file.name} (${Math.round((file.size||0)/1024)} KB)` : 'Файл не выбран'}</div>
      </div>
      <div className="flex items-center gap-3">
        <label className="text-sm">Движок:</label>
        <label className="text-sm flex items-center gap-1" onClick={(e)=>e.stopPropagation()}>
          <input type="radio" name="engine" checked={engine==='unstructured'} onChange={()=>setEngine('unstructured')} /> Unstructured
        </label>
        <label className="text-sm flex items-center gap-1" onClick={(e)=>e.stopPropagation()}>
          <input type="radio" name="engine" checked={engine==='adobe'} onChange={()=>setEngine('adobe')} /> Adobe
        </label>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="border rounded p-3">
          <div className="font-semibold mb-2">Preview</div>
          <canvas ref={canvasRef} className="border rounded" />
        </div>
        <div className="border rounded p-3 text-sm">
          <div className="font-semibold mb-2">Статус</div>
          <div className="text-gray-600">{busy ? 'Загрузка…' : (file ? 'Готово к загрузке' : 'Файл не выбран')}</div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button className="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50" onClick={start} disabled={!file || busy}>Загрузить</button>
        {error && <div className="text-red-700 text-sm">{error}</div>}
        {!error && steps.every(s=>s.status==='ok') && engine==='adobe' && (
          <div className="text-sm text-green-700">Готово: результаты Adobe сохранены в GCS (Adobe_Destination)</div>
        )}
      </div>
      <div>
        <div className="font-semibold mb-2">Статус</div>
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {steps.map((s, i) => (
            <li key={i} className={`px-3 py-2 rounded border text-sm ${s.status==='ok' ? 'bg-green-50 border-green-300' : s.status==='err' ? 'bg-red-50 border-red-300' : s.status==='running' ? 'bg-yellow-50 border-yellow-300' : 'bg-white'}`}>
              <span className="font-medium mr-2">{s.name}</span>
              <span className="text-gray-500">{s.status}</span>
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}
