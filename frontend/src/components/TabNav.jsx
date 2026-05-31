export default function TabNav({ active, onChange }) {
  const tabs = [
    { id: 'match', label: 'Match Predictor' },
    { id: 'compare', label: 'Compare' },
    { id: 'bracket', label: 'World Cup Bracket' },
  ]

  return (
    <nav
      className="flex gap-1 p-1.5 wc-card overflow-x-auto"
      role="tablist"
      aria-label="Main sections"
    >
      {tabs.map((tab) => {
        const isActive = active === tab.id
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            className={`flex-1 sm:flex-none px-4 sm:px-5 py-2.5 rounded-xl text-sm font-semibold transition-all whitespace-nowrap font-display tracking-wide ${
              isActive
                ? 'wc-tab-active text-accent shadow-sm'
                : 'text-muted hover:text-white hover:bg-white/5'
            }`}
          >
            {tab.label}
          </button>
        )
      })}
    </nav>
  )
}
