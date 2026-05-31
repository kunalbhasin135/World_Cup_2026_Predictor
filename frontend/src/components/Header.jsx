import { useTheme } from '../context/ThemeContext'
import FootballIcon from './icons/FootballIcon'

export default function Header({ status }) {
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="sticky top-0 z-50 border-b border-pitch-line/50 bg-pitch-light/90 backdrop-blur-md">
      <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-accent/60 to-transparent" />
      <div className="max-w-6xl mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-start gap-4">
          <div
            className="hidden sm:flex w-12 h-12 rounded-full items-center justify-center shrink-0 border border-accent/25 bg-accent/10 text-accent"
            aria-hidden
          >
            <FootballIcon className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-gold" aria-hidden />
              <p className="text-gold text-xs font-semibold tracking-[0.2em] uppercase font-display">
                FIFA World Cup 2026
              </p>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-gold" aria-hidden />
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight font-display text-white">
              Match Predictor
            </h1>
            <p className="text-muted text-sm mt-0.5">
              ML scouting · bracket simulation · tournament analytics
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {status && (
            <>
              <Badge label="Data" value={status.feature_source} />
              <Badge label="Model" value={status.probability_model?.replace(/_/g, ' ')} />
              {status.model_metadata?.test_accuracy && (
                <Badge
                  label="Accuracy"
                  value={`${(status.model_metadata.test_accuracy * 100).toFixed(0)}%`}
                />
              )}
            </>
          )}
          <button
            type="button"
            onClick={toggleTheme}
            className="px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-muted hover:text-white hover:border-accent/30 transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? 'Light' : 'Dark'}
          </button>
        </div>
      </div>
    </header>
  )
}

function Badge({ label, value }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-pitch-card/80 border border-pitch-line/60 text-xs">
      <span className="text-muted">{label}</span>
      <span className="text-accent font-medium capitalize">{value}</span>
    </span>
  )
}
