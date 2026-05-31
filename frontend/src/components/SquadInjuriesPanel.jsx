const STATUS_STYLE = {
  fit: 'bg-accent/15 text-accent border-accent/30',
  doubtful: 'bg-gold/15 text-gold border-gold/30',
  out: 'bg-red-500/15 text-red-300 border-red-500/30',
  suspended: 'bg-red-500/15 text-red-300 border-red-500/30',
  recovering: 'bg-sky-400/15 text-sky-300 border-sky-400/30',
}

export default function SquadInjuriesPanel({ squadStatus, teamA, teamB }) {
  const entries = [teamA, teamB].filter((t) => squadStatus?.[t])
  if (!entries.length) return null

  return (
    <section className="wc-card p-6">
      <p className="text-xs text-accent uppercase tracking-widest font-display mb-1">Squad feed</p>
      <h2 className="text-lg font-semibold font-display tracking-wide mb-4">
        Injuries &amp; availability
      </h2>
      <div className="grid md:grid-cols-2 gap-6">
        {entries.map((team) => (
          <TeamSquad key={team} status={squadStatus[team]} />
        ))}
      </div>
    </section>
  )
}

function TeamSquad({ status }) {
  return (
    <div className="rounded-xl border border-pitch-line/50 bg-pitch/40 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <h3 className="font-semibold">{status.team}</h3>
        <span className="text-[10px] text-muted uppercase">
          {status.source} · {status.last_updated}
        </span>
      </div>
      <p className="text-sm text-white/85 mb-4">{status.injury_summary}</p>
      {status.injuries.length === 0 ? (
        <p className="text-xs text-muted">No flagged absences in feed.</p>
      ) : (
        <ul className="space-y-2">
          {status.injuries.map((inj) => (
            <li
              key={inj.player}
              className="flex flex-wrap items-start gap-2 text-sm border-t border-white/5 pt-2 first:border-0 first:pt-0"
            >
              <span
                className={`text-[10px] uppercase px-2 py-0.5 rounded-full border shrink-0 ${
                  STATUS_STYLE[inj.status] || STATUS_STYLE.doubtful
                }`}
              >
                {inj.status}
              </span>
              <div>
                <span className="font-medium">{inj.player}</span>
                <span className="text-muted"> — {inj.detail}</span>
                {inj.expected_return && (
                  <p className="text-xs text-muted mt-0.5">Return: {inj.expected_return}</p>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
