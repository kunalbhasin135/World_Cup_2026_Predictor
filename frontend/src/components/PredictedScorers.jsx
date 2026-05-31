export default function PredictedScorers({ scorers }) {
  if (!scorers?.length) return null

  return (
    <section className="wc-card p-6 shadow-xl">
      <h2 className="text-lg font-semibold mb-1">Predicted scorers</h2>
      <p className="text-muted text-sm mb-5">
        Likelihood each player scores at least once, based on role, form, and projected team goals.
      </p>
      <div className="space-y-3">
        {scorers.map((s) => (
          <div
            key={`${s.team}-${s.name}`}
            className="flex flex-col sm:flex-row sm:items-center gap-3 p-4 rounded-xl bg-pitch border border-white/10"
          >
            <div className="flex items-center gap-3 sm:w-48 shrink-0">
              <span className="w-8 h-8 rounded-lg bg-accent/20 text-accent flex items-center justify-center font-bold text-sm">
                {s.rank}
              </span>
              <div>
                <p className="font-semibold">{s.name}</p>
                <p className="text-xs text-muted">
                  {s.team} · {s.position}
                </p>
              </div>
            </div>
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-muted">Score probability</span>
                <span className="font-semibold text-accent">{s.score_probability.toFixed(1)}%</span>
              </div>
              <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent rounded-full transition-all duration-500"
                  style={{ width: `${s.score_probability}%` }}
                />
              </div>
              <p className="text-xs text-white/60 mt-2 leading-relaxed">{s.rationale}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
