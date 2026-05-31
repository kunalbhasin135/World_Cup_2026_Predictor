import { useMemo, useState } from 'react'
import { api } from '../api/client'
import LoadingSpinner from './LoadingSpinner'
import TournamentBracket from './TournamentBracket'

const KNOCKOUT_ROUNDS = [
  { key: 'Round of 32', label: 'Round of 32', short: 'R32' },
  { key: 'Round of 16', label: 'Round of 16', short: 'R16' },
  { key: 'Quarter-finals', label: 'Quarter-finals', short: 'QF' },
  { key: 'Semi-finals', label: 'Semi-finals', short: 'SF' },
  { key: 'Final', label: 'Final', short: 'F' },
  { key: 'Third place', label: 'Third-place play-off', short: '3P' },
]

export default function WhatIfPanel({ baseBracket, onResult }) {
  const [overrides, setOverrides] = useState({})
  const [activeRound, setActiveRound] = useState('Round of 32')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [showResultBracket, setShowResultBracket] = useState(false)

  const allMatches = useMemo(() => {
    if (!baseBracket?.knockout_rounds) return []
    const list = []
    for (const { key, label } of KNOCKOUT_ROUNDS) {
      const matches = baseBracket.knockout_rounds[key] || []
      for (const m of matches) {
        list.push({ ...m, roundLabel: label, roundKey: key })
      }
    }
    return list
  }, [baseBracket])

  const matchesByRound = useMemo(() => {
    const map = {}
    for (const { key } of KNOCKOUT_ROUNDS) {
      map[key] = allMatches.filter((m) => m.roundKey === key)
    }
    return map
  }, [allMatches])

  const activeMatches = matchesByRound[activeRound] || []

  if (!baseBracket?.knockout_rounds) return null

  function setOverride(matchId, team) {
    setOverrides((prev) => ({ ...prev, [matchId]: team }))
  }

  function clearOverride(matchId) {
    setOverrides((prev) => {
      const next = { ...prev }
      delete next[matchId]
      return next
    })
  }

  function clearAll() {
    setOverrides({})
    setResult(null)
    onResult?.(null)
  }

  async function runWhatIf() {
    if (Object.keys(overrides).length === 0) return
    setLoading(true)
    setError(null)
    try {
      const data = await api.whatIfBracket(overrides)
      setResult(data)
      onResult?.(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const overrideEntries = Object.entries(overrides)

  return (
    <section className="wc-card overflow-hidden border-accent/15">
      {/* Header */}
      <div className="px-5 sm:px-6 py-5 border-b border-white/10 bg-accent/5">
        <h2 className="text-lg font-semibold mb-1">What-if scenario builder</h2>
        <p className="text-muted text-sm max-w-2xl">
          Pick a different winner for any knockout match (R32 through the final). Unchanged
          matches still use ML predictions. Later rounds update automatically based on your picks.
        </p>
        <ol className="mt-3 text-xs text-muted space-y-1 list-decimal list-inside sm:flex sm:gap-6 sm:list-none">
          <li>
            <span className="font-medium text-white/80">1.</span> Choose a round tab
          </li>
          <li>
            <span className="font-medium text-white/80">2.</span> Click the team you want to win
          </li>
          <li>
            <span className="font-medium text-white/80">3.</span> Run scenario
          </li>
        </ol>
      </div>

      {/* Selected overrides */}
      {overrideEntries.length > 0 && (
        <div className="px-5 sm:px-6 py-3 border-b border-white/10 bg-pitch/50">
          <p className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">
            Your picks ({overrideEntries.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {overrideEntries.map(([matchId, team]) => {
              const match = allMatches.find((m) => m.match_id === matchId)
              const modelWinner = match?.predicted_winner
              const changed = modelWinner && modelWinner !== team
              return (
                <button
                  key={matchId}
                  type="button"
                  onClick={() => clearOverride(matchId)}
                  className={`inline-flex items-center gap-1.5 pl-2.5 pr-1.5 py-1 rounded-full text-xs border transition-colors ${
                    changed
                      ? 'border-gold/40 bg-gold/10 text-gold'
                      : 'border-accent/30 bg-accent/10 text-accent'
                  }`}
                  title="Click to remove"
                >
                  <span className="font-mono text-muted">{matchId}</span>
                  <span className="font-semibold">{team}</span>
                  {changed && <span className="text-[10px] opacity-80">≠ model</span>}
                  <span className="ml-0.5 opacity-60 hover:opacity-100">×</span>
                </button>
              )
            })}
            <button
              type="button"
              onClick={clearAll}
              className="text-xs text-muted hover:text-white px-2 py-1"
            >
              Clear all
            </button>
          </div>
        </div>
      )}

      {/* Round tabs */}
      <div className="px-3 sm:px-4 pt-3 flex gap-1 overflow-x-auto border-b border-white/10">
        {KNOCKOUT_ROUNDS.map(({ key, short }) => {
          const count = matchesByRound[key]?.length || 0
          const picksInRound = (matchesByRound[key] || []).filter((m) => overrides[m.match_id])
            .length
          return (
            <button
              key={key}
              type="button"
              onClick={() => setActiveRound(key)}
              className={`shrink-0 px-3 py-2 text-xs sm:text-sm font-semibold rounded-t-lg border-b-2 transition-colors ${
                activeRound === key
                  ? 'border-accent text-accent bg-white/5'
                  : 'border-transparent text-muted hover:text-white'
              }`}
            >
              {short}
              <span className="ml-1 opacity-60">({count})</span>
              {picksInRound > 0 && (
                <span className="ml-1 inline-flex w-4 h-4 items-center justify-center rounded-full bg-accent text-pitch text-[10px]">
                  {picksInRound}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Match grid */}
      <div className="p-4 sm:p-5 max-h-[420px] overflow-y-auto">
        <p className="text-sm font-medium mb-3 text-white/90">
          {KNOCKOUT_ROUNDS.find((r) => r.key === activeRound)?.label}
          <span className="text-muted font-normal ml-2">
            — click a team to force them through
          </span>
        </p>
        <div className="grid sm:grid-cols-2 gap-3">
          {activeMatches.map((match) => (
            <MatchPicker
              key={match.match_id}
              match={match}
              override={overrides[match.match_id]}
              onPick={setOverride}
              onClear={() => clearOverride(match.match_id)}
            />
          ))}
        </div>
        {activeMatches.length === 0 && (
          <p className="text-muted text-sm text-center py-8">No matches in this round.</p>
        )}
      </div>

      {/* Actions */}
      <div className="px-5 sm:px-6 py-4 border-t border-white/10 flex flex-wrap items-center gap-3 bg-pitch/30">
        <button
          type="button"
          onClick={runWhatIf}
          disabled={loading || overrideEntries.length === 0}
          className="px-5 py-2.5 rounded-xl bg-accent text-pitch font-semibold text-sm disabled:opacity-40 hover:bg-accent-dim transition-colors"
        >
          {loading ? 'Simulating…' : 'Run what-if scenario'}
        </button>
        <button
          type="button"
          onClick={clearAll}
          className="px-4 py-2.5 rounded-xl border border-white/15 text-sm text-muted hover:text-white"
        >
          Reset everything
        </button>
        {overrideEntries.length === 0 && (
          <span className="text-xs text-muted">Select at least one match winner above</span>
        )}
      </div>

      {error && (
        <p className="px-5 pb-4 text-red-300 text-sm">{error}</p>
      )}
      {loading && (
        <div className="px-5 pb-5">
          <LoadingSpinner />
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="border-t border-accent/20 bg-accent/5 px-5 sm:px-6 py-5 space-y-4">
          <h3 className="font-semibold">Scenario result</h3>
          <div className="grid sm:grid-cols-2 gap-4">
            <OutcomeCard
              label="Original prediction"
              champion={baseBracket.champion}
              runnerUp={baseBracket.runner_up}
              muted
            />
            <OutcomeCard
              label="Your what-if"
              champion={result.champion}
              runnerUp={result.runner_up}
              highlight
            />
          </div>
          {result.champion !== baseBracket.champion && (
            <p className="text-sm text-gold">
              Champion changed: {baseBracket.champion} →{' '}
              <strong>{result.champion}</strong>
            </p>
          )}
          <button
            type="button"
            onClick={() => setShowResultBracket((v) => !v)}
            className="text-sm text-accent hover:underline"
          >
            {showResultBracket ? 'Hide' : 'Show'} full what-if bracket
          </button>
          {showResultBracket && (
            <TournamentBracket bracketTree={result.bracket_tree} champion={result.champion} />
          )}
        </div>
      )}
    </section>
  )
}

function MatchPicker({ match, override, onPick, onClear }) {
  const { match_id, team_a, team_b, predicted_winner, predicted_score, roundLabel } = match
  const hasOverride = Boolean(override)
  const differsFromModel = hasOverride && override !== predicted_winner

  return (
    <div
      className={`rounded-xl border p-3 transition-colors ${
        hasOverride
          ? differsFromModel
            ? 'border-gold/40 bg-gold/5'
            : 'border-accent/40 bg-accent/5'
          : 'border-white/10 bg-pitch/40'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] font-mono text-muted uppercase">{match_id}</span>
        {hasOverride && (
          <button
            type="button"
            onClick={onClear}
            className="text-[10px] text-muted hover:text-white"
          >
            Undo
          </button>
        )}
      </div>

      <TeamOption
        name={team_a}
        score={predicted_score.team_a}
        isModelPick={predicted_winner === team_a && !hasOverride}
        isSelected={override === team_a}
        isModelWinner={predicted_winner === team_a}
        onSelect={() => onPick(match_id, team_a)}
      />

      <div className="text-center text-[10px] text-muted py-0.5 font-semibold">VS</div>

      <TeamOption
        name={team_b}
        score={predicted_score.team_b}
        isModelPick={predicted_winner === team_b && !hasOverride}
        isSelected={override === team_b}
        isModelWinner={predicted_winner === team_b}
        onSelect={() => onPick(match_id, team_b)}
      />

      {!hasOverride && (
        <p className="mt-2 text-[10px] text-center text-muted">
          Model picks <span className="text-white/80 font-medium">{predicted_winner}</span>
        </p>
      )}
      {differsFromModel && (
        <p className="mt-2 text-[10px] text-center text-gold">
          Upset vs model ({predicted_winner} → {override})
        </p>
      )}
    </div>
  )
}

function TeamOption({ name, score, isSelected, isModelWinner, onSelect }) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
        isSelected
          ? 'bg-accent text-pitch font-semibold ring-2 ring-accent/50'
          : isModelWinner
            ? 'bg-white/5 border border-white/10 hover:bg-white/10'
            : 'bg-transparent border border-transparent hover:bg-white/5'
      }`}
    >
      <span className="truncate text-left">{name}</span>
      <span className="flex items-center gap-2 shrink-0">
        {isModelWinner && !isSelected && (
          <span className="text-[9px] uppercase tracking-wide text-accent/80">ML</span>
        )}
        <span className={`tabular-nums ${isSelected ? '' : 'text-muted'}`}>{score}</span>
      </span>
    </button>
  )
}

function OutcomeCard({ label, champion, runnerUp, highlight, muted }) {
  return (
    <div
      className={`rounded-xl p-4 border ${
        highlight ? 'border-accent/30 bg-accent/10' : 'border-white/10 bg-pitch/50'
      }`}
    >
      <p className="text-xs text-muted uppercase tracking-wide mb-2">{label}</p>
      <p className={`text-xl font-bold ${muted ? 'text-white/70' : 'text-accent'}`}>{champion}</p>
      <p className="text-xs text-muted mt-1">Runner-up: {runnerUp}</p>
    </div>
  )
}
