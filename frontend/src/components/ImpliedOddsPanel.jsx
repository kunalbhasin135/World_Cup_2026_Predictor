const ROUND_LABELS = {
  'Semi-finals': 'semi-final',
  'Quarter-finals': 'quarter-final',
  Final: 'final',
  'Round of 16': 'round of 16',
  'Round of 32': 'round of 32',
}

export default function ImpliedOddsPanel({ impliedOdds, bracketContext, teamA, teamB, matchRound }) {
  if (!impliedOdds) return null

  const roundLabel = matchRound ? ROUND_LABELS[matchRound] || matchRound.toLowerCase() : null

  return (
    <section className="wc-card p-6 border-gold/15">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <p className="text-xs text-gold uppercase tracking-widest font-display mb-1">Betting lines</p>
          <h2 className="text-lg font-semibold font-display tracking-wide">
            {roundLabel ? `Implied ${roundLabel} odds` : 'Model-implied match odds'}
          </h2>
          <p className="text-muted text-xs mt-1 max-w-xl">{impliedOdds.disclaimer}</p>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-white/5 border border-pitch-line/50 text-muted uppercase">
          {impliedOdds.market_type === 'match_winner' ? '2-way' : '1X2'}
        </span>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
        {impliedOdds.outcomes.map((o) => (
          <OutcomeCard key={o.label} outcome={o} favored={o.label !== 'Draw'} />
        ))}
      </div>

      {bracketContext && (
        <div className="rounded-xl bg-pitch/60 border border-pitch-line/50 p-4 space-y-3">
          <p className="text-xs text-accent uppercase tracking-widest font-display">
            Bracket path · {bracketContext.round}
          </p>
          <div className="grid sm:grid-cols-3 gap-3 text-sm">
            <Stat
              label="Both reach round"
              value={`${bracketContext.both_reach_round_pct}%`}
              sub={`of ${bracketContext.simulations} sims`}
            />
            <Stat
              label="Meet in this round"
              value={`${bracketContext.face_in_round_pct}%`}
              sub={`${teamA} vs ${teamB}`}
            />
            {bracketContext.team_a_wins_if_meet_pct != null && (
              <Stat
                label={`${teamA} wins if paired`}
                value={`${bracketContext.team_a_wins_if_meet_pct}%`}
                sub="in bracket sims"
              />
            )}
          </div>
          <p className="text-xs text-muted leading-relaxed">{bracketContext.scenario_note}</p>
          <p className="text-xs text-gold/90">
            H2H prices above assume the fixture is played — use together with meet probability for a
            full scenario view.
          </p>
        </div>
      )}
    </section>
  )
}

function OutcomeCard({ outcome, favored }) {
  const isDraw = outcome.label === 'Draw'
  return (
    <div
      className={`rounded-xl p-4 border ${
        isDraw
          ? 'bg-gold/5 border-gold/20'
          : 'bg-white/5 border-pitch-line/50'
      }`}
    >
      <p className="text-sm text-muted mb-1">{outcome.label}</p>
      <p className="text-2xl font-bold font-display text-accent">{outcome.decimal_odds.toFixed(2)}</p>
      <p className="text-xs text-muted mt-2">
        {outcome.fractional_odds} · {formatAmerican(outcome.american_odds)}
      </p>
      <p className="text-xs text-white/70 mt-1">{outcome.probability_pct}% model win</p>
    </div>
  )
}

function Stat({ label, value, sub }) {
  return (
    <div>
      <p className="text-muted text-xs">{label}</p>
      <p className="text-lg font-semibold text-white">{value}</p>
      <p className="text-[10px] text-muted">{sub}</p>
    </div>
  )
}

function formatAmerican(n) {
  return n > 0 ? `+${n}` : `${n}`
}
