import { useEffect, useState } from 'react'
import { api } from './api'

type NameCheck =
  | { status: 'idle' }
  | { status: 'checking' }
  | { status: 'available' | 'taken'; message: string }

interface Result {
  query: string
  available: boolean
  message: string
}

/** Pergunta à API, enquanto a pessoa digita, se o nome já está em uso (com debounce). */
export function useNameCheck(name: string, enabled: boolean): NameCheck {
  const query = name.trim().replace(/\s+/g, ' ')
  const [result, setResult] = useState<Result | null>(null)
  const active = enabled && query.length >= 2

  useEffect(() => {
    if (!active) return
    let current = true
    const timer = setTimeout(() => {
      api<Omit<Result, 'query'>>(`/auth/name-available?name=${encodeURIComponent(query)}`)
        .then((r) => {
          if (current) setResult({ query, ...r })
        })
        .catch(() => undefined) // sem resposta: o cadastro valida no envio de qualquer jeito
    }, 400)
    return () => {
      current = false
      clearTimeout(timer)
    }
  }, [query, active])

  if (!active) return { status: 'idle' }
  if (result?.query !== query) return { status: 'checking' }
  return { status: result.available ? 'available' : 'taken', message: result.message }
}
