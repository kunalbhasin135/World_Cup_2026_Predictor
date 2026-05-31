const FORM_STYLE = {
  excellent: 'text-accent bg-accent/15 border-accent/30',
  strong: 'text-sky-400 bg-sky-400/15 border-sky-400/30',
  mixed: 'text-gold bg-gold/15 border-gold/30',
  poor: 'text-red-400 bg-red-500/15 border-red-500/30',
}

const INJURY_STYLE = {
  fit: 'text-accent bg-accent/15 border-accent/30',
  doubtful: 'text-gold bg-gold/15 border-gold/30',
  out: 'text-red-300 bg-red-500/15 border-red-500/30',
  suspended: 'text-red-300 bg-red-500/15 border-red-500/30',
  recovering: 'text-sky-300 bg-sky-400/15 border-sky-400/30',
}

export default function PlayerAnalysisSection({ teamA, teamB, playerAnalysis }) {
  const playersA = playerAnalysis?.[teamA] || []
  const playersB = playerAnalysis?.[teamB] || []
  if (!playersA.length && !playersB.length) return null

  return (
    <section>
      <h2 className="text-lg font-semibold mb-4">Key player analysis</h2>
      <div className="grid lg:grid-cols-2 gap-6">
        <PlayerColumn team={teamA} players={playersA} />
        <PlayerColumn team={teamB} players={playersB} />
      </div>
    </section>
  )
}

function PlayerColumn({ team, players }) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-muted uppercase tracking-wide">{team}</h3>
      {players.map((p) => (
        <PlayerCard key={p.name} player={p} />
      ))}
    </div>
  )
}

function PlayerCard({ player }) {
  const formClass = FORM_STYLE[player.recent_form?.toLowerCase()] || FORM_STYLE.mixed

  return (
    <article className="wc-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-2 mb-3">
        <div>
          <h4 className="font-bold text-lg">{player.name}</h4>
          <p className="text-sm text-muted">
            {player.position} · {player.role}
          </p>
        </div>
        <span className={`text-xs px-2.5 py-1 rounded-full border capitalize ${formClass}`}>
          {player.recent_form} form
        </span>
        {player.injury_status && (
          <span
            className={`text-xs px-2.5 py-1 rounded-full border capitalize ${
              INJURY_STYLE[player.injury_status] || INJURY_STYLE.doubtful
            }`}
          >
            {player.injury_status}
          </span>
        )}
      </div>

      {(player.intl_goals > 0 || player.intl_caps > 0) && (
        <p className="text-xs text-muted mb-3">
          {player.intl_goals} intl. goals · {player.intl_caps} caps
        </p>
      )}

      <p className="text-sm text-white/85 leading-relaxed mb-4">{player.analysis}</p>
      {player.injury_detail && (
        <p className="text-xs text-gold/90 mb-3 border-l-2 border-gold/40 pl-3">{player.injury_detail}</p>
      )}

      <div className="grid sm:grid-cols-2 gap-3 mb-4 text-sm">
        <div>
          <p className="text-xs text-accent uppercase tracking-wide mb-1">Strengths</p>
          <ul className="space-y-0.5">
            {player.strengths.map((s) => (
              <li key={s} className="text-white/75">
                + {s}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs text-red-400 uppercase tracking-wide mb-1">Weaknesses</p>
          <ul className="space-y-0.5">
            {player.weaknesses.map((w) => (
              <li key={w} className="text-white/75">
                − {w}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="p-3 rounded-lg bg-gold/5 border border-gold/20">
        <p className="text-xs text-gold font-semibold uppercase tracking-wide mb-1">Watch out for</p>
        <p className="text-sm text-white/80">{player.watch_out_for}</p>
      </div>
    </article>
  )
}
