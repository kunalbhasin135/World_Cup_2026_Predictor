import { useEffect, useState } from 'react'
import { api } from '../api/client'
import LoadingSpinner from './LoadingSpinner'

export default function MonteCarloSection() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [simulations, setSimulations] = useState(500)

  useEffect(() => {
    setLoading(true)
    setError(null)
    api
      .getMonteCarlo(simulations)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [simulations])

  if (loading) {
    return (
      <section className="wc-card p-6">
        <p className="text-center text-muted text-sm mb-4">
          Running {simulations} Monte Carlo simulations (same ML model as bracket)…
        </p>
        <LoadingSpinner />
      </section>
    )
  }

  if (error) {
    return (
      <section className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
        {error}
      </section>
    )
  }

  if (!data) return null

  const maxPct = Math.max(...data.champion_odds.map((o) => o.champion_pct), 1)

  return (
    <section className="wc-card p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4 mb-5">
        <div>
          <h2 className="text-lg font-semibold mb-1">Monte Carlo champion odds</h2>
          <p className="text-muted text-sm mb-2">
            {data.simulations.toLocaleString()} probabilistic knockout runs · symmetric ML +
            strength-adjusted probabilities
          </p>
          <p className="text-sm">
            MC favorite:{' '}
            <span className="text-accent font-semibold">{data.simulated_champion_favorite}</span>
            <span className="text-muted"> · Deterministic bracket below: </span>
            <span className="font-semibold">{data.deterministic_champion}</span>
          </p>
        </div>
        <select
          value={simulations}
          onChange={(e) => setSimulations(Number(e.target.value))}
          className="bg-pitch border border-white/15 rounded-lg px-3 py-2 text-sm"
        >
          <option value={200}>200 sims</option>
          <option value={500}>500 sims</option>
          <option value={1000}>1,000 sims</option>
        </select>
      </div>

      <div className="space-y-2">
        {data.champion_odds.slice(0, 12).map((o) => (
          <div key={o.team} className="flex items-center gap-3 text-sm">
            <span className="w-28 truncate font-medium">{o.team}</span>
            <div className="flex-1 h-3 bg-white/5 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-accent/80 to-accent rounded-full"
                style={{ width: `${(o.champion_pct / maxPct) * 100}%` }}
              />
            </div>
            <span className="w-14 text-right tabular-nums text-accent font-semibold">
              {o.champion_pct}%
            </span>
            <span className="w-20 text-right text-xs text-muted hidden sm:inline">
              F: {o.finalist_pct}%
            </span>
          </div>
        ))}
      </div>
    </section>
  )
}
