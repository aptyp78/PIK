// Minimal GCS helper: upload JSON and list objects under a prefix
import path from 'path';

export async function getStorage() {
  const { Storage } = await import('@google-cloud/storage');
  const keyFile = process.env.GCS_SA_KEY_FILE || process.env.GDRIVE_SA_PRIVATE_KEY || '';
  const opts: any = {};
  if (keyFile) opts.keyFilename = path.resolve(keyFile);
  return new Storage(opts);
}

export async function uploadJson(bucket: string, objectName: string, json: any) {
  const storage = await getStorage();
  const bucketRef = storage.bucket(bucket);
  const file = bucketRef.file(objectName);
  const buf = Buffer.from(typeof json === 'string' ? json : JSON.stringify(json));
  await file.save(buf, { contentType: 'application/json', resumable: false, validation: false });
  return `gs://${bucket}/${objectName}`;
}

export async function listPrefix(bucket: string, prefix: string, maxResults = 200) {
  const storage = await getStorage();
  const [files] = await storage.bucket(bucket).getFiles({ prefix, maxResults, autoPaginate: false });
  return files.map((f: any) => ({ name: f.name, size: Number(f.metadata?.size || 0), updated: f.metadata?.updated || f.metadata?.timeCreated }));
}

export async function downloadText(bucket: string, objectName: string): Promise<string> {
  const storage = await getStorage();
  const file = storage.bucket(bucket).file(objectName);
  const [exists] = await file.exists();
  if (!exists) throw new Error('Object not found');
  const [buf] = await file.download();
  return buf.toString('utf8');
}

export async function downloadBuffer(bucket: string, objectName: string): Promise<Buffer> {
  const storage = await getStorage();
  const file = storage.bucket(bucket).file(objectName);
  const [exists] = await file.exists();
  if (!exists) throw new Error('Object not found');
  const [buf] = await file.download();
  return Buffer.from(buf);
}

export default { getStorage, uploadJson, listPrefix };
