export default function TeamReportCard({ report }) {
  return (
    <article className="bg-pitch rounded-xl p-5 border border-white/10 h-full">
      <h3 className="text-xl font-bold mb-3">{report.name}</h3>

      <div className="mb-4">
        <p className="text-xs text-accent font-semibold uppercase tracking-wide mb-1">Style of play</p>
        <p className="text-sm text-white/85 leading-relaxed">{report.style_of_play}</p>
      </div>

      <TagList title="Strengths" items={report.strengths} color="text-accent" />
      <TagList title="Weaknesses" items={report.weaknesses} color="text-red-400" />

      <div className="mb-4">
        <p className="text-xs text-muted font-semibold uppercase tracking-wide mb-2">Key players</p>
        <div className="flex flex-wrap gap-2">
          {report.key_players.map((p) => (
            <span key={p} className="px-2.5 py-1 rounded-lg bg-white/5 text-sm border border-white/10">
              {p}
            </span>
          ))}
        </div>
      </div>

      <div className="mb-4 p-3 rounded-lg bg-white/5 border border-white/10">
        <p className="text-xs text-muted font-semibold uppercase tracking-wide mb-1">Injury / team news</p>
        <p className="text-sm text-white/70">{report.injury_news}</p>
      </div>

      <div>
        <p className="text-xs text-gold font-semibold uppercase tracking-wide mb-1">Why it matters</p>
        <p className="text-sm text-white/85 leading-relaxed">{report.why_it_matters}</p>
      </div>
    </article>
  )
}

function TagList({ title, items, color }) {
  return (
    <div className="mb-4">
      <p className="text-xs text-muted font-semibold uppercase tracking-wide mb-2">{title}</p>
      <ul className="space-y-1">
        {items.map((item) => (
          <li key={item} className={`text-sm flex items-center gap-2 ${color}`}>
            <span className="w-1 h-1 rounded-full bg-current" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}
