export default function MatchupAnalysis({ text }) {
  return (
    <section className="wc-card border-accent/20 p-6 shadow-xl bg-gradient-to-br from-pitch-card to-pitch-light">
      <h2 className="text-lg font-semibold mb-3 text-gold">Why this matchup matters</h2>
      <p className="text-sm sm:text-base text-white/85 leading-relaxed">{text}</p>
    </section>
  )
}
