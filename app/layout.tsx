import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Q-Reach: Quantum-Inspired Traffic Route Optimization',
  description: 'Smart India Hackathon 2026 (SIH26137) - Intelligent Multi-Vehicle Route Optimization using QPSO & Metaheuristics',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full bg-slate-50">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
      </head>
      <body className="h-full text-slate-900 bg-slate-50 antialiased selection:bg-indigo-100 selection:text-indigo-700">
        {children}
      </body>
    </html>
  );
}
