import { useEffect, useState } from 'react'
import { api } from './api/client'
import Header from './components/Header'
import TabNav from './components/TabNav'
import Hero from './components/Hero'
import TeamSelector from './components/TeamSelector'
import PredictionCard from './components/PredictionCard'
import ExplanationSection from './components/ExplanationSection'
import TacticalMatchup from './components/TacticalMatchup'
import FormComparison from './components/FormComparison'
import TeamReportCard from './components/TeamReportCard'
import MatchupAnalysis from './components/MatchupAnalysis'
import PredictedScorers from './components/PredictedScorers'
import PlayerAnalysisSection from './components/PlayerAnalysisSection'
import ModelTransparencyPanel from './components/ModelTransparencyPanel'
import ImpliedOddsPanel from './components/ImpliedOddsPanel'
import SquadInjuriesPanel from './components/SquadInjuriesPanel'
import BracketView from './components/BracketView'
import CompareView from './components/CompareView'
import LoadingSpinner from './components/LoadingSpinner'

export default function App() {
  const [tab, setTab] = useState('match')
  const [teams, setTeams] = useState([])
  const [status, setStatus] = useState(null)
  const [teamA, setTeamA] = useState('Spain')
  const [teamB, setTeamB] = useState('Portugal')
  const [knockout, setKnockout] = useState(true)
  const [matchRound, setMatchRound] = useState('Semi-finals')
  const [prediction, setPrediction] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [initError, setInitError] = useState(null)

  useEffect(() => {
    Promise.all([api.getTeams(), api.getDataStatus()])
      .then(([teamsRes, statusRes]) => {
        setTeams(teamsRes.teams)
        setStatus(statusRes)
      })
      .catch((err) => setInitError(err.message))
  }, [])

  async function handlePredict() {
    setLoading(true)
    setError(null)
    try {
      const result = await api.predict(teamA, teamB, knockout, matchRound)
      setPrediction(result)
    } catch (err) {
      setError(err.message)
      setPrediction(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen pb-16 flex flex-col">
      <Header status={status} />

      <main className="flex-1 max-w-6xl mx-auto px-4 py-8 space-y-6 w-full">
        {initError && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
            Cannot reach API — start the backend with{' '}
            <code className="text-red-200">uvicorn app.main:app --reload --port 8000</code>
            <br />
            <span className="text-red-400/80">{initError}</span>
          </div>
        )}

        {!initError && <Hero status={status} />}

        <TabNav active={tab} onChange={setTab} />

        {tab === 'match' && (
          <>
            <TeamSelector
              teams={teams}
              teamA={teamA}
              teamB={teamB}
              knockout={knockout}
              matchRound={matchRound}
              onKnockoutChange={setKnockout}
              onMatchRoundChange={setMatchRound}
              onTeamAChange={setTeamA}
              onTeamBChange={setTeamB}
              onPredict={handlePredict}
              loading={loading}
            />

            {error && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
                {error}
              </div>
            )}

            {loading && <LoadingSpinner />}

            {prediction && !loading && (
              <div className="space-y-6">
                <PredictionCard prediction={prediction} />
                <ImpliedOddsPanel
                  impliedOdds={prediction.implied_odds}
                  bracketContext={prediction.bracket_context}
                  teamA={prediction.team_a}
                  teamB={prediction.team_b}
                  matchRound={matchRound}
                />
                <SquadInjuriesPanel
                  squadStatus={prediction.squad_status}
                  teamA={prediction.team_a}
                  teamB={prediction.team_b}
                />
                <ModelTransparencyPanel modelInfo={prediction.model_info} />
                <PredictedScorers scorers={prediction.predicted_scorers} />
                <ExplanationSection reasons={prediction.reasons} />
                <FormComparison
                  teamA={prediction.team_a}
                  teamB={prediction.team_b}
                  recentForm={prediction.recent_form}
                />
                <TacticalMatchup bullets={prediction.tactical_matchup} />
                <PlayerAnalysisSection
                  teamA={prediction.team_a}
                  teamB={prediction.team_b}
                  playerAnalysis={prediction.player_analysis}
                />
                <section>
                  <h2 className="text-lg font-semibold mb-4">Team reports</h2>
                  <div className="grid md:grid-cols-2 gap-6">
                    <TeamReportCard report={prediction.team_reports[prediction.team_a]} />
                    <TeamReportCard report={prediction.team_reports[prediction.team_b]} />
                  </div>
                </section>
                <MatchupAnalysis text={prediction.matchup_analysis} />
              </div>
            )}

            {!prediction && !loading && !initError && teams.length > 0 && (
              <p className="text-center text-muted text-sm py-8">
                Select two teams and click <strong className="text-white">Predict Match</strong>{' '}
                to generate a scouting report.
              </p>
            )}
          </>
        )}

        {tab === 'compare' && !initError && <CompareView teams={teams} />}

        {tab === 'bracket' && !initError && <BracketView />}
      </main>

      <footer className="border-t border-pitch-line/40 py-6 text-center text-xs text-muted">
        <p className="font-display tracking-widest uppercase text-[10px] text-accent/80 mb-1">
          FIFA World Cup 2026
        </p>
        <p>ML predictions for portfolio demo · not affiliated with FIFA</p>
      </footer>
    </div>
  )
}
