import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { useAppStore } from "../store/useAppStore";
import ExportAndSave from "./ExportAndSave";

const SEVERITY_COLOR: Record<string, string> = {
  LOW: "#22c55e",
  MODERATE: "#eab308",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

function StatCard({
  label,
  value,
  sub,
  changePct,
}: {
  label: string;
  value: string;
  sub?: string;
  changePct?: number;
}) {
  const positive = (changePct ?? 0) >= 0;
  return (
    <div className="rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-900/60 p-4 shadow-sm shadow-black/10">
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-semibold tracking-tight text-slate-100">{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
      {changePct !== undefined && (
        <p className={`text-sm mt-1 font-medium ${positive ? "text-emerald-400" : "text-red-400"}`}>
          {positive ? "▲" : "▼"} {Math.abs(changePct).toFixed(1)}%
        </p>
      )}
    </div>
  );
}

export default function ResultsDashboard() {
  const analysis = useAppStore((s) => s.analysis);

  if (!analysis) {
    return (
      <div className="flex h-full min-h-64 items-center justify-center p-8 text-center">
        <div className="max-w-xs"><div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-2xl border border-slate-700 bg-slate-900 text-slate-500">⌁</div><h2 className="text-sm font-semibold text-slate-300">Your analysis will appear here</h2><p className="mt-2 text-xs leading-relaxed text-slate-500">Select a region, search for imagery, then compare two observations to see the results.</p></div>
      </div>
    );
  }

  const chartData = [
    { name: "Vegetation", before: analysis.vegetation.before_pct, after: analysis.vegetation.after_pct, unit: "%" },
    { name: "Water (km²)", before: analysis.water.before_area_km2, after: analysis.water.after_area_km2, unit: "km²" },
    { name: "Urban (km²)", before: analysis.urban.before_area_km2, after: analysis.urban.after_area_km2, unit: "km²" },
  ];

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-4 sm:p-5">
      <div className="flex items-end justify-between gap-3"><div><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-cyan-300">Analysis overview</p><h2 className="mt-1 text-sm font-semibold text-slate-100">Change summary</h2></div><span className="rounded-md border border-slate-800 bg-slate-900 px-2 py-1 text-[10px] text-slate-500">{analysis.method}</span></div>
      {analysis.is_demo && (
        <div className="flex gap-2.5 rounded-xl border border-amber-500/20 bg-amber-500/[0.06] px-3 py-2.5 text-[11px] leading-relaxed text-amber-200/90">
          ⚠ DEMO DATA — synthetic imagery, for platform demonstration only.
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <StatCard
          label="Vegetation (NDVI coverage)"
          value={`${analysis.vegetation.after_pct.toFixed(1)}%`}
          sub={`was ${analysis.vegetation.before_pct.toFixed(1)}%`}
          changePct={analysis.vegetation.change_pct}
        />
        <StatCard
          label="Water coverage"
          value={`${analysis.water.after_area_km2.toFixed(2)} km²`}
          sub={`was ${analysis.water.before_area_km2.toFixed(2)} km²`}
          changePct={analysis.water.change_pct}
        />
        <StatCard
          label="Built-up area"
          value={`${analysis.urban.after_area_km2.toFixed(2)} km²`}
          sub={`was ${analysis.urban.before_area_km2.toFixed(2)} km²`}
          changePct={analysis.urban.change_pct}
        />
        <div
          className="rounded-lg p-4 border"
          style={{
            borderColor: SEVERITY_COLOR[analysis.overall_severity] + "55",
            background: SEVERITY_COLOR[analysis.overall_severity] + "11",
          }}
        >
          <p className="text-xs uppercase tracking-wide text-slate-500">Overall severity</p>
          <p className="text-2xl font-semibold mt-1" style={{ color: SEVERITY_COLOR[analysis.overall_severity] }}>
            {analysis.overall_severity}
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            {(analysis.total_changed_fraction * 100).toFixed(1)}% of region changed
          </p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 h-56">
        <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">Before vs. after</p>
        <ResponsiveContainer width="100%" height="90%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
            <YAxis stroke="#64748b" fontSize={11} />
            <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", fontSize: 12 }} />
            <Bar dataKey="before" fill="#475569" radius={[3, 3, 0, 0]} />
            <Bar dataKey="after" fill="#22d3ee" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">
          Detected change regions ({analysis.regions.length}) — method: {analysis.method}
        </p>
        {analysis.regions.length === 0 ? (
          <p className="text-slate-600 text-sm">No significant change regions detected above threshold.</p>
        ) : (
          <div className="flex flex-col gap-2 max-h-64 overflow-y-auto">
            {analysis.regions.map((r) => (
              <div key={r.id} className="flex items-center justify-between text-xs bg-slate-800/60 rounded px-3 py-2">
                <div>
                  <span
                    className="inline-block w-2 h-2 rounded-full mr-2"
                    style={{ background: SEVERITY_COLOR[r.severity] }}
                  />
                  <span className="font-medium text-slate-200">Change #{r.id} — {r.change_type}</span>
                  <p className="text-slate-500 mt-0.5 ml-4">
                    {r.area_km2.toFixed(2)} km² · confidence {(r.confidence * 100).toFixed(0)}% · {r.before_value.toFixed(2)} → {r.after_value.toFixed(2)}
                  </p>
                </div>
                <span className="text-slate-400 font-medium">{r.severity}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <p className="text-xs text-slate-600 border-t border-slate-800 pt-3">{analysis.disclaimer}</p>

      <ExportAndSave />
    </div>
  );
}
