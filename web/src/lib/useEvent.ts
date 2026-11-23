import { useEffect, useState } from 'react'
import { api } from './api'
import type { EventInfo } from './types'

// Cache em memória: trocar de aba não pisca "carregando" toda hora.
let cached: EventInfo | null = null

export function useEvent() {
  const [event, setEvent] = useState<EventInfo | null>(cached)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    api<EventInfo>('/event')
      .then((fresh) => {
        cached = fresh
        if (active) setEvent(fresh)
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : 'Erro ao carregar o evento.')
      })
    return () => {
      active = false
    }
  }, [])

  return { event, error }
}
