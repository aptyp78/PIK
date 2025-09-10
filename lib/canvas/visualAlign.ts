import fs from 'fs/promises';
import { CanvasTransform, fitToCanonical } from './transform';

export type VisualAlignResult = {
  profileId: string;
  transform: CanvasTransform;
  matchScore: number; // 0..1
  pageWidth: number;
  pageHeight: number;
};

export async function visualAlignFirstPage(pdfPath: string): Promise<VisualAlignResult> {
  // Minimal implementation: read PDF dims via pdfjs-dist and compute fit transform.
  // pHash/template matching can be added; for now return a reasonable default.
  const { getDocument } = await import('pdfjs-dist');
  const data = new Uint8Array(await fs.readFile(pdfPath));
  const loadingTask = getDocument({ data });
  const pdf = await loadingTask.promise;
  const page = await pdf.getPage(1);
  const viewport = page.getViewport({ scale: 1.0 });
  const pageWidth = viewport.width;
  const pageHeight = viewport.height;

  // Use canonical profile PIK_BusinessModel_v5
  const canonicalW = 1000; const canonicalH = 1400;
  const transform = fitToCanonical(pageWidth, pageHeight, canonicalW, canonicalH);
  const matchScore = 0.7; // placeholder score
  return { profileId: 'PIK_BusinessModel_v5', transform, matchScore, pageWidth, pageHeight };
}

export default visualAlignFirstPage;

