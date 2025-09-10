import './globals.css';
import Link from 'next/link';
import { ReactNode } from 'react';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans">
        <header className="border-b bg-white">
          <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-4">
            <Link href="/" className="font-semibold">PIK‑AI</Link>
            <nav className="flex items-center gap-3 text-sm">
              <Link className="underline" href="/upload">Upload</Link>
              <Link className="underline" href="/docs">Docs</Link>
              <Link className="underline" href="/frames">Frames</Link>
              <Link className="underline" href="/compare">Compare</Link>
            </nav>
          </div>
        </header>
        <div className="px-4">
          {children}
        </div>
      </body>
    </html>
  );
}
