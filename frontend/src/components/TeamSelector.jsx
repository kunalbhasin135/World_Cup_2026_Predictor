export default function TeamSelector({
  teams,
  teamA,
  teamB,
  knockout,
  matchRound,
  onKnockoutChange,
  onMatchRoundChange,
  onTeamAChange,
  onTeamBChange,
  onPredict,
  loading,
}) {
  const canPredict = teamA && teamB && teamA !== teamB && !loading
  const roundForcesKnockout = matchRound && matchRound !== 'Group stage'

  return (
    <section className="wc-card p-6">
      <h2 className="text-lg font-semibold mb-1 font-display tracking-wide">Select matchup</h2>
      <p className="text-muted text-xs mb-4">
        Choose nations and stage — get ML probabilities, implied betting lines, and injury context
      </p>
      <div className="grid sm:grid-cols-[1fr_auto_1fr] gap-4 items-end">
        <Select label="Home / Team A" value={teamA} onChange={onTeamAChange} teams={teams} exclude={teamB} />
        <div className="hidden sm:flex flex-col items-center justify-center pb-2 px-2">
          <span className="text-[10px] text-muted uppercase tracking-widest font-display">vs</span>
          <span className="w-8 h-px bg-gradient-to-r from-transparent via-gold/50 to-transparent mt-1" />
        </div>
        <Select label="Away / Team B" value={teamB} onChange={onTeamBChange} teams={teams} exclude={teamA} />
      </div>
      <div className="grid sm:grid-cols-2 gap-4 mt-4">
        <div>
          <label className="block text-sm text-muted mb-2">Tournament stage</label>
          <select
            value={matchRound}
            onChange={(e) => onMatchRoundChange(e.target.value)}
            className="w-full bg-pitch border border-white/15 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-accent/50"
          >
            <option value="Group stage">Group stage (1X2)</option>
            <option value="Round of 32">Round of 32</option>
            <option value="Round of 16">Round of 16</option>
            <option value="Quarter-finals">Quarter-finals</option>
            <option value="Semi-finals">Semi-finals</option>
            <option value="Final">Final</option>
          </select>
        </div>
        <div className="flex items-end">
          <label className="flex items-center gap-2 text-sm text-muted cursor-pointer pb-3">
            <input
              type="checkbox"
              checked={knockout || roundForcesKnockout}
              disabled={roundForcesKnockout}
              onChange={(e) => onKnockoutChange(e.target.checked)}
              className="rounded border-white/20 accent-accent disabled:opacity-60"
            />
            Knockout model (no draw)
            {roundForcesKnockout && (
              <span className="text-xs text-accent"> — auto for knockout rounds</span>
            )}
          </label>
        </div>
      </div>
      {teamA && teamB && teamA === teamB && (
        <p className="text-red-400 text-sm mt-3">Please select two different teams.</p>
      )}
      <button
        onClick={onPredict}
        disabled={!canPredict}
        className="mt-5 w-full sm:w-auto px-8 py-3 wc-btn-primary disabled:cursor-not-allowed"
      >
        {loading ? 'Analyzing…' : 'Predict Match'}
      </button>
    </section>
  )
}

function Select({ label, value, onChange, teams, exclude }) {
  return (
    <div>
      <label className="block text-sm text-muted mb-2">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-pitch border border-white/15 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-accent/50 appearance-none cursor-pointer"
      >
        <option value="">Choose a team…</option>
        {teams
          .filter((t) => t !== exclude)
          .map((team) => (
            <option key={team} value={team}>
              {team}
            </option>
          ))}
      </select>
    </div>
  )
}
