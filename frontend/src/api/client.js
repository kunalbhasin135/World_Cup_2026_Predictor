const API_BASE = import.meta.env.VITE_API_URL || '/api'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  getTeams: () => request('/teams'),
  getDataStatus: () => request('/data/status'),
  getBracket: () => request('/bracket/predictions'),
  getMonteCarlo: (simulations = 500, seed = 42) =>
    request(`/bracket/monte-carlo?simulations=${simulations}&seed=${seed}`),
  whatIfBracket: (overrides) =>
    request('/bracket/what-if', {
      method: 'POST',
      body: JSON.stringify({ overrides }),
    }),
  predict: (teamA, teamB, knockout = false, matchRound = null) =>
    request('/predict', {
      method: 'POST',
      body: JSON.stringify({
        team_a: teamA,
        team_b: teamB,
        knockout,
        match_round: matchRound === 'Group stage' ? null : matchRound,
      }),
    }),
  compare: (matchups) =>
    request('/predict/compare', {
      method: 'POST',
      body: JSON.stringify({
        matchups: matchups.map(([team_a, team_b]) => ({ team_a, team_b })),
      }),
    }),
}
