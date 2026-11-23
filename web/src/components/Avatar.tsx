import { avatarColor, initials } from '../lib/format'

const SIZES = {
  sm: 'size-9 text-sm',
  md: 'size-11 text-base',
  lg: 'size-20 text-3xl',
}

export function Avatar({ name, size = 'md' }: { name: string; size?: keyof typeof SIZES }) {
  return (
    <span
      aria-hidden
      className={`grid shrink-0 place-items-center rounded-full font-bold text-white ${SIZES[size]}`}
      style={{ backgroundColor: avatarColor(name) }}
    >
      {initials(name)}
    </span>
  )
}
