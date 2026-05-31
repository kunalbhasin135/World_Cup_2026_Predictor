import { useMemo } from 'react'

const MATCH_HEIGHT = 56
const COLUMN_GAP = 40
const MATCH_WIDTH = 168

/**
 * Horizontal single-elimination bracket with SVG tree connectors.
 */
export default function TournamentBracket({ bracketTree, champion }) {
  const rounds = useMemo(() => {
    if (!bracketTree?.length) return []
    return bracketTree.filter((r) => r.round !== 'Third place')
  }, [bracketTree])

  const layout = useMemo(() => {
    if (!rounds.length) return null

    const roundLayouts = rounds.map((round, roundIdx) => {
      const count = round.matches.length
      const blockHeight = count * MATCH_HEIGHT + Math.max(0, count - 1) * _gapForCount(count)
      const gap = _gapForCount(count)

      const matches = round.matches.map((match, matchIdx) => {
        const top = matchIdx * (MATCH_HEIGHT + gap) + blockHeight / 2 - (rounds[0].matches.length * (MATCH_HEIGHT + _gapForCount(rounds[0].matches.length)) + (_gapForCount(rounds[0].matches.length) * (rounds[0].matches.length - 1))) / 2
        // Center entire bracket vertically based on R32 height
        const r32Count = rounds[0].matches.length
        const r32Block =
          r32Count * MATCH_HEIGHT + Math.max(0, r32Count - 1) * _gapForCount(r32Count)
        const centeredTop = matchIdx * (MATCH_HEIGHT + gap) + (r32Block - blockHeight) / 2
        return { match, top: centeredTop, matchIdx }
      })

      return { round, roundIdx, count, blockHeight, gap, matches, x: roundIdx * (MATCH_WIDTH + COLUMN_GAP) }
    })

    return roundLayouts
  }, [rounds])

  if (!layout?.length) return null

  const totalWidth = layout.length * (MATCH_WIDTH + COLUMN_GAP) + 80
  const r32Count = rounds[0].matches.length
  const totalHeight =
    r32Count * MATCH_HEIGHT + Math.max(0, r32Count - 1) * _gapForCount(r32Count) + 40

  const connectors = _buildConnectors(layout)

  return (
    <section className="wc-card p-4 sm:p-6 overflow-x-auto">
      <h2 className="text-lg font-semibold mb-1 font-display tracking-wide">Knockout bracket</h2>
      <p className="text-muted text-xs sm:text-sm mb-6">
        Official FIFA knockout paths (M73–M104) · ML picks each fixture · winners advance right
      </p>

      <div className="relative min-w-[960px]" style={{ width: totalWidth, height: totalHeight }}>
        <svg
          className="absolute inset-0 pointer-events-none"
          width={totalWidth}
          height={totalHeight}
          aria-hidden
        >
          {connectors.map((d, i) => (
            <path
              key={i}
              d={d}
              fill="none"
              stroke="rgba(255,255,255,0.18)"
              strokeWidth="1.5"
            />
          ))}
        </svg>

        {layout.map(({ round, matches, x }) => (
          <div
            key={round.round}
            className="absolute top-0"
            style={{ left: x, width: MATCH_WIDTH, height: totalHeight }}
          >
            <div
              className={`text-center text-xs font-semibold uppercase tracking-wide mb-3 px-2 py-1 rounded-lg font-display ${
                round.round === 'Final' ? 'bg-gold/15 text-gold border border-gold/25' : 'bg-white/5 text-muted border border-pitch-line/40'
              }`}
            >
              {round.round}
            </div>
            {matches.map(({ match, top }) => (
              <div
                key={match.match_id}
                className="absolute left-0 right-0"
                style={{ top: top + 28 }}
              >
                <MatchCard
                  match={match}
                  isFinal={round.round === 'Final'}
                  isChampion={round.round === 'Final' && match.predicted_winner === champion}
                />
              </div>
            ))}
          </div>
        ))}

        <div
          className="absolute flex flex-col items-center justify-center"
          style={{ left: layout.length * (MATCH_WIDTH + COLUMN_GAP), top: totalHeight / 2 - 40 }}
        >
          <span className="text-2xl mb-1" aria-hidden>
            🏆
          </span>
          <span className="text-xs text-muted uppercase tracking-wide">Champion</span>
          <span className="text-accent font-bold text-sm mt-1">{champion}</span>
        </div>
      </div>
    </section>
  )
}

function _gapForCount(count) {
  if (count >= 8) return 6
  if (count >= 4) return 20
  if (count >= 2) return 52
  return 0
}

function _buildConnectors(layout) {
  const paths = []
  const yOffset = 28

  for (let r = 0; r < layout.length - 1; r++) {
    const curr = layout[r]
    const next = layout[r + 1]
    const x1 = curr.x + MATCH_WIDTH
    const xMid = x1 + COLUMN_GAP / 2
    const x2 = next.x

    curr.matches.forEach(({ top, matchIdx }) => {
      const nextIdx = Math.floor(matchIdx / 2)
      if (nextIdx >= next.matches.length) return

      const y1 = top + yOffset + MATCH_HEIGHT / 2
      const y2 = next.matches[nextIdx].top + yOffset + MATCH_HEIGHT / 2

      // Only draw from even-indexed matches (top of pair) to avoid duplicate lines
      if (matchIdx % 2 === 0) {
        const pairMatch = curr.matches[matchIdx + 1]
        if (pairMatch) {
          const y1b = pairMatch.top + yOffset + MATCH_HEIGHT / 2
          const yMid = (y1 + y1b) / 2
          paths.push(
            `M ${x1} ${y1} H ${xMid} V ${yMid} H ${x2} V ${y2}`
          )
        } else {
          paths.push(`M ${x1} ${y1} H ${xMid} V ${y2} H ${x2}`)
        }
      }
    })
  }

  return paths
}

function MatchCard({ match, isFinal, isChampion }) {
  const { team_a, team_b, predicted_winner, predicted_score } = match

  return (
    <div
      className={`rounded-lg border overflow-hidden text-xs shadow-md ${
        isFinal ? 'border-gold/40 bg-gold/5' : 'border-white/15 bg-pitch'
      } ${isChampion ? 'ring-2 ring-accent/60' : ''}`}
    >
      <TeamRow
        name={team_a}
        score={predicted_score.team_a}
        isWinner={predicted_winner === team_a}
      />
      <div className="border-t border-white/10" />
      <TeamRow
        name={team_b}
        score={predicted_score.team_b}
        isWinner={predicted_winner === team_b}
      />
    </div>
  )
}

function TeamRow({ name, score, isWinner }) {
  return (
    <div
      className={`flex items-center justify-between px-2.5 py-2 ${
        isWinner ? 'bg-accent/15 font-semibold' : 'text-white/75'
      }`}
    >
      <span className={`truncate pr-2 ${isWinner ? 'text-accent' : ''}`}>{name}</span>
      <span className={`tabular-nums ${isWinner ? 'text-accent' : 'text-muted'}`}>{score}</span>
    </div>
  )
}
