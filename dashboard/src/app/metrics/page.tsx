"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getMetrics, type MetricsResponse } from "@/lib/api";

const CHART_COLORS = { precision: "#F0B429", recall: "#3FB950", f1: "#E5484D" };

export default function MetricsPage() {
  const [data, setData] = useState<MetricsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMetrics()
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur inconnue"));
  }, []);

  if (error) {
    return (
      <div className="py-16">
        <div className="border border-[var(--danger)] bg-[var(--danger-bg)] p-4 text-sm text-[var(--danger)] max-w-xl">
          {error}. Vérifie que l&apos;API tourne et que train_models.py a bien été exécuté.
        </div>
      </div>
    );
  }

  if (!data) {
    return <div className="py-16 text-[var(--text-secondary)] text-sm font-mono">Chargement des métriques…</div>;
  }

  const chartData = Object.entries(data.model_results.results).map(([name, m]) => ({
    name: name.replace("_", " "),
    precision: m.precision,
    recall: m.recall,
    f1: m.f1,
  }));

  const bestModel = data.model_results.best_model;
  const typeBreakdown = data.robustness.accuracy_by_type?.[bestModel] ?? {};
  const langBreakdown = data.robustness.accuracy_by_language?.[bestModel] ?? {};
  const tactics = data.robustness.detection_rate_by_tactic ?? {};

  return (
    <div className="py-16 pb-24">
      <p className="font-mono text-xs text-[var(--accent)] tracking-widest mb-4">MÉTRIQUES</p>
      <h1 className="font-display font-bold text-2xl mb-2">Performance du modèle</h1>
      <p className="text-sm text-[var(--text-secondary)] mb-10">
        Meilleur modèle : <span className="font-mono text-[var(--text)]">{bestModel}</span>
      </p>

      <Section title="Comparaison des modèles">
        <div className="h-64 border border-[var(--border)] bg-[var(--surface)] p-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="name" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} />
              <YAxis domain={[0, 1]} tick={{ fill: "var(--text-secondary)", fontSize: 12 }} />
              <Tooltip
                contentStyle={{ background: "var(--bg)", border: "1px solid var(--border)", fontSize: 12 }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="precision" fill={CHART_COLORS.precision} />
              <Bar dataKey="recall" fill={CHART_COLORS.recall} />
              <Bar dataKey="f1" fill={CHART_COLORS.f1} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Section>

      <Section title="Exactitude par type de donnée">
        <Table
          rows={Object.entries(typeBreakdown).map(([type, v]) => [
            type,
            `${(v.accuracy * 100).toFixed(1)}%`,
            `n=${v.n}`,
          ])}
        />
      </Section>

      <Section title="Exactitude par langue">
        <Table
          rows={Object.entries(langBreakdown).map(([lang, v]) => [
            lang,
            `${(v.accuracy * 100).toFixed(1)}%`,
            `n=${v.n}`,
          ])}
        />
      </Section>

      <Section title="Taux de détection par tactique psychologique (phishing IA)">
        <div className="space-y-2">
          {Object.entries(tactics).map(([tactic, stats]) => (
            <div key={tactic} className="flex items-center gap-4">
              <div className="w-28 text-sm text-[var(--text-secondary)] font-mono shrink-0">{tactic}</div>
              <div className="flex-1 bg-[var(--surface)] border border-[var(--border)] h-5">
                <div className="h-full bg-[var(--accent)]" style={{ width: `${stats.rate}%` }} />
              </div>
              <div className="w-20 text-sm font-mono text-right">
                {stats.rate.toFixed(0)}% <span className="text-[var(--text-muted)]">(n={stats.n})</span>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Explicabilité (SHAP)">
        <p className="text-xs text-[var(--text-secondary)] mb-3">
          Copie <code className="font-mono">explainability/shap_summary.png</code> dans{" "}
          <code className="font-mono">dashboard/public/shap_summary.png</code> pour l&apos;afficher ici.
        </p>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/shap_summary.png"
          alt="SHAP summary plot"
          className="w-full border border-[var(--border)]"
        />
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mt-12">
      <h2 className="font-display font-bold text-lg mb-4">{title}</h2>
      {children}
    </div>
  );
}

function Table({ rows }: { rows: [string, string, string][] }) {
  return (
    <div className="border border-[var(--border)]">
      {rows.map(([label, value, n], i) => (
        <div
          key={label}
          className={`flex items-center justify-between px-4 py-3 text-sm ${
            i !== rows.length - 1 ? "border-b border-[var(--border)]" : ""
          }`}
        >
          <span className="text-[var(--text-secondary)] font-mono">{label}</span>
          <span className="flex gap-3 font-mono">
            <span className="font-bold">{value}</span>
            <span className="text-[var(--text-muted)]">{n}</span>
          </span>
        </div>
      ))}
    </div>
  );
}