import fs from 'fs/promises';
import path from 'path';

export type LogLevel = 'info' | 'warn' | 'error';

export interface LogRecord {
  t: string;           // ISO timestamp
  level: LogLevel;
  event: string;       // short event key, e.g. 'upload:success'
  requestId?: string;  // optional request correlation id
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

async function ensureDir(dir: string) {
  try { await fs.mkdir(dir, { recursive: true }); } catch {}
}

export async function logEvent(event: string, data: Record<string, unknown> = {}, level: LogLevel = 'info') {
  try {
    const dir = path.join(process.cwd(), 'logs', 'events');
    await ensureDir(dir);
    const now = new Date();
    const file = path.join(dir, `${now.toISOString().slice(0,10)}.jsonl`);
    const rec: LogRecord = { t: now.toISOString(), level, event, ...data };
    await fs.appendFile(file, JSON.stringify(rec) + '\n', 'utf8');
  } catch {
    // Swallow logging errors to avoid impacting request flow
  }
}

export default logEvent;

