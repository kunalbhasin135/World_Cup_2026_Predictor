import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import LoadingSpinner from './LoadingSpinner'
import TournamentBracket from './TournamentBracket'
import MonteCarloSection from './MonteCarloSection'
import WhatIfPanel from './WhatIfPanel'
import BracketExportButton from './BracketExportButton'

export default function BracketView() {
  const [bracket, setBracket] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const bracketRef = useRef(null)

  useEffect(() => {
    api
      .getBracket()
      .then(setBracket)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div>
        <p className="text-center text-muted text-sm mb-4">
          Running 100+ ML predictions (ensemble + historical features) — may take 15–30 seconds…
        </p>
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
        {error}
      </div>
    )
  }

  if (!bracket) return null

  const thirdPlace = bracket.knockout_rounds?.['Third place']

  return (
    <div className="space-y-8">
      <section className="wc-section-top wc-champion-band rounded-2xl pt-6 p-6 sm:p-8 text-center">
        <p className="text-gold text-xs font-semibold uppercase tracking-[0.2em] mb-2 font-display">
          {bracket.tournament}
        </p>
        <h2 className="text-3xl sm:text-4xl font-bold mb-2 font-display">
          Predicted champion:{' '}
          <span className="text-trophy">{bracket.champion}</span>
        </h2>
        <p className="text-muted text-sm mb-4">
          Runner-up: {bracket.runner_up}
          {bracket.third_place ? ` · Third: ${bracket.third_place}` : ''}
        </p>

        <div className="flex flex-wrap justify-center gap-2 mb-4">
          <Badge label="Model" value={bracket.prediction_model?.replace(/_/g, ' ')} />
          <Badge label="Features" value={bracket.feature_source} />
          {bracket.draw_last_updated && (
            <Badge label="Draw updated" value={bracket.draw_last_updated} />
          )}
        </div>

        {bracket.top_contenders?.length > 0 && (
          <div className="flex flex-wrap justify-center gap-2">
            {bracket.top_contenders.map((c) => (
              <span
                key={c.team}
                className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm"
              >
                {c.team}{' '}
                <span className="text-muted">STR {c.strength_rating}</span>
              </span>
            ))}
          </div>
        )}
        <p className="text-xs text-muted mt-4 max-w-2xl mx-auto">{bracket.note}</p>
      </section>

      <MonteCarloSection />

      <WhatIfPanel baseBracket={bracket} />

      <div ref={bracketRef}>
        <div className="flex justify-end mb-3">
          <BracketExportButton targetRef={bracketRef} />
        </div>
        <TournamentBracket bracketTree={bracket.bracket_tree} champion={bracket.champion} />
      </div>

      {thirdPlace?.length > 0 && (
        <section className="wc-card p-4">
          <h3 className="font-semibold mb-2 text-muted font-display uppercase tracking-wide text-sm">Third-place play-off</h3>
          {thirdPlace.map((m) => (
            <p key={m.match_id} className="text-sm">
              <span className={m.predicted_winner === m.team_a ? 'text-accent font-semibold' : ''}>
                {m.team_a}
              </span>{' '}
              {m.predicted_score.team_a}–{m.predicted_score.team_b}{' '}
              <span className={m.predicted_winner === m.team_b ? 'text-accent font-semibold' : ''}>
                {m.team_b}
              </span>{' '}
              → {m.predicted_winner}
            </p>
          ))}
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold mb-4 font-display tracking-wide">Group stage predictions</h2>
        <p className="text-muted text-sm mb-5">{bracket.format}</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {bracket.groups.map((g) => (
            <GroupCard key={g.group} group={g} />
          ))}
        </div>
      </section>
    </div>
  )
}

function Badge({ label, value }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs capitalize">
      <span className="text-muted">{label}:</span>
      <span className="text-accent font-medium">{value}</span>
    </span>
  )
}

function GroupCard({ group }) {
  return (
    <div className="wc-card overflow-hidden rounded-xl">
      <div className="px-4 py-2 bg-accent/10 border-b border-pitch-line/50 font-bold font-display tracking-wider">
        Group {group.group}
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-muted text-xs">
            <th className="text-left px-3 py-2">#</th>
            <th className="text-left px-1 py-2">Team</th>
            <th className="px-2 py-2">GD</th>
            <th className="px-2 py-2">Pts</th>
          </tr>
        </thead>
        <tbody>
          {group.standings.map((s) => (
            <tr
              key={s.team}
              className={`border-t border-white/5 ${s.advances ? 'bg-accent/5' : ''}`}
            >
              <td className="px-3 py-2 text-muted">{s.position}</td>
              <td className="px-1 py-2 font-medium">
                {s.team}
                {s.advances && <span className="ml-1 text-accent text-xs">✓</span>}
              </td>
              <td className="px-2 py-2 text-center">
                {s.goal_difference >= 0 ? '+' : ''}
                {s.goal_difference}
              </td>
              <td className="px-2 py-2 text-center font-semibold">{s.points}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
