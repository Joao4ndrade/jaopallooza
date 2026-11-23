import type { EventInfo } from './types'

const TIME_ZONE = 'America/Sao_Paulo'

export const EM_BREVE = 'Em breve'

export function eventWhen(event: EventInfo | null): { date: string; time: string; weekday: string } | null {
  if (!event?.starts_at) return null
  const start = new Date(event.starts_at)
  const date = new Intl.DateTimeFormat('pt-BR', { day: 'numeric', month: 'long', timeZone: TIME_ZONE }).format(start)
  const time = new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit', timeZone: TIME_ZONE }).format(start)
  const weekday = new Intl.DateTimeFormat('pt-BR', { weekday: 'long', year: 'numeric', timeZone: TIME_ZONE }).format(start)
  return { date, time, weekday }
}

export function formatTime(iso: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: TIME_ZONE,
  }).format(new Date(iso))
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/)
  const first = parts[0]?.[0] ?? '?'
  const last = parts.length > 1 ? parts[parts.length - 1][0] : ''
  return (first + last).toUpperCase()
}

const AVATAR_COLORS = ['#c81e15', '#121212', '#e3261c', '#7d120c', '#3d3d3d', '#a3170f']

export function avatarColor(name: string): string {
  let hash = 0
  for (const char of name) hash = (hash * 31 + char.charCodeAt(0)) | 0
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length]
}

export function plural(count: number, singular: string, pluralForm: string): string {
  return `${count} ${count === 1 ? singular : pluralForm}`
}
