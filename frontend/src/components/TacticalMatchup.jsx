export default function TacticalMatchup({ bullets }) {
  return (
    <section className="wc-card p-6 shadow-xl">
      <h2 className="text-lg font-semibold mb-4">Tactical matchup breakdown</h2>
      <ul className="space-y-4">
        {bullets.map((bullet, i) => (
          <li
            key={i}
            className="pl-4 border-l-2 border-accent/40 text-sm text-white/85 leading-relaxed"
          >
            {bullet}
          </li>
        ))}
      </ul>
    </section>
  )
}
