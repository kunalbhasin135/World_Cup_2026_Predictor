import html2canvas from 'html2canvas'

export async function exportBracketImage(element, filename = 'wc2026-bracket.png') {
  if (!element) return
  const canvas = await html2canvas(element, {
    backgroundColor: getComputedStyle(document.body).backgroundColor,
    scale: 2,
    useCORS: true,
  })
  const link = document.createElement('a')
  link.download = filename
  link.href = canvas.toDataURL('image/png')
  link.click()
}

export default function BracketExportButton({ targetRef }) {
  async function handleExport() {
    const el = targetRef?.current
    if (!el) return
    try {
      await exportBracketImage(el)
    } catch {
      alert('Could not export bracket image. Try again.')
    }
  }

  return (
    <button
      type="button"
      onClick={handleExport}
      className="px-4 py-2 rounded-lg border border-white/15 text-sm hover:bg-white/5 text-muted hover:text-white"
    >
      Export bracket PNG
    </button>
  )
}
