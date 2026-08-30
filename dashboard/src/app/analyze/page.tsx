"use client";

import { useState } from "react";
import { predictEmail, type PredictResponse } from "@/lib/api";

export default function AnalyzePage() {
  const [emailText, setEmailText] = useState("");
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    if (!emailText.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await predictEmail(emailText);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="py-16 max-w-2xl">
      <p className="font-mono text-xs text-[var(--accent)] tracking-widest mb-4">ANALYSER UN EMAIL</p>
      <h1 className="font-display font-bold text-2xl mb-8">
        Colle le texte d&apos;un email pour voir le verdict du modèle
      </h1>

      <div className="relative">
        <textarea
          value={emailText}
          onChange={(e) => setEmailText(e.target.value)}
          placeholder="Objet, corps du message..."
          rows={10}
          className="w-full bg-[var(--surface)] border border-[var(--border)] p-4 text-sm font-mono resize-y focus:outline-none focus:border-[var(--accent)] placeholder:text-[var(--text-muted)]"
        />
        {loading && <span className="scan-line" />}
      </div>

      <button
        onClick={handleAnalyze}
        disabled={loading || !emailText.trim()}
        className="mt-4 px-5 py-3 bg-[var(--accent)] text-[var(--accent-contrast)] font-medium text-sm hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
      >
        {loading ? "Analyse en cours…" : "Analyser →"}
      </button>

      {error && (
        <div className="mt-8 border border-[var(--danger)] bg-[var(--danger-bg)] p-4 text-sm text-[var(--danger)]">
          {error}. Vérifie que l&apos;API tourne (uvicorn main:app --reload --port 8000).
        </div>
      )}

      {result && (
        <>
          <div
            className={`mt-8 border p-6 ${
              result.prediction === "phishing"
                ? "border-[var(--danger)] bg-[var(--danger-bg)]"
                : "border-[var(--safe)] bg-[var(--safe-bg)]"
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="font-mono text-xs tracking-widest text-[var(--text-secondary)]">VERDICT</div>
              <div className="font-mono text-xs text-[var(--text-muted)]">modèle : {result.model_used}</div>
            </div>
            <div
              className={`font-display font-bold text-2xl mt-2 ${
                result.prediction === "phishing" ? "text-[var(--danger)]" : "text-[var(--safe)]"
              }`}
            >
              {result.prediction === "phishing" ? "⚠ PHISHING" : "✓ LÉGITIME"}
            </div>
            <div className="font-mono text-sm text-[var(--text-secondary)] mt-2">
              confiance : {(result.confidence * 100).toFixed(1)}%
            </div>
          </div>

          {result.top_features.length > 0 && (
            <div className="mt-6">
              <h2 className="font-display font-bold text-sm mb-1">Pourquoi ce verdict&nbsp;?</h2>
              <p className="text-xs text-[var(--text-secondary)] mb-4">
                Termes ayant le plus influencé la décision (régression logistique). Rouge = pousse vers
                phishing, vert = pousse vers légitime.
              </p>
              <div className="space-y-1.5">
                {result.top_features.map((f) => {
                  const maxAbs = Math.max(...result.top_features.map((x) => Math.abs(x.weight)));
                  const widthPct = (Math.abs(f.weight) / maxAbs) * 100;
                  const isPhishing = f.direction === "phishing";
                  return (
                    <div key={f.term} className="flex items-center gap-3">
                      <div className="w-28 text-xs font-mono text-[var(--text-secondary)] truncate shrink-0">
                        {f.term}
                      </div>
                      <div className="flex-1 h-4 bg-[var(--surface)] border border-[var(--border)] relative">
                        <div
                          className={`h-full ${isPhishing ? "bg-[var(--danger)]" : "bg-[var(--safe)]"}`}
                          style={{ width: `${widthPct}%` }}
                        />
                      </div>
                      <div className="w-14 text-xs font-mono text-right text-[var(--text-muted)]">
                        {f.weight > 0 ? "+" : ""}
                        {f.weight.toFixed(2)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {result.model_comparison.length > 0 && (
            <div className="mt-8">
              <h2 className="font-display font-bold text-sm mb-4">Comparaison des 3 modèles</h2>
              <div className="border border-[var(--border)]">
                {result.model_comparison.map((v, i) => (
                  <div
                    key={v.model}
                    className={`flex items-center justify-between px-4 py-3 text-sm ${
                      i !== result.model_comparison.length - 1 ? "border-b border-[var(--border)]" : ""
                    }`}
                  >
                    <span className="font-mono text-[var(--text-secondary)]">{v.model.replace("_", " ")}</span>
                    <span className="flex items-center gap-3">
                      <span
                        className={`font-mono text-xs ${
                          v.prediction === "phishing" ? "text-[var(--danger)]" : "text-[var(--safe)]"
                        }`}
                      >
                        {v.prediction === "phishing" ? "PHISHING" : "LÉGITIME"}
                      </span>
                      <span className="font-mono text-xs text-[var(--text-muted)] w-12 text-right">
                        {(v.confidence * 100).toFixed(0)}%
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
