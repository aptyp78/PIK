import { getAccessToken } from './drive';

function getEnv() {
  const bucket = process.env.GCS_SOURCE_BUCKET || process.env.GCS_ADOBE_BUCKET;
  if (!bucket) throw new Error('GCS bucket is not configured (GCS_SOURCE_BUCKET)');
  return { bucket };
}

export async function uploadObject(
  bucket: string,
  objectName: string,
  contentType: string,
  data: Uint8Array | Buffer
) {
  const token = await getAccessToken('https://www.googleapis.com/auth/devstorage.read_write');
  const url = `https://storage.googleapis.com/upload/storage/v1/b/${encodeURIComponent(bucket)}/o?uploadType=media&name=${encodeURIComponent(objectName)}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': contentType },
    body: data,
  });
  if (!res.ok) {
    const t = await res.text().catch(() => '');
    throw new Error(`GCS upload error ${res.status}: ${t.slice(0, 200)}`);
  }
  return res.json();
}

export async function simpleUpload(objectName: string, content: string | Uint8Array, contentType = 'application/octet-stream', bucket?: string) {
  const bkt = bucket || getEnv().bucket;
  const data = typeof content === 'string' ? new TextEncoder().encode(content) : content;
  return uploadObject(bkt, objectName, contentType, data);
}

export default { uploadObject, simpleUpload };

