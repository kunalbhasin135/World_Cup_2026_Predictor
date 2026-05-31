const RESULT_STYLE = {
  W: 'bg-accent/25 text-accent border-accent/40',
  D: 'bg-gold/20 text-gold border-gold/40',
  L: 'bg-red-500/20 text-red-400 border-red-500/40',
}

export default function FormComparison({ teamA, teamB, recentForm }) {
  const formA = recentForm[teamA]
  const formB = recentForm[teamB]
  if (!formA || !formB) return null

  return (
    <section className="wc-card p-6 shadow-xl">
      <h2 className="text-lg font-semibold mb-5">Recent form comparison</h2>
      <div className="grid md:grid-cols-2 gap-6">
        <FormCard team={teamA} form={formA} variant="a" />
        <FormCard team={teamB} form={formB} variant="b" />
      </div>
    </section>
  )
}

function FormCard({ team, form, variant }) {
  const titleClass = variant === 'a' ? 'text-accent' : 'text-sky-400'
  const results = form.last_5_results.split('-')

  return (
    <div className="bg-pitch rounded-xl p-5 border border-white/10">
      <h3 className={`font-semibold mb-4 ${titleClass}`}>{team}</h3>

      <div className="flex gap-2 mb-5">
        {results.map((r, i) => (
          <span
            key={i}
            className={`w-9 h-9 rounded-lg flex items-center justify-center text-sm font-bold border ${RESULT_STYLE[r] || RESULT_STYLE.D}`}
          >
            {r}
          </span>
        ))}
      </div>

      <div className="space-y-3 text-sm">
        <StatBar label="Goals scored / game" value={form.goals_scored_avg} max={3.5} color="bg-accent" />
        <StatBar label="Goals conceded / game" value={form.goals_conceded_avg} max={3.5} color="bg-red-400" invert />
        <div className="flex justify-between pt-2 border-t border-white/10">
          <span className="text-muted">Goal difference (last 10)</span>
          <span className={`font-semibold ${form.goal_difference >= 0 ? 'text-accent' : 'text-red-400'}`}>
            {form.goal_difference >= 0 ? '+' : ''}
            {form.goal_difference.toFixed(1)}
          </span>
        </div>
      </div>
    </div>
  )
}

function StatBar({ label, value, max, color }) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-muted">{label}</span>
        <span className="font-medium">{value.toFixed(1)}</span>
      </div>
      <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
