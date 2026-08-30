import Link from "next/link";

export default function HomePage() {
  return (
    <div className="py-20">
      <p className="font-mono text-xs text-[var(--accent)] tracking-widest mb-6">
        MEMBRE&nbsp;B — DATA&nbsp;&amp;&nbsp;IA
      </p>
      <h1 className="font-display font-bold text-4xl md:text-5xl leading-[1.15] max-w-3xl">
        Un phishing écrit par IA trompe-t-il plus facilement,
        <span className="text-[var(--text-secondary)]">
          {" "}
          et un modèle NLP le détecte-t-il quand même&nbsp;?
        </span>
      </h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-[var(--border)] mt-14 border border-[var(--border)]">
        <Stat label="Emails générés (IA)" value="300" />
        <Stat label="Dataset final" value="1 000" />
        <Stat label="Modèles comparés" value="3" />
        <Stat label="F1 (meilleur modèle)" value="0.986" />
      </div>

      <div className="flex flex-col sm:flex-row gap-4 mt-14">
        <Link
          href="/analyze"
          className="px-5 py-3 bg-[var(--accent)] text-[var(--accent-contrast)] font-medium text-sm text-center hover:opacity-90 transition-opacity"
        >
          Tester un email →
        </Link>
        <Link
          href="/metrics"
          className="px-5 py-3 border border-[var(--border)] text-sm text-center hover:border-[var(--text-secondary)] transition-colors"
        >
          Voir les métriques
        </Link>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[var(--bg)] p-5">
      <div className="font-mono text-2xl font-bold">{value}</div>
      <div className="text-xs text-[var(--text-secondary)] mt-1">{label}</div>
    </div>
  );
}
