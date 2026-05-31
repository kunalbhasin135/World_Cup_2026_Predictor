export default function ExplanationSection({ reasons }) {
  return (
    <section className="wc-card p-6 shadow-xl">
      <h2 className="text-lg font-semibold mb-4">Why the model predicted this</h2>
      <ul className="space-y-3">
        {reasons.map((reason, i) => (
          <li key={i} className="flex gap-3 text-sm leading-relaxed">
            <span className="shrink-0 w-6 h-6 rounded-full bg-accent/20 text-accent flex items-center justify-center text-xs font-bold">
              {i + 1}
            </span>
            <span className="text-white/90">{reason}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
