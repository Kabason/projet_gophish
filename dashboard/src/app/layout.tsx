import type { Metadata } from "next";
import { Space_Grotesk, Inter, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import { ThemeProvider, THEME_INIT_SCRIPT } from "@/lib/theme";
import ThemeToggle from "@/components/ThemeToggle";
import "./globals.css";

const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "700"],
});
const body = Inter({ subsets: ["latin"], variable: "--font-body" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "PFE Phishing IA — Détecteur",
  description: "Génération de phishing par IA générative et détection par NLP",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <head>
        {/* Runs before paint - sets data-theme from localStorage so there's
            no flash of the wrong theme on load. */}
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body
        className={`${display.variable} ${body.variable} ${mono.variable} font-body min-h-screen bg-[var(--bg)] text-[var(--text)]`}
      >
        <ThemeProvider>
          <header className="border-b border-[var(--border)]">
            <nav className="max-w-5xl mx-auto flex items-center justify-between px-6 py-4">
              <Link href="/" className="font-display font-bold tracking-tight text-sm">
                PFE&nbsp;PHISHING·IA
              </Link>
              <div className="flex items-center gap-6 text-sm text-[var(--text-secondary)]">
                <Link href="/analyze" className="hover:text-[var(--text)] transition-colors">
                  Analyser
                </Link>
                <Link href="/metrics" className="hover:text-[var(--text)] transition-colors">
                  Métriques
                </Link>
                <ThemeToggle />
              </div>
            </nav>
          </header>
          <main className="max-w-5xl mx-auto px-6">{children}</main>
        </ThemeProvider>
      </body>
    </html>
  );
}
