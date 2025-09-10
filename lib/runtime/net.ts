// Ensure Node prefers IPv4 when resolving hostnames to avoid environments
// with partial IPv6 connectivity causing `fetch failed` errors.
// This only affects Node.js runtime (API routes, scripts), not the browser.
import dns from 'node:dns';

try {
  // Node 18+ supports setting default DNS result order
  dns.setDefaultResultOrder('ipv4first');
} catch {
  // ignore if not supported
}

