/** Subtle football / soccer ball outline for branding */
export default function FootballIcon({ className = 'w-5 h-5', ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.25"
      className={className}
      aria-hidden
      {...props}
    >
      <circle cx="12" cy="12" r="10" />
      <path
        d="M12 2.5 14.8 8.2 12 12 9.2 8.2 12 2.5zM12 12l2.8 5.7L12 21.5 9.2 17.7 12 12zM2.5 12l5.7-2.8L12 12 6.3 14.8 2.5 12zM21.5 12l-5.7-2.8L12 12l5.7 2.8 21.5 12z"
        strokeLinejoin="round"
        opacity="0.55"
      />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" opacity="0.4" />
    </svg>
  )
}
