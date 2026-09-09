import { useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { generateReport } from "../lib/api";

export default function ReportPanel() {
  const { analysis, report } = useAppStore();
  const setReport = useAppStore((s) => s.setReport);
  const [loading, setLoading] = useState(false);

  if (!analysis) {
    return (
      <div className="p-6 text-sm text-slate-600 text-center">
        Run change detection first to generate a report.
      </div>
    );
  }

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const result = await generateReport(analysis, "the selected region");
      setReport(result);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 flex flex-col gap-4">
      {!report ? (
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white rounded py-1.5 text-sm font-medium"
        >
          {loading ? "Generating…" : "Generate analytical report"}
        </button>
      ) : (
        <>
          <div className="bg-amber-950/30 border border-amber-900 text-amber-300 text-xs rounded px-3 py-2">
            {report.disclaimer}
          </div>

          <section>
            <h3 className="text-cyan-400 text-xs uppercase tracking-wide font-semibold mb-1">Executive summary</h3>
            <p className="text-slate-300 text-sm">{report.executive_summary}</p>
          </section>

          <section>
            <h3 className="text-cyan-400 text-xs uppercase tracking-wide font-semibold mb-1">Key findings</h3>
            <ul className="list-disc list-inside text-slate-300 text-sm space-y-1">
              {report.key_findings.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </section>

          <section>
            <h3 className="text-cyan-400 text-xs uppercase tracking-wide font-semibold mb-1">Significant areas</h3>
            <ul className="text-slate-300 text-sm space-y-1">
              {report.significant_areas.map((a) => (
                <li key={a.region_id} className="bg-slate-900 border border-slate-800 rounded px-2 py-1.5">
                  {a.observation}
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h3 className="text-cyan-400 text-xs uppercase tracking-wide font-semibold mb-1">Possible explanations</h3>
            <div className="flex flex-col gap-2">
              {report.possible_explanations.map((e) => (
                <div key={e.region_id} className="bg-slate-900 border border-slate-800 rounded p-2 text-xs">
                  <p className="text-slate-200 mb-1"><span className="text-slate-500">Observed: </span>{e.observed_change}</p>
                  <p className="text-slate-400 mb-1"><span className="text-slate-500">Inference: </span>{e.model_inference}</p>
                  <ul className="list-disc list-inside text-slate-500 mb-1">
                    {e.hypotheses.map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                  <p className="text-slate-600 italic">{e.caveat}</p>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h3 className="text-cyan-400 text-xs uppercase tracking-wide font-semibold mb-1">Recommendations</h3>
            <ul className="list-disc list-inside text-slate-300 text-sm space-y-1">
              {report.recommendations.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  );
}
