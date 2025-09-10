export type CanvasTransform = {
  scaleX: number;
  scaleY: number;
  offsetX: number;
  offsetY: number;
  rotation?: number;
  flipY?: boolean;
};

export function fitToCanonical(pageWidth: number, pageHeight: number, canonicalW: number, canonicalH: number): CanvasTransform {
  const sx = canonicalW / pageWidth;
  const sy = canonicalH / pageHeight;
  const k = Math.min(sx, sy);
  return { scaleX: k, scaleY: k, offsetX: 0, offsetY: 0, rotation: 0, flipY: true };
}

export function applyTransformBBox(bbox: [number, number, number, number], t: CanvasTransform, pageH?: number): [number, number, number, number] {
  let [x0, y0, x1, y1] = bbox;
  if (t.flipY && typeof pageH === 'number') {
    const ny0 = pageH - y1;
    const ny1 = pageH - y0;
    y0 = ny0; y1 = ny1;
  }
  const ax0 = x0 * t.scaleX + (t.offsetX || 0);
  const ay0 = y0 * t.scaleY + (t.offsetY || 0);
  const ax1 = x1 * t.scaleX + (t.offsetX || 0);
  const ay1 = y1 * t.scaleY + (t.offsetY || 0);
  return [ax0, ay0, ax1, ay1];
}

export function pointInPolygon(pt: [number, number], poly: [number, number][]): boolean {
  // Ray-casting algorithm
  const [x, y] = pt;
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const xi = poly[i][0], yi = poly[i][1];
    const xj = poly[j][0], yj = poly[j][1];
    const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / ((yj - yi) || 1e-9) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
}

