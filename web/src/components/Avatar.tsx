import { useState } from 'react'
import { photoSrc } from '../lib/api'
import { avatarColor, initials } from '../lib/format'

const SIZES = {
  sm: 'size-9 text-sm',
  md: 'size-11 text-base',
  lg: 'size-20 text-3xl',
}

interface AvatarProps {
  name: string
  photoUrl?: string | null
  size?: keyof typeof SIZES
  className?: string
}

/** Foto de perfil; sem foto (ou se ela falhar ao carregar), mostra as iniciais. */
export function Avatar({ name, photoUrl, size = 'md', className = '' }: AvatarProps) {
  const [brokenUrl, setBrokenUrl] = useState<string | null>(null)

  if (photoUrl && photoUrl !== brokenUrl) {
    return (
      <img
        src={photoSrc(photoUrl)}
        alt=""
        aria-hidden
        loading="lazy"
        decoding="async"
        onError={() => setBrokenUrl(photoUrl)}
        className={`shrink-0 rounded-full bg-surface object-cover ${SIZES[size]} ${className}`}
      />
    )
  }

  return (
    <span
      aria-hidden
      className={`grid shrink-0 place-items-center rounded-full font-bold text-white ${SIZES[size]} ${className}`}
      style={{ backgroundColor: avatarColor(name) }}
    >
      {initials(name)}
    </span>
  )
}
