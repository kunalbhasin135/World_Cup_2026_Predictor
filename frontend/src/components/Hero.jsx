import FootballIcon from './icons/FootballIcon'

export default function Hero({ status }) {
  const meta = status?.model_metadata

  return (
    <section className="wc-section-top relative overflow-hidden rounded-2xl wc-champion-band pt-6 p-8 sm:p-10 text-center">
      <div
        className="absolute inset-0 opacity-[0.07] pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle at 50% 50%, transparent 28%, rgba(45,184,122,0.4) 29%, transparent 30%),
            radial-gradient(circle at 50% 50%, transparent 68%, rgba(45,184,122,0.3) 69%, transparent 70%)`,
        }}
        aria-hidden
      />
      <div className="relative">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-gold/30 bg-gold/10 text-gold text-xs font-semibold uppercase tracking-widest mb-4 font-display">
          <FootballIcon className="w-3.5 h-3.5" />
          Tournament intelligence
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mb-3 font-display text-white">
          Predict every match. Simulate the full bracket.
        </h2>
        <p className="text-muted max-w-2xl mx-auto text-sm sm:text-base mb-6">
          Calibrated ensemble model trained on 49k+ international results — Elo ratings,
          form, head-to-head, and World Cup context on neutral ground.
        </p>
        <div className="flex flex-wrap justify-center gap-3 text-xs">
          {meta?.training_samples && (
            <StatPill label="Matches analyzed" value={meta.training_samples.toLocaleString()} />
          )}
          {meta?.test_accuracy && (
            <StatPill label="Model accuracy" value={`${(meta.test_accuracy * 100).toFixed(0)}%`} />
          )}
          {meta?.log_loss && <StatPill label="Log loss" value={meta.log_loss} />}
          {status?.teams_with_features && (
            <StatPill label="Teams profiled" value={status.teams_with_features} />
          )}
        </div>
      </div>
    </section>
  )
}

function StatPill({ label, value }) {
  return (
    <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-pitch-card/60 border border-pitch-line/50 backdrop-blur-sm">
      <span className="text-muted">{label}</span>
      <span className="text-accent font-semibold font-display text-sm">{value}</span>
    </span>
  )
}
