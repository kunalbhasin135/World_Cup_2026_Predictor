const CONFIDENCE_STYLE = {
  High: 'bg-accent/20 text-accent border-accent/30',
  Medium: 'bg-gold/20 text-gold border-gold/30',
  Low: 'bg-white/10 text-muted border-white/20',
}

export default function PredictionCard({ prediction }) {
  const { team_a, team_b, probabilities, predicted_score, confidence, favored_team } = prediction
  const favored =
    favored_team && favored_team !== 'Draw' ? favored_team : favored_team === 'Draw' ? null : null
  const isDraw = favored_team === 'Draw' || (!favored_team && probabilities.draw >= probabilities.team_a_win && probabilities.draw >= probabilities.team_b_win)

  return (
    <section className="wc-card p-6">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
        <div>
          <p className="text-xs text-muted uppercase tracking-widest font-display mb-1">Full-time forecast</p>
          <h2 className="text-lg font-semibold text-muted mb-1">Match prediction</h2>
          {probabilities.draw === 0 && (
            <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-white/5 text-muted mb-1">
              Knockout mode (matches bracket)
            </span>
          )}
          {isDraw ? (
            <p className="text-2xl font-bold text-gold">Draw most likely</p>
          ) : favored ? (
            <p className="text-2xl font-bold">
              <span className="text-accent">{favored}</span> favored
            </p>
          ) : null}
        </div>
        <span
          className={`self-start px-3 py-1 rounded-full text-sm font-medium border ${CONFIDENCE_STYLE[confidence]}`}
        >
          {confidence} confidence
        </span>
      </div>

      <div className="space-y-3 mb-8">
        <ProbBar label={team_a} value={probabilities.team_a_win} color="bg-accent" />
        {probabilities.draw > 0 && (
          <ProbBar label="Draw" value={probabilities.draw} color="bg-gold" />
        )}
        <ProbBar label={team_b} value={probabilities.team_b_win} color="bg-accent/70" />
      </div>

      <div className="text-center py-6 rounded-xl bg-pitch/60 border border-pitch-line/50">
        <p className="text-muted text-xs uppercase tracking-widest font-display mb-3">Full time</p>
        <p className="text-4xl sm:text-5xl font-bold tracking-tight font-display">
          <span className="text-white/90">{team_a}</span>{' '}
          <span className={predicted_score.team_a >= predicted_score.team_b ? 'text-accent' : 'text-white/60'}>
            {predicted_score.team_a}
          </span>
          <span className="text-gold/60 mx-3 text-3xl">–</span>
          <span className={predicted_score.team_b > predicted_score.team_a ? 'text-accent' : 'text-white/60'}>
            {predicted_score.team_b}
          </span>{' '}
          <span className="text-white/90">{team_b}</span>
        </p>
      </div>
    </section>
  )
}

function ProbBar({ label, value, color }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span>{label}</span>
        <span className="font-semibold">{value.toFixed(1)}%</span>
      </div>
      <div className="h-2.5 bg-white/10 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-700 ease-out`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}
