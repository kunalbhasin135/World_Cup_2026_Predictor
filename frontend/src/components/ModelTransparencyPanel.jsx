export default function ModelTransparencyPanel({ modelInfo }) {
  if (!modelInfo) return null

  const { feature_contributions: contributions = [], ...meta } = modelInfo
  const maxImpact = Math.max(...contributions.map((c) => Math.abs(c.impact)), 0.001)

  return (
    <section className="wc-card p-5 sm:p-6">
      <h2 className="text-lg font-semibold mb-1">Model transparency</h2>
      <p className="text-muted text-sm mb-5">
        How the prediction engine reached this call — features ranked by logistic regression
        impact.
      </p>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <MetaTile label="Outcome model" value={meta.probability_model?.replace(/_/g, ' ')} />
        <MetaTile label="Score model" value={meta.score_model?.replace(/_/g, ' ')} />
        <MetaTile label="Features" value={meta.feature_source} />
        {meta.test_accuracy != null && (
          <MetaTile label="Test accuracy" value={`${(meta.test_accuracy * 100).toFixed(0)}%`} />
        )}
        {meta.log_loss != null && <MetaTile label="Log loss" value={meta.log_loss} />}
        {meta.brier_score != null && <MetaTile label="Brier score" value={meta.brier_score} />}
        {meta.trained_at && (
          <MetaTile label="Trained" value={new Date(meta.trained_at).toLocaleDateString()} />
        )}
      </div>

      {contributions.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-muted uppercase tracking-wide mb-3">
            Top feature drivers
          </h3>
          <ul className="space-y-2">
            {contributions.map((c) => (
              <li key={c.feature} className="flex items-center gap-3 text-sm">
                <span className="w-36 shrink-0 text-muted truncate" title={c.feature}>
                  {c.feature.replace(/_/g, ' ')}
                </span>
                <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${c.impact >= 0 ? 'bg-accent' : 'bg-red-400'}`}
                    style={{ width: `${(Math.abs(c.impact) / maxImpact) * 100}%` }}
                  />
                </div>
                <span className="w-16 text-right tabular-nums text-xs text-muted">
                  {c.impact >= 0 ? '+' : ''}
                  {c.impact.toFixed(3)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

function MetaTile({ label, value }) {
  return (
    <div className="px-3 py-2 rounded-lg bg-white/5 border border-white/10">
      <p className="text-xs text-muted mb-0.5 capitalize">{label}</p>
      <p className="text-sm font-medium capitalize">{value}</p>
    </div>
  )
}
