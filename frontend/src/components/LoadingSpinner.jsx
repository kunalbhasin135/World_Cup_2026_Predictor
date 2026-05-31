export default function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-4">
      <div className="w-12 h-12 border-4 border-accent/30 border-t-accent rounded-full animate-spin" />
      <p className="text-muted text-sm">Running prediction engine…</p>
    </div>
  )
}
