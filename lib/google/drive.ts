import crypto from 'crypto';
import fs from 'fs/promises';
import os from 'os';
import path from 'path';

type SAConfig = {
  client_email: string;
  private_key: string;
  token_uri?: string;
};

function getServiceAccount(): SAConfig {
  const emailEnv = process.env.GDRIVE_SA_EMAIL || '';
  const keyFile = process.env.GDRIVE_SA_KEY_FILE || '';
  let pkRaw = process.env.GDRIVE_SA_PRIVATE_KEY || '';
  // Prefer JSON from file
  if (keyFile) {
    try {
      const txt = require('fs').readFileSync(keyFile, 'utf8');
      const j = JSON.parse(txt);
      return { client_email: j.client_email, private_key: j.private_key, token_uri: j.token_uri || 'https://oauth2.googleapis.com/token' };
    } catch {}
  }
  // If env var contains a path to JSON, accept it as well
  if (pkRaw && /\.json$/i.test(pkRaw)) {
    try {
      const txt = require('fs').readFileSync(pkRaw, 'utf8');
      const j = JSON.parse(txt);
      return { client_email: j.client_email, private_key: j.private_key, token_uri: j.token_uri || 'https://oauth2.googleapis.com/token' };
    } catch {}
  }
  if (!emailEnv && !pkRaw) throw new Error('GDrive SA not configured');
  const trimmed = pkRaw.trim();
  // Full JSON in env
  if (trimmed.startsWith('{')) {
    try {
      const json = JSON.parse(trimmed);
      return { client_email: json.client_email || emailEnv, private_key: json.private_key, token_uri: json.token_uri || 'https://oauth2.googleapis.com/token' } as SAConfig;
    } catch {}
  }
  // Base64 JSON in env
  const b64 = process.env.GDRIVE_SA_JSON_B64 || '';
  if (b64) {
    try {
      const json = JSON.parse(Buffer.from(b64, 'base64').toString('utf8'));
      return { client_email: json.client_email || emailEnv, private_key: json.private_key, token_uri: json.token_uri || 'https://oauth2.googleapis.com/token' } as SAConfig;
    } catch {}
  }
  // PEM in env
  const pk = pkRaw.replace(/\\n/g, '\n');
  return { client_email: emailEnv, private_key: pk, token_uri: 'https://oauth2.googleapis.com/token' };
}

function b64url(input: Buffer | string) {
  const s = (input instanceof Buffer ? input : Buffer.from(String(input))).toString('base64');
  return s.replace(/=+$/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

export async function getAccessToken(scope: string): Promise<string> {
  const sa = getServiceAccount();
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: 'RS256', typ: 'JWT' };
  const claim = {
    iss: sa.client_email,
    scope,
    aud: sa.token_uri || 'https://oauth2.googleapis.com/token',
    exp: now + 3600,
    iat: now,
  };
  const signInput = `${b64url(JSON.stringify(header))}.${b64url(JSON.stringify(claim))}`;
  const signer = crypto.createSign('RSA-SHA256');
  signer.update(signInput);
  const sig = signer.sign(sa.private_key);
  const jwt = `${signInput}.${b64url(sig)}`;
  const body = new URLSearchParams();
  body.set('grant_type', 'urn:ietf:params:oauth:grant-type:jwt-bearer');
  body.set('assertion', jwt);
  const res = await fetch(sa.token_uri || 'https://oauth2.googleapis.com/token', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: body.toString() });
  if (!res.ok) {
    const t = await res.text().catch(() => '');
    throw new Error(`Drive token error ${res.status}: ${t.slice(0, 200)}`);
  }
  const j = await res.json();
  const token = j?.access_token;
  if (!token) throw new Error('No access_token');
  return token;
}

export async function getFileMeta(fileId: string): Promise<{ id: string; name: string; mimeType: string }> {
  const token = await getAccessToken('https://www.googleapis.com/auth/drive.readonly');
  const res = await fetch(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(fileId)}?fields=id,name,mimeType&supportsAllDrives=true`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) {
    const t = await res.text().catch(() => '');
    throw new Error(`Drive meta error ${res.status}: ${t.slice(0, 200)}`);
  }
  return res.json();
}

export async function downloadFileToTemp(fileId: string, suggestedName?: string): Promise<string> {
  const token = await getAccessToken('https://www.googleapis.com/auth/drive.readonly');
  const meta = await getFileMeta(fileId).catch(() => ({ id: fileId, name: suggestedName || fileId, mimeType: 'application/octet-stream' }));
  const res = await fetch(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(fileId)}?alt=media&supportsAllDrives=true`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) {
    const t = await res.text().catch(() => '');
    throw new Error(`Drive download error ${res.status}: ${t.slice(0, 200)}`);
  }
  const ab = await res.arrayBuffer();
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'gdrive-'));
  // Pick extension based on mimeType
  let ext = '';
  const mt = (meta as any).mimeType || '';
  if (mt.includes('pdf')) ext = '.pdf'; else if (mt.includes('png')) ext = '.png';
  const file = path.join(dir, (meta as any).name || (suggestedName || `${fileId}${ext || ''}`));
  await fs.writeFile(file, Buffer.from(ab));
  return file;
}

