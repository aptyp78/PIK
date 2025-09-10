"use client";
import { useState } from 'react';

export default function DocClient({ docId, blockCount, pages }: { docId: number; blockCount: number; pages?: number }) {
  const [report, setReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  return (
    <div className="flex flex-col gap-4 mb-6 text-sm">
      <div className="flex items-center gap-4">
        <span className="px-2 py-1 bg-gray-100 rounded">Pages: {pages ?? 'unknown'}</span>
        <span className="px-2 py-1 bg-gray-100 rounded">Blocks: {blockCount}</span>
        <button
          onClick={async () => {
            try {
              setLoading(true);
              const res = await fetch(`/api/ingest/${docId}/report`, { cache: 'no-store' });
              if (res.ok) {
                const json = await res.json();
                setReport(json);
              } else {
                setReport({ error: `Failed to load report: ${res.status}` });
              }
            } finally {
              setLoading(false);
            }
          }}
          className="px-3 py-1 border rounded bg-white"
          disabled={loading}
        >
          {loading ? 'Reporting…' : 'Report'}
        </button>
      </div>
      {report && (
        <div className="border rounded p-3 text-sm">
          {report.error ? (
            <div className="text-red-600">{report.error}</div>
          ) : (
            <ul className="list-disc pl-5 space-y-0.5">
              <li>Total blocks: {report.totalBlocks}</li>
              <li>Tables: {report.tables}</li>
              <li>Empty text blocks: {report.emptyTextBlocks}</li>
              <li>Empty pages: {Array.isArray(report.emptyPages) && report.emptyPages.length > 0 ? report.emptyPages.join(', ') : 'none'}</li>
              <li>By role: {report.byRole ? Object.entries(report.byRole).map(([k, v]) => `${k}:${v}`).join(', ') : '—'}</li>
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
