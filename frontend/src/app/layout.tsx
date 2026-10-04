import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'RazorGuard – Payment Risk & Reconciliation Control Center',
  description:
    'Enterprise fintech risk operations console providing deterministic transaction decisioning (APPROVED, REVIEW, BLOCKED), automated reconciliation, and compliance enrichment.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased selection:bg-teal-500/20 selection:text-teal-900 min-h-screen">
        {children}
      </body>
    </html>
  );
}
