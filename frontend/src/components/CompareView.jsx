import { useState } from 'react'
import { api } from '../api/client'
import LoadingSpinner from './LoadingSpinner'

export default function CompareView({ teams }) {
  const [pairs, setPairs] = useState([
    ['Argentina', 'France'],
    ['Brazil', 'England'],
  ])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  function updatePair(index, field, value) {
    setPairs((prev) => {
      const next = prev.map((p) => [...p])
      next[index][field === 'a' ? 0 : 1] = value
      return next
    })
  }

  function addPair() {
    if (pairs.length >= 4) return
    setPairs((prev) => [...prev, ['Spain', 'Germany']])
  }

  async function handleCompare() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.compare(pairs)
      setResult(data)
    } catch (err) {
      setError(err.message)
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <section className="wc-card p-5 sm:p-6">
        <h2 className="text-lg font-semibold mb-1">Compare matchups</h2>
        <p className="text-muted text-sm mb-5">
          Side-by-side predictions for 2–4 fixtures using the same ML ensemble.
        </p>

        <div className="space-y-3 mb-5">
          {pairs.map((pair, i) => (
            <div key={i} className="flex flex-wrap items-center gap-2">
              <select
                value={pair[0]}
                onChange={(e) => updatePair(i, 'a', e.target.value)}
                className="flex-1 min-w-[120px] bg-pitch border border-white/15 rounded-lg px-3 py-2 text-sm"
              >
                {teams.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <span className="text-muted text-sm">vs</span>
              <select
                value={pair[1]}
                onChange={(e) => updatePair(i, 'b', e.target.value)}
                className="flex-1 min-w-[120px] bg-pitch border border-white/15 rounded-lg px-3 py-2 text-sm"
              >
                {teams.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleCompare}
            disabled={loading}
            className="px-5 py-2.5 rounded-lg bg-accent text-pitch font-semibold text-sm hover:bg-accent-dim disabled:opacity-50"
          >
            {loading ? 'Comparing…' : 'Compare matchups'}
          </button>
          {pairs.length < 4 && (
            <button
              type="button"
              onClick={addPair}
              className="px-4 py-2.5 rounded-lg border border-white/15 text-sm text-muted hover:text-white"
            >
              + Add matchup
            </button>
          )}
        </div>
      </section>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
          {error}
        </div>
      )}

      {loading && <LoadingSpinner />}

      {result && !loading && (
        <>
          <div className="grid sm:grid-cols-2 gap-4">
            {result.matchups.map((m) => (
              <CompareCard key={`${m.team_a}-${m.team_b}`} matchup={m} />
            ))}
          </div>
          {result.model_info && (
            <p className="text-center text-xs text-muted">
              Model: {result.model_info.probability_model?.replace(/_/g, ' ')} ·{' '}
              {result.model_info.feature_source} features
            </p>
          )}
        </>
      )}
    </div>
  )
}

function CompareCard({ matchup }) {
  const { team_a, team_b, probabilities, predicted_score, confidence, favored_team } = matchup
  const probs = [
    { label: team_a, value: probabilities.team_a_win },
    { label: 'Draw', value: probabilities.draw },
    { label: team_b, value: probabilities.team_b_win },
  ]

  return (
    <div className="wc-card p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold">
          {team_a} vs {team_b}
        </h3>
        <span className="text-xs px-2 py-1 rounded-full bg-white/5 text-muted">{confidence}</span>
      </div>
      <p className="text-2xl font-bold text-accent mb-3 tabular-nums">
        {predicted_score.team_a} – {predicted_score.team_b}
      </p>
      <p className="text-sm text-muted mb-3">
        Favored: <span className="text-white font-medium">{favored_team}</span>
      </p>
      <div className="space-y-2">
        {probs.map((p) => (
          <div key={p.label} className="flex items-center gap-2 text-xs">
            <span className="w-24 truncate text-muted">{p.label}</span>
            <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
              <div className="h-full bg-accent rounded-full" style={{ width: `${p.value}%` }} />
            </div>
            <span className="w-10 text-right tabular-nums">{p.value}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}