export async function listFilesInFolder(folderId: string, recursive = false, exts: string[] = ['pdf', 'png']): Promise<{ id: string; name: string; mimeType: string }[]> {
  const token = await getAccessToken('https://www.googleapis.com/auth/drive.readonly');
  const results: { id: string; name: string; mimeType: string }[] = [];
  async function listOnce(parent: string) {
    let pageToken: string | undefined = undefined;
    do {
      const q = encodeURIComponent(`'${parent}' in parents and trashed=false`);
      const fields = encodeURIComponent('files(id,name,mimeType),nextPageToken');
      const url = `https://www.googleapis.com/drive/v3/files?q=${q}&pageSize=1000&fields=${fields}&includeItemsFromAllDrives=true&supportsAllDrives=true${pageToken ? `&pageToken=${pageToken}` : ''}`;
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error(`Drive list error ${res.status}`);
      const j = await res.json();
      const files = j?.files || [];
      for (const f of files) {
        if (f.mimeType === 'application/vnd.google-apps.folder') {
          if (recursive) await listOnce(f.id);
          continue;
        }
        const ext = String(f.name || '').split('.').pop()?.toLowerCase();
        if (!ext || !exts.includes(ext)) continue;
        results.push({ id: f.id, name: f.name, mimeType: f.mimeType });
      }
      pageToken = j?.nextPageToken;
    } while (pageToken);
  }
  await listOnce(folderId);
  return results;
}

export async function copyFile(fileId: string, targetFolderId: string, newName?: string): Promise<{ id: string; name: string }> {
  const token = await getAccessToken('https://www.googleapis.com/auth/drive');
  const body: any = { parents: [targetFolderId] };
  if (newName) body.name = newName;
  const res = await fetch(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(fileId)}/copy?supportsAllDrives=true`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const t = await res.text().catch(() => '');
    throw new Error(`Drive copy error ${res.status}: ${t.slice(0, 200)}`);
  }
  const j = await res.json();
  return { id: j.id, name: j.name };
}

export async function deleteFile(fileId: string): Promise<void> {
  const token = await getAccessToken('https://www.googleapis.com/auth/drive');
  const res = await fetch(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(fileId)}`, {
    method: 'DELETE', headers: { Authorization: `Bearer ${token}` },
  });
  if (!(res.status === 204 || res.status === 200)) {
    const t = await res.text().catch(() => '');
    throw new Error(`Drive delete error ${res.status}: ${t.slice(0, 120)}`);
  }
}

export async function deleteAllInFolder(folderId: string): Promise<{ deleted: number }> {
  const files = await listFilesInFolder(folderId, false, ['pdf','png','json']);
  let deleted = 0;
  for (const f of files) {
    try { await deleteFile(f.id); deleted++; } catch {}
  }
  return { deleted };
}

export async function uploadFileBuffer(buffer: Buffer, name: string, mimeType: string, parentFolderId: string): Promise<{ id: string; name: string }> {
  const token = await getAccessToken('https://www.googleapis.com/auth/drive');
  const meta = { name, parents: [parentFolderId] };
  const boundary = '-------314159265358979323846';
  const delimiter = `\r\n--${boundary}\r\n`;
  const closeDelim = `\r\n--${boundary}--`;
  const body = Buffer.concat([
    Buffer.from(delimiter + 'Content-Type: application/json; charset=UTF-8\r\n\r\n' + JSON.stringify(meta)),
    Buffer.from(delimiter + `Content-Type: ${mimeType}\r\n\r\n`),
    buffer,
    Buffer.from(closeDelim),
  ]);
  const res = await fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': `multipart/related; boundary=${boundary}` },
    body,
  });
  if (!res.ok) { const t = await res.text().catch(()=> ''); throw new Error(`Drive upload error ${res.status}: ${t.slice(0,200)}`); }
  const j = await res.json();
  return { id: j.id, name: j.name };
}

export async function createShortcut(targetFileId: string, name: string, parentFolderId: string): Promise<{ id: string; name: string }> {
  const token = await getAccessToken('https://www.googleapis.com/auth/drive');
  const body = {
    name,
    mimeType: 'application/vnd.google-apps.shortcut',
    parents: [parentFolderId],
    shortcutDetails: { targetId: targetFileId },
  } as any;
  const res = await fetch('https://www.googleapis.com/drive/v3/files', {
    method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  if (!res.ok) { const t = await res.text().catch(()=> ''); throw new Error(`Drive shortcut error ${res.status}: ${t.slice(0,200)}`); }
  const j = await res.json();
  return { id: j.id, name: j.name };
}

export default { downloadFileToTemp, listFilesInFolder, getFileMeta };
