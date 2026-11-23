import { Link } from 'react-router-dom'

export function Logo({ className = '' }: { className?: string }) {
  return (
    <Link to="/" className={`inline-flex items-center gap-2 ${className}`} aria-label="JAOPALLOOZA, início">
      <span className="grid size-9 place-items-center rounded-xl bg-brand-600 font-display text-xl text-white shadow-sm">
        J
      </span>
      <span className="font-display text-2xl tracking-wide text-brand-600">JAOPALLOOZA</span>
    </Link>
  )
}
